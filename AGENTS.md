# AGENTS.md — lega

## Project Summary

`lega` built with typescript, python, javascript, shell (monorepo architecture) with 8 module(s) and 21 dependencies.

## Entry Points

- `bvi-api/main.py`
- `vitrine/backend/main.py`

## Key Commands

```bash
cd bvi-api && pip install -r requirements.txt
cd bvi-dashboard && npm run dev
cd bvi-shop && npm run dev
```

## Conventions

- mixed, absolute imports, flat file organization
- Tests: `test_*.py`
- Patterns: helper, model

## Architecture Flow

**Type:** monorepo

```
Entry (bvi-api/main.py)
  → Modules: bvi-api, bvi-dashboard, bvi-shop, docs, logs
```

## Modules

- `bvi-api`
- `bvi-dashboard`
- `bvi-shop`
- `docs`
- `logs`
- `scripts`
- `searxng`
- `vitrine`

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

## Build Status

See `docs/progress.md` for current implementation state.
