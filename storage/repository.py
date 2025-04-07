"""
Product data storage and retrieval functionality.
"""

import os
import json
import logging
import datetime
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from ..models.product import TrendingProduct
from ..config import DATA_DIR

logger = logging.getLogger("amazon_scraper.repository")

class ProductRepository:
    """Repository for saving and retrieving product data."""
    
    def __init__(self, output_dir: Union[str, Path] = DATA_DIR):
        """
        Initialize the repository with an output directory.
        
        Args:
            output_dir: Directory to store scraped data
        """
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
            logger.info(f"Created output directory: {self.output_dir}")
    
    def save_products(self, products: List[TrendingProduct], site_name: str) -> Path:
        """
        Save products to a JSON file with timestamp.
        
        Args:
            products: List of products to save
            site_name: Name of the source site
            
        Returns:
            Path: Path to the saved file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{site_name}_trending_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Convert dataclass objects to dictionaries
        products_dict = [product.to_dict() for product in products]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(products_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(products)} products to {filepath}")
        return filepath
    
    def load_products(self, filepath: Union[str, Path]) -> List[TrendingProduct]:
        """
        Load products from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            List[TrendingProduct]: List of loaded products
        """
        filepath = Path(filepath)
        logger.info(f"Loading products from {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                products_dict = json.load(f)
            
            products = [TrendingProduct.from_dict(item) for item in products_dict]
            logger.info(f"Loaded {len(products)} products from {filepath}")
            return products
        except Exception as e:
            logger.error(f"Error loading products from {filepath}: {str(e)}")
            return []
    
    def get_latest_file(self, site_name: str) -> Optional[Path]:
        """
        Get the most recent data file for a specific site.
        
        Args:
            site_name: Name of the source site
            
        Returns:
            Optional[Path]: Path to the latest file or None if not found
        """
        pattern = f"{site_name}_trending_*.json"
        files = list(self.output_dir.glob(pattern))
        
        if not files:
            logger.warning(f"No data files found for {site_name}")
            return None
        
        # Sort files by modification time
        latest_file = max(files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Found latest file for {site_name}: {latest_file}")
        return latest_file
    
    def load_latest_products(self, site_name: str) -> List[TrendingProduct]:
        """
        Load the most recent products for a specific site.
        
        Args:
            site_name: Name of the source site
            
        Returns:
            List[TrendingProduct]: List of loaded products
        """
        latest_file = self.get_latest_file(site_name)
        if not latest_file:
            return []
        
        return self.load_products(latest_file)
    
    def export_to_csv(self, products: List[TrendingProduct], output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Export products to a CSV file.
        
        Args:
            products: List of products to export
            output_path: Custom output path (optional)
            
        Returns:
            Path: Path to the exported CSV file
        """
        if not output_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"products_export_{timestamp}.csv"
        else:
            output_path = Path(output_path)
        
        # Convert products to DataFrame
        df = pd.DataFrame([product.to_dict() for product in products])
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(products)} products to CSV: {output_path}")
        
        return output_path
    
    def load_and_combine_all(self, site_name: Optional[str] = None) -> pd.DataFrame:
        """
        Load and combine all product data into a single DataFrame.
        
        Args:
            site_name: Optional filter for specific site
            
        Returns:
            pd.DataFrame: Combined product data
        """
        pattern = f"{site_name}_trending_*.json" if site_name else "*_trending_*.json"
        files = list(self.output_dir.glob(pattern))
        
        if not files:
            logger.warning(f"No data files found{' for ' + site_name if site_name else ''}")
            return pd.DataFrame()
        
        all_products = []
        for file in files:
            products = self.load_products(file)
            all_products.extend(products)
        
        df = pd.DataFrame([product.to_dict() for product in all_products])
        logger.info(f"Combined {len(all_products)} products from {len(files)} files")
        
        return df