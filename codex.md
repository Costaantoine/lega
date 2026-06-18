# codex.md — lega

## Overview

`lega` built with typescript, python, javascript, shell (monorepo architecture) with 8 module(s) and 21 dependencies.

## Setup

```bash
cd bvi-api && pip install -r requirements.txt
cd bvi-dashboard && npm run dev
cd bvi-shop && npm run dev
```

## Project Structure

- **Architecture:** monorepo
- **Entry points:** `bvi-api/main.py`, `vitrine/backend/main.py`

**Modules:**
- `bvi-api` (16 files)
- `bvi-dashboard` (21 files)
- `bvi-shop` (7 files)
- `docs` (8 files)
- `logs` (5 files)
- `scripts` (3 files)
- `searxng` (2 files)
- `vitrine` (51 files)

## Conventions

- **Naming:** mixed
- **File Organization:** flat
- **Import Style:** absolute
- **Test Pattern:** `test_*.py`
- **Patterns:** helper, model

**Examples from codebase:**
- Functions: `search_sources`, `KB_PATH`, `parse_robust`, `parse_codimatra`, `logger`
- Classes: `ScraperHandler`, `BROWSER`, `ProductCreate`, `ProductUpdate`, `AgentSiteAction`

## Dependencies

puppeteer-core (^25.1.0), puppeteer-extra (^3.3.6), puppeteer-extra-plugin-stealth (^2.11.2), fastapi (==0.135.3), uvicorn (==0.44.0), asyncpg (==0.31.0), httpx (==0.28.1), beautifulsoup4 (==4.14.3), pydantic (==2.12.5), pydantic-settings (==2.2.1), crewai (==0.30.10), langchain-ollama (==0.1.3), PyJWT (==2.8.0), python-multipart (==0.0.9), edge-tts (>=6.1.12)

_...and 6 more._
