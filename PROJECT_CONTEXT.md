# Project Context — lega

## Summary

`lega` built with typescript, python, javascript, shell (monorepo architecture) with 8 module(s) and 21 dependencies.

## Languages

- typescript
- python
- javascript
- shell

## Architecture

**Type:** monorepo

**Entry Points:**
- `bvi-api/main.py`
- `vitrine/backend/main.py`

**Services:**
- `bvi-api` — bvi-api
- `bvi-dashboard` — bvi-dashboard
- `bvi-shop` — bvi-shop

**Infrastructure:** Docker

## Modules

### bvi-api
- **Path:** `bvi-api`
- **Language:** python
- **Files:** 16

**Key Files:**
- `bvi-api/kb_retriever.py` — error handling
  Exports: `search_sources`, `KB_PATH`
- `bvi-api/scraper_stealth.js` — error handling
- `bvi-api/web_utils.py` — utilities
  Exports: `parse_robust`, `parse_codimatra`, `logger`, `DB_URL`, `SEARXNG_URL`
- `bvi-api/scraper_server.py` — error handling
  Exports: `ScraperHandler`, `main`, `logger`, `BROWSER`
- `bvi-api/main.py` — API routes
  Exports: `create_jwt_token`, `verify_jwt_token`, `ProductCreate`, `ProductUpdate`, `AgentSiteAction`, `detect_language`, `tony_quick_ack`, `load_kb` (+40 more)
- `bvi-api/crews/fiche_crew.py` — error handling
  Exports: `gen_fiche`
- `bvi-api/crews/__init__.py` — database models
  Exports: `get_llm`, `load_kb`, `run`
- `bvi-api/crews/veille_crew.py` — error handling
- `bvi-api/crews/argus_crew.py` — error handling
  Exports: `gen_argus`

### bvi-dashboard
- **Path:** `bvi-dashboard`
- **Language:** typescript
- **Files:** 21

**Key Files:**
- `bvi-dashboard/next.config.js` — configuration
- `bvi-dashboard/app/page.tsx` — authentication
  Exports: `AdminDashboard`
- `bvi-dashboard/app/layout.tsx`
  Exports: `RootLayout`, `metadata`
- `bvi-dashboard/app/login/page.tsx` — API routes
  Exports: `LoginPage`
- `bvi-dashboard/app/components/AdminChatPage.tsx` — UI components
  Exports: `AdminChatPage`
- `bvi-dashboard/app/components/SourceManager.tsx` — authentication
  Exports: `SourceManager`
- `bvi-dashboard/app/components/ProductsPage.tsx` — database models
  Exports: `ProductsPage`
- `bvi-dashboard/app/components/SiteVitrinePage.tsx` — configuration
  Exports: `SiteVitrinePage`
- `bvi-dashboard/app/components/MonitoringPage.tsx` — database models
  Exports: `MonitoringPage`
- `bvi-dashboard/app/components/TasksPage.tsx` — authentication
  Exports: `TasksPage`

### bvi-shop
- **Path:** `bvi-shop`
- **Language:** typescript
- **Files:** 7

**Key Files:**
- `bvi-shop/next.config.js` — configuration
- `bvi-shop/app/page.tsx` — UI components
  Exports: `ClientApp`
- `bvi-shop/app/layout.tsx`
  Exports: `RootLayout`, `metadata`

### docs
- **Path:** `docs`
- **Files:** 8

**Key Files:**
- `docs/README.md`
- `docs/reglementation/transport_portugal.md`
- `docs/machines/cat_320d.md`
- `docs/machines/volvo_ec220.md`
- `docs/machines/komatsu_pc138.md`

### logs
- **Path:** `logs`
- **Files:** 5

**Key Files:**
- `logs/qa-free-agents-v2-2026-05-30-12.json`
- `logs/qa-free-agents-v2-2026-05-30-02.json`
- `logs/qa-free-agents-2026-05-29-19.json`
- `logs/qa-free-agents-v2-2026-05-29-22.json`
- `logs/qa-free-agents-v2-2026-05-29-20.json`

### scripts
- **Path:** `scripts`
- **Language:** shell
- **Files:** 3

**Key Files:**
- `scripts/test_free_agents.py` — tests
  Exports: `PROMPTS`

### searxng
- **Path:** `searxng`
- **Files:** 2

**Key Files:**
- `searxng/settings.yml`
- `searxng/uwsgi.ini`

### vitrine
- **Path:** `vitrine`
- **Language:** typescript
- **Files:** 51

**Key Files:**
- `vitrine/backend/main.py` — API routes
  Exports: `ProductCreate`, `ConfigUpdate`, `TranslationUpdate`, `TranslationsBulkUpdate`, `SectionUpdate`, `ContactRequest`, `DocDownloadReq`, `UPLOAD_DIR` (+18 more)
- `vitrine/frontend/next.config.js` — configuration
- `vitrine/frontend/next-env.d.ts` — configuration
- `vitrine/frontend/components/PasswordInput.tsx` — type definitions
  Exports: `PasswordInput`
- `vitrine/frontend/components/HeroCarousel.tsx` — database models
  Exports: `HeroCarousel`
- `vitrine/frontend/app/page.tsx` — UI components
  Exports: `LegaSite`
- `vitrine/frontend/app/layout.tsx` — API routes
  Exports: `RootLayout`, `metadata`

## Key Files

- `bvi-api/main.py` — API routes
  Exports: `create_jwt_token`, `verify_jwt_token`, `ProductCreate`, `ProductUpdate`, `AgentSiteAction`, `detect_language` (+42 more)
  Imports: `asyncpg`, `asyncio`, `json`, `logging`, `os`, `re` (+16 more)
- `vitrine/backend/main.py` — API routes
  Exports: `ProductCreate`, `ConfigUpdate`, `TranslationUpdate`, `TranslationsBulkUpdate`, `SectionUpdate`, `ContactRequest` (+20 more)
  Imports: `asyncpg`, `asyncio`, `hashlib`, `json`, `logging`, `os` (+18 more)
- `bvi-api/web_utils.py` — utilities
  Exports: `parse_robust`, `parse_codimatra`, `logger`, `DB_URL`, `SEARXNG_URL`
  Imports: `httpx`, `bs4`, `typing`
- `bvi-api/scraper_server.py` — error handling
  Exports: `ScraperHandler`, `main`, `logger`, `BROWSER`
  Imports: `asyncio`, `http.server`, `urllib.parse`, `playwright.async_api`
- `bvi-api/crews/__init__.py` — database models
  Exports: `get_llm`, `load_kb`, `run`
  Imports: `os`, `crewai`, `langchain_ollama`
- `bvi-api/kb_retriever.py` — error handling
  Exports: `search_sources`, `KB_PATH`
  Imports: `json`, `os`
- `bvi-dashboard/app/layout.tsx`
  Exports: `RootLayout`, `metadata`
- `bvi-shop/app/layout.tsx`
  Exports: `RootLayout`, `metadata`
- `vitrine/frontend/app/layout.tsx` — API routes
  Exports: `RootLayout`, `metadata`
  Imports: `next`
- `bvi-api/crews/fiche_crew.py` — error handling
  Exports: `gen_fiche`
  Imports: `crews.base_crew`
- `bvi-api/crews/argus_crew.py` — error handling
  Exports: `gen_argus`
  Imports: `crews.base_crew`
- `bvi-dashboard/app/page.tsx` — authentication
  Exports: `AdminDashboard`
  Imports: `react`, `next/navigation`, `./components/MonitoringPage`, `./components/AgentsPage`, `./components/TasksPage`, `./components/ProductsPage` (+6 more)
- `bvi-dashboard/app/login/page.tsx` — API routes
  Exports: `LoginPage`
  Imports: `react`, `next/navigation`
- `bvi-dashboard/app/components/AdminChatPage.tsx` — UI components
  Exports: `AdminChatPage`
  Imports: `react`
- `bvi-dashboard/app/components/SourceManager.tsx` — authentication
  Exports: `SourceManager`
  Imports: `react`

## Dependencies

### Runtime Dependencies

| Package | Version | Ecosystem |
|---------|---------|-----------|
| puppeteer-core | ^25.1.0 | npm |
| puppeteer-extra | ^3.3.6 | npm |
| puppeteer-extra-plugin-stealth | ^2.11.2 | npm |
| fastapi | ==0.135.3 | pypi |
| uvicorn | ==0.44.0 | pypi |
| asyncpg | ==0.31.0 | pypi |
| httpx | ==0.28.1 | pypi |
| beautifulsoup4 | ==4.14.3 | pypi |
| pydantic | ==2.12.5 | pypi |
| pydantic-settings | ==2.2.1 | pypi |
| crewai | ==0.30.10 | pypi |
| langchain-ollama | ==0.1.3 | pypi |
| PyJWT | ==2.8.0 | pypi |
| python-multipart | ==0.0.9 | pypi |
| edge-tts | >=6.1.12 | pypi |
| next | 14.2.0 | npm |
| react | 18.3.1 | npm |
| react-dom | 18.3.1 | npm |

### Development Dependencies

| Package | Version | Ecosystem |
|---------|---------|-----------|
| @types/node | 25.5.2 | npm |
| @types/react | 19.2.14 | npm |
| typescript | 6.0.2 | npm |

## Conventions

- **Naming:** mixed
- **File Organization:** flat
- **Import Style:** absolute
- **Test Pattern:** `test_*.py`
- **Patterns:** helper, model

**Examples from codebase:**
- Functions: `search_sources`, `KB_PATH`, `parse_robust`, `parse_codimatra`, `logger`
- Classes: `ScraperHandler`, `BROWSER`, `ProductCreate`, `ProductUpdate`, `AgentSiteAction`

## Git Insights

- **Branch:** `main`
- **Total commits:** 125
- **Contributors:** Costaantoine, Antoine LEGA, BVI Dev, Antoine Costa, Deploy Bot, Antoine

**Most Changed Files (Hotspots):**
- `bvi-api/main.py`
- `ETAT_SESSION.md`
- `bvi-shop/app/page.tsx`
- `docker-compose.yml`
- `bvi-dashboard/app/components/SiteVitrinePage.tsx`
- `.claude/settings.local.json`
- `bvi-api/web_utils.py`
- `bvi-dashboard/app/page.tsx`
- `vitrine/frontend/next.config.js`
- `bvi-dashboard/app/components/ActivationsPage.tsx`

**Recently Modified:**
- `SCRAPLING_README.md`
- `bvi-api/main.py`
- `bvi-api/package-lock.json`
- `bvi-api/package.json`
- `bvi-api/scraper_server.py`
- `bvi-api/scraper_stealth.js`
- `bvi-api/web_utils.py`
- `docker-compose.yml`
- `lega_fournisseurs_20260603.csv`
- `logs/qa-free-agents-v2-2026-05-30-12.json`

## Scan Metadata

- **Scanned at:** 2026-06-18 08:11:26.569675+00:00
- **Tool version:** 0.1.0
- **Git SHA:** `8a7a82c0e1449d2d7d1b5920617f7e7c1ea35f40`
- **Scan duration:** 0.368s
