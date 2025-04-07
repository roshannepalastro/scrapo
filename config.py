"""
Configuration settings for the Amazon Scraper.
"""

import os
import logging
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CHARTS_DIR = BASE_DIR / "data" / "charts"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, CHARTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


#common scraper setting
COMMON_SCRAPER_SETTINGS = {
    "max_retries": 3,
    "retry_delay": 2.0,
    "timeout": 30,
    "request_delay": 1.5,  # Delay between requests in seconds
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}
COMMON_SCRAPER_SETTINGS = {
    "max_retries": 3,
    "retry_delay": 2.0,
    "timeout": 30,
    "request_delay": 1.5,  # Delay between requests in seconds
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

# Scraper configurations
SCRAPER_CONFIG = {
    "amazon_in": {
        "base_url": "https://www.amazon.in",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "trending_pages": [
            "/gp/bestsellers/",
            "/gp/new-releases/",
            "/gp/movers-and-shakers/",
            "/deals/"
        ],
        "max_retries": 3,
        "retry_delay": 2.0,
        "timeout": 30,
        "request_delay": 1.5,  # Delay between requests in seconds
    },
    'daraz_np':{

    }
}

# Analysis configurations
ANALYSIS_CONFIG = {
    "price_currency": "₹",
    "charts_dir": CHARTS_DIR,
    "default_chart_format": "png",
    "default_chart_dpi": 300,
    "max_products_per_site": 50,
    "min_products_for_analysis": 5,
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOGS_DIR / "amazon_scraper.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": LOGS_DIR / "error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
    },
    "loggers": {
        "amazon_scraper": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False
        }
    }
}

# Default scraper settings
DEFAULT_SCRAPER = "amazon_in"
DEFAULT_OUTPUT_FORMAT = "json"
DEFAULT_SAVE_PATH = DATA_DIR

# Request headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}