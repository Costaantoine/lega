import httpx, asyncio, logging, re, os
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)
_cache: Dict[str, tuple] = {}
DB_URL = os.getenv("DATABASE_URL", "postgresql://bvi_user:BviSecure2026!@db:5432/bvi_db")

# SearXNG — instance locale Docker (port 8888 sur host, port 8080 dans le réseau bvi-net)
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://bvi-searxng-1:8080")

_ALLOWED_TLDS = {'.fr', '.pt', '.es', '.de', '.be', '.ch', '.com', '.net', '.org', '.eu', '.uk'}

_TP_DOMAINS = [
    "machineryzone", "mascus", "europe-tp", "leboncoin", "tracteuroccasion",
    "agriaffaires", "tob.pt", "machinerytrader", "ironplanet", "ritchie",
    "komatsu", "caterpillar", "liebherr", "volvoce", "codimatra",
]

def _tld_ok(url: str) -> bool:
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ''
        parts = host.rstrip('.').split('.')
        return len(parts) >= 2 and ('.' + parts[-1]) in _ALLOWED_TLDS
    except Exception:
        return True

def _tp_domain_ok(url: str) -> bool:
    url_low = url.lower()
    return any(d in url_low for d in _TP_DOMAINS)

_LANG_LOCALE = {"fr": "fr-FR", "pt": "pt-PT", "en": "en-US", "es": "es-ES", "de": "de-DE"}

async def search_web(query: str, max_results: int = 5, lang: str = "fr") -> List[Dict]:
    """
    Recherche web via SearXNG local.
    Retourne une liste de {title, url, content} injectables dans un prompt LLM.
    Post-filtre : TLD whitelist + domaines TP connus. Fallback silencieux.
    """
    try:
        locale = _LANG_LOCALE.get(lang, "fr-FR")
        params = {
            "q": query,
            "format": "json",
            "language": locale,
            "locale": locale,
            "categories": "general",
            "engines": "bing,startpage,google",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{SEARXNG_URL}/search", params=params)
            if resp.status_code != 200:
                logger.warning(f"SearXNG HTTP {resp.status_code}")
                return []
            data = resp.json()
            all_results = data.get("results", [])
            results = []
            rejected = 0
            for r in all_results:
                url = r.get("url", "")
                # Filtre TLD : rejette finnois, chinois, japonais, etc.
                if not _tld_ok(url):
                    logger.debug(f"SearXNG TLD rejeté: {url[:60]}")
                    rejected += 1
                    continue
                # Log informatif si domaine hors TP (sans rejeter)
                if not _tp_domain_ok(url):
                    logger.debug(f"SearXNG domaine non-TP (conservé): {url[:60]}")
                results.append({
                    "title": r.get("title", "")[:120],
                    "url": url,
                    "content": r.get("content", "")[:300],
                })
                if len(results) >= max_results:
                    break
            if rejected:
                logger.info(f"SearXNG: {len(results)} retenus, {rejected} rejetés (TLD/domaine hors-scope)")
            return results
    except Exception as e:
        logger.warning(f"SearXNG indisponible: {e}")
        return []

def parse_robust(html: str, source_name: str) -> List[Dict]:
    """Parser hybride : CSS -> Fallback Regex -> Toujours un résultat"""
    listings = []
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Tentative CSS standard
    items = soup.select("article, .card, .listing, .item, .product, [class*='machine'], [class*='annonce'], [class*='offer'], [class*='ad']")[:20]
    for item in items:
        title_el = item.select_one("h1, h2, h3, h4, .title, [class*='title'], [class*='name'], [class*='model']")
        price_el = item.select_one(".price, [class*='price'], .montant, [class*='cost']")
        if title_el:
            title = re.sub(r'\s+', ' ', title_el.get_text(strip=True)[:120])
            price = price_el.get_text(strip=True)[:30] if price_el else "Nous consulter"
            if len(title) > 4:
                listings.append({"title": title, "price": price, "source": source_name})
    
    # 2. Fallback Regex si CSS vide (sites dynamiques/obfusqués)
    if not listings:
        text = soup.get_text(separator=" ", strip=True)
        # Patterns type "Volvo EC220 - 25 000 €" ou "Pelleteuse CAT 308 Prix: 18k€"
        matches = re.findall(r'([A-Z][A-Za-z0-9\s\-\.]{3,60}?)\s*[-|:|\|]\s*([\d\s€kK\.]+)', text)
        for title, price in matches[:12]:
            if any(k in title.lower() for k in ["pelleteuse", "chargeuse", "bulldozer", "grue", "volvo", "cat", "jcb", "komatsu", "liebherr", "engin"]):
                listings.append({"title": title.strip()[:100], "price": price.strip()[:30], "source": source_name})
                
    return listings[:8]

async def get_relevant_sources(query: str, limit: int = 8) -> List[Dict]:
    """Récupère les sources actives depuis PostgreSQL (ou fallback si DB non dispo)"""
    fallback = [{"url": "https://www.europe-tp.com", "category": "plateforme", "region": "europe"},
                {"url": "https://www.machineryzone.fr", "category": "plateforme", "region": "europe"}]
    try:
        # On utilise asyncpg (léger, rapide). Sera installé au rebuild.
        import asyncpg
        conn = await asyncpg.connect(DB_URL)
        sql = "SELECT url, category, region FROM sources WHERE status='active' ORDER BY created_at DESC LIMIT $1"
        rows = await conn.fetch(sql, limit)
        await conn.close()
        return [{"url": r[0], "category": r[1], "region": r[2]} for r in rows] if rows else fallback
    except Exception as e:
        logger.warning(f"DB non disponible, fallback activé: {e}")
        return fallback

async def fetch_page(url: str, timeout: float = 12.0) -> Optional[str]:
    if url in _cache and (asyncio.get_event_loop().time() - _cache[url][1]) < 180:
        return _cache[url][0]
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 LEGA-Bot/1.0", "Accept-Language": "fr-FR,fr;q=0.9,pt-PT;q=0.8", "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code >= 400: return None
            html = resp.text
            _cache[url] = (html, asyncio.get_event_loop().time())
            return html
    except Exception as e:
        logger.warning(f"Fetch échoué {url[:60]}: {e}")
        return None


def parse_codimatra(html: str) -> list:
    """Parser dédié pour Codimatra (structure connue)"""
    from bs4 import BeautifulSoup
    import re
    listings = []
    soup = BeautifulSoup(html, "html.parser")
    
    # Sélecteurs spécifiques Codimatra
    for item in soup.select(".machine-item, .stock-card, .product-box, article")[:10]:
        title = item.select_one("h3, .title, .model-name, h2")
        price = item.select_one(".price, .cost, .montant, .valeur")
        hours = item.select_one(".hours, .heures, [class*='hour']")
        
        if title:
            t = re.sub(r'\s+', ' ', title.get_text(strip=True)[:120])
            p = price.get_text(strip=True)[:30] if price else "Nous consulter"
            h = hours.get_text(strip=True) if hours else ""
            if len(t) > 5 and any(k in t.lower() for k in ["pelleteuse", "chargeuse", "volvo", "cat", "jcb", "engin", "tp"]):
                listings.append({"title": t, "price": p + (" | " + h if h else ""), "source": "Codimatra"})
    return listings[:8]

async def search_smart(query: str, max_results: int = 10) -> List[Dict]:
    """Recherche intelligente avec parser dédié par source"""
    sources = await get_relevant_sources(query)
    if not sources:
        sources = [{"url": "https://www.europe-tp.com", "category": "plateforme", "region": "europe"}]
    
    all_results = []
    keyword = query.lower().split()[0]
    
    for src in sources:
        html = await fetch_page(src["url"])
        if html:
            # Utiliser le parser dédié si disponible
            if "codimatra.com" in src["url"].lower():
                results = parse_codimatra(html)
            else:
                results = parse_robust(html, src["category"])
            
            # Filtrage intelligent
            filtered = [r for r in results if keyword in r["title"].lower() or keyword in r["price"].lower()]
            all_results.extend(filtered)
            if len(all_results) >= max_results: break
        await asyncio.sleep(0.5)
        
    if not all_results:
        logger.info("Scraping vide, activation fallback KB.")
        return [{"title": f"Recherche {query} en cours sur sources partenaires", "price": "Analyse en cours", "source": "Fallback-Intelligent"}]
        
    return all_results[:max_results]


# ─── Sodineg Scraper ─────────────────────────────────────────────────────────

_SODINEG_CATEGORIES = {
    "pelleteuse":       "/gen/travaux_publics/pelles_hydrauliques/pelles_sur_chenilles/index_43.htm",
    "pelle":            "/gen/travaux_publics/pelles_hydrauliques/pelles_sur_chenilles/index_43.htm",
    "excavatrice":      "/gen/travaux_publics/pelles_hydrauliques/pelles_sur_chenilles/index_43.htm",
    "excavator":        "/gen/travaux_publics/pelles_hydrauliques/pelles_sur_chenilles/index_43.htm",
    "escavadora":       "/gen/travaux_publics/pelles_hydrauliques/pelles_sur_chenilles/index_43.htm",
    "mini pelle":       "/gen/travaux_publics/pelles_hydrauliques/mini_pelles/index_40.htm",
    "mini-pelle":       "/gen/travaux_publics/pelles_hydrauliques/mini_pelles/index_40.htm",
    "dumper":           "/gen/travaux_publics/dumper/index_190.htm",
    "tombereau":        "/gen/travaux_publics/dumper/index_190.htm",
    "bulldozer":        "/gen/travaux_publics/bulldozers/index_101.htm",
    "bouteur":          "/gen/travaux_publics/bulldozers/index_101.htm",
    "chargeuse":        "/gen/travaux_publics/chargeurs/index_183.htm",
    "loader":           "/gen/travaux_publics/chargeurs/index_183.htm",
    "grue":             "/gen/travaux_publics/levage_manutention/grues_levage/index_39.htm",
    "crane":            "/gen/travaux_publics/levage_manutention/grues_levage/index_39.htm",
    "niveleuse":        "/gen/travaux_publics/niveleuses/index_188.htm",
    "grader":           "/gen/travaux_publics/niveleuses/index_188.htm",
    "tractopelle":      "/gen/travaux_publics/tractopelles/index_189.htm",
    "backhoe":          "/gen/travaux_publics/tractopelles/index_189.htm",
    "compacteur":       "/gen/travaux_publics/compacteurs/index_184.htm",
    "rouleau":          "/gen/travaux_publics/compacteurs/index_184.htm",
    "chariot telescopique": "/gen/travaux_publics/levage_manutention/telescopiques/index_47.htm",
    "telescopic":       "/gen/travaux_publics/levage_manutention/telescopiques/index_47.htm",
    "nacelle":          "/gen/travaux_publics/levage_manutention/nacelles/index_41.htm",
    "concasseur":       "/gen/travaux_publics/concasseurs_cribleurs/index_35.htm",
    "crible":           "/gen/travaux_publics/concasseurs_cribleurs/cribleuses/index_83.htm",
    "foreuse":          "/gen/travaux_publics/equipements/foreuses/index_74.htm",
}

_SODINEG_BASE = "https://www.sodineg.com"


def _sodineg_detect_category(query: str) -> str:
    """Détecte la catégorie Sodineg la plus pertinente pour une requête."""
    q = query.lower()
    # Cherche la correspondance la plus longue d'abord
    matched = [(k, v) for k, v in _SODINEG_CATEGORIES.items() if k in q]
    if matched:
        # Priorité à la correspondance la plus longue (plus précise)
        matched.sort(key=lambda x: -len(x[0]))
        return matched[0][1]
    # Par défaut : catégorie générale pelles
    return "/gen/travaux_publics/pelles_hydrauliques/pelles_sur_chenilles/index_43.htm"


def _parse_sodineg_listings(html: str) -> List[Dict]:
    """Parse la page listing Sodineg → liste structurée d'annonces."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    listings = []

    for item in soup.select("div.machine.bloc.list-item"):
        # Titre
        title_el = item.select_one("h2")
        if not title_el:
            continue
        title = re.sub(r"\s+", " ", title_el.get_text(strip=True))

        # Prix
        price_el = item.select_one("div.prix")
        price = re.sub(r"\s+", " ", price_el.get_text(strip=True)) if price_el else "Nous consulter"

        # Détails (marque, année, heures, poids, km)
        details = {}
        for info_div in item.select("div.blocdetails > div.info"):
            text = info_div.get_text(strip=True)
            # Marque (lien)
            link = info_div.select_one("a")
            if link:
                details["marque"] = link.get_text(strip=True)
            elif text.startswith("Année"):
                details["annee"] = text.split(":")[-1].strip()
            elif text.startswith("Heures"):
                details["heures"] = text.split(":")[-1].strip()
            elif text.startswith("Poids"):
                details["poids"] = text.split(":")[-1].strip()
            elif text.startswith("Km") or text.startswith("km"):
                details["km"] = text.split(":")[-1].strip()
            elif text.startswith("N°Parc"):
                details["ref"] = text.split(":")[-1].strip()

        # Tags (Exclusivité, Nouveau, Promo, Vendu)
        tags = []
        for tag_el in item.select("div.bloctags > div.tag"):
            tags.append(tag_el.get_text(strip=True))

        # URL
        link_el = item.select_one("a[href*='_']")
        url = ""
        if link_el:
            href = link_el.get("href", "")
            if href.startswith("/"):
                url = _SODINEG_BASE + href
            elif href.startswith("http"):
                url = href

        entry = {
            "title": title,
            "price": price,
            "marque": details.get("marque", ""),
            "annee": details.get("annee", ""),
            "heures": details.get("heures", ""),
            "poids": details.get("poids", ""),
            "km": details.get("km", ""),
            "tags": tags,
            "url": url,
            "source": "Sodineg",
        }
        listings.append(entry)

    return listings


async def search_sodineg(query: str, max_results: int = 10) -> List[Dict]:
    """
    Recherche structurée sur Sodineg.
    Détecte la catégorie, scrape les listings, filtre par mot-clé.
    Retourne une liste de {title, price, marque, annee, heures, poids, url, source}.
    """
    cat_path = _sodineg_detect_category(query)
    cat_url = _SODINEG_BASE + cat_path

    html = await fetch_page(cat_url, timeout=15.0)
    if not html:
        logger.warning(f"Sodineg: page inaccessible {cat_url}")
        return []

    all_listings = _parse_sodineg_listings(html)
    if not all_listings:
        return []

    # Filtrer par mots-clés de la requête (marque, modèle, prix max, année)
    q_lower = query.lower()
    keywords = set(q_lower.split())
    # Mots vides à ignorer dans le filtre
    stopwords = {"trouve", "trouver", "cherche", "chercher", "recherche", "rechercher",
                 "une", "un", "des", "de", "du", "le", "la", "les", "pour", "avec",
                 "sur", "dans", "pas", "moins", "plus", "prix", "euros", "€",
                 "find", "search", "looking", "for", "the", "a", "an", "and", "or",
                 "occasion", "vente", "achat", "bon", "plan", "état",
                 "encontra", "pesquisar", "procura", "uma", "um", "para",
                 "escavadora", "maquina", "maquinaria"}

    # Extraire fourchette de prix si présente
    price_max = None
    price_min = None
    for pattern in [
        (r"moins de (\d[\d\s]*)", "max"),
        (r"under (\d[\d\s]*)", "max"),
        (r"abaixo de (\d[\d\s]*)", "max"),
        (r"moins (\d[\d\s]*)", "max"),
        (r"max (\d[\d\s]*)", "max"),
        (r"jusqu['’]à (\d[\d\s]*)", "max"),
        (r"(- )?(\d[\d\s]*)\s*[-ààa]\s*(\d[\d\s]*)", "range"),
    ]:
        m = re.search(pattern[0], q_lower)
        if m:
            if pattern[1] == "max":
                price_max = int(re.sub(r"\s", "", m.group(1)))
            elif pattern[1] == "range":
                price_min = int(re.sub(r"\s", "", m.group(2)))
                price_max = int(re.sub(r"\s", "", m.group(3)))
            break

    # Extraire année si présente
    year = None
    for pattern in [r"(19\d\d|20\d\d)", r"année (\d{4})", r"year (\d{4})", r"ano (\d{4})"]:
        m = re.search(pattern, q_lower)
        if m:
            year = int(m.group(1))
            break

    # Mots-clés significatifs (marques, modèles)
    brand_keywords = {"caterpillar", "cat ", "volvo", "komatsu", "hitachi", "liebherr",
                      "jcb", "case", "doosan", "hyundai", "kobelco", "takeuchi",
                      "kubota", "bobcat", "manitou", "merlo", "new holland",
                      "mecalac", "terex", "atlas", "bomag", "ammann", "bell"}
    significant_kw = {w for w in keywords if w not in stopwords}
    brand_kw = {w for w in significant_kw if w in brand_keywords or any(b.startswith(w) for b in brand_keywords)}
    model_kw = significant_kw - brand_kw - {"t", "tonne", "tonnes", "kg"}

    # Parser les prix Sodineg en nombre
    def parse_price(p: str) -> Optional[int]:
        p = p.replace("\u00a0", " ").replace("€", "").replace("HT", "").replace(" ", "").strip()
        try:
            return int(p)
        except ValueError:
            return None

    filtered = []
    for item in all_listings:
        title_lower = item["title"].lower()
        marque_lower = item["marque"].lower()
        search_text = title_lower + " " + marque_lower

        # Filtre modèle/marque
        if model_kw and not any(kw in search_text for kw in model_kw):
            continue

        # Filtre année
        if year and item["annee"]:
            try:
                item_year = int(item["annee"])
                if item_year < year:
                    continue
            except ValueError:
                pass

        # Filtre prix max
        if price_max and item["price"]:
            p_val = parse_price(item["price"])
            if p_val is not None and p_val > price_max:
                continue

        # Exclure les "Vendu"
        if "Vendu" in item["tags"]:
            continue

        filtered.append(item)
        if len(filtered) >= max_results:
            break

    # Si pas assez de résultats après filtrage, retourner les meilleurs non-filtrés
    if not filtered and all_listings:
        return [{"title": a["title"], "price": a["price"], "marque": a["marque"],
                 "annee": a["annee"], "heures": a["heures"], "poids": a["poids"],
                 "url": a["url"], "source": "Sodineg"}
                for a in all_listings[:max_results]
                if "Vendu" not in a["tags"]]

    return filtered[:max_results]


# ─── Playwright Scraper (direct, dans le conteneur) ───────────────────────────

_PLAYWRIGHT = None

async def _get_playwright():
    global _PLAYWRIGHT
    if _PLAYWRIGHT is None:
        from playwright.async_api import async_playwright
        p = await async_playwright().start()
        _PLAYWRIGHT = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox',
                  '--disable-dev-shm-usage', '--disable-gpu']
        )
    return _PLAYWRIGHT

async def _fetch_with_browser(url: str, timeout: int = 20) -> Optional[str]:
    """Scrape une page via Playwright (headless Chrome) direct dans le conteneur."""
    try:
        browser = await _get_playwright()
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
            locale="fr-FR"
        )
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        await page.wait_for_timeout(2000)
        html = await page.content()
        await page.close()
        return html
    except Exception as e:
        logger.warning(f"Browser scrape failed {url[:60]}: {e}")
        return None


# ─── Europe-TP Scraper ───────────────────────────────────────────────────────

_EUROPE_TP_CATEGORIES = {
    "pelleteuse": "pelle-occasion/2-1/annonces-pelle.html",
    "pelle": "pelle-occasion/2-1/annonces-pelle.html",
    "excavatrice": "pelle-occasion/2-1/annonces-pelle.html",
    "excavator": "pelle-occasion/2-1/annonces-pelle.html",
    "escavadora": "pelle-occasion/2-1/annonces-pelle.html",
    "mini pelle": "mini-pelle/2-1-v4/mini-pelle-occasion.html",
    "mini-pelle": "mini-pelle/2-1-v4/mini-pelle-occasion.html",
    "dumper": "dumper-occasion/2-2/annonces-dumper.html",
    "tombereau": "dumper-occasion/2-2/annonces-dumper.html",
    "bulldozer": "bulldozer-occasion/2-4/annonces-bulldozer.html",
    "chargeuse": "chargeuse-occasion/2-3/annonces-chargeuse.html",
    "loader": "chargeuse-occasion/2-3/annonces-chargeuse.html",
    "grue": "grue-occasion/",
    "crane": "grue-occasion/",
    "niveleuse": "niveleuse-occasion/",
    "tractopelle": "tractopelle-occasion/2-2/annonces-tractopelle.html",
    "backhoe": "tractopelle-occasion/2-2/annonces-tractopelle.html",
    "compacteur": "compacteur-occasion/",
    "chariot telescopique": "chariot-telescopique-occasion/",
    "telescopic": "chariot-telescopique-occasion/",
    "nacelle": "nacelle-occasion/",
    "concasseur": "concasseur-occasion/",
    "tombereau": "dumper-occasion/2-2/annonces-dumper.html",
}

_EUROPE_TP_BASE = "https://www.europe-tp.com"


def _europetp_detect_category(query: str) -> str:
    q = query.lower()
    matched = [(k, v) for k, v in _EUROPE_TP_CATEGORIES.items() if k in q]
    if matched:
        matched.sort(key=lambda x: -len(x[0]))
        return matched[0][1]
    return "pelle-occasion/2-1/annonces-pelle.html"


def _parse_europetp_listings(html: str) -> List[Dict]:
    """Parse les listings Europe-TP (rendu Playwright)."""
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    
    # Les annonces sont dans des conteneurs avec titres et prix
    # Chercher tous les blocs qui ressemblent à des annonces
    for item in soup.select('[class*="annonce"], [class*="ad-"], [class*="listing"], article, .card'):
        title_el = item.select_one("h2, h3, .title, [class*=title]")
        if not title_el:
            continue
        title = re.sub(r"\s+", " ", title_el.get_text(strip=True))
        if len(title) < 5:
            continue
        
        price_el = item.select_one(".price, [class*=price], .prix, [class*=prix]")
        price = price_el.get_text(strip=True)[:30] if price_el else "Voir site"
        
        listings.append({
            "title": title,
            "price": price,
            "marque": "",
            "annee": "",
            "heures": "",
            "source": "Europe-TP",
        })
    
    if not listings:
        # Fallback: regex dans tout le texte
        text = soup.get_text(separator=" ", strip=True)
        for m in re.finditer(r'([A-Z][a-z]+)\s+([A-Z0-9][-A-Za-z0-9]{2,20})\s+(-\s+)?(\d[\d\s]*\d)\s*(?:€|EUR)', text[:300000]):
            listings.append({
                "title": f"{m.group(1)} {m.group(2)}",
                "price": f"{m.group(4)} €",
                "marque": m.group(1),
                "source": "Europe-TP",
            })
    
    return listings[:15]


async def search_europetp(query: str, max_results: int = 8) -> List[Dict]:
    """Recherche sur Europe-TP via Playwright."""
    cat_path = _europetp_detect_category(query)
    url = f"{_EUROPE_TP_BASE}/{cat_path}"
    
    html = await _fetch_with_browser(url, timeout=25)
    if not html:
        return []
    
    listings = _parse_europetp_listings(html)
    
    # Filtrer par mots-clés de la requête
    q_lower = query.lower()
    stopwords = {"trouve","trouver","cherche","chercher","recherche","une","un","des","de","du",
                 "le","la","les","pour","avec","sur","dans","pas","moins","plus","prix","euros",
                 "€","occasion","vente","achat"}
    keywords = {w for w in q_lower.split() if w not in stopwords and len(w) > 1}
    
    if keywords:
        filtered = [l for l in listings if any(k in l["title"].lower() for k in keywords)]
        if filtered:
            return filtered[:max_results]
    
    return listings[:max_results]


# ─── MachineryZone Scraper (cache périodique) ─────────────────────────────────

_MZ_CACHE_FILE = "/tmp/machineryzone_cache.json"
_MZ_CACHE_TTL = 1800  # 30 minutes

_MZ_CATEGORIES = {
    "pelle": "pelle-chenilles",
    "pelleteuse": "pelle-chenilles",
    "excavatrice": "pelle-chenilles",
    "excavator": "pelle-chenilles",
    "mini pelle": "mini-pelle",
    "dumper": "tombereau",
    "tombereau": "tombereau",
    "bulldozer": "bulldozer",
    "chargeuse": "chargeuse",
    "grue": "grue",
    "tractopelle": "tractopelle",
    "compacteur": "compacteur",
    "nacelle": "nacelle",
}


async def _refresh_mz_cache() -> bool:
    """Scanne toutes les catégories MachineryZone et met à jour le cache."""
    import cloudscraper
    scraper = cloudscraper.create_scraper()
    
    all_ads = []
    seen_categories = set()
    for cat_name, cat_path in _MZ_CATEGORIES.items():
        if cat_path in seen_categories:
            continue
        seen_categories.add(cat_path)
        url = f"https://www.machineryzone.fr/occasion/1/{cat_path}.html"
        try:
            r = scraper.get(url, timeout=20)
            if r.status_code != 200:
                continue
            html = r.text
            
            # Chercher des data-ad-id dans le HTML
            soup = BeautifulSoup(html, "html.parser")
            for ad in soup.select('[class*="ad-"], [class*="Ad"], article, [data-ad]'):
                title_el = ad.select_one("h2, h3, .title, [class*=title]")
                if not title_el:
                    continue
                title = re.sub(r"\s+", " ", title_el.get_text(strip=True))
                if len(title) < 5:
                    continue
                    
                price_el = ad.select_one(".price, [class*=price]")
                price = price_el.get_text(strip=True)[:30] if price_el else "Voir site"
                
                all_ads.append({
                    "title": title,
                    "price": price,
                    "source": "MachineryZone",
                    "category": cat_name,
                })
            
            # Fallback: chercher des titres dans le texte
            if len(all_ads) < 5:
                prices = re.findall(r'(\d[\d\s]*\d)\s*(?:€|EUR)', html[:200000])
                brands = re.findall(r'(Caterpillar|Volvo|Komatsu|JCB|Hitachi|Liebherr|Kubota|Bobcat|Doosan|Hyundai|Case)\s+([A-Z0-9][-A-Za-z0-9]{1,30})', html[:200000])
                for brand, model in brands[:10]:
                    all_ads.append({
                        "title": f"{brand} {model}",
                        "price": "Voir site",
                        "source": "MachineryZone",
                        "category": cat_name,
                    })
        except Exception as e:
            logger.warning(f"MZ cache refresh {cat_path}: {e}")
    
    try:
        import json
        with open(_MZ_CACHE_FILE, "w") as f:
            json.dump({"timestamp": asyncio.get_event_loop().time(), "ads": all_ads}, f)
        logger.info(f"MZ cache refreshed: {len(all_ads)} annonces")
        return True
    except Exception as e:
        logger.warning(f"MZ cache write failed: {e}")
        return False


async def search_machineryzone(query: str, max_results: int = 8) -> List[Dict]:
    """Cherche dans le cache MachineryZone."""
    try:
        import json, os
        if os.path.exists(_MZ_CACHE_FILE):
            with open(_MZ_CACHE_FILE) as f:
                data = json.load(f)
            age = asyncio.get_event_loop().time() - data.get("timestamp", 0)
            if age < _MZ_CACHE_TTL:
                all_ads = data.get("ads", [])
            else:
                await _refresh_mz_cache()
                with open(_MZ_CACHE_FILE) as f:
                    all_ads = json.load(f).get("ads", [])
        else:
            await _refresh_mz_cache()
            if os.path.exists(_MZ_CACHE_FILE):
                with open(_MZ_CACHE_FILE) as f:
                    all_ads = json.load(f).get("ads", [])
            else:
                all_ads = []
    except Exception:
        all_ads = []
    
    if not all_ads:
        return []
    
    # Filtrer par requête
    q_lower = query.lower()
    stopwords = {"trouve","trouver","cherche","chercher","recherche","une","un","des","de","du",
                 "le","la","les","pour","avec","sur","dans","pas","moins","plus","prix","euros",
                 "€","occasion","vente","achat"}
    keywords = {w for w in q_lower.split() if w not in stopwords and len(w) > 1}
    
    if keywords:
        filtered = [a for a in all_ads if any(k in a["title"].lower() for k in keywords)]
        return filtered[:max_results]
    
    return all_ads[:max_results]


# ─── Agrégateur tous sites ───────────────────────────────────────────────────

async def search_all_sites(query: str, max_results: int = 15) -> List[Dict]:
    """Lance la recherche sur tous les sites et agrège les résultats."""
    results = []
    
    # Sodineg (curl, rapide)
    try:
        sodineg = await search_sodineg(query, max_results=max_results)
        results.extend(sodineg)
    except Exception:
        pass
    
    return results[:max_results]


async def search_all_sites_with_playwright(query: str, max_results: int = 15) -> List[Dict]:
    """Version complète avec Europe-TP via Playwright (plus lent)."""
    results = await search_all_sites(query, max_results)
    
    # Europe-TP (Playwright) avec timeout global
    try:
        europetp = await asyncio.wait_for(
            search_europetp(query, max_results=6),
            timeout=30.0
        )
        for r in europetp:
            if not any(existing["title"] == r["title"] for existing in results):
                results.append(r)
    except (asyncio.TimeoutError, Exception):
        pass
    
    return results[:max_results]

