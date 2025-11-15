"""
Product catalog utilities for the BoundCart governed agent commerce reference.
"""

import json
from typing import List, Optional
from pathlib import Path

from ..models.schemas import Product
from ..storage import storage


class CatalogManager:
    """Manages product catalog operations."""
    
    def __init__(self, products_file: str = "data/products.json"):
        """Initialize catalog manager with products file path."""
        self.products_file = Path(products_file)
        self._load_catalog()
    
    def _load_catalog(self) -> None:
        """Load products from JSON file into storage."""
        try:
            with open(self.products_file, 'r') as f:
                products_data = json.load(f)
                
            for product_data in products_data:
                product = Product(**product_data)
                storage.add_product(product)
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Products file not found: {self.products_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in products file: {e}")
    
    def get_all_products(self) -> List[Product]:
        """Get all products in the catalog."""
        return storage.get_all_products()
    
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Get a specific product by ID."""
        return storage.get_product(product_id)
    
    def filter_by_category(self, category: str) -> List[Product]:
        """Filter products by category."""
        products = storage.get_all_products()
        return [p for p in products if p.category == category]
    
    def filter_by_max_price(self, max_price: float) -> List[Product]:
        """Filter products by maximum price."""
        products = storage.get_all_products()
        return [p for p in products if p.price <= max_price]
    
    def filter_by_shipping_speed(self, max_days: int) -> List[Product]:
        """Filter products by maximum shipping days."""
        products = storage.get_all_products()
        return [p for p in products if p.shipping_eta_days <= max_days]
    
    def filter_by_availability(self, min_inventory: int = 1) -> List[Product]:
        """Filter products by availability."""
        products = storage.get_all_products()
        return [p for p in products if p.inventory >= min_inventory]
    
    def search_candidates(
        self,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        max_shipping_days: Optional[int] = None,
        min_inventory: int = 1
    ) -> List[Product]:
        """Search for products matching multiple criteria."""
        products = storage.get_all_products()
        
        # Apply filters sequentially
        if category:
            products = [p for p in products if p.category == category]
        
        if max_price is not None:
            products = [p for p in products if p.price <= max_price]
        
        if max_shipping_days is not None:
            products = [p for p in products if p.shipping_eta_days <= max_shipping_days]
        
        products = [p for p in products if p.inventory >= min_inventory]
        
        return products
    
    def get_shortlisted_candidates(
        self,
        category: str,
        max_price: float,
        max_shipping_days: int,
        limit: int = 5
    ) -> List[Product]:
        """Get shortlisted candidates for a given criteria."""
        candidates = self.search_candidates(
            category=category,
            max_price=max_price,
            max_shipping_days=max_shipping_days
        )
        
        # Sort by price (ascending) and then by shipping time (ascending)
        candidates.sort(key=lambda p: (p.price, p.shipping_eta_days))
        
        return candidates[:limit]
    
    def check_availability(self, product_id: str, quantity: int = 1) -> bool:
        """Check if a product is available in the requested quantity."""
        product = storage.get_product(product_id)
        if not product:
            return False
        return product.inventory >= quantity
    
    def reserve_inventory(self, product_id: str, quantity: int = 1) -> bool:
        """Reserve inventory for a product (mock implementation)."""
        product = storage.get_product(product_id)
        if not product or product.inventory < quantity:
            return False
        
        # In a real system, this would update inventory atomically
        # For now, we'll just return True to indicate the reservation
        return True
    
    def release_inventory(self, product_id: str, quantity: int = 1) -> bool:
        """Release reserved inventory (mock implementation)."""
        # In a real system, this would update inventory atomically
        # For now, we'll just return True to indicate the release
        return True


# Global catalog manager instance
catalog_manager = CatalogManager()
