"""
Data processing functionality for product analysis.
"""

import re
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from ..models.product import TrendingProduct
from ..storage.repository import ProductRepository
from ..config import ANALYSIS_CONFIG

logger = logging.getLogger("amazon_scraper.processor")

class ProductAnalyzer:
    """Analyzer for processing product data."""
    
    def __init__(self, repository: Optional[ProductRepository] = None):
        """
        Initialize the analyzer.
        
        Args:
            repository: Optional repository instance for data loading
        """
        self.repository = repository or ProductRepository()
        logger.info("ProductAnalyzer initialized")
    
    def extract_numeric_price(self, price_str: Optional[str]) -> Optional[float]:
        """
        Extract numeric price from price string.
        
        Args:
            price_str: Price string (e.g., "₹1,499.00")
            
        Returns:
            Optional[float]: Numeric price or None if extraction fails
        """
        if not price_str:
            return None
        
        # Extract digits and decimal point from price string
        numeric_str = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(numeric_str)
        except ValueError:
            return None
    
    def prepare_dataframe(self, products: List[TrendingProduct]) -> pd.DataFrame:
        """
        Prepare a DataFrame from product list with additional computed columns.
        
        Args:
            products: List of products
            
        Returns:
            pd.DataFrame: Processed DataFrame
        """
        logger.info("Preparing product DataFrame for analysis")
        
        # Convert products to DataFrame
        df = pd.DataFrame([product.to_dict() for product in products])
        
        if df.empty:
            logger.warning("Empty product list, returning empty DataFrame")
            return df
        
        # Extract numeric prices
        if 'price' in df.columns:
            df['price_numeric'] = df['price'].apply(self.extract_numeric_price)
            logger.debug(f"Extracted numeric prices for {df['price_numeric'].notna().sum()} products")
        
        # Convert timestamp strings to datetime
        if 'extracted_at' in df.columns:
            df['extracted_at'] = pd.to_datetime(df['extracted_at'])
        
        # Process ratings if available
        if 'rating' in df.columns:
            # Ensure rating is numeric
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            
            # Create rating buckets
            df['rating_group'] = pd.cut(
                df['rating'], 
                bins=[0, 2, 3, 4, 5], 
                labels=['0-2 ★', '2-3 ★', '3-4 ★', '4-5 ★'],
                include_lowest=True
            )
            
            logger.debug("Created rating groups")
        
        # Process review counts if available
        if 'review_count' in df.columns:
            # Ensure review_count is numeric
            df['review_count'] = pd.to_numeric(df['review_count'], errors='coerce')
            
            # Create logarithmic review count for better visualization
            positive_reviews = df['review_count'].clip(lower=1)
            df['log_review_count'] = np.log10(positive_reviews)
            
            logger.debug("Processed review counts")
        
        logger.info(f"DataFrame prepared with {len(df)} products and {len(df.columns)} columns")
        return df
    
    def analyze_products(self, products: Optional[List[TrendingProduct]] = None, 
                        site_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on product data.
        
        Args:
            products: Optional list of products to analyze
            site_name: Optional site name to load latest products if products not provided
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        logger.info(f"Starting product analysis{'for ' + site_name if site_name else ''}")
        
        # Load products if not provided
        if products is None:
            if site_name:
                products = self.repository.load_latest_products(site_name)
            else:
                logger.error("Neither products nor site_name provided for analysis")
                return {"error": "No data provided for analysis"}
        
        if not products:
            logger.warning("No products available for analysis")
            return {"error": "No products available for analysis"}
        
        # Prepare DataFrame with computed columns
        df = self.prepare_dataframe(products)
        
        # Initialize results dictionary
        results = {
            "product_count": len(df),
            "analysis_time": pd.Timestamp.now().isoformat(),
            "source": site_name or df['source'].iloc[0] if not df.empty and 'source' in df.columns else "unknown"
        }
        
        # Price analysis
        if 'price_numeric' in df.columns:
            price_data = df['price_numeric'].dropna()
            results["price_analysis"] = {
                "mean": price_data.mean(),
                "median": price_data.median(),
                "min": price_data.min(),
                "max": price_data.max(),
                "std": price_data.std(),
                "quartiles": price_data.quantile([0.25, 0.5, 0.75]).to_dict()
            }
            logger.debug("Completed price analysis")
        
        # Rating analysis
        if 'rating' in df.columns:
            rating_data = df['rating'].dropna()
            results["rating_analysis"] = {
                "mean": rating_data.mean(),
                "median": rating_data.median(),
                "distribution": df['rating_group'].value_counts().to_dict() if 'rating_group' in df.columns else {}
            }
            logger.debug("Completed rating analysis")
        
        # Review count analysis
        if 'review_count' in df.columns:
            review_count_data = df['review_count'].dropna()
            results["review_analysis"] = {
                "total": review_count_data.sum(),
                "mean": review_count_data.mean(),
                "median": review_count_data.median(),
                "max": review_count_data.max()
            }
            logger.debug("Completed review count analysis")
        
        # Category analysis
        if 'category' in df.columns:
            results["category_analysis"] = {
                "count": df['category'].nunique(),
                "distribution": df['category'].value_counts().to_dict()
            }
            logger.debug("Completed category analysis")
        
        # Price range recommendations (marketing insights)
        if 'price_numeric' in df.columns:
            price_data = df['price_numeric'].dropna()
            low_price = price_data.quantile(0.25)
            high_price = price_data.quantile(0.75)
            
            results["price_range_recommendations"] = {
                "budget": [0, low_price],
                "mid_range": [low_price, high_price],
                "premium": [high_price, price_data.max()]
            }
            logger.debug("Generated price range recommendations")
        
        # Top products by different metrics
        results["top_products"] = {}
        
        # Top rated products
        if 'rating' in df.columns and 'title' in df.columns:
            top_rated = df.nlargest(5, 'rating')[['title', 'rating', 'price']]
            results["top_products"]["highest_rated"] = top_rated.to_dict('records')
        
        # Most reviewed products
        if 'review_count' in df.columns and 'title' in df.columns:
            most_reviewed = df.nlargest(5, 'review_count')[['title', 'review_count', 'rating']]
            results["top_products"]["most_reviewed"] = most_reviewed.to_dict('records')
        
        # Price-performance analysis (high rating, reasonable price)
        if all(col in df.columns for col in ['rating', 'price_numeric', 'title']):
            # Create a price-performance score
            df_valid = df.dropna(subset=['rating', 'price_numeric'])
            if not df_valid.empty:
                df_valid['price_percentile'] = df_valid['price_numeric'].rank(pct=True)
                df_valid['rating_percentile'] = df_valid['rating'].rank(pct=True)
                
                # Higher rating and lower price is better
                df_valid['value_score'] = df_valid['rating_percentile'] * (1 - df_valid['price_percentile'])
                
                best_value = df_valid.nlargest(5, 'value_score')[['title', 'rating', 'price', 'value_score']]
                results["top_products"]["best_value"] = best_value.to_dict('records')
        
        # Time-based analysis if multiple timestamps are available
        if 'extracted_at' in df.columns:
            unique_dates = df['extracted_at'].dt.date.nunique()
            if unique_dates > 1:
                results["time_analysis"] = {
                    "date_range": [df['extracted_at'].min().isoformat(), df['extracted_at'].max().isoformat()],
                    "unique_dates": unique_dates
                }
                logger.debug("Completed time-based analysis")
        
        logger.info(f"Completed product analysis with {len(results)} result categories")
        return results
    
    def generate_insights(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Generate human-readable insights from analysis results.
        
        Args:
            analysis_results: Analysis results from analyze_products
            
        Returns:
            List[str]: List of insight statements
        """
        insights = []
        
        # Check if we have valid analysis results
        if not analysis_results or "error" in analysis_results:
            return ["Insufficient data for meaningful insights."]
        
        # Product count insight
        product_count = analysis_results.get("product_count", 0)
        insights.append(f"Analysis based on {product_count} products from {analysis_results.get('source', 'unknown')}.")
        
        # Price insights
        price_analysis = analysis_results.get("price_analysis", {})
        if price_analysis:
            currency = ANALYSIS_CONFIG.get("price_currency", "₹")
            avg_price = price_analysis.get("mean")
            if avg_price:
                insights.append(f"Average product price is {currency}{avg_price:.2f}.")
            
            price_range = price_analysis.get("max", 0) - price_analysis.get("min", 0)
            if price_range > 0:
                insights.append(f"Price range spans {currency}{price_analysis.get('min', 0):.2f} to {currency}{price_analysis.get('max', 0):.2f}.")
        
        # Rating insights
        rating_analysis = analysis_results.get("rating_analysis", {})
        if rating_analysis:
            avg_rating = rating_analysis.get("mean")
            if avg_rating:
                insights.append(f"Average product rating is {avg_rating:.1f}/5.0 stars.")
            
            # Distribution insight
            distribution = rating_analysis.get("distribution", {})
            if distribution:
                best_group = max(distribution.items(), key=lambda x: x[1])[0]
                insights.append(f"Most products fall in the {best_group} rating range.")
        
        # Review insights
        review_analysis = analysis_results.get("review_analysis", {})
        if review_analysis:
            total_reviews = review_analysis.get("total")
            if total_reviews:
                insights.append(f"Products have accumulated a total of {total_reviews:.0f} reviews.")
            
            avg_reviews = review_analysis.get("mean")
            if avg_reviews:
                insights.append(f"Products average {avg_reviews:.0f} reviews each.")
        
        # Category insights
        category_analysis = analysis_results.get("category_analysis", {})
        if category_analysis:
            category_count = category_analysis.get("count")
            if category_count:
                insights.append(f"Products span {category_count} different categories.")
            
            # Top category
            distribution = category_analysis.get("distribution", {})
            if distribution:
                top_category = max(distribution.items(), key=lambda x: x[1])
                insights.append(f"The most common category is '{top_category[0]}' with {top_category[1]} products.")
        
        # Best value insights
        top_products = analysis_results.get("top_products", {})
        best_value = top_products.get("best_value", [])
        if best_value:
            top_value = best_value[0]
            insights.append(f"Best value for money: '{top_value.get('title', 'Unknown')}' with a {top_value.get('rating', 0):.1f} rating.")
        
        # Price range recommendation
        price_ranges = analysis_results.get("price_range_recommendations", {})
        if price_ranges:
            currency = ANALYSIS_CONFIG.get("price_currency", "₹")
            mid_range = price_ranges.get("mid_range", [0, 0])
            if mid_range[1] > mid_range[0]:
                insights.append(f"Recommended mid-range products fall between {currency}{mid_range[0]:.2f} and {currency}{mid_range[1]:.2f}.")
        
        logger.info(f"Generated {len(insights)} insights from analysis results")
        return insights
    
    def compare_sites(self, site_names: List[str]) -> Dict[str, Any]:
        """
        Compare product data across different sites.
        
        Args:
            site_names: List of site names to compare
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        if not site_names or len(site_names) < 2:
            logger.warning("Need at least two sites for comparison")
            return {"error": "Need at least two sites for comparison"}
        
        logger.info(f"Comparing data across {len(site_names)} sites")
        comparison = {
            "sites": site_names,
            "timestamp": pd.Timestamp.now().isoformat(),
            "metrics": {},
            "site_data": {}
        }
        
        # Get data for each site
        for site in site_names:
            products = self.repository.load_latest_products(site)
            if not products:
                logger.warning(f"No products found for site: {site}")
                comparison["site_data"][site] = {"error": "No data available"}
                continue
                
            # Analyze site data
            site_analysis = self.analyze_products(products, site)
            comparison["site_data"][site] = site_analysis
        
        # Skip comparison if we don't have enough valid data
        valid_sites = [site for site, data in comparison["site_data"].items() 
                      if not data.get("error")]
                      
        if len(valid_sites) < 2:
            logger.warning("Not enough valid data for site comparison")
            comparison["metrics"] = {"error": "Not enough valid data for comparison"}
            return comparison
        
        # Compare price metrics
        price_metrics = {}
        for site in valid_sites:
            site_data = comparison["site_data"][site]
            price_analysis = site_data.get("price_analysis", {})
            if price_analysis:
                price_metrics[site] = {
                    "mean": price_analysis.get("mean"),
                    "median": price_analysis.get("median"),
                    "min": price_analysis.get("min"),
                    "max": price_analysis.get("max")
                }
        
        if price_metrics:
            comparison["metrics"]["price"] = price_metrics
        
        # Compare rating metrics
        rating_metrics = {}
        for site in valid_sites:
            site_data = comparison["site_data"][site]
            rating_analysis = site_data.get("rating_analysis", {})
            if rating_analysis:
                rating_metrics[site] = {
                    "mean": rating_analysis.get("mean"),
                    "median": rating_analysis.get("median")
                }
        
        if rating_metrics:
            comparison["metrics"]["rating"] = rating_metrics
        
        # Generate comparison insights
        comparison["insights"] = self._generate_comparison_insights(comparison)
        
        logger.info(f"Completed comparison across {len(valid_sites)} sites")
        return comparison
    
    def _generate_comparison_insights(self, comparison: Dict[str, Any]) -> List[str]:
        """
        Generate insights from site comparison.
        
        Args:
            comparison: Comparison results
            
        Returns:
            List[str]: List of comparison insights
        """
        insights = []
        
        # Check if we have valid metrics
        metrics = comparison.get("metrics", {})
        if not metrics or "error" in metrics:
            return ["Insufficient data for meaningful comparison."]
        
        valid_sites = [site for site, data in comparison["site_data"].items() 
                      if not data.get("error")]
        
        # Product count comparison
        product_counts = {}
        for site in valid_sites:
            site_data = comparison["site_data"][site]
            product_counts[site] = site_data.get("product_count", 0)
        
        if product_counts:
            max_site = max(product_counts.items(), key=lambda x: x[1])
            insights.append(f"{max_site[0]} has the most products ({max_site[1]}).")
        
        # Price comparison
        price_metrics = metrics.get("price", {})
        if price_metrics and len(price_metrics) >= 2:
            avg_prices = {site: data.get("mean") for site, data in price_metrics.items() if data.get("mean")}
            if avg_prices:
                lowest_price_site = min(avg_prices.items(), key=lambda x: x[1])
                highest_price_site = max(avg_prices.items(), key=lambda x: x[1])
                
                currency = ANALYSIS_CONFIG.get("price_currency", "₹")
                insights.append(f"{lowest_price_site[0]} has the lowest average price ({currency}{lowest_price_site[1]:.2f}).")
                insights.append(f"{highest_price_site[0]} has the highest average price ({currency}{highest_price_site[1]:.2f}).")
        
        # Rating comparison
        rating_metrics = metrics.get("rating", {})
        if rating_metrics and len(rating_metrics) >= 2:
            avg_ratings = {site: data.get("mean") for site, data in rating_metrics.items() if data.get("mean")}
            if avg_ratings:
                highest_rating_site = max(avg_ratings.items(), key=lambda x: x[1])
                lowest_rating_site = min(avg_ratings.items(), key=lambda x: x[1])
                
                insights.append(f"{highest_rating_site[0]} has the highest average rating ({highest_rating_site[1]:.1f}/5.0).")
                insights.append(f"{lowest_rating_site[0]} has the lowest average rating ({lowest_rating_site[1]:.1f}/5.0).")
        
        logger.info(f"Generated {len(insights)} comparison insights")
        return insights