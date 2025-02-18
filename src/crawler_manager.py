import asyncio
import aiohttp
from models import BaseUrl
from strategies import URLDiscoveryStrategy
from domain_crawler import DomainCrawler

class CrawlerManager:
    """
    Manages crawling of multiple base URLs concurrently.
    
    What it does:
      - Instantiate DomainCrawler for each base URL.
      - Execute crawlers asynchronously.
      - Collate and return the results mapping each base URL to its product URLs.
    """
    def __init__(self, base_urls: list[BaseUrl], strategy: URLDiscoveryStrategy, max_depth: int = 2, max_scroll: int  = 5):
        self.base_urls = base_urls
        self.strategy = strategy
        self.max_depth = max_depth
        self.max_scroll = max_scroll

    async def run(self):
        results = {}
        connector = aiohttp.TCPConnector(limit_per_host=200)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for base_url in self.base_urls:
                crawler = DomainCrawler(base_url, self.strategy, self.max_depth, self.max_scroll, session)
                task = crawler.start()
                tasks.append((f'{base_url.domain}{base_url.relative_path}', task))
            if tasks:
                urls, tasks_only = zip(*tasks)
                all_product_urls = await asyncio.gather(*tasks_only)
                results = {url: list(product_urls) for url, product_urls in zip(urls, all_product_urls)}
        return results
