"""
Entry point for the Amazon Scraper project.
"""
import sys
import os
# Get the absolute path of the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import logging
import logging.config
from amazon_scraper.config import LOGGING_CONFIG, SCRAPER_CONFIG
from amazon_scraper.scraper.daraz import DarazNpScraper
from amazon_scraper.scraper.amazon import AmazonInScraper
from amazon_scraper.storage.repository import ProductRepository
from amazon_scraper.analysis.processor import ProductAnalyzer
from amazon_scraper.analysis.visualizer import ProductVisualizer

def main():
    # Set up logging
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("amazon_scraper.main")
    logger.info("Starting Amazon Scraper")
    
    # Initialize scraper
    scraper = AmazonInScraper()
    
    # Get trending products
    products = scraper.get_trending_products()
    if not products:
        logger.error("No products found")
        return
    
    # Save products
    repository = ProductRepository()
    repository.save_products(products, "amazon_in")
    
    # Analyze products
    analyzer = ProductAnalyzer(repository)
    analysis_results = analyzer.analyze_products(products, "amazon_in")
    
    # Generate insights
    insights = analyzer.generate_insights(analysis_results)
    for insight in insights:
        logger.info(insight)
    
    # Create visualizations
    visualizer = ProductVisualizer(analyzer)
    visualizer.generate_all_charts(products, "amazon_in")
    
    logger.info("Scraping and analysis completed successfully")

if __name__ == "__main__":
    main()