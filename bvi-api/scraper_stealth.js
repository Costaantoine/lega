#!/usr/bin/env node
/**
 * Scraper anti-Cloudflare via Puppeteer-Extra + Stealth Plugin
 * Appelé depuis l'API Python via subprocess
 * Usage: node scraper_stealth.js <url> [timeout_seconds]
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const url = process.argv[2];
const timeout = parseInt(process.argv[3] || '25') * 1000;

if (!url) {
    console.error(JSON.stringify({error: 'Missing URL argument'}));
    process.exit(1);
}

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        executablePath: '/usr/bin/chromium-browser',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--window-size=1920,1080',
        ],
    });

    const page = await browser.newPage();
    await page.setViewport({width: 1920, height: 1080});
    await page.setUserAgent(
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    try {
        await page.goto(url, {
            waitUntil: 'networkidle0',
            timeout: timeout,
        });

        // Scroll pour déclencher le lazy loading
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await new Promise(r => setTimeout(r, 2000));

        const title = await page.title();
        const html = await page.content();
        const finalUrl = page.url();

        // Détecter si toujours bloqué
        const blocked = html.includes('cf-browser-verification') ||
                        html.includes('challenge-platform') ||
                        html.includes('Checking your browser') ||
                        html.length < 5000;

        console.log(JSON.stringify({
            success: !blocked,
            title: title,
            url: finalUrl,
            size: html.length,
            html: blocked ? '' : html,
            blocked: blocked,
        }));
    } catch (err) {
        console.log(JSON.stringify({
            success: false,
            error: err.message.substring(0, 200),
        }));
    }

    await browser.close();
})();
