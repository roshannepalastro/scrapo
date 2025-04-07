# Amazon Scraper

A web scraper for extracting trending product information from Amazon.in, analyzing the data, and generating visualizations.

## Features

- Scrape trending products from Amazon.in
- Save product data to JSON files
- Analyze product data (price, rating, reviews, etc.)
- Generate human-readable insights from the analysis
- Create visualizations (price distribution, rating charts, scatter plots, etc.)

## Project Structure

- `config.py`: Configuration settings for scraping, analysis, and logging
- `scraper/`: Web scraping modules
  - `base.py`: Abstract base class for scrapers
  - `amazon.py`: Amazon.in scraper implementation
  - `utils.py`: Utility functions for scraping
- `models/`: Data models
  - `product.py`: Product data model (`TrendingProduct` dataclass)
- `storage/`: Data storage and retrieval
  - `repository.py`: Product repository for saving/loading data
- `analysis/`: Data analysis and visualization
  - `processor.py`: Data processing and analysis
  - `visualizer.py`: Data visualization with matplotlib/seaborn
- `logs/`: Directory for log files
- `data/`: Directory for scraped data and charts
  - `charts/`: Subdirectory for visualization outputs
- `main.py`: Entry point of the application
- `requirements.txt`: Dependencies
- `README.md`: Project documentation

## Installation

1. Clone the repository: