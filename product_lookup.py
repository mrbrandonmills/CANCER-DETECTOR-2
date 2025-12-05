"""
Local Product Database Lookup
Fallback when Open Food Facts/Open Products Facts don't have ingredient data.
"""

import json
from pathlib import Path
from typing import List, Optional
from unified_database import ProductResult

# Load product database
DB_PATH = Path(__file__).parent / "product_database.json"
_product_db = None

def _load_database():
    """Load product database from JSON file."""
    global _product_db
    if _product_db is None:
        with open(DB_PATH, 'r') as f:
            _product_db = json.load(f)
    return _product_db


def search_local_products(query: str, limit: int = 5) -> List[ProductResult]:
    """
    Search local product database by name/brand.

    Args:
        query: Product name or brand to search for
        limit: Maximum results to return

    Returns:
        List of ProductResult objects
    """
    db = _load_database()
    query_lower = query.lower()
    results = []

    for product in db['products']:
        # Check if query matches product name, brand, or search terms
        if any([
            query_lower in product['name'].lower(),
            query_lower in product['brand'].lower(),
            any(term in query_lower or query_lower in term for term in product['search_terms'])
        ]):
            results.append(ProductResult(
                found=True,
                name=product['name'],
                brand=product.get('brand'),
                ingredients_list=product.get('ingredients', []),
                image_url=None,
                source=f"Local DB ({product.get('source', 'Manual')})",
                barcode=product.get('barcode')
            ))

            if len(results) >= limit:
                break

    return results


def lookup_by_barcode(barcode: str) -> Optional[ProductResult]:
    """
    Look up product by exact barcode match.

    Args:
        barcode: Product barcode

    Returns:
        ProductResult if found, None otherwise
    """
    db = _load_database()

    for product in db['products']:
        if product.get('barcode') == barcode:
            return ProductResult(
                found=True,
                name=product['name'],
                brand=product.get('brand'),
                ingredients_list=product.get('ingredients', []),
                image_url=None,
                source=f"Local DB ({product.get('source', 'Manual')})",
                barcode=product.get('barcode')
            )

    return None


def get_all_products() -> List[dict]:
    """Get all products in local database."""
    db = _load_database()
    return db['products']


def add_product(
    name: str,
    brand: str,
    ingredients: List[str],
    category: str = "cleaning",
    barcode: Optional[str] = None,
    search_terms: Optional[List[str]] = None,
    source: str = "Manual"
):
    """
    Add a new product to the database.

    Args:
        name: Product name
        brand: Brand name
        ingredients: List of ingredient names
        category: Product category
        barcode: Optional barcode
        search_terms: Optional search terms
        source: Data source (e.g., "SmartLabel", "Manual")
    """
    db = _load_database()

    new_product = {
        "name": name,
        "brand": brand,
        "category": category,
        "ingredients": ingredients,
        "source": source
    }

    if barcode:
        new_product["barcode"] = barcode

    if search_terms:
        new_product["search_terms"] = search_terms
    else:
        # Auto-generate search terms
        new_product["search_terms"] = [
            name.lower(),
            brand.lower(),
            f"{brand} {name}".lower()
        ]

    db['products'].append(new_product)

    # Save to file
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)

    # Reload database
    global _product_db
    _product_db = None
    _load_database()

    print(f"✓ Added {name} to local database")


if __name__ == "__main__":
    # Test the database
    print("Testing local product database...")

    # Test search
    results = search_local_products("clorox")
    print(f"\nFound {len(results)} products matching 'clorox':")
    for r in results:
        print(f"  - {r.name}: {len(r.ingredients_list)} ingredients")

    # Test barcode lookup
    result = lookup_by_barcode("0055500016099")
    if result:
        print(f"\nBarcode lookup: {result.name}")
        print(f"Ingredients: {', '.join(result.ingredients_list[:3])}...")
