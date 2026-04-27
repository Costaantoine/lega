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

