import asyncio
import json
import time
import logging
from crawler_manager import CrawlerManager
from strategies import RegexBasedDiscoveryStrategy
from models import BaseUrl
from config import configuration

# -----------------------------------------------------------------------------
# Main Function to Execute the Crawler
# -----------------------------------------------------------------------------

def main():
    logging.basicConfig(level=configuration["log_level"])
    
    # Load base URLs and patterns from config file
    base_urls_list = [BaseUrl(url["domain"], url["path"], url["path_validation"]) for url in configuration["base_urls"]]
    
    # Create the discovery strategy (Strategy Pattern)
    strategy = RegexBasedDiscoveryStrategy(configuration["patterns"])
    
    # Create the manager and run crawlers concurrently
    manager = CrawlerManager(base_urls_list, strategy, max_depth=configuration["max_depth"], max_scroll=configuration["max_scroll"])
    results = asyncio.run(manager.run())
    
    # Save the structured results to a JSON file.
    with open("../output/product_urls.json", "w") as f:
        json.dump(results, f, indent=4)
    
    logging.info("Crawling completed. Results saved to product_urls.json")

if __name__ == "__main__":
    main()