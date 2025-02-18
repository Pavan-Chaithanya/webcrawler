import asyncio
from playwright.async_api import async_playwright

async def crawl_with_playwright(url: str, max_scrolls: int = 5) -> str:
    """
    Launches a headless browser to load the page, simulating infinite scrolling by scrolling
    down a fixed number of times. Returns the fully rendered HTML.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        for _ in range(max_scrolls):
            # Scroll down by the full height of the document.
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            # Wait a bit for content to load.
            await asyncio.sleep(1)
        content = await page.content()
        await browser.close()
        return content
