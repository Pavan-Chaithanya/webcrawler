
# -----------------------------------------------------------------------------
# Fake Response and Session Classes for Testing
# -----------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, status, text):
        self.status = status
        self._text = text

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

class FakeSession:
    """
    A fake session that maps URLs to (status, text) responses.
    Optionally, it can raise an exception for specified URLs.
    """
    def __init__(self, url_to_response, raise_on=None):
        self.url_to_response = url_to_response
        self.raise_on = raise_on if raise_on is not None else set()

    async def get(self, url):
        if url in self.raise_on:
            raise Exception("Test exception")
        if url in self.url_to_response:
            status, text = self.url_to_response[url]
        else:
            status, text = (404, "")
        return FakeResponse(status, text)


def fake_crawl_with_playwright_factory(html_return_value):
    def fake_crawl_with_playwright(url: str, max_scrolls: int = 5) -> str:
        # You could even log or assert something here if needed.
        return html_return_value
    return fake_crawl_with_playwright