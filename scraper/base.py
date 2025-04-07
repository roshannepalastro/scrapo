"""
Abstract base classes for website scrapers.
"""

import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import time

from ..models.product import TrendingProduct

logger = logging.getLogger("amazon_scraper.base")

class WebsiteScraper(ABC):
    """Abstract base class for website scrapers."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize the scraper with base URL and optional headers."""
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.session = requests.Session()
        
        # Default headers to mimic a browser
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Use provided headers or default ones
        self.headers = headers if headers else default_headers
        self.session.headers.update(self.headers)
        logger.info(f"Initialized scraper for domain: {self.domain}")
    
    def get_page(self, url_path: str, retry: int = 3, backoff_factor: float = 0.5) -> Optional[requests.Response]:
        """
        Get a page from the website with error handling and retry logic.
        
        Args:
            url_path: The path or complete URL to fetch
            retry: Number of retry attempts
            backoff_factor: Exponential backoff factor for retries
            
        Returns:
            Optional[requests.Response]: The response object or None on failure
        """
        url = self.base_url + url_path if not url_path.startswith('http') else url_path
        logger.info(f"Fetching page: {url}")
        
        for attempt in range(retry):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                logger.info(f"Successfully fetched page: {url} (Status: {response.status_code})")
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt+1}/{retry} failed for {url}: {str(e)}")
                if attempt < retry - 1:  # Don't sleep on the last attempt
                    sleep_time = backoff_factor * (2 ** attempt)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
        
        logger.error(f"Failed to fetch page after {retry} attempts: {url}")
        return None
    
    @abstractmethod
    def get_trending_products(self) -> List[TrendingProduct]:
        """
        Abstract method to get trending products from the website.
        
        Returns:
            List[TrendingProduct]: A list of trending products
        """
        pass