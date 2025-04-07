"""
Implementation of Amazon.in scraper.
"""

import logging
import re
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

from ..config import SCRAPER_CONFIG
from ..models.product import TrendingProduct
from .base import WebsiteScraper

logger = logging.getLogger("amazon_scraper.amazon")

class AmazonInScraper(WebsiteScraper):
    """Concrete implementation of WebsiteScraper for Amazon.in."""
    
    def __init__(self):
        """Initialize the Amazon.in scraper using configuration."""
        config = SCRAPER_CONFIG["amazon_in"]
        headers = {"User-Agent": config["user_agent"]} if "user_agent" in config else None
        super().__init__(config["base_url"], headers)
        self.trending_pages = config.get("trending_pages", ["/gp/bestsellers/"])
        logger.info("AmazonInScraper initialized")
    
    def get_trending_products(self) -> List[TrendingProduct]:
        """
        Get trending products from Amazon.in.
        
        Returns:
            List[TrendingProduct]: A list of trending products
        """
        logger.info("Starting to fetch trending products from Amazon.in")
        
        # Try different product listing pages in order
        for page_path in self.trending_pages:
            logger.info(f"Attempting to fetch trending products from page: {page_path}")
            products = self._extract_products_from_page(page_path)
            
            if products:
                logger.info(f"Successfully found {len(products)} trending products on {page_path}")
                return products
        
        logger.warning("Could not find trending products on any standard pages. Falling back to homepage.")
        return self._extract_products_from_homepage()
    
    def _extract_products_from_page(self, page_path: str) -> List[TrendingProduct]:
        """Extract products from a specific Amazon page using BeautifulSoup."""
        response = self.get_page(page_path)
        if not response:
            return []
        
        products = []
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.debug("Successfully parsed page with BeautifulSoup")
            
            # Find the product grid items
            # First try bestseller grid items
            product_items = soup.select('li.a-carousel-card, div[data-asin]:not([data-asin=""])') or \
                           soup.select('.a-carousel-card') or \
                           soup.select('[data-asin]:not([data-asin=""])')
            
            logger.info(f"Found {len(product_items)} potential product items")
            
            for i, item in enumerate(product_items[:20]):  # Limit to top 20
                try:
                    # Extract ASIN
                    asin = item.get('data-asin')
                    if not asin and hasattr(item, 'attrs'):
                        for attr_name, attr_value in item.attrs.items():
                            if 'asin' in attr_name.lower() and attr_value:
                                asin = attr_value
                                break
                    
                    # Try to get title
                    title_elem = item.select_one('.a-size-medium, .a-size-base, .a-link-normal > span') or \
                                item.select_one('img[alt]')
                    
                    title = ""
                    if title_elem:
                        if title_elem.name == 'img' and title_elem.has_attr('alt'):
                            title = title_elem['alt']
                        else:
                            title = title_elem.get_text().strip()
                    
                    if not title:
                        # Try to find any text that might be a title
                        potential_title = item.get_text().strip()
                        if potential_title:
                            title = potential_title[:100]  # Limit title length
                        else:
                            title = f"Unknown Product {asin or i+1}"
                    
                    # Extract URL
                    url = None
                    link_elem = item.select_one('a[href]')
                    if link_elem and link_elem.has_attr('href'):
                        url = link_elem['href']
                        if not url.startswith('http'):
                            url = f"{self.base_url}{url}"
                    else:
                        url = f"{self.base_url}/dp/{asin}" if asin else f"{self.base_url}/s?k=trending"
                            
                    # Extract price with broader selectors
                    price = None
                    price_selectors = [
                        '.a-price .a-offscreen',
                        '.a-price-whole',
                        '.p13n-sc-price',
                        '[data-a-price-whole]'
                    ]
                    for selector in price_selectors:
                        price_elem = item.select_one(selector)
                        if price_elem:
                            price = price_elem.get_text().strip()
                            break
                    if not price:
                        # Fallback to any span with currency symbol
                        price_elem = item.find('span', string=lambda x: x and '₹' in x)
                        price = price_elem.get_text().strip() if price_elem else None

                    # Extract image URL
                    image_url = None
                    img_elem = item.select_one('img[src]')
                    if img_elem and img_elem.has_attr('src'):
                        image_url = img_elem['src']
                    
                    # Extract rating with more options
                    rating = None
                    rating_selectors = [
                        'i.a-icon-star',
                        '.a-star-medium-4',
                        'span[data-a-icon-alt*="out of 5 stars"]',
                        '.a-icon-alt'
                    ]
                    for selector in rating_selectors:
                        rating_elem = item.select_one(selector)
                        if rating_elem:
                            rating_text = rating_elem.get_text().strip()
                            rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                            if rating_match:
                                rating = float(rating_match.group(1))
                                break
                    if not rating:
                        # Fallback to attribute or parent text
                        rating_elem = item.find(class_=re.compile('star'))
                        if rating_elem and rating_elem.get('title'):
                            rating_match = re.search(r'(\d+(\.\d+)?)', rating_elem['title'])
                            rating = float(rating_match.group(1)) if rating_match else None
                                    
                    # Extract review count with more robust selectors
                    review_count = None
                    review_selectors = [
                        'a.a-link-normal[title*="review"]',
                        '.a-size-small[aria-label*="review"]',
                        'span[id*="customerReviews"]'
                    ]
                    for selector in review_selectors:
                        review_elem = item.select_one(selector)
                        if review_elem:
                            review_text = review_elem.get_text().strip()
                            count_match = re.search(r'(\d+[\d,]*)', review_text)
                            if count_match:
                                review_count = int(count_match.group(1).replace(',', ''))
                                break
                    if not review_count:
                        # Fallback to nearby text
                        review_elem = item.find('span', string=re.compile(r'\d+[\d,]*\s*(ratings|reviews)'))
                        if review_elem:
                            count_match = re.search(r'(\d+[\d,]*)', review_elem.text)
                            review_count = int(count_match.group(1).replace(',', '')) if count_match else None

                            
                    # Extract category if available
                    category = None
                    breadcrumb = soup.select_one('#wayfinding-breadcrumbs_feature_div')
                    if breadcrumb:
                        category_elems = breadcrumb.select('a')
                        if category_elems:
                            category = category_elems[-1].get_text().strip()
                    
                    # Create product object
                    product = TrendingProduct(
                        title=title,
                        url=url,
                        price=price,
                        image_url=image_url,
                        rating=rating,
                        review_count=review_count,
                        rank=i + 1,
                        category=category
                    )
                    
                    products.append(product)
                    logger.debug(f"Extracted product: {title} (Rank: {i+1})")
                    
                except Exception as e:
                    logger.error(f"Error extracting product {i+1}: {str(e)}")
            
            logger.info(f"Extracted {len(products)} products from {page_path}")
            return products
            
        except Exception as e:
            logger.error(f"Error parsing products page: {str(e)}")
            return []
    
    def _extract_products_from_homepage(self) -> List[TrendingProduct]:
        """Extract featured products from Amazon homepage as fallback."""
        logger.info("Attempting to extract trending products from homepage")
        response = self.get_page("/")
        if not response:
            logger.error("Failed to fetch homepage")
            return []
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for carousel items which often contain trending/featured products
            carousel_items = soup.select('.a-carousel-card') or \
                            soup.select('.feed-carousel-card')
            
            logger.info(f"Found {len(carousel_items)} carousel items on homepage")
            
            products = []
            for i, item in enumerate(carousel_items[:10]):  # Limit to top 10
                try:
                    # Extract title
                    title_elem = item.select_one('img[alt]') or item.select_one('a[title]')
                    title = ""
                    if title_elem:
                        if title_elem.name == 'img' and title_elem.has_attr('alt'):
                            title = title_elem['alt']
                        elif title_elem.has_attr('title'):
                            title = title_elem['title']
                        else:
                            title = title_elem.get_text().strip()
                    
                    if not title:
                        title = f"Featured Product {i+1}"
                    
                    # Extract URL
                    url = self.base_url
                    link_elem = item.select_one('a[href]')
                    if link_elem and link_elem.has_attr('href'):
                        url = link_elem['href']
                        if not url.startswith('http'):
                            url = f"{self.base_url}{url}"
                    
                    # Extract image URL
                    image_url = None
                    img_elem = item.select_one('img[src]')
                    if img_elem and img_elem.has_attr('src'):
                        image_url = img_elem['src']
                    
                    product = TrendingProduct(
                        title=title,
                        url=url,
                        image_url=image_url,
                        rank=i + 1,
                        source="amazon.in_homepage"
                    )
                    
                    products.append(product)
                    logger.debug(f"Extracted featured product: {title}")
                    
                except Exception as e:
                    logger.error(f"Error parsing homepage product: {str(e)}")
            
            if products:
                logger.info(f"Extracted {len(products)} featured products from homepage")
                return products
            else:
                logger.warning("No featured products found on homepage")
                return [TrendingProduct(
                    title="No trending products found",
                    url="https://www.amazon.in",
                    source="amazon.in_not_found"
                )]
                
        except Exception as e:
            logger.error(f"Error parsing homepage: {str(e)}")
            return []
            
    def get_product_details(self, product: TrendingProduct) -> TrendingProduct:
        """
        Enrich a product with additional details from its product page.
        
        Args:
            product: The basic product to enrich
            
        Returns:
            TrendingProduct: Enriched product with additional details
        """
        logger.info(f"Fetching detailed information for product: {product.title}")
        
        response = self.get_page(product.url)
        if not response:
            logger.warning(f"Failed to fetch product details page: {product.url}")
            return product
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract description
            description = None
            desc_elem = soup.select_one('#productDescription, #feature-bullets, #aplus')
            if desc_elem:
                description = desc_elem.get_text().strip()[:500]  # Limit length
                product.description = description
            
            # Extract features
            features = []
            feature_elems = soup.select('#feature-bullets li, #detailBullets li, .a-unordered-list li')
            for elem in feature_elems[:10]:  # Limit to 10 features
                feature_text = elem.get_text().strip()
                if feature_text and len(feature_text) > 5:  # Minimum length filter
                    features.append(feature_text)
            
            if features:
                product.features = features
            
            # Extract availability
            availability = None
            avail_elem = soup.select_one('#availability, #outOfStock')
            if avail_elem:
                availability = avail_elem.get_text().strip()
                product.availability = availability
            
            # Update category if we didn't have it
            if not product.category:
                breadcrumb = soup.select_one('#wayfinding-breadcrumbs_feature_div')
                if breadcrumb:
                    category_elems = breadcrumb.select('a')
                    if category_elems:
                        product.category = category_elems[-1].get_text().strip()
            
            logger.info(f"Successfully enriched product: {product.title}")
            return product
            
        except Exception as e:
            logger.error(f"Error extracting product details: {str(e)}")
            return product