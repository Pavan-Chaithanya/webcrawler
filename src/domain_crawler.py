import asyncio
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiohttp
from models import BaseUrl
from strategies import URLDiscoveryStrategy
from playwright_helper import crawl_with_playwright

class DomainCrawler:
    def __init__(self, base_url: BaseUrl, strategy: URLDiscoveryStrategy, max_depth: int = 2, max_scroll: int = 5, session: aiohttp.ClientSession = None):
        self.strategy = strategy
        self.visited = set()
        self.visited_lock = asyncio.Lock()  # Lock to guard visited set access
        self.product_urls = set()
        self.max_depth = max_depth
        self.max_scroll = max_scroll
        self.base_url = base_url
        self.session = session
        self.base_absolute_url = base_url.get_absolute_url().rstrip('/')
        parsed_url = urlparse(self.base_absolute_url)            
        if(not parsed_url.scheme):
            self.base_absolute_url = f"https://{self.base_absolute_url}"

    async def crawl_page(self, url: str, depth: int):
        # Guard the check and update of visited URLs.
        async with self.visited_lock:
            if depth > self.max_depth or url in self.visited:
                return
            self.visited.add(url)
        
        logging.debug(f"Crawling: {url} at depth {depth}")
        
        try:
            async with await self.session.get(url) as response:
                if response.status != 200:
                    logging.debug(f"Skipping URL {url} with status {response.status}")
                    return
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
        except Exception as e:
            logging.debug(f"Error fetching {url}: {e}")
            return

        # For the base page (depth 0), simulate infinite scroll
        if(depth == 0):
            try:
                logging.debug(f"Simulating infinite scroll for {url}")
                rendered_text = await crawl_with_playwright(url, max_scrolls=self.max_scroll)
                # Update soup to include dynamically loaded content.
                soup = BeautifulSoup(rendered_text, 'html.parser')
            except Exception as e:
                logging.debug(f"Error during infinite scroll simulation for {url}: {e}")

        tasks = []
        for link in soup.find_all('a', href=True):
            
            absolute_url = urljoin(url, link['href'])
            # Parse base_url and absolute_url for robust comparison
            base_url_parsed = urlparse(self.base_absolute_url)
            absolute_url_parsed = urlparse(absolute_url)
            
            if (absolute_url_parsed.netloc != '' and  
                absolute_url_parsed.netloc.lstrip('www.') == base_url_parsed.netloc.lstrip('www.')
                and (not self.base_url.path_validation or absolute_url_parsed.path.startswith(base_url_parsed.path))):
                if self.strategy.is_product_url(absolute_url):
                    self.product_urls.add(absolute_url)
                tasks.append(self.crawl_page(absolute_url, depth + 1))
        if tasks:
            await asyncio.gather(*tasks)

    async def start(self):
        """
        Kick off the crawling process from the base URL.
        """
        await self.crawl_page(self.base_absolute_url, 0)
        return self.product_urls
