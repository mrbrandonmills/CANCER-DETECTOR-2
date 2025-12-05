"""
Clorox Scan Debug Test
======================
Tests each step of the scan flow to identify where it fails.
"""

import asyncio
import sys
from serpapi_client import identify_product_from_image
from unified_database import unified_product_search, unified_barcode_lookup
from scoring import calculate_cancer_score


async def test_clorox_scan():
    """Test full Clorox scan flow step by step."""

    print("=" * 80)
    print("CLOROX SCAN DEBUG TEST")
    print("=" * 80)

    # Use sample Clorox product image
    test_image_url = "https://m.media-amazon.com/images/I/71VpzTRMqCL._AC_SL1500_.jpg"

    # STEP 1: Test SerpAPI identification
    print("\n[STEP 1] Testing SerpAPI Google Lens identification...")
    print(f"Image URL: {test_image_url}")

    lens_result = await identify_product_from_image(test_image_url)

    print(f"\nSerpAPI Result:")
    print(f"  Success: {lens_result.success}")
    print(f"  Product Name: {lens_result.product_name}")
    print(f"  Brand: {lens_result.brand}")
    print(f"  Search Query: {lens_result.search_query}")
    print(f"  Detected Text: {lens_result.detected_text}")
    print(f"  Confidence: {lens_result.confidence}")

    if lens_result.all_matches:
        print(f"  All Matches ({len(lens_result.all_matches)}):")
        for match in lens_result.all_matches[:3]:
            print(f"    - {match}")

    if not lens_result.success:
        print(f"\n❌ FAILURE POINT: SerpAPI identification")
        print(f"   Error: {lens_result.error}")
        return

    # STEP 2: Test database lookup with identified product
    print("\n" + "=" * 80)
    print("[STEP 2] Testing database lookup with identified product...")

    if lens_result.search_query:
        print(f"Searching for: '{lens_result.search_query}'")

        search_results = await unified_product_search(lens_result.search_query, limit=3)

        print(f"\nDatabase Search Results: {len(search_results)} found")
        for i, result in enumerate(search_results, 1):
            print(f"\n  Result {i}:")
            print(f"    Name: {result.name}")
            print(f"    Brand: {result.brand}")
            print(f"    Source: {result.source}")
            print(f"    Has ingredients: {bool(result.ingredients_list)}")
            if result.ingredients_list:
                print(f"    Ingredients count: {len(result.ingredients_list)}")
                print(f"    First 5 ingredients: {result.ingredients_list[:5]}")

        if not search_results:
            print(f"\n⚠️ FAILURE POINT: Database lookup returned no results")
            print(f"   The product '{lens_result.search_query}' was not found in:")
            print(f"   - Open Products Facts")
            print(f"   - Open Beauty Facts")
            print(f"   - Open Food Facts")
            return

        # Check if any result has ingredients
        has_ingredients = any(r.ingredients_list for r in search_results)
        if not has_ingredients:
            print(f"\n⚠️ FAILURE POINT: Products found but no ingredients")
            print(f"   Products were found in database but none have ingredient data")
            return

        # STEP 3: Test scoring with ingredients
        print("\n" + "=" * 80)
        print("[STEP 3] Testing ingredient scoring...")

        product_with_ingredients = next((r for r in search_results if r.ingredients_list), None)

        if product_with_ingredients:
            print(f"Scoring product: {product_with_ingredients.name}")
            print(f"Ingredients: {product_with_ingredients.ingredients_list}")

            score_result = calculate_cancer_score(product_with_ingredients.ingredients_list)

            print(f"\nScoring Result:")
            print(f"  Cancer Score: {score_result.cancer_score}/100")
            print(f"  Color: {score_result.color}")
            print(f"  Summary: {score_result.summary}")
            print(f"  Worst Ingredient: {score_result.worst_ingredient}")
            print(f"  Carcinogen Count: {score_result.carcinogen_count}")
            print(f"  Carcinogens Found: {score_result.carcinogens_found}")

            print(f"\n✅ SUCCESS: Full scan flow completed")
            print(f"   1. SerpAPI identified product: ✓")
            print(f"   2. Database found product: ✓")
            print(f"   3. Ingredients available: ✓")
            print(f"   4. Scoring calculated: ✓")
    else:
        print(f"\n⚠️ FAILURE POINT: No search query generated")
        print(f"   SerpAPI identified product but couldn't generate search query")


async def test_specific_clorox_searches():
    """Test specific Clorox product searches."""

    print("\n" + "=" * 80)
    print("[BONUS] Testing specific Clorox product searches...")
    print("=" * 80)

    test_queries = [
        "Clorox",
        "Clorox wipes",
        "Clorox disinfecting wipes",
        "Clorox bleach",
        "disinfecting wipes"
    ]

    for query in test_queries:
        print(f"\n--- Searching: '{query}' ---")
        results = await unified_product_search(query, limit=2)
        print(f"Found {len(results)} results")
        for r in results:
            print(f"  - {r.name} ({r.source}) - Ingredients: {bool(r.ingredients_list)}")


async def test_barcode_lookup():
    """Test if Clorox products have barcodes in the database."""

    print("\n" + "=" * 80)
    print("[BONUS] Testing barcode lookup...")
    print("=" * 80)

    # Common Clorox product barcodes (you can add actual ones if known)
    test_barcodes = [
        "044600316796",  # Clorox Disinfecting Wipes
        "044600316826",  # Clorox Bleach
    ]

    for barcode in test_barcodes:
        print(f"\nTesting barcode: {barcode}")
        result = await unified_barcode_lookup(barcode)
        print(f"  Found: {result.found}")
        if result.found:
            print(f"  Name: {result.name}")
            print(f"  Has ingredients: {bool(result.ingredients_list)}")


if __name__ == "__main__":
    asyncio.run(test_clorox_scan())
    asyncio.run(test_specific_clorox_searches())
    asyncio.run(test_barcode_lookup())
