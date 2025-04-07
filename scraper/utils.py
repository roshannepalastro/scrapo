"""
Utility functions for web scraping.
"""

import logging
import time
import random
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin

logger = logging.getLogger("amazon_scraper.utils")

def normalize_url(base_url: str, url_path: str) -> str:
    """
    Normalize a URL by joining base URL and path properly.
    
    Args:
        base_url: Base URL
        url_path: URL path or complete URL
        
    Returns:
        str: Normalized URL
    """
    if url_path.startswith('http'):
        return url_path
    
    # Remove leading slash if base_url ends with slash
    if base_url.endswith('/') and url_path.startswith('/'):
        url_path = url_path[1:]
    
    return urljoin(base_url, url_path)

def extract_asin(url: str) -> Optional[str]:
    """
    Extract ASIN from Amazon URL.
    
    Args:
        url: Amazon product URL
        
    Returns:
        Optional[str]: ASIN or None if not found
    """
    # Patterns to match ASIN in URL
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'asin=([A-Z0-9]{10})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    logger.debug(f"Could not extract ASIN from URL: {url}")
    return None

def extract_numeric(text: str) -> Optional[float]:
    """
    Extract numeric value from text.
    
    Args:
        text: Text containing a number
        
    Returns:
        Optional[float]: Extracted number or None if not found
    """
    if not text:
        return None
    
    # Extract digits and decimal point
    numeric_str = re.sub(r'[^\d.]', '', text)
    try:
        return float(numeric_str)
    except ValueError:
        logger.debug(f"Could not extract numeric value from: {text}")
        return None

def random_delay(min_delay: float = 1.0, max_delay: float = 3.0) -> None:
    """
    Wait for a random amount of time to avoid detection.
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
    """
    delay = random.uniform(min_delay, max_delay)
    logger.debug(f"Sleeping for {delay:.2f} seconds")
    time.sleep(delay)

def extract_hostname(url: str) -> str:
    """
    Extract hostname from URL.
    
    Args:
        url: URL
        
    Returns:
        str: Hostname
    """
    return urlparse(url).netloc

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.
    
    Args:
        text: Input text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()

def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        
    Returns:
        str: Truncated text with ellipsis if necessary
    """
    if not text or len(text) <= max_length:
        return text or ""
    # Truncate at the last space before max_length to avoid cutting words
    truncated = text[:max_length].rsplit(' ', 1)[0] + '...'
    logger.debug(f"Truncated text from {len(text)} to {len(truncated)} characters")
    return truncated