import pytest
import aiohttp
import playwright_helper
from domain_crawler import DomainCrawler
from crawler_manager import CrawlerManager
from strategies import RegexBasedDiscoveryStrategy, URLDiscoveryStrategy
from models import BaseUrl
from test_helper_fakes import FakeResponse, FakeSession, fake_crawl_with_playwright_factory
# ---------------------------------------------------------------------------
# Test URLDiscoveryStrategy
# ---------------------------------------------------------------------------
def test_regex_based_discovery_strategy():
    strategy = RegexBasedDiscoveryStrategy([r'/product/', r'/item/'])
    assert strategy.is_product_url("https://example.com/product/123")
    assert strategy.is_product_url("https://example.com/item/456")
    assert not strategy.is_product_url("https://example.com/about")

# ---------------------------------------------------------------------------
# Test DomainCrawler
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_domain_crawler(monkeypatch):
    # Setup fake responses for a fake domain "testdomain.com"
    html_base = '''
    <html>
      <body>
        <a href="/product/1">Product 1</a>
        <a href="/about">About Us</a>
      </body>
    </html>
    '''
    html_product = '<html><body><p>Product Page</p></body></html>'
    html_about = '<html><body><p>About Us</p></body></html>'

    fake_responses = {
        "https://testdomain.com": (200, html_base),
        "https://testdomain.com/product/1": (200, html_product),
        "https://testdomain.com/about": (200, html_about),
    }
    fake_session = FakeSession(fake_responses)
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    
    fake_crawl = fake_crawl_with_playwright_factory(html_base)
    
    # Replace the real function with our fake version.
    monkeypatch.setattr(playwright_helper, "crawl_with_playwright", fake_crawl)

    crawler = DomainCrawler(BaseUrl('testdomain.com'), strategy, max_depth=2, session=fake_session)
    product_urls = await crawler.start()

    # Verify that the product URL is detected and that non-product pages are ignored.
    assert "https://testdomain.com/product/1" in product_urls
    assert "https://testdomain.com/about" not in product_urls

# -----------------------------------------------------------------------------
# Tests for DomainCrawler
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_domain_crawler_normal(monkeypatch):
    # Base HTML includes one valid product link, one non-product link,
    # and a duplicate product link.
    html_base = """
    <html>
      <body>
         <a href="/product/1">Product 1</a>
         <a href="/ignore/1">Ignore</a>
         <a href="/product/1">Duplicate Product 1</a>
      </body>
    </html>
    """
    html_product = "<html><body><p>Product Page</p></body></html>"
    html_ignore = "<html><body><p>Ignore Page</p></body></html>"
    fake_responses = {
        "https://testdomain.com": (200, html_base),
        "https://testdomain.com/product/1": (200, html_product),
        "https://testdomain.com/ignore/1": (200, html_ignore),
    }
    session = FakeSession(fake_responses)
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    
    fake_crawl = fake_crawl_with_playwright_factory(html_base)

    # Replace the real function with our fake version.
    monkeypatch.setattr(playwright_helper,"crawl_with_playwright", fake_crawl)

    crawler = DomainCrawler(BaseUrl("testdomain.com"), strategy, max_depth=2, session=session)
    product_urls = await crawler.start()
    # Verify that only the product URL is collected once.
    assert "https://testdomain.com/product/1" in product_urls
    assert "https://testdomain.com/ignore/1" not in product_urls
    assert len(product_urls) == 1

@pytest.mark.asyncio
async def test_domain_crawler_exception():
    # Simulate an exception when fetching the product page.
    fake_responses = {
    }
    session = FakeSession(fake_responses, raise_on={"https://testdomain.com"})
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    crawler = DomainCrawler(BaseUrl("testdomain.com"), strategy, max_depth=2, session=session)
    product_urls = await crawler.start()
    # The exception should be caught and the product URL not added.
    assert "https://testdomain.com/product/1" not in product_urls
    
@pytest.mark.asyncio
async def test_domain_crawler_non200():
    # Simulate an exception when fetching the product page.
    fake_responses = {
    }
    session = FakeSession(fake_responses)
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    crawler = DomainCrawler(BaseUrl("testdomain.com"), strategy, max_depth=2, session=session)
    product_urls = await crawler.start()
    # The exception should be caught and the product URL not added.
    assert "https://testdomain.com/product/1" not in product_urls

@pytest.mark.asyncio
async def test_domain_crawler_scrollable200():
    # Simulate an exception when fetching the product page.
    fake_responses = {
        "https://google.com": (200, ''),
    }
    session = FakeSession(fake_responses)
    strategy = RegexBasedDiscoveryStrategy([r'google'])
    crawler = DomainCrawler(BaseUrl("google.com"), strategy, max_depth=1, session=session)
    product_urls = await crawler.start()
    assert len(product_urls)>0

@pytest.mark.asyncio
async def test_domain_crawler_max_depth(monkeypatch):
    # Create a chain of pages deeper than the max_depth.
    html_level0 = '<html><body><a href="/page1">Page 1</a></body></html>'
    html_level1 = '<html><body><a href="/page2">Page 2</a></body></html>'
    html_level2 = '<html><body><a href="/product/1">Product 1</a></body></html>'
    fake_responses = {
        "https://testdomain.com": (200, html_level0),
        "https://testdomain.com/page1": (200, html_level1),
        "https://testdomain.com/page2": (200, html_level2),
        "https://testdomain.com/product/1": (200, "<html><body>Product Page</body></html>"),
    }
    session = FakeSession(fake_responses)
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    
    fake_crawl = fake_crawl_with_playwright_factory(html_level0)

    monkeypatch.setattr(playwright_helper,"crawl_with_playwright", fake_crawl)

    
    # With max_depth=1, the chain should stop before reaching /page2.
    crawler = DomainCrawler(BaseUrl("testdomain.com"), strategy, max_depth=1, session=session)
    product_urls = await crawler.start()
    assert "https://testdomain.com/product/1" not in product_urls

    # With max_depth=2, the product should be found.
    crawler = DomainCrawler(BaseUrl("testdomain.com"), strategy, max_depth=2,  session=session)
    product_urls = await crawler.start()
    assert "https://testdomain.com/product/1" in product_urls

# -----------------------------------------------------------------------------
# Tests for CrawlerManager
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_crawler_manager(monkeypatch):
    # Set up fake responses for two domains.
    html_domain1 = """
    <html>
      <body>
         <a href="/product/1">Product 1</a>
      </body>
    </html>
    """
    html_domain2 = """
    <html>
      <body>
         <a href="/product/2">Product 2</a>
      </body>
    </html>
    """
    fake_responses = {
        "https://domain1.com": (200, html_domain1),
        "https://domain1.com/product/1": (200, "<html><body>Product Page</body></html>"),
        "https://domain2.com": (200, html_domain2),
        "https://domain2.com/product/2": (200, "<html><body>Product Page</body></html>"),
    }
    # Create a combined fake session that handles both domains.
    class CombinedFakeSession:
        def __init__(self):
            self.fake_session = FakeSession(fake_responses)
        async def get(self, url):
            return await self.fake_session.get(url)
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(aiohttp, "ClientSession", lambda *args, **kwargs: CombinedFakeSession())

    base_urls = [
        BaseUrl("domain1.com"),
        BaseUrl("domain2.com"),
    ]
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    manager = CrawlerManager(base_urls, strategy, max_depth=2)
    results = await manager.run()
    # Results keys are formatted as "domain[relative_path]"
    assert "domain1.com" in results
    assert "domain2.com" in results
    assert "https://domain1.com/product/1" in results["domain1.com"]
    assert "https://domain2.com/product/2" in results["domain2.com"]

@pytest.mark.asyncio
async def test_domain_crawler_no_links(monkeypatch):
    # Test with a page that has no links.
    html_base = "<html><body>No links here</body></html>"
    fake_responses = {
        "https://testdomain.com": (200, html_base),
    }
    session = FakeSession(fake_responses)
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    
    fake_crawl = fake_crawl_with_playwright_factory(html_base)

    monkeypatch.setattr(playwright_helper, "crawl_with_playwright", fake_crawl)

    crawler = DomainCrawler(BaseUrl("testdomain.com"), strategy, max_depth=2, session=session)
    product_urls = await crawler.start()
    assert len(product_urls) == 0

@pytest.mark.asyncio
async def test_domain_crawler_multiple_product_links(monkeypatch):
    # Test with a page that has multiple product links.
    html_base = """
    <html>
      <body>
         <a href="/product/1">Product 1</a>
         <a href="/product/2">Product 2</a>
         <a href="/product/3">Product 3</a>
      </body>
    </html>
    """
    fake_responses = {
        "https://testdomain.com": (200, html_base),
        "https://testdomain.com/product/1": (200, "<html><body>Product 1 Page</body></html>"),
        "https://testdomain.com/product/2": (200, "<html><body>Product 2 Page</body></html>"),
        "https://testdomain.com/product/3": (200, "<html><body>Product 3 Page</body></html>"),
    }
    session = FakeSession(fake_responses)
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    
    fake_crawl = fake_crawl_with_playwright_factory(html_base)

    monkeypatch.setattr(playwright_helper, "crawl_with_playwright", fake_crawl)

    crawler = DomainCrawler(BaseUrl("testdomain.com"), strategy, max_depth=2, session=session)
    product_urls = await crawler.start()
    assert "https://testdomain.com/product/1" in product_urls
    assert "https://testdomain.com/product/2" in product_urls
    assert "https://testdomain.com/product/3" in product_urls
    assert len(product_urls) == 3

@pytest.mark.asyncio
async def test_crawler_manager_no_product_links(monkeypatch):
    # Test with domains that have no product links.
    html_domain1 = "<html><body>No product links here</body></html>"
    html_domain2 = "<html><body>No product links here either</body></html>"
    fake_responses = {
        "https://domain1.com": (200, html_domain1),
        "https://domain2.com": (200, html_domain2),
    }
    class CombinedFakeSession:
        def __init__(self):
            self.fake_session = FakeSession(fake_responses)
        async def get(self, url):
            return await self.fake_session.get(url)
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(aiohttp, "ClientSession", lambda *args, **kwargs: CombinedFakeSession())

    base_urls = [
        BaseUrl("domain1.com"),
        BaseUrl("domain2.com"),
    ]
    strategy = RegexBasedDiscoveryStrategy([r'/product/'])
    manager = CrawlerManager(base_urls, strategy, max_depth=2)
    results = await manager.run()
    assert "domain1.com" in results
    assert "domain2.com" in results
    assert len(results["domain1.com"]) == 0
    assert len(results["domain2.com"]) == 0

def test_url_discovery_strategy_abstract_instantiation():
    with pytest.raises(TypeError):
        URLDiscoveryStrategy()

def test_url_discovery_strategy_parent_method_called():
    
    class DummyDiscovery(URLDiscoveryStrategy):
        def is_product_url(self, url: str) -> bool:
            return URLDiscoveryStrategy.is_product_url(self, url)
        
    dummy = DummyDiscovery()
    # Since the parent's method body is just "pass", it returns None.
    # We assert that calling our dummy implementation returns None.
    assert dummy.is_product_url("https://example.com") is None
