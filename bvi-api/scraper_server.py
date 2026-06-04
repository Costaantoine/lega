#!/usr/bin/env python3
"""
Scraper Server — utilise Playwright (hôte) pour scraper les sites JS.
L'API Docker appelle ce serveur via HTTP.
Port: 9998
"""

import asyncio, json, re, logging, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper-server")

BROWSER = None

async def get_browser():
    global BROWSER
    if BROWSER is None:
        p = await async_playwright().start()
        BROWSER = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox',
                  '--disable-dev-shm-usage', '--disable-gpu']
        )
    return BROWSER

async def scrape_url(url: str, wait_selector: str = "", timeout: int = 25) -> dict:
    """Scrape une URL avec Playwright, retourne le HTML + infos."""
    browser = await get_browser()
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
        locale="fr-FR"
    )
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        
        # Attendre le contenu chargé
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=10000)
            except:
                pass
        await page.wait_for_timeout(2000)
        
        # Scroll pour déclencher le lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        
        title = await page.title()
        html = await page.content()
        url_final = page.url
        
        await context.close()
        return {"success": True, "title": title, "html": html, "url": url_final, "size": len(html)}
    except Exception as e:
        await context.close()
        return {"success": False, "error": str(e)[:200]}

async def shutdown():
    global BROWSER
    if BROWSER:
        await BROWSER.close()


class ScraperHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if parsed.path == "/health":
            self._json({"status": "ok"})
            return
        
        if parsed.path == "/scrape":
            url = params.get("url", [None])[0]
            wait = params.get("wait", [""])[0]
            timeout = int(params.get("timeout", ["25"])[0])
            
            if not url:
                self._json({"error": "Missing url parameter"}, 400)
                return
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(scrape_url(url, wait, timeout))
            loop.close()
            self._json(result)
            return
        
        self._json({"error": "Not found"}, 404)
    
    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")


def main():
    port = int(os.getenv("SCRAPER_PORT", "9998"))
    server = HTTPServer(("0.0.0.0", port), ScraperHandler)
    logger.info(f"Scraper server started on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(shutdown())
        server.server_close()

if __name__ == "__main__":
    main()
