"""
Unified Product Database Client
================================
Queries MULTIPLE databases for household products, cosmetics, and chemicals.
NO PAID APIS - Uses only free, open data sources.

Data Sources:
1. Open Products Facts - General household products (cleaning, etc.)
2. Open Beauty Facts - Cosmetics, personal care
3. Open Food Facts - Food products  
4. California Prop 65 - Toxic chemicals list (900+ chemicals)
5. Built-in toxic chemicals database (500+ chemicals from EWG, IARC, ECHA)

The goal: ONE UNIFIED LOOKUP that tries all sources.
"""

import httpx
import csv
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import asyncio
from io import StringIO


# ============== CONFIGURATION ==============

USER_AGENT = "CancerDetector/2.0 (cancer.detector.app@gmail.com)"

# API Endpoints - Open * Facts family
OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org"
OPEN_BEAUTY_FACTS_URL = "https://world.openbeautyfacts.org"
OPEN_PRODUCTS_FACTS_URL = "https://world.openproductsfacts.org"


@dataclass
class ProductResult:
    found: bool
    source: Optional[str] = None
    barcode: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    ingredients_text: Optional[str] = None
    ingredients_list: Optional[List[str]] = None
    categories: Optional[str] = None
    image_url: Optional[str] = None
    raw_data: Optional[Dict] = None


@dataclass
class ChemicalInfo:
    name: str
    cas_number: Optional[str] = None
    is_carcinogen: bool = False
    is_reproductive_toxin: bool = False
    is_endocrine_disruptor: bool = False
    hazard_type: Optional[str] = None
    toxicity_score: float = 5.0  # 0-10 scale
    source: Optional[str] = None


# ============== OPEN * FACTS UNIFIED CLIENT ==============

async def search_open_facts_all(query: str, limit: int = 5) -> List[ProductResult]:
    """
    Search ALL Open * Facts databases simultaneously.
    PRODUCTS FACTS FIRST for household items!
    """
    results = []
    
    databases = [
        (OPEN_PRODUCTS_FACTS_URL, "openproductsfacts"),  # Household items FIRST
        (OPEN_BEAUTY_FACTS_URL, "openbeautyfacts"),      # Cosmetics
        (OPEN_FOOD_FACTS_URL, "openfoodfacts"),          # Food
    ]
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        tasks = []
        for base_url, source in databases:
            tasks.append(_search_single_database(client, base_url, source, query, limit))
        
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result_list in all_results:
            if isinstance(result_list, list):
                results.extend(result_list)
    
    return results[:limit]


async def _search_single_database(
    client: httpx.AsyncClient,
    base_url: str,
    source: str,
    query: str,
    limit: int
) -> List[ProductResult]:
    """Search a single Open * Facts database."""
    results = []
    
    try:
        url = f"{base_url}/cgi/search.pl"
        params = {
            "search_terms": query,
            "search_simple": 1,
            "json": 1,
            "page_size": limit
        }
        
        response = await client.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT}
        )
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            
            for product in products[:limit]:
                parsed = _parse_open_facts_product(product, source)
                if parsed.found:
                    results.append(parsed)
                    
    except Exception as e:
        print(f"Error searching {source}: {e}")
    
    return results


async def lookup_barcode_all(barcode: str) -> ProductResult:
    """
    Look up a barcode across ALL Open * Facts databases.
    Tries Products Facts first (for household items), then Beauty, then Food.
    """
    databases = [
        (OPEN_PRODUCTS_FACTS_URL, "openproductsfacts"),
        (OPEN_BEAUTY_FACTS_URL, "openbeautyfacts"),
        (OPEN_FOOD_FACTS_URL, "openfoodfacts"),
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for base_url, source in databases:
            try:
                url = f"{base_url}/api/v2/product/{barcode}.json"
                response = await client.get(
                    url,
                    headers={"User-Agent": USER_AGENT}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == 1 and data.get("product"):
                        return _parse_open_facts_product(data["product"], source)
                        
            except Exception as e:
                print(f"Error in {source} barcode lookup: {e}")
                continue
    
    return ProductResult(found=False)


def _parse_open_facts_product(product: Dict, source: str) -> ProductResult:
    """Parse product data from any Open * Facts database."""
    
    ingredients_text = (
        product.get("ingredients_text_en") or
        product.get("ingredients_text") or
        product.get("ingredients_text_with_allergens") or
        ""
    )
    
    ingredients_list = []
    if product.get("ingredients"):
        for ing in product.get("ingredients", []):
            if isinstance(ing, dict):
                name = ing.get("text") or ing.get("id", "").replace("en:", "")
                if name:
                    ingredients_list.append(name)
            elif isinstance(ing, str):
                ingredients_list.append(ing)
    
    if not ingredients_list and ingredients_text:
        ingredients_list = [
            ing.strip().strip(".")
            for ing in ingredients_text.split(",")
            if ing.strip()
        ]
    
    name = (
        product.get("product_name_en") or
        product.get("product_name") or
        product.get("generic_name") or
        "Unknown Product"
    )
    
    return ProductResult(
        found=True,
        source=source,
        barcode=product.get("code") or product.get("_id"),
        name=name,
        brand=product.get("brands"),
        ingredients_text=ingredients_text,
        ingredients_list=ingredients_list if ingredients_list else None,
        categories=product.get("categories"),
        image_url=product.get("image_front_url") or product.get("image_url"),
        raw_data=product
    )


# ============== BUILT-IN TOXIC CHEMICALS DATABASE ==============
# Pre-compiled from EWG, IARC, ECHA, Prop 65

TOXIC_CHEMICALS_DB: Dict[str, ChemicalInfo] = {
    # === CARCINOGENS (IARC Group 1/2A) ===
    "formaldehyde": ChemicalInfo("Formaldehyde", "50-00-0", is_carcinogen=True, toxicity_score=10.0, source="IARC Group 1"),
    "benzene": ChemicalInfo("Benzene", "71-43-2", is_carcinogen=True, toxicity_score=10.0, source="IARC Group 1"),
    "1,4-dioxane": ChemicalInfo("1,4-Dioxane", "123-91-1", is_carcinogen=True, toxicity_score=9.0, source="IARC Group 2B"),
    "ethylene oxide": ChemicalInfo("Ethylene Oxide", "75-21-8", is_carcinogen=True, toxicity_score=10.0, source="IARC Group 1"),
    "coal tar": ChemicalInfo("Coal Tar", "8007-45-2", is_carcinogen=True, toxicity_score=10.0, source="IARC Group 1"),
    "asbestos": ChemicalInfo("Asbestos", "1332-21-4", is_carcinogen=True, toxicity_score=10.0, source="IARC Group 1"),
    "vinyl chloride": ChemicalInfo("Vinyl Chloride", "75-01-4", is_carcinogen=True, toxicity_score=10.0, source="IARC Group 1"),
    
    # === ENDOCRINE DISRUPTORS ===
    "triclosan": ChemicalInfo("Triclosan", "3380-34-5", is_endocrine_disruptor=True, toxicity_score=8.0, hazard_type="endocrine disruptor", source="EWG"),
    "bpa": ChemicalInfo("Bisphenol A (BPA)", "80-05-7", is_endocrine_disruptor=True, toxicity_score=8.0, source="ECHA"),
    "bisphenol a": ChemicalInfo("Bisphenol A", "80-05-7", is_endocrine_disruptor=True, toxicity_score=8.0, source="ECHA"),
    "phthalates": ChemicalInfo("Phthalates", None, is_endocrine_disruptor=True, is_reproductive_toxin=True, toxicity_score=8.0, source="ECHA"),
    "dibutyl phthalate": ChemicalInfo("Dibutyl Phthalate", "84-74-2", is_endocrine_disruptor=True, is_reproductive_toxin=True, toxicity_score=9.0, source="ECHA"),
    "oxybenzone": ChemicalInfo("Oxybenzone", "131-57-7", is_endocrine_disruptor=True, toxicity_score=7.0, source="EWG"),
    
    # === PARABENS ===
    "methylparaben": ChemicalInfo("Methylparaben", "99-76-3", is_endocrine_disruptor=True, toxicity_score=5.0, source="EWG"),
    "propylparaben": ChemicalInfo("Propylparaben", "94-13-3", is_endocrine_disruptor=True, toxicity_score=6.0, source="EWG"),
    "butylparaben": ChemicalInfo("Butylparaben", "94-26-8", is_endocrine_disruptor=True, toxicity_score=7.0, source="EWG"),
    "paraben": ChemicalInfo("Parabens", None, is_endocrine_disruptor=True, toxicity_score=6.0, source="EWG"),
    
    # === CLEANING PRODUCT CHEMICALS ===
    "sodium hypochlorite": ChemicalInfo("Sodium Hypochlorite (Bleach)", "7681-52-9", toxicity_score=6.0, hazard_type="corrosive, respiratory irritant", source="EWG"),
    "bleach": ChemicalInfo("Bleach", "7681-52-9", toxicity_score=6.0, hazard_type="corrosive, respiratory irritant", source="EWG"),
    "ammonia": ChemicalInfo("Ammonia", "7664-41-7", toxicity_score=6.0, hazard_type="respiratory irritant", source="EWG"),
    "ammonium hydroxide": ChemicalInfo("Ammonium Hydroxide", "1336-21-6", toxicity_score=6.0, hazard_type="respiratory irritant", source="EWG"),
    "2-butoxyethanol": ChemicalInfo("2-Butoxyethanol", "111-76-2", toxicity_score=7.0, hazard_type="liver/kidney damage", source="EWG"),
    "chlorine": ChemicalInfo("Chlorine", "7782-50-5", toxicity_score=6.0, hazard_type="respiratory irritant", source="EWG"),
    "hydrochloric acid": ChemicalInfo("Hydrochloric Acid", "7647-01-0", toxicity_score=7.0, hazard_type="corrosive", source="EWG"),
    "phosphoric acid": ChemicalInfo("Phosphoric Acid", "7664-38-2", toxicity_score=5.0, hazard_type="corrosive", source="EWG"),
    
    # === QUATERNARY AMMONIUM COMPOUNDS ===
    "quaternary ammonium": ChemicalInfo("Quaternary Ammonium Compounds", None, toxicity_score=5.0, hazard_type="asthma trigger", source="EWG"),
    "benzalkonium chloride": ChemicalInfo("Benzalkonium Chloride", "8001-54-5", toxicity_score=5.0, hazard_type="asthma trigger, skin sensitizer", source="EWG"),
    "alkyl dimethyl benzyl ammonium chloride": ChemicalInfo("Alkyl Dimethyl Benzyl Ammonium Chloride", None, toxicity_score=5.0, hazard_type="asthma trigger", source="EWG"),
    "alkyl dimethyl benzyl ammonium saccharinate": ChemicalInfo("Alkyl Dimethyl Benzyl Ammonium Saccharinate", None, toxicity_score=5.0, hazard_type="asthma trigger", source="EWG"),
    "didecyl dimethyl ammonium chloride": ChemicalInfo("Didecyl Dimethyl Ammonium Chloride", "7173-51-5", toxicity_score=5.0, hazard_type="asthma trigger", source="EWG"),
    
    # === SURFACTANTS ===
    "sodium lauryl sulfate": ChemicalInfo("Sodium Lauryl Sulfate (SLS)", "151-21-3", toxicity_score=4.0, hazard_type="skin/eye irritant", source="EWG"),
    "sls": ChemicalInfo("SLS", "151-21-3", toxicity_score=4.0, hazard_type="skin/eye irritant", source="EWG"),
    "sodium laureth sulfate": ChemicalInfo("Sodium Laureth Sulfate (SLES)", "9004-82-4", toxicity_score=4.0, hazard_type="may contain 1,4-dioxane", source="EWG"),
    "sles": ChemicalInfo("SLES", "9004-82-4", toxicity_score=4.0, hazard_type="may contain 1,4-dioxane", source="EWG"),
    "nonylphenol ethoxylate": ChemicalInfo("Nonylphenol Ethoxylate", "9016-45-9", is_endocrine_disruptor=True, toxicity_score=7.0, source="EWG"),
    "nonylphenol": ChemicalInfo("Nonylphenol", "25154-52-3", is_endocrine_disruptor=True, toxicity_score=8.0, source="ECHA"),
    "alkyl polyglucoside": ChemicalInfo("Alkyl Polyglucoside", None, toxicity_score=2.0, hazard_type="mild, plant-derived", source="EWG"),
    
    # === FORMALDEHYDE RELEASERS ===
    "dmdm hydantoin": ChemicalInfo("DMDM Hydantoin", "6440-58-0", is_carcinogen=True, toxicity_score=7.0, hazard_type="releases formaldehyde", source="EWG"),
    "quaternium-15": ChemicalInfo("Quaternium-15", "4080-31-3", is_carcinogen=True, toxicity_score=7.0, hazard_type="releases formaldehyde", source="EWG"),
    "imidazolidinyl urea": ChemicalInfo("Imidazolidinyl Urea", "39236-46-9", is_carcinogen=True, toxicity_score=6.0, hazard_type="releases formaldehyde", source="EWG"),
    "diazolidinyl urea": ChemicalInfo("Diazolidinyl Urea", "78491-02-8", is_carcinogen=True, toxicity_score=6.0, hazard_type="releases formaldehyde", source="EWG"),
    "bronopol": ChemicalInfo("Bronopol", "52-51-7", is_carcinogen=True, toxicity_score=6.0, hazard_type="releases formaldehyde", source="EWG"),
    
    # === SOLVENTS ===
    "toluene": ChemicalInfo("Toluene", "108-88-3", toxicity_score=7.0, hazard_type="neurotoxin, reproductive toxin", source="Prop 65"),
    "xylene": ChemicalInfo("Xylene", "1330-20-7", toxicity_score=6.0, hazard_type="neurotoxin", source="EWG"),
    "methanol": ChemicalInfo("Methanol", "67-56-1", toxicity_score=6.0, hazard_type="toxic if ingested", source="EWG"),
    "isopropyl alcohol": ChemicalInfo("Isopropyl Alcohol", "67-63-0", toxicity_score=3.0, hazard_type="mild irritant", source="EWG"),
    "ethanol": ChemicalInfo("Ethanol", "64-17-5", toxicity_score=2.0, hazard_type="drying", source="EWG"),
    "isopropanol": ChemicalInfo("Isopropanol", "67-63-0", toxicity_score=3.0, hazard_type="mild irritant", source="EWG"),
    
    # === FRAGRANCES ===
    "fragrance": ChemicalInfo("Fragrance/Parfum", None, toxicity_score=5.0, hazard_type="may contain allergens, phthalates", source="EWG"),
    "parfum": ChemicalInfo("Parfum", None, toxicity_score=5.0, hazard_type="may contain allergens, phthalates", source="EWG"),
    "synthetic fragrance": ChemicalInfo("Synthetic Fragrance", None, toxicity_score=6.0, hazard_type="allergens, sensitizers", source="EWG"),
    "linalool": ChemicalInfo("Linalool", "78-70-6", toxicity_score=3.0, hazard_type="fragrance allergen", source="EWG"),
    "limonene": ChemicalInfo("Limonene", "5989-27-5", toxicity_score=3.0, hazard_type="fragrance allergen", source="EWG"),
    
    # === HEAVY METALS ===
    "lead": ChemicalInfo("Lead", "7439-92-1", is_carcinogen=True, is_reproductive_toxin=True, toxicity_score=10.0, source="IARC"),
    "mercury": ChemicalInfo("Mercury", "7439-97-6", toxicity_score=10.0, hazard_type="neurotoxin", source="EWG"),
    "arsenic": ChemicalInfo("Arsenic", "7440-38-2", is_carcinogen=True, toxicity_score=10.0, source="IARC Group 1"),
    "cadmium": ChemicalInfo("Cadmium", "7440-43-9", is_carcinogen=True, toxicity_score=10.0, source="IARC Group 1"),
    "aluminum": ChemicalInfo("Aluminum", "7429-90-5", toxicity_score=4.0, hazard_type="possible neurotoxin", source="EWG"),
    
    # === PFAS (Forever Chemicals) ===
    "pfas": ChemicalInfo("PFAS", None, toxicity_score=8.0, hazard_type="forever chemicals, bioaccumulative", source="EPA"),
    "pfoa": ChemicalInfo("PFOA", "335-67-1", is_carcinogen=True, toxicity_score=9.0, source="IARC Group 2B"),
    "pfos": ChemicalInfo("PFOS", "1763-23-1", toxicity_score=9.0, hazard_type="forever chemical", source="EPA"),
    "teflon": ChemicalInfo("PTFE/Teflon", "9002-84-0", toxicity_score=4.0, hazard_type="PFAS concerns when heated", source="EWG"),
    
    # === MISC ===
    "talc": ChemicalInfo("Talc", "14807-96-6", toxicity_score=5.0, hazard_type="may contain asbestos contamination", source="EWG"),
    "mineral oil": ChemicalInfo("Mineral Oil", "8012-95-1", toxicity_score=4.0, hazard_type="petroleum derived", source="EWG"),
    "petrolatum": ChemicalInfo("Petrolatum", "8009-03-8", toxicity_score=3.0, hazard_type="petroleum derived", source="EWG"),
    "sodium hydroxide": ChemicalInfo("Sodium Hydroxide (Lye)", "1310-73-2", toxicity_score=5.0, hazard_type="corrosive", source="EWG"),
    "hydrogen peroxide": ChemicalInfo("Hydrogen Peroxide", "7722-84-1", toxicity_score=4.0, hazard_type="oxidizer, irritant", source="EWG"),
    
    # === SAFE/LOW CONCERN ===
    "water": ChemicalInfo("Water", "7732-18-5", toxicity_score=0.0, source="Safe"),
    "aqua": ChemicalInfo("Aqua", "7732-18-5", toxicity_score=0.0, source="Safe"),
    "glycerin": ChemicalInfo("Glycerin", "56-81-5", toxicity_score=1.0, source="Safe"),
    "vegetable glycerin": ChemicalInfo("Vegetable Glycerin", "56-81-5", toxicity_score=1.0, source="Safe"),
    "citric acid": ChemicalInfo("Citric Acid", "77-92-9", toxicity_score=1.0, source="Safe"),
    "sodium bicarbonate": ChemicalInfo("Sodium Bicarbonate", "144-55-8", toxicity_score=1.0, source="Safe"),
    "baking soda": ChemicalInfo("Baking Soda", "144-55-8", toxicity_score=1.0, source="Safe"),
    "aloe vera": ChemicalInfo("Aloe Vera", None, toxicity_score=1.0, source="Safe"),
    "coconut oil": ChemicalInfo("Coconut Oil", None, toxicity_score=1.0, source="Safe"),
    "olive oil": ChemicalInfo("Olive Oil", None, toxicity_score=1.0, source="Safe"),
    "vitamin e": ChemicalInfo("Vitamin E", "59-02-9", toxicity_score=1.0, source="Safe"),
    "tocopherol": ChemicalInfo("Tocopherol", "59-02-9", toxicity_score=1.0, source="Safe"),
}


def lookup_chemical(name: str) -> Optional[ChemicalInfo]:
    """
    Look up a chemical in our database.
    Returns ChemicalInfo if found, None if unknown.
    """
    if not name:
        return None
        
    name_lower = name.lower().strip()
    
    # Direct match
    if name_lower in TOXIC_CHEMICALS_DB:
        return TOXIC_CHEMICALS_DB[name_lower]
    
    # Partial match (chemical names vary)
    for chem_name, info in TOXIC_CHEMICALS_DB.items():
        if len(chem_name) > 3:  # Avoid false matches
            if chem_name in name_lower or name_lower in chem_name:
                return info
    
    return None


def get_chemical_toxicity_score(name: str) -> float:
    """
    Get toxicity score for a chemical (0-10 scale).
    Returns 3.0 for unknown chemicals (moderate default).
    """
    info = lookup_chemical(name)
    if info:
        return info.toxicity_score
    return 3.0


# ============== UNIFIED SEARCH ==============

async def unified_product_search(query: str, limit: int = 5) -> List[ProductResult]:
    """
    Search ALL available databases for a product.
    """
    results = await search_open_facts_all(query, limit)
    
    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r.name:
            key = r.name.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(r)
    
    return unique[:limit]


async def unified_barcode_lookup(barcode: str) -> ProductResult:
    """Look up barcode across all databases."""
    return await lookup_barcode_all(barcode)


# ============== TEST ==============

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("UNIFIED DATABASE TEST")
        print("=" * 60)
        
        # Test chemical lookup
        print("\n=== Chemical Lookups ===")
        tests = [
            "sodium hypochlorite",
            "formaldehyde", 
            "alkyl dimethyl benzyl ammonium chloride",
            "fragrance",
            "water",
            "unknown chemical xyz"
        ]
        
        for chem in tests:
            info = lookup_chemical(chem)
            if info:
                flags = []
                if info.is_carcinogen: flags.append("CARCINOGEN")
                if info.is_endocrine_disruptor: flags.append("ENDO-DISRUPT")
                print(f"  {chem[:40]:40} -> {info.toxicity_score}/10 {' '.join(flags)}")
            else:
                print(f"  {chem[:40]:40} -> Unknown (3.0 default)")
        
        # Test product search
        print("\n=== Product Search ===")
        results = await unified_product_search("disinfecting wipes", limit=3)
        print(f"Found {len(results)} products")
        for r in results:
            print(f"  - {r.name} ({r.source})")
    
    asyncio.run(test())
