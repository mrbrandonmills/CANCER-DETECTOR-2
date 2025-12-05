"""
Open Food Facts API Client
==========================
Primary database for product ingredients.
3+ million products, FREE API, no authentication required.

Endpoints:
- GET /api/v2/product/{barcode}.json - Lookup by barcode
- GET /cgi/search.pl?search_terms={query}&json=1 - Search by name
"""

import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import asyncio


# API Configuration
OFF_BASE_URL = "https://world.openfoodfacts.org"
OFF_USER_AGENT = "CancerDetector/2.0 (contact@yourapp.com)"  # Required by OFF

# Also check Open Beauty Facts for cosmetics/personal care
OBF_BASE_URL = "https://world.openbeautyfacts.org"

# And Open Products Facts for household items
OPF_BASE_URL = "https://world.openproductsfacts.org"


@dataclass
class ProductData:
    found: bool
    barcode: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    ingredients_text: Optional[str] = None
    ingredients_list: Optional[List[str]] = None
    image_url: Optional[str] = None
    categories: Optional[str] = None
    source: Optional[str] = None  # "openfoodfacts", "openbeautyfacts", etc.
    raw_data: Optional[Dict] = None


async def lookup_by_barcode(barcode: str) -> ProductData:
    """
    Look up a product by barcode across all Open * Facts databases.
    Tries: Open Food Facts → Open Beauty Facts → Open Products Facts
    """
    databases = [
        (OFF_BASE_URL, "openfoodfacts"),
        (OBF_BASE_URL, "openbeautyfacts"),
        (OPF_BASE_URL, "openproductsfacts"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for base_url, source_name in databases:
            try:
                url = f"{base_url}/api/v2/product/{barcode}.json"
                response = await client.get(
                    url,
                    headers={"User-Agent": OFF_USER_AGENT}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == 1 and data.get("product"):
                        product = data["product"]
                        return _parse_product(product, source_name)
                        
            except Exception as e:
                print(f"Error querying {source_name}: {e}")
                continue
    
    return ProductData(found=False)


async def search_by_name(query: str, limit: int = 5) -> List[ProductData]:
    """
    Search for products by name.
    Returns list of matching products.
    """
    results = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Search Open Food Facts
        try:
            url = f"{OFF_BASE_URL}/cgi/search.pl"
            params = {
                "search_terms": query,
                "search_simple": 1,
                "json": 1,
                "page_size": limit
            }
            
            response = await client.get(
                url,
                params=params,
                headers={"User-Agent": OFF_USER_AGENT}
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                for product in products[:limit]:
                    parsed = _parse_product(product, "openfoodfacts")
                    if parsed.found:
                        results.append(parsed)
                        
        except Exception as e:
            print(f"Error searching Open Food Facts: {e}")
    
    # Also search Open Products Facts for household items
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            url = f"{OPF_BASE_URL}/cgi/search.pl"
            params = {
                "search_terms": query,
                "search_simple": 1,
                "json": 1,
                "page_size": limit
            }
            
            response = await client.get(
                url,
                params=params,
                headers={"User-Agent": OFF_USER_AGENT}
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                for product in products[:limit]:
                    parsed = _parse_product(product, "openproductsfacts")
                    if parsed.found:
                        results.append(parsed)
                        
        except Exception as e:
            print(f"Error searching Open Products Facts: {e}")
    
    return results[:limit]


def _parse_product(product: Dict[str, Any], source: str) -> ProductData:
    """Parse raw API response into ProductData."""
    
    # Get ingredients - try multiple fields
    ingredients_text = (
        product.get("ingredients_text_en") or
        product.get("ingredients_text") or
        product.get("ingredients_text_with_allergens") or
        ""
    )
    
    # Parse ingredients list
    ingredients_list = []
    if product.get("ingredients"):
        # Structured ingredients data
        for ing in product.get("ingredients", []):
            if isinstance(ing, dict):
                name = ing.get("text") or ing.get("id", "").replace("en:", "")
                if name:
                    ingredients_list.append(name)
            elif isinstance(ing, str):
                ingredients_list.append(ing)
    
    # Fallback: parse from text
    if not ingredients_list and ingredients_text:
        # Simple split on commas, clean up
        ingredients_list = [
            ing.strip().strip(".")
            for ing in ingredients_text.split(",")
            if ing.strip()
        ]
    
    # Get name
    name = (
        product.get("product_name_en") or
        product.get("product_name") or
        product.get("generic_name") or
        "Unknown Product"
    )
    
    return ProductData(
        found=True,
        barcode=product.get("code") or product.get("_id"),
        name=name,
        brand=product.get("brands"),
        ingredients_text=ingredients_text,
        ingredients_list=ingredients_list if ingredients_list else None,
        image_url=product.get("image_front_url") or product.get("image_url"),
        categories=product.get("categories"),
        source=source,
        raw_data=product
    )


# Quick test
if __name__ == "__main__":
    async def test():
        # Test barcode lookup (Coca-Cola)
        print("Testing barcode lookup...")
        result = await lookup_by_barcode("5449000000996")
        print(f"Found: {result.found}")
        if result.found:
            print(f"Name: {result.name}")
            print(f"Brand: {result.brand}")
            print(f"Ingredients: {result.ingredients_list}")
        
        print("\n" + "="*50 + "\n")
        
        # Test name search
        print("Testing name search...")
        results = await search_by_name("clorox wipes")
        print(f"Found {len(results)} results")
        for r in results:
            print(f"  - {r.name} ({r.brand})")
    
    asyncio.run(test())
