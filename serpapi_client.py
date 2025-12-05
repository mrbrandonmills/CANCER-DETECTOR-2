"""
SerpAPI Google Lens Client
==========================
Takes a photo URL and identifies the product using Google Lens.
Returns product name, brand, and any detected text.

IMPORTANT: Image must be a publicly accessible URL.
Upload to Cloudinary/S3 first, then pass URL to this.
"""

import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import os


SERPAPI_KEY = os.getenv("SERPAPI_KEY", "c25dc75f65016c369dea37c26ffea95067162e8e96a472ba6df8831010c1094e")


@dataclass
class LensResult:
    success: bool
    product_name: Optional[str] = None
    brand: Optional[str] = None
    detected_text: Optional[str] = None
    search_query: Optional[str] = None  # Best query to use for database lookup
    confidence: float = 0.0
    all_matches: Optional[List[Dict]] = None
    error: Optional[str] = None


async def identify_product_from_image(image_url: str) -> LensResult:
    """
    Use Google Lens via SerpAPI to identify a product from an image.
    
    Args:
        image_url: Publicly accessible URL of the product image
        
    Returns:
        LensResult with product identification
    """
    if not SERPAPI_KEY:
        return LensResult(
            success=False,
            error="SERPAPI_KEY not configured"
        )
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Google Lens API via SerpAPI
            params = {
                "api_key": SERPAPI_KEY,
                "engine": "google_lens",
                "url": image_url,
            }
            
            response = await client.get(
                "https://serpapi.com/search",
                params=params
            )
            
            if response.status_code != 200:
                return LensResult(
                    success=False,
                    error=f"SerpAPI returned status {response.status_code}"
                )
            
            data = response.json()
            
            # Extract product information from various result types
            product_name = None
            brand = None
            detected_text_parts = []
            all_matches = []
            
            # Check visual_matches (most reliable for products)
            visual_matches = data.get("visual_matches", [])
            if visual_matches:
                # First match is usually best
                top_match = visual_matches[0]
                product_name = top_match.get("title")
                
                # Try to extract brand from title
                if product_name:
                    # Common pattern: "Brand - Product Name" or "Brand Product Name"
                    brand = _extract_brand(product_name)
                
                all_matches = [
                    {"title": m.get("title"), "source": m.get("source")}
                    for m in visual_matches[:5]
                ]
            
            # Check knowledge_graph for more structured data
            knowledge_graph = data.get("knowledge_graph", {})
            if knowledge_graph:
                if not product_name:
                    product_name = knowledge_graph.get("title")
                if not brand:
                    brand = knowledge_graph.get("subtitle")
            
            # Check text_results for OCR text on product
            text_results = data.get("text_results", [])
            if text_results:
                detected_text_parts = [t.get("text", "") for t in text_results[:10]]
            
            # Check reverse_image_search for product details
            reverse_results = data.get("reverse_image_search", [])
            if reverse_results and not product_name:
                product_name = reverse_results[0].get("title")
            
            # Build best search query for database lookup
            search_query = _build_search_query(product_name, brand, detected_text_parts)
            
            if product_name or search_query:
                return LensResult(
                    success=True,
                    product_name=product_name,
                    brand=brand,
                    detected_text=" | ".join(detected_text_parts) if detected_text_parts else None,
                    search_query=search_query,
                    confidence=0.8 if visual_matches else 0.5,
                    all_matches=all_matches
                )
            else:
                return LensResult(
                    success=False,
                    error="Could not identify product from image"
                )
                
        except Exception as e:
            return LensResult(
                success=False,
                error=f"SerpAPI error: {str(e)}"
            )


def _extract_brand(product_title: str) -> Optional[str]:
    """Try to extract brand name from product title."""
    # Common household product brands
    known_brands = [
        "Clorox", "Lysol", "Tide", "Gain", "Downy", "Febreze",
        "Windex", "Pledge", "Glade", "Air Wick", "Method",
        "Mrs. Meyer's", "Seventh Generation", "Arm & Hammer",
        "OxiClean", "Cascade", "Dawn", "Palmolive", "Ajax",
        "Pine-Sol", "Mr. Clean", "Swiffer", "Bounty", "Charmin",
        "Cottonelle", "Scott", "Kleenex", "Puffs", "Huggies",
        "Pampers", "Always", "Tampax", "Dove", "Dial", "Irish Spring",
        "Softsoap", "Bath & Body Works", "Old Spice", "Secret",
        "Degree", "Gillette", "Schick", "Nivea", "Neutrogena",
        "Olay", "CeraVe", "Cetaphil", "Aveeno", "Eucerin",
        "Vaseline", "Aquaphor", "Lubriderm", "Jergens"
    ]
    
    title_lower = product_title.lower()
    for brand in known_brands:
        if brand.lower() in title_lower:
            return brand
    
    # Try to get first word if it looks like a brand (capitalized)
    parts = product_title.split()
    if parts and parts[0][0].isupper():
        return parts[0]
    
    return None


def _build_search_query(
    product_name: Optional[str],
    brand: Optional[str],
    detected_text: List[str]
) -> Optional[str]:
    """Build the best possible search query for database lookup."""
    
    if product_name:
        # Clean up the product name
        query = product_name
        # Remove common suffixes that hurt search
        for suffix in [" - Amazon", " | Target", " - Walmart", " | eBay"]:
            query = query.replace(suffix, "")
        return query.strip()
    
    if brand and detected_text:
        # Combine brand with relevant detected text
        relevant_text = " ".join(detected_text[:3])
        return f"{brand} {relevant_text}"[:100]
    
    if detected_text:
        # Just use detected text
        return " ".join(detected_text[:5])[:100]
    
    return None


# Alternative: Use Google reverse image search for backup
async def reverse_image_search(image_url: str) -> LensResult:
    """
    Backup method using Google reverse image search.
    Less accurate for products but doesn't require Lens.
    """
    if not SERPAPI_KEY:
        return LensResult(success=False, error="SERPAPI_KEY not configured")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            params = {
                "api_key": SERPAPI_KEY,
                "engine": "google_reverse_image",
                "image_url": image_url,
            }
            
            response = await client.get(
                "https://serpapi.com/search",
                params=params
            )
            
            if response.status_code != 200:
                return LensResult(success=False, error=f"Status {response.status_code}")
            
            data = response.json()
            
            # Get inline images results
            inline_images = data.get("inline_images", [])
            if inline_images:
                return LensResult(
                    success=True,
                    product_name=inline_images[0].get("title"),
                    search_query=inline_images[0].get("title"),
                    confidence=0.6
                )
            
            return LensResult(success=False, error="No results from reverse image search")
            
        except Exception as e:
            return LensResult(success=False, error=str(e))


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test with a sample image URL
        test_url = "https://m.media-amazon.com/images/I/71VpzTRMqCL._AC_SL1500_.jpg"  # Clorox wipes
        
        print("Testing Google Lens identification...")
        result = await identify_product_from_image(test_url)
        
        print(f"Success: {result.success}")
        if result.success:
            print(f"Product: {result.product_name}")
            print(f"Brand: {result.brand}")
            print(f"Search Query: {result.search_query}")
            print(f"Confidence: {result.confidence}")
        else:
            print(f"Error: {result.error}")
    
    asyncio.run(test())
