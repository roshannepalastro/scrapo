"""
Implementation of Daraz.np scraper.
"""

import logging
import re
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

from ..config import SCRAPER_CONFIG
from ..models.product import TrendingProduct
from .base import WebsiteScraper

logger = logging.getLogger("amazon_scraper.daraz")

class DarazNpScraper(WebsiteScraper):
    """Concrete implementation of WebsiteScraper for Daraz.np."""
    
    def __init__(self):
        """Initialize the Daraz.np scraper using configuration."""
        config = SCRAPER_CONFIG["daraz_np"]
        headers = {"User-Agent": config["user_agent"]} if "user_agent" in config else None
        super().__init__(config["base_url"], headers)
        self.trending_pages = config.get("trending_pages", ["/trending-products/", "/top-selling-products/"])
        logger.info("DarazNpScraper initialized")
    
    def get_trending_products(self) -> List[TrendingProduct]:
        """
        Get trending products from Daraz.np.
        
        Returns:
            List[TrendingProduct]: A list of trending products
        """
        logger.info("Starting to fetch trending products from Daraz.np")
        
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
        """Extract products from a specific Daraz page using BeautifulSoup."""
        response = self.get_page(page_path)
        if not response:
            return []
        
        products = []
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.debug("Successfully parsed page with BeautifulSoup")
            
            # Find the product grid items
            # Daraz typically uses different class names than Amazon
            product_items = soup.select('.Bm3ON, .c2iYAv') or \
                           soup.select('.c1ZEkM') or \
                           soup.select('.c5TXIP')
            
            logger.info(f"Found {len(product_items)} potential product items")
            
            for i, item in enumerate(product_items[:20]):  # Limit to top 20
                try:
                    # Extract product ID if available
                    product_id = None
                    if hasattr(item, 'attrs'):
                        for attr_name, attr_value in item.attrs.items():
                            if 'data-item-id' in attr_name.lower() and attr_value:
                                product_id = attr_value
                                break
                    
                    # Try to get title
                    title_elem = item.select_one('.c16H9d, .c3KeDq, .c16TX_') or \
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
                            title = f"Unknown Product {product_id or i+1}"
                    
                    # Extract URL
                    url = None
                    link_elem = item.select_one('a[href]')
                    if link_elem and link_elem.has_attr('href'):
                        url = link_elem['href']
                        if not url.startswith('http'):
                            url = f"{self.base_url}{url}"
                    else:
                        url = f"{self.base_url}/products/{product_id}" if product_id else f"{self.base_url}/trending-products/"
                            
                    # Extract price with broader selectors
                    price = None
                    price_selectors = [
                        '.c13VH6, .c1-B2V',  # Common Daraz price classes
                        '.c3gUW0',           # Sale price
                        '.c1hkC1'            # Original price
                    ]
                    for selector in price_selectors:
                        price_elem = item.select_one(selector)
                        if price_elem:
                            price = price_elem.get_text().strip()
                            break
                    if not price:
                        # Fallback to any span with currency symbol
                        price_elem = item.find('span', string=lambda x: x and ('Rs.' in x or 'रू' in x or 'NPR' in x))
                        price = price_elem.get_text().strip() if price_elem else None

                    # Extract image URL
                    image_url = None
                    img_elem = item.select_one('img[src]')
                    if img_elem and img_elem.has_attr('src'):
                        image_url = img_elem['src']
                    elif img_elem and img_elem.has_attr('data-src'):
                        image_url = img_elem['data-src']  # Daraz often uses lazy loading
                    
                    # Extract rating with more options
                    rating = None
                    rating_selectors = [
                        '.c3XbGJ',  # Rating stars container
                        '.c3dn4k',  # Rating value
                        '[data-rating]'  # Elements with data-rating attribute
                    ]
                    for selector in rating_selectors:
                        rating_elem = item.select_one(selector)
                        if rating_elem:
                            if rating_elem.has_attr('data-rating'):
                                try:
                                    rating = float(rating_elem['data-rating'])
                                    break
                                except (ValueError, TypeError):
                                    pass
                            
                            rating_text = rating_elem.get_text().strip()
                            rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                            if rating_match:
                                rating = float(rating_match.group(1))
                                break
                    
                    # Extract review count with more robust selectors
                    review_count = None
                    review_selectors = [
                        '.c3XbGJ + span',  # Reviews count often next to rating
                        '.c2JB4x',         # Common review count class
                        'span[data-reviews]'  # Elements with data-reviews attribute
                    ]
                    for selector in review_selectors:
                        review_elem = item.select_one(selector)
                        if review_elem:
                            if review_elem.has_attr('data-reviews'):
                                try:
                                    review_count = int(review_elem['data-reviews'])
                                    break
                                except (ValueError, TypeError):
                                    pass
                                
                            review_text = review_elem.get_text().strip()
                            count_match = re.search(r'(\d+[\d,]*)', review_text)
                            if count_match:
                                review_count = int(count_match.group(1).replace(',', ''))
                                break
                    
                    # Extract category if available
                    category = None
                    breadcrumb = soup.select_one('.c1nVRb, .ant-breadcrumb')  # Daraz breadcrumb classes
                    if breadcrumb:
                        category_elems = breadcrumb.select('a, span')
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
        """Extract featured products from Daraz homepage as fallback."""
        logger.info("Attempting to extract trending products from homepage")
        response = self.get_page("/")
        if not response:
            logger.error("Failed to fetch homepage")
            return []
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for carousel items which often contain trending/featured products
            carousel_items = soup.select('.card-jfy-item-wrapper, .slick-slide > div') or \
                            soup.select('.c1_t2i, .c2iYAv')
            
            logger.info(f"Found {len(carousel_items)} carousel items on homepage")
            
            products = []
            for i, item in enumerate(carousel_items[:10]):  # Limit to top 10
                try:
                    # Extract title
                    title_elem = item.select_one('img[alt]') or item.select_one('.c16H9d, .c3KeDq')
                    title = ""
                    if title_elem:
                        if title_elem.name == 'img' and title_elem.has_attr('alt'):
                            title = title_elem['alt']
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
                    elif img_elem and img_elem.has_attr('data-src'):
                        image_url = img_elem['data-src']
                    
                    # Extract price if available on homepage
                    price = None
                    price_elem = item.select_one('.c13VH6, .c1-B2V, .c3gUW0')
                    if price_elem:
                        price = price_elem.get_text().strip()
                    
                    product = TrendingProduct(
                        title=title,
                        url=url,
                        image_url=image_url,
                        price=price,
                        rank=i + 1,
                        source="daraz.np_homepage"
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
                    url="https://www.daraz.np",
                    source="daraz.np_not_found"
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
            desc_elem = soup.select_one('.html-content, .pdp-product-desc, .pdp-mod-description')
            if desc_elem:
                description = desc_elem.get_text().strip()[:500]  # Limit length
                product.description = description
            
            # Extract features/specifications
            features = []
            feature_elems = soup.select('.specification-keys, .pdp-product-highlights li, .key-features li')
            for elem in feature_elems[:10]:  # Limit to 10 features
                feature_text = elem.get_text().strip()
                if feature_text and len(feature_text) > 5:  # Minimum length filter
                    features.append(feature_text)
            
            if features:
                product.features = features
            
            # Extract availability
            availability = None
            avail_elem = soup.select_one('.quantity-content, .pdp-stock')
            if avail_elem:
                availability = avail_elem.get_text().strip()
                product.availability = availability
            
            # Update category if we didn't have it
            if not product.category:
                breadcrumb = soup.select_one('.c1nVRb, .ant-breadcrumb, .pdp-breadcrumb')
                if breadcrumb:
                    category_elems = breadcrumb.select('a, span')
                    if category_elems:
                        product.category = category_elems[-1].get_text().strip()
            
            # Extract seller information if available
            seller_elem = soup.select_one('.seller-name, .pdp-seller-info-name')
            if seller_elem:
                product.seller = seller_elem.get_text().strip()
            
            # Extract discount percentage if available
            discount_elem = soup.select_one('.pdp-product-price__discount, .discount-percentage')
            if discount_elem:
                discount_text = discount_elem.get_text().strip()
                discount_match = re.search(r'(\d+)%', discount_text)
                if discount_match:
                    product.discount_percentage = int(discount_match.group(1))
            
            logger.info(f"Successfully enriched product: {product.title}")
            return product
            
        except Exception as e:
            logger.error(f"Error extracting product details: {str(e)}")
            return product
