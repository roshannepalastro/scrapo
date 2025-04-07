"""
Data models for product information.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import datetime
import re

@dataclass
class TrendingProduct:
    """Data model for a trending product."""
    title: str
    url: str
    price: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    image_url: Optional[str] = None
    rank: Optional[int] = None
    category: Optional[str] = None
    availability: Optional[str] = None
    description: Optional[str] = None
    features: List[str] = field(default_factory=list)
    source: str = "amazon.in"
    extracted_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the product to a dictionary."""
        return asdict(self)
    
    def get_numeric_price(self) -> Optional[float]:
        """Extract numeric price from price string."""
        if not self.price:
            return None
        
        # Extract digits and decimal point from price string
        numeric_str = re.sub(r'[^\d.]', '', self.price)
        try:
            return float(numeric_str)
        except ValueError:
            return None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendingProduct':
        """Create a product instance from a dictionary."""
        # Filter out keys that are not fields in the dataclass
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)