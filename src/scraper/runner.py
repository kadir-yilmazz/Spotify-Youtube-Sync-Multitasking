import sys
import os
import warnings
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from src.scraper.spotify_spider import SpotifyPlaylistSpider

def main():
    """Main entry point for the spider runner."""
    # Suppress warnings and unnecessary logs
    warnings.filterwarnings("ignore")
    logging.getLogger('scrapy').setLevel(logging.ERROR)
    logging.getLogger('filelock').setLevel(logging.ERROR)
    logging.getLogger('hpack').setLevel(logging.ERROR)

    if len(sys.argv) < 2:
        print("Usage: python -m src.scraper.runner <playlist_url>")
        sys.exit(2)

    playlist_url = sys.argv[1]

    settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "LOG_LEVEL": "ERROR", # Show only errors
    }

    configure_logging(settings=settings)
    process = CrawlerProcess(settings=settings)

    try:
        process.crawl(SpotifyPlaylistSpider, playlist_url=playlist_url)
        process.start()
    except Exception as exc: # pylint: disable=broad-exception-caught
        print(f"Spider failed: {exc}")
        sys.exit(1)

    # Force exit to prevent async loop hangs on Windows
    os._exit(0)

if __name__ == "__main__":
    main()
