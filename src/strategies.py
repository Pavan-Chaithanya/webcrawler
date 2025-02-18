from abc import ABC, abstractmethod
import re

class URLDiscoveryStrategy(ABC):
    """
    Abstract base class representing a strategy for identifying product URLs.
    This will be used as an interface for different strategies.
    """
    @abstractmethod
    def is_product_url(self, url: str) -> bool:
        """
        Determine if the given URL points to a product page.
        """
        pass

class RegexBasedDiscoveryStrategy(URLDiscoveryStrategy):
    """
    A concrete strategy that uses regular expressions to detect product URLs.
    This strategy can be extended by adding more patterns.
    """
    def __init__(self, patterns: list):
        self.patterns = patterns

    def is_product_url(self, url: str) -> bool:
        for pattern in self.patterns:
            if re.search(pattern, url):
                return True
        return False
