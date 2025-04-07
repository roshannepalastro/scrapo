"""
Data visualization functionality for product analysis.
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

from ..models.product import TrendingProduct
from ..storage.repository import ProductRepository
from ..analysis.processor import ProductAnalyzer
from ..config import ANALYSIS_CONFIG

logger = logging.getLogger("amazon_scraper.visualizer")

class ProductVisualizer:
    """Visualizer for creating charts and plots from product data."""
    
    def __init__(self, analyzer: Optional[ProductAnalyzer] = None, 
                 output_dir: Optional[Path] = None):
        """
        Initialize the visualizer.
        
        Args:
            analyzer: Optional ProductAnalyzer instance
            output_dir: Optional output directory for saving charts
        """
        self.analyzer = analyzer or ProductAnalyzer()
        self.output_dir = output_dir or Path(ANALYSIS_CONFIG["charts_dir"])
        self.default_format = ANALYSIS_CONFIG.get("default_chart_format", "png")
        self.default_dpi = ANALYSIS_CONFIG.get("default_chart_dpi", 300)
        plt.rcParams['font.family'] = 'Arial'  # Add this line
        # Create output directory if it doesn't exist
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
        
        # Set default style
        sns.set_style("whitegrid")
        logger.info("ProductVisualizer initialized")
    
    def create_price_distribution(self, products: List[TrendingProduct], 
                                 site_name: str = None, 
                                 save: bool = True) -> Optional[Path]:
        """
        Create a price distribution chart.
        
        Args:
            products: List of products to visualize
            site_name: Optional site name for chart title and filename
            save: Whether to save the chart to disk
            
        Returns:
            Optional[Path]: Path to saved chart if save=True
        """
        logger.info("Creating price distribution chart")
        
        # Prepare DataFrame
        df = self.analyzer.prepare_dataframe(products)
        if df.empty or 'price_numeric' not in df.columns:
            logger.warning("Insufficient data for price distribution chart")
            return None
        
        # Drop missing values
        price_data = df['price_numeric'].dropna()
        if len(price_data) < 5:  # Arbitrary minimum for meaningful distribution
            logger.warning("Not enough price data for distribution chart")
            return None
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Create distribution plot
        sns.histplot(price_data, kde=True, bins=20)
        
        # Add vertical lines for statistics
        plt.axvline(price_data.mean(), color='r', linestyle='--', alpha=0.7, label=f'Mean: {price_data.mean():.2f}')
        plt.axvline(price_data.median(), color='g', linestyle='-.', alpha=0.7, label=f'Median: {price_data.median():.2f}')
        
        # Set title and labels
        title = f"Price Distribution - {site_name}" if site_name else "Price Distribution"
        plt.title(title, fontsize=14)
        plt.xlabel(f"Price ({ANALYSIS_CONFIG.get('price_currency', '₹')})", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.legend()
        
        # Save chart if requested
        if save:
            filename = f"price_distribution_{site_name or 'all'}.{self.default_format}"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=self.default_dpi, bbox_inches='tight')
            logger.info(f"Saved price distribution chart to {filepath}")
            plt.close()
            return filepath
        
        return None
    
    def create_rating_chart(self, products: List[TrendingProduct], 
                           site_name: str = None,
                           save: bool = True) -> Optional[Path]:
        """
        Create a rating distribution chart.
        
        Args:
            products: List of products to visualize
            site_name: Optional site name for chart title and filename
            save: Whether to save the chart to disk
            
        Returns:
            Optional[Path]: Path to saved chart if save=True
        """
        logger.info("Creating rating distribution chart")
        
        # Prepare DataFrame
        df = self.analyzer.prepare_dataframe(products)
        if df.empty or 'rating' not in df.columns:
            logger.warning("Insufficient data for rating chart")
            return None
        
        # Create figure
        plt.figure(figsize=(10, 6))
        
        # Create countplot grouped by rating group
        if 'rating_group' in df.columns:
            order = ['0-2 ★', '2-3 ★', '3-4 ★', '4-5 ★']  # Ensure correct order
            ax = sns.countplot(data=df, x='rating_group', hue='rating_group', order=order, 
                       palette='viridis', legend=False)
            
            # Add count labels on top of bars
            for container in ax.containers:
                ax.bar_label(container)
        else:
            # Fallback to histogram of ratings
            sns.histplot(df['rating'].dropna(), bins=10, kde=True)
        
        # Set title and labels
        title = f"Rating Distribution - {site_name}" if site_name else "Rating Distribution"
        plt.title(title, fontsize=14)
        plt.xlabel("Rating Range", fontsize=12)
        plt.ylabel("Number of Products", fontsize=12)
        
        # Save chart if requested
        if save:
            filename = f"rating_distribution_{site_name or 'all'}.{self.default_format}"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=self.default_dpi, bbox_inches='tight')
            logger.info(f"Saved rating distribution chart to {filepath}")
            plt.close()
            return filepath
        
        return None
    
    def create_price_rating_scatter(self, products: List[TrendingProduct], 
                                   site_name: str = None,
                                   save: bool = True) -> Optional[Path]:
        """
        Create a price vs. rating scatter plot.
        
        Args:
            products: List of products to visualize
            site_name: Optional site name for chart title and filename
            save: Whether to save the chart to disk
            
        Returns:
            Optional[Path]: Path to saved chart if save=True
        """
        logger.info("Creating price vs. rating scatter plot")
        
        # Prepare DataFrame
        df = self.analyzer.prepare_dataframe(products)
        if df.empty or 'price_numeric' not in df.columns or 'rating' not in df.columns:
            logger.warning("Insufficient data for price-rating scatter plot")
            return None
        
        # Drop missing values
        df_clean = df.dropna(subset=['price_numeric', 'rating'])
        if len(df_clean) < 5:  # Arbitrary minimum for meaningful plot
            logger.warning("Not enough data points for scatter plot")
            return None
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Create scatter plot with size proportional to review count if available
        if 'review_count' in df_clean.columns and df_clean['review_count'].notna().any():
            # Use log scale for size to handle large differences in review counts
            size_col = 'log_review_count' if 'log_review_count' in df_clean.columns else 'review_count'
            sizes = 20 + 100 * df_clean[size_col] / df_clean[size_col].max()
            
            scatter = plt.scatter(
                df_clean['price_numeric'], 
                df_clean['rating'],
                s=sizes,
                alpha=0.6,
                c=df_clean['rating'],
                cmap='viridis',
                edgecolors='w'
            )
            
            # Add a colorbar
            cbar = plt.colorbar(scatter)
            cbar.set_label('Rating', rotation=270, labelpad=20)
            
            # Add size legend
            handles, labels = scatter.legend_elements(prop="sizes", alpha=0.6, 
                                                     num=4, func=lambda x: (x - 20) / 100 * df_clean[size_col].max())
            legend_labels = [f"{int(float(l.split('{')[1].split('}')[0]))} reviews" for l in labels]
            plt.legend(handles, legend_labels, loc="upper right", title="Review Count")
            
        else:
            # Simple scatter plot without review count sizing
            plt.scatter(df_clean['price_numeric'], df_clean['rating'], alpha=0.7)
        
        # Add a trend line
        sns.regplot(x='price_numeric', y='rating', data=df_clean, 
                   scatter=False, ci=None, color='red', line_kws={'linestyle': '--'})
        
        # Set title and labels
        title = f"Price vs. Rating - {site_name}" if site_name else "Price vs. Rating"
        plt.title(title, fontsize=14)
        plt.xlabel(f"Price ({ANALYSIS_CONFIG.get('price_currency', '₹')})", fontsize=12)
        plt.ylabel("Rating (out of 5)", fontsize=12)
        
        # Limit y-axis to reasonable rating range
        plt.ylim(0, 5.5)
        
        # Save chart if requested
        if save:
            filename = f"price_rating_scatter_{site_name or 'all'}.{self.default_format}"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=self.default_dpi, bbox_inches='tight')
            logger.info(f"Saved price-rating scatter plot to {filepath}")
            plt.close()
            return filepath
        
        return None
    
    def create_category_analysis(self, products: List[TrendingProduct], 
                               site_name: str = None,
                               save: bool = True) -> Optional[Path]:
        """
        Create a category analysis chart.
        
        Args:
            products: List of products to visualize
            site_name: Optional site name for chart title and filename
            save: Whether to save the chart to disk
            
        Returns:
            Optional[Path]: Path to saved chart if save=True
        """
        logger.info("Creating category analysis chart")
        
        # Prepare DataFrame
        df = self.analyzer.prepare_dataframe(products)
        if df.empty or 'category' not in df.columns:
            logger.warning("Insufficient data for category analysis chart")
            return None
        
        # Count categories
        category_counts = df['category'].value_counts()
        if len(category_counts) < 2:
            logger.warning("Not enough different categories for analysis chart")
            return None
        
        # Limit to top categories if there are too many
        if len(category_counts) > 10:
            other_count = category_counts[10:].sum()
            category_counts = category_counts[:10]
            category_counts['Other'] = other_count
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Create pie chart
        plt.pie(
            category_counts,
            labels=category_counts.index,
            autopct='%1.1f%%',
            shadow=False,
            startangle=90,
            explode=[0.05] * len(category_counts)  # Slight separation for all slices
        )
        
        # Equal aspect ratio ensures the pie chart is drawn as a circle
        plt.axis('equal')
        
        # Set title
        title = f"Category Distribution - {site_name}" if site_name else "Category Distribution"
        plt.title(title, fontsize=14)
        
        # Save chart if requested
        if save:
            filename = f"category_distribution_{site_name or 'all'}.{self.default_format}"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=self.default_dpi, bbox_inches='tight')
            logger.info(f"Saved category distribution chart to {filepath}")
            plt.close()
            return filepath
        
        return None
    
    def create_price_by_category(self, products: List[TrendingProduct],
                                site_name: str = None,
                                save: bool = True) -> Optional[Path]:
        """
        Create a box plot showing price distribution by category.
        
        Args:
            products: List of products to visualize
            site_name: Optional site name for chart title and filename
            save: Whether to save the chart to disk
            
        Returns:
            Optional[Path]: Path to saved chart if save=True
        """
        logger.info("Creating price by category box plot")
        
        # Prepare DataFrame
        df = self.analyzer.prepare_dataframe(products)
        if df.empty or 'price_numeric' not in df.columns or 'category' not in df.columns:
            logger.warning("Insufficient data for price by category plot")
            return None
            
        # Drop missing values
        df_clean = df.dropna(subset=['price_numeric', 'category'])
        if len(df_clean) < 5:
            logger.warning("Not enough data points for box plot")
            return None
            
        # Get the most common categories (limit to top 8)
        top_categories = df_clean['category'].value_counts().head(8).index.tolist()
        df_filtered = df_clean[df_clean['category'].isin(top_categories)]
        
        if len(df_filtered) < 5:
            logger.warning("Not enough data points after category filtering")
            return None
        
        # Create figure
        plt.figure(figsize=(14, 8))
        
        # Create box plot
        ax = sns.boxplot(x='category', y='price_numeric', data=df_filtered)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Set title and labels
        title = f"Price Distribution by Category - {site_name}" if site_name else "Price Distribution by Category"
        plt.title(title, fontsize=14)
        plt.xlabel("Category", fontsize=12)
        plt.ylabel(f"Price ({ANALYSIS_CONFIG.get('price_currency', '₹')})", fontsize=12)
        
        # Adjust layout for rotated labels
        plt.tight_layout()
        
        # Save chart if requested
        if save:
            filename = f"price_by_category_{site_name or 'all'}.{self.default_format}"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=self.default_dpi, bbox_inches='tight')
            logger.info(f"Saved price by category box plot to {filepath}")
            plt.close()
            return filepath
        
        return None
    
    def create_dashboard(self, products: List[TrendingProduct], 
                       site_name: str = None,
                       save: bool = True) -> Optional[Path]:
        """
        Create a comprehensive dashboard with multiple charts.
        
        Args:
            products: List of products to visualize
            site_name: Optional site name for chart title and filename
            save: Whether to save the chart to disk
            
        Returns:
            Optional[Path]: Path to saved dashboard if save=True
        """
        logger.info("Creating comprehensive dashboard")
        
        # Prepare DataFrame
        df = self.analyzer.prepare_dataframe(products)
        if df.empty:
            logger.warning("Insufficient data for dashboard")
            return None
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(18, 14))
        fig.subplots_adjust(hspace=0.3, wspace=0.3)
        
        # Set dashboard title
        dashboard_title = f"Product Analysis Dashboard - {site_name}" if site_name else "Product Analysis Dashboard"
        fig.suptitle(dashboard_title, fontsize=16, y=0.95)
        
        # 1. Price Distribution (top-left)
        if 'price_numeric' in df.columns:
            price_data = df['price_numeric'].dropna()
            if len(price_data) >= 5:
                sns.histplot(price_data, kde=True, bins=20, ax=axes[0, 0])
                axes[0, 0].axvline(price_data.mean(), color='r', linestyle='--', 
                                  alpha=0.7, label=f'Mean: {price_data.mean():.2f}')
                axes[0, 0].axvline(price_data.median(), color='g', linestyle='-.', 
                                  alpha=0.7, label=f'Median: {price_data.median():.2f}')
                axes[0, 0].set_title("Price Distribution", fontsize=12)
                axes[0, 0].set_xlabel(f"Price ({ANALYSIS_CONFIG.get('price_currency', '₹')})")
                axes[0, 0].set_ylabel("Frequency")
                axes[0, 0].legend(loc='upper right')
        
        # 2. Rating Distribution (top-right)
        if 'rating_group' in df.columns:
            order = ['0-2 ★', '2-3 ★', '3-4 ★', '4-5 ★']
            sns.countplot(data=df, x='rating_group', hue='rating_group', order=order, 
                  palette='viridis', ax=axes[0, 1], legend=False)

            axes[0, 1].set_title("Rating Distribution", fontsize=12)
            axes[0, 1].set_xlabel("Rating Range")
            axes[0, 1].set_ylabel("Number of Products")
            for container in axes[0, 1].containers:
                axes[0, 1].bar_label(container)
        elif 'rating' in df.columns:
            sns.histplot(df['rating'].dropna(), bins=10, kde=True, ax=axes[0, 1])
            axes[0, 1].set_title("Rating Distribution", fontsize=12)
            axes[0, 1].set_xlabel("Rating")
            axes[0, 1].set_ylabel("Frequency")
        
        # 3. Price vs. Rating Scatter (bottom-left)
        if all(col in df.columns for col in ['price_numeric', 'rating']):
            df_clean = df.dropna(subset=['price_numeric', 'rating'])
            if len(df_clean) >= 5:
                if 'review_count' in df_clean.columns and df_clean['review_count'].notna().any():
                    size_col = 'log_review_count' if 'log_review_count' in df_clean.columns else 'review_count'
                    sizes = 20 + 100 * df_clean[size_col] / df_clean[size_col].max()
                    
                    scatter = axes[1, 0].scatter(
                        df_clean['price_numeric'], 
                        df_clean['rating'],
                        s=sizes,
                        alpha=0.6,
                        c=df_clean['rating'],
                        cmap='viridis',
                        edgecolors='w'
                    )
                else:
                    scatter = axes[1, 0].scatter(df_clean['price_numeric'], df_clean['rating'], alpha=0.7)
                
                sns.regplot(x='price_numeric', y='rating', data=df_clean, 
                           scatter=False, ci=None, color='red', line_kws={'linestyle': '--'}, ax=axes[1, 0])
                axes[1, 0].set_title("Price vs. Rating", fontsize=12)
                axes[1, 0].set_xlabel(f"Price ({ANALYSIS_CONFIG.get('price_currency', '₹')})")
                axes[1, 0].set_ylabel("Rating (out of 5)")
                axes[1, 0].set_ylim(0, 5.5)
        
        # 4. Category Distribution (bottom-right)
        if 'category' in df.columns:
            category_counts = df['category'].value_counts()
            if len(category_counts) >= 2:
                if len(category_counts) > 7:
                    other_count = category_counts[7:].sum()
                    category_counts = category_counts[:7]
                    category_counts['Other'] = other_count
                
                axes[1, 1].pie(
                    category_counts,
                    labels=category_counts.index,
                    autopct='%1.1f%%',
                    shadow=False,
                    startangle=90
                )
                axes[1, 1].set_title("Category Distribution", fontsize=12)
                axes[1, 1].axis('equal')
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Save dashboard if requested
        if save:
            filename = f"dashboard_{site_name or 'all'}.{self.default_format}"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=self.default_dpi, bbox_inches='tight')
            logger.info(f"Saved dashboard to {filepath}")
            plt.close()
            return filepath
        
        return None
    
    def generate_all_charts(self, products: List[TrendingProduct], site_name: str = None) -> List[Path]:
        """
        Generate all available charts for the given products.
        
        Args:
            products: List of products to visualize
            site_name: Optional site name for chart titles and filenames
            
        Returns:
            List[Path]: Paths to all saved charts
        """
        logger.info(f"Generating all charts for {'site: ' + site_name if site_name else 'all products'}")
        
        saved_charts = []
        
        # Create and save individual charts
        chart_methods = [
            self.create_price_distribution,
            self.create_rating_chart,
            self.create_price_rating_scatter,
            self.create_category_analysis,
            self.create_price_by_category
        ]
        
        for method in chart_methods:
            try:
                chart_path = method(products, site_name)
                if chart_path:
                    saved_charts.append(chart_path)
            except Exception as e:
                logger.error(f"Error creating chart {method.__name__}: {str(e)}")
        
        # Create and save dashboard
        try:
            dashboard_path = self.create_dashboard(products, site_name)
            if dashboard_path:
                saved_charts.append(dashboard_path)
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
        
        logger.info(f"Generated {len(saved_charts)} charts")
        return saved_charts