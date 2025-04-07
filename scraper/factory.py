"""
Factory for creating website-specific scrapers.
"""

import logging
from typing import Type, Dict, Optional
from .base import WebsiteScraper
from .amazon import AmazonInScraper
from .daraz import DarazNpScraper
from ..config import WEBSITE_CONFIGS

logger = logging.getLogger("web_scraper.factory")

class ScraperFactory:
    """Factory class for creating website-specific scrapers."""
    
    _scrapers: Dict[str, Type[WebsiteScraper]] = {
        "amazon_in": AmazonInScraper,
        "daraz_np": DarazNpScraper,
        # Add more scrapers here
    }
    
    @classmethod
    def create_scraper(cls, website_key: str) -> Optional[WebsiteScraper]:
        """
        Create a scraper instance for the specified website.
        
        Args:
            website_key: Key identifying the website (e.g., 'amazon_in')
            
        Returns:
            WebsiteScraper: Instance of the appropriate scraper
        """
        if website_key not in WEBSITE_CONFIGS:
            logger.error(f"No configuration found for website: {website_key}")
            return None
            
        scraper_class = cls._scrapers.get(website_key)
        if not scraper_class:
            logger.error(f"No scraper implementation found for website: {website_key}")
            return None
            
        return scraper_class()
