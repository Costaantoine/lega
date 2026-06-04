--- Ajout Scrapling + fournisseurs (3 juin 2026) ---

## 🕷️ Scrapling — Nouvel outil de scraping puissant

Scrapling v0.4.8 est maintenant disponible sur France#2 (72.62.25.52, Paris).
Le VPS Hub (Allemagne) a des restrictions géographiques → toujours passer par France#2.

### Installation sur un nouveau VPS
```bash
pip3 install scrapling patchright browserforge msgspec curl_cffi playwright --break-system-packages
patchright install chromium
```

### Script scraping
- `/root/scraping.py` sur le Hub ET France#2
- Usage: `python3 scraping.py "mots-cles" --pages 2 --details`
- Batch: `python3 scraping.py --batch queries.txt --pages 2 --output resultats`

### URLs Europages (fonctionnelles depuis France#2)
Format: `https://www.europages.fr/entreprises/{mot-cle}.html`
Exemple: `https://www.europages.fr/entreprises/location-engins-Bordeaux.html`

### État actuel
- ✅ Scrapling installé sur France#2 + Hub
- ✅ StealthyFetcher fonctionnel (bypass Cloudflare)
- ✅ Cookies langue française
- ✅ Anti-bot intégré
- ⬜ Scraper dédié pour les sites TP (Mascus, MachineryZone...)
- ⬜ Améliorer sélecteurs Europages (description, pays)

## 📋 Fournisseurs LEGA (Bordeaux et Nouvelle-Aquitaine)

Fichier: `/opt/bvi/lega_fournisseurs_20260603.csv`
- 193 entreprises uniques (192 avec URL Europages)
- Recherches effectuées depuis France#2 (Paris)
- Catégories : location engins, TP, VRD, carrière, voirie, génie civil

### Résultats pertinents
| Entreprise | Activité |
|-----------|----------|
| DIFFUSION MATERIEL INDUSTRIEL DMI FRANCE | Location engins |
| CONSEILS ET CONSTRUCTION | Travaux publics |
| SAS THIERRY TP 31 | Travaux publics |
| TRAMAK MACHINERY CONCRETE PUMP | Engins TP |
| EUROMAT'EQUIP | Engins TP |
| ASN TRANSPORT | Carrière/Transport |
| SFT GONDRAND | Matériel chantier |
| B*BATI | Carrière/Bâtiment |
| ALBERTO | Engins TP |
| SAFRAN POWER UNITS | Engins TP |

### Prochaines étapes possibles
1. Scraper les pages produits Europages (on a déjà les URLs) → infos détaillées
2. Trouver les sites web réels des fournisseurs prometteurs
3. Intégrer les données dans la base LEGA (table suppliers)
4. Pipeline automatique Nego → Mel pour démarchage
