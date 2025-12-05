"""
CANCER DETECTOR v3.1 - ADVANCED EDITION
========================================
Complete Analysis System: Ingredients + Materials + Condition Assessment

Features:
- Consumable products (food, cosmetics, cleaning) → Ingredient analysis
- Non-consumables (containers, cookware, items) → Material analysis
- Condition assessment from visual inspection
- Care tips and safer alternatives
- Comprehensive scoring system
"""

import os
import json
import base64
import re
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import anthropic

# ============================================
# CONFIGURATION
# ============================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not set!")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# ============================================
# TOXICITY DATABASE (103 ingredients)
# ============================================

# Hazard ratings: 0 = safe, 10 = extremely hazardous
TOXICITY_DATABASE = {
    # ========== KNOWN CARCINOGENS (IARC Group 1) ==========
    "formaldehyde": {"score": 10, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["cancer", "respiratory irritation"]},
    "benzene": {"score": 10, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["leukemia", "blood cancer"]},
    "asbestos": {"score": 10, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["mesothelioma", "lung cancer"]},
    "1,4-dioxane": {"score": 9, "category": "carcinogen", "source": "IARC Group 2B", "concerns": ["cancer", "organ toxicity"]},
    "ethylene oxide": {"score": 10, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["cancer", "reproductive harm"]},

    # ========== ENDOCRINE DISRUPTORS ==========
    "triclosan": {"score": 8, "category": "endocrine_disruptor", "source": "EPA", "concerns": ["hormone disruption", "antibiotic resistance"]},
    "triclocarban": {"score": 8, "category": "endocrine_disruptor", "source": "EPA", "concerns": ["hormone disruption"]},
    "bisphenol a": {"score": 8, "category": "endocrine_disruptor", "source": "FDA", "concerns": ["hormone disruption", "reproductive harm"]},
    "bpa": {"score": 8, "category": "endocrine_disruptor", "source": "FDA", "concerns": ["hormone disruption", "reproductive harm"]},
    "phthalate": {"score": 7, "category": "endocrine_disruptor", "source": "EPA", "concerns": ["hormone disruption", "reproductive harm"]},
    "dibutyl phthalate": {"score": 8, "category": "endocrine_disruptor", "source": "Prop 65", "concerns": ["reproductive harm"]},
    "dehp": {"score": 8, "category": "endocrine_disruptor", "source": "Prop 65", "concerns": ["reproductive harm"]},
    "parabens": {"score": 5, "category": "endocrine_disruptor", "source": "EU SCCS", "concerns": ["weak hormone disruption"]},
    "methylparaben": {"score": 4, "category": "endocrine_disruptor", "source": "EU SCCS", "concerns": ["weak hormone disruption"]},
    "propylparaben": {"score": 5, "category": "endocrine_disruptor", "source": "EU SCCS", "concerns": ["hormone disruption"]},
    "butylparaben": {"score": 6, "category": "endocrine_disruptor", "source": "EU SCCS", "concerns": ["hormone disruption"]},
    "oxybenzone": {"score": 6, "category": "endocrine_disruptor", "source": "EWG", "concerns": ["hormone disruption", "coral reef damage"]},

    # ========== QUATERNARY AMMONIUM COMPOUNDS (Cleaning Products) ==========
    "benzalkonium chloride": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["asthma", "skin irritation", "antibiotic resistance"]},
    "alkyl dimethyl benzyl ammonium chloride": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["asthma", "skin irritation"]},
    "quaternary ammonium": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["asthma", "skin irritation"]},
    "didecyl dimethyl ammonium chloride": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["respiratory irritation"]},
    "alkyl dimethyl ethylbenzyl ammonium chloride": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["asthma"]},
    "cetrimonium chloride": {"score": 4, "category": "irritant", "source": "CIR", "concerns": ["skin irritation"]},

    # ========== CHLORINE COMPOUNDS ==========
    "sodium hypochlorite": {"score": 5, "category": "irritant", "source": "EPA", "concerns": ["respiratory irritation", "skin burns", "toxic fumes when mixed"]},
    "chlorine": {"score": 6, "category": "irritant", "source": "EPA", "concerns": ["respiratory irritation", "toxic fumes"]},
    "chlorine dioxide": {"score": 5, "category": "irritant", "source": "EPA", "concerns": ["respiratory irritation"]},
    "hypochlorous acid": {"score": 3, "category": "irritant", "source": "EPA", "concerns": ["mild irritation"]},

    # ========== SOLVENTS ==========
    "2-butoxyethanol": {"score": 6, "category": "solvent", "source": "EPA", "concerns": ["liver damage", "kidney damage", "narcosis"]},
    "ethylene glycol": {"score": 7, "category": "solvent", "source": "EPA", "concerns": ["kidney damage", "toxic if ingested"]},
    "methanol": {"score": 7, "category": "solvent", "source": "EPA", "concerns": ["blindness", "organ damage"]},
    "isopropyl alcohol": {"score": 2, "category": "solvent", "source": "EPA", "concerns": ["mild irritation"]},
    "ethanol": {"score": 1, "category": "solvent", "source": "EPA", "concerns": ["minimal"]},
    "denatured alcohol": {"score": 2, "category": "solvent", "source": "EPA", "concerns": ["drying"]},
    "acetone": {"score": 3, "category": "solvent", "source": "EPA", "concerns": ["irritation", "drying"]},
    "toluene": {"score": 7, "category": "solvent", "source": "Prop 65", "concerns": ["reproductive harm", "neurological damage"]},
    "xylene": {"score": 6, "category": "solvent", "source": "EPA", "concerns": ["neurological effects"]},
    "perchloroethylene": {"score": 8, "category": "solvent", "source": "IARC Group 2A", "concerns": ["probable carcinogen", "neurological effects"]},

    # ========== FRAGRANCES & PRESERVATIVES ==========
    "fragrance": {"score": 5, "category": "undisclosed", "source": "EWG", "concerns": ["allergies", "undisclosed chemicals", "potential hormone disruptors"]},
    "parfum": {"score": 5, "category": "undisclosed", "source": "EWG", "concerns": ["allergies", "undisclosed chemicals"]},
    "synthetic fragrance": {"score": 5, "category": "undisclosed", "source": "EWG", "concerns": ["allergies", "undisclosed chemicals"]},
    "dmdm hydantoin": {"score": 7, "category": "preservative", "source": "EWG", "concerns": ["formaldehyde releaser", "allergies"]},
    "quaternium-15": {"score": 7, "category": "preservative", "source": "EWG", "concerns": ["formaldehyde releaser", "allergies"]},
    "imidazolidinyl urea": {"score": 6, "category": "preservative", "source": "EWG", "concerns": ["formaldehyde releaser"]},
    "diazolidinyl urea": {"score": 6, "category": "preservative", "source": "EWG", "concerns": ["formaldehyde releaser"]},
    "bronopol": {"score": 6, "category": "preservative", "source": "EU", "concerns": ["formaldehyde releaser", "nitrosamine formation"]},
    "methylisothiazolinone": {"score": 7, "category": "preservative", "source": "EU", "concerns": ["severe allergies", "neurotoxicity"]},
    "methylchloroisothiazolinone": {"score": 7, "category": "preservative", "source": "EU", "concerns": ["severe allergies"]},
    "phenoxyethanol": {"score": 3, "category": "preservative", "source": "CIR", "concerns": ["mild irritation"]},
    "sodium benzoate": {"score": 2, "category": "preservative", "source": "FDA", "concerns": ["benzene formation with vitamin C"]},
    "potassium sorbate": {"score": 1, "category": "preservative", "source": "FDA", "concerns": ["minimal"]},

    # ========== SURFACTANTS ==========
    "sodium lauryl sulfate": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["skin irritation", "drying"]},
    "sls": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["skin irritation"]},
    "sodium laureth sulfate": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["potential 1,4-dioxane contamination"]},
    "sles": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["potential contamination"]},
    "cocamidopropyl betaine": {"score": 2, "category": "surfactant", "source": "CIR", "concerns": ["rare allergies"]},
    "lauramine oxide": {"score": 3, "category": "surfactant", "source": "EPA", "concerns": ["mild irritation"]},
    "ammonium lauryl sulfate": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["irritation"]},

    # ========== HEAVY METALS & CONTAMINANTS ==========
    "lead": {"score": 10, "category": "heavy_metal", "source": "CDC", "concerns": ["neurotoxicity", "developmental harm"]},
    "mercury": {"score": 10, "category": "heavy_metal", "source": "CDC", "concerns": ["neurotoxicity"]},
    "arsenic": {"score": 10, "category": "heavy_metal", "source": "IARC Group 1", "concerns": ["cancer", "organ damage"]},
    "cadmium": {"score": 9, "category": "heavy_metal", "source": "IARC Group 1", "concerns": ["cancer", "kidney damage"]},
    "chromium vi": {"score": 10, "category": "heavy_metal", "source": "IARC Group 1", "concerns": ["lung cancer"]},
    "thimerosal": {"score": 5, "category": "preservative", "source": "FDA", "concerns": ["mercury-based"]},

    # ========== PETROLEUM DERIVATIVES ==========
    "mineral oil": {"score": 3, "category": "petroleum", "source": "CIR", "concerns": ["contamination concerns", "comedogenic"]},
    "petrolatum": {"score": 3, "category": "petroleum", "source": "CIR", "concerns": ["contamination concerns if unrefined"]},
    "petroleum": {"score": 4, "category": "petroleum", "source": "EU", "concerns": ["contamination"]},
    "paraffin": {"score": 3, "category": "petroleum", "source": "CIR", "concerns": ["contamination concerns"]},
    "coal tar": {"score": 9, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["cancer"]},

    # ========== AMMONIA & BASES ==========
    "ammonia": {"score": 5, "category": "irritant", "source": "EPA", "concerns": ["respiratory irritation", "toxic fumes"]},
    "ammonium hydroxide": {"score": 5, "category": "irritant", "source": "EPA", "concerns": ["burns", "respiratory irritation"]},
    "sodium hydroxide": {"score": 5, "category": "caustic", "source": "EPA", "concerns": ["burns", "corrosive"]},
    "potassium hydroxide": {"score": 5, "category": "caustic", "source": "EPA", "concerns": ["burns", "corrosive"]},

    # ========== ACIDS ==========
    "hydrochloric acid": {"score": 6, "category": "caustic", "source": "EPA", "concerns": ["burns", "toxic fumes"]},
    "phosphoric acid": {"score": 4, "category": "acid", "source": "EPA", "concerns": ["irritation"]},
    "sulfuric acid": {"score": 7, "category": "caustic", "source": "EPA", "concerns": ["severe burns"]},
    "citric acid": {"score": 1, "category": "acid", "source": "FDA", "concerns": ["minimal"]},
    "lactic acid": {"score": 1, "category": "acid", "source": "FDA", "concerns": ["minimal"]},

    # ========== ARTIFICIAL COLORS & FOOD ADDITIVES ==========
    "red 40": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity in children", "allergic reactions"]},
    "allura red": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity in children"]},
    "yellow 5": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity", "allergies"]},
    "tartrazine": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity", "allergies"]},
    "yellow 6": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity", "allergies"]},
    "sunset yellow": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity"]},
    "blue 1": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["allergic reactions"]},
    "brilliant blue": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["allergies"]},
    "blue 2": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["allergies"]},
    "green 3": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["allergies"]},
    "bha": {"score": 7, "category": "preservative", "source": "IARC Group 2B", "concerns": ["possible carcinogen", "endocrine disruption"]},
    "butylated hydroxyanisole": {"score": 7, "category": "preservative", "source": "IARC Group 2B", "concerns": ["possible carcinogen"]},
    "bht": {"score": 7, "category": "preservative", "source": "IARC Group 3", "concerns": ["possible endocrine disruption"]},
    "butylated hydroxytoluene": {"score": 7, "category": "preservative", "source": "IARC Group 3", "concerns": ["endocrine concerns"]},
    "hfcs": {"score": 6, "category": "sweetener", "source": "FDA", "concerns": ["metabolic issues", "obesity", "diabetes risk"]},
    "high fructose corn syrup": {"score": 6, "category": "sweetener", "source": "FDA", "concerns": ["metabolic issues", "obesity"]},
    "sodium nitrite": {"score": 7, "category": "preservative", "source": "IARC Group 2A", "concerns": ["forms carcinogenic nitrosamines", "processed meat risk"]},
    "sodium nitrate": {"score": 6, "category": "preservative", "source": "IARC Group 2A", "concerns": ["converts to nitrite", "cancer risk"]},
    "msg": {"score": 3, "category": "flavor_enhancer", "source": "FDA", "concerns": ["headaches in sensitive individuals", "allergies"]},
    "monosodium glutamate": {"score": 3, "category": "flavor_enhancer", "source": "FDA", "concerns": ["headaches", "allergies"]},
    "tbhq": {"score": 6, "category": "preservative", "source": "FDA", "concerns": ["vision problems", "DNA damage in studies"]},
    "tertiary butylhydroquinone": {"score": 6, "category": "preservative", "source": "FDA", "concerns": ["vision problems"]},

    # ========== SAFE INGREDIENTS ==========
    "water": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "aqua": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "glycerin": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "vegetable glycerin": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "aloe vera": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "aloe barbadensis": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "coconut oil": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "shea butter": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "jojoba oil": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "vitamin e": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "tocopherol": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "baking soda": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "sodium bicarbonate": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "vinegar": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "acetic acid": {"score": 1, "category": "safe", "source": "FDA", "concerns": []},
    "hydrogen peroxide": {"score": 2, "category": "oxidizer", "source": "FDA", "concerns": ["irritation at high concentrations"]},
    "sodium chloride": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "salt": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "essential oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["possible allergies"]},
    "lavender oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["possible allergies"]},
    "tea tree oil": {"score": 2, "category": "safe", "source": "FDA", "concerns": ["possible allergies", "hormone effects in children"]},
    "eucalyptus oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["possible allergies"]},
    "lemon oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["photosensitivity"]},
    "orange oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["photosensitivity"]},
    "sodium carbonate": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["mild irritation"]},
    "washing soda": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["mild irritation"]},
}

# ============================================
# MATERIAL DATABASE
# ============================================

MATERIAL_DATABASE = {
    # === PLASTICS ===
    "pet": {
        "full_name": "Polyethylene Terephthalate",
        "recycling_code": "#1",
        "score": 75,
        "concerns": ["microplastics when scratched", "antimony leaching potential"],
        "safe_for": ["cold beverages", "single use"],
        "avoid": ["hot liquids", "reuse when scratched", "dishwasher"]
    },
    "hdpe": {
        "full_name": "High-Density Polyethylene",
        "recycling_code": "#2",
        "score": 90,
        "concerns": ["minimal"],
        "safe_for": ["food storage", "beverages", "reuse"],
        "avoid": ["very high heat"]
    },
    "pvc": {
        "full_name": "Polyvinyl Chloride",
        "recycling_code": "#3",
        "score": 30,
        "concerns": ["phthalates", "dioxins", "lead stabilizers", "chlorine"],
        "safe_for": ["non-food applications only"],
        "avoid": ["food contact", "heating", "children's products"]
    },
    "ldpe": {
        "full_name": "Low-Density Polyethylene",
        "recycling_code": "#4",
        "score": 85,
        "concerns": ["minimal"],
        "safe_for": ["food storage bags", "squeeze bottles"],
        "avoid": ["high heat"]
    },
    "pp": {
        "full_name": "Polypropylene",
        "recycling_code": "#5",
        "score": 95,
        "concerns": ["minimal"],
        "safe_for": ["microwave", "food storage", "hot liquids"],
        "avoid": []
    },
    "polypropylene": {
        "full_name": "Polypropylene",
        "recycling_code": "#5",
        "score": 95,
        "concerns": ["minimal"],
        "safe_for": ["microwave", "food storage", "hot liquids"],
        "avoid": []
    },
    "ps": {
        "full_name": "Polystyrene",
        "recycling_code": "#6",
        "score": 40,
        "concerns": ["styrene leaching", "possible carcinogen", "not recyclable"],
        "safe_for": ["cold items only", "single use"],
        "avoid": ["hot food", "fatty foods", "microwave", "reuse"]
    },
    "polycarbonate": {
        "full_name": "Polycarbonate",
        "recycling_code": "#7",
        "score": 35,
        "concerns": ["BPA leaching", "hormone disruption"],
        "safe_for": ["nothing if contains BPA"],
        "avoid": ["food contact", "baby bottles", "heating"]
    },

    # === GLASS ===
    "glass": {
        "full_name": "Glass",
        "recycling_code": "♻",
        "score": 98,
        "concerns": ["breakage"],
        "safe_for": ["everything", "microwave", "dishwasher", "hot liquids"],
        "avoid": ["dropping"]
    },
    "borosilicate glass": {
        "full_name": "Borosilicate Glass",
        "recycling_code": "♻",
        "score": 99,
        "concerns": ["none"],
        "safe_for": ["everything", "extreme temperatures", "oven safe"],
        "avoid": []
    },

    # === METALS ===
    "stainless steel": {
        "full_name": "Stainless Steel",
        "recycling_code": "♻",
        "score": 95,
        "concerns": ["nickel leaching for sensitive individuals"],
        "safe_for": ["food storage", "cooking", "beverages"],
        "avoid": ["highly acidic foods for extended time"]
    },
    "aluminum": {
        "full_name": "Aluminum",
        "recycling_code": "♻",
        "score": 70,
        "concerns": ["acidic food reaction", "potential alzheimer's link debated"],
        "safe_for": ["dry goods", "beverages in cans"],
        "avoid": ["acidic foods", "scratched surfaces"]
    },
    "cast iron": {
        "full_name": "Cast Iron",
        "recycling_code": "♻",
        "score": 90,
        "concerns": ["iron leaching (usually beneficial)"],
        "safe_for": ["cooking", "high heat"],
        "avoid": ["acidic foods for long periods", "soap"]
    },

    # === COATINGS ===
    "teflon": {
        "full_name": "PTFE (Polytetrafluoroethylene)",
        "recycling_code": "N/A",
        "score": 50,
        "concerns": ["PFOA (legacy)", "toxic fumes when overheated", "microplastics when scratched"],
        "safe_for": ["low-medium heat cooking when intact"],
        "avoid": ["high heat >500°F", "metal utensils", "use when scratched"]
    },
    "ceramic coating": {
        "full_name": "Ceramic Non-Stick Coating",
        "recycling_code": "N/A",
        "score": 80,
        "concerns": ["durability", "may contain nanoparticles"],
        "safe_for": ["low-medium heat cooking"],
        "avoid": ["high heat", "metal utensils"]
    },

    # === SILICONE ===
    "silicone": {
        "full_name": "Food-Grade Silicone",
        "recycling_code": "N/A",
        "score": 85,
        "concerns": ["quality varies", "may contain fillers in cheap versions"],
        "safe_for": ["baking", "food storage", "microwave", "freezer"],
        "avoid": ["direct flame", "cheap unbranded versions"]
    },

    # === WOOD/BAMBOO ===
    "bamboo": {
        "full_name": "Bamboo",
        "recycling_code": "♻",
        "score": 80,
        "concerns": ["melamine binders in some products", "mold if not dried"],
        "safe_for": ["utensils", "cutting boards"],
        "avoid": ["dishwasher", "soaking", "products with melamine"]
    },
    "wood": {
        "full_name": "Natural Wood",
        "recycling_code": "♻",
        "score": 85,
        "concerns": ["mold if not dried", "finishes may contain chemicals"],
        "safe_for": ["utensils", "cutting boards"],
        "avoid": ["dishwasher", "soaking"]
    }
}

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="Cancer Detector API v3.1 - ADVANCED",
    description="Complete Analysis: Ingredients + Materials + Condition Assessment",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# MODELS
# ============================================

class ScanResult(BaseModel):
    product_name: str
    brand: Optional[str] = None
    product_type: str  # "consumable", "container", "cookware", "baby_item", "other"

    # For consumables
    ingredients: Optional[List[str]] = None
    ingredients_source: Optional[str] = None

    # For non-consumables
    materials: Optional[List[Dict[str, Any]]] = None

    # Condition analysis
    condition: Optional[Dict[str, Any]] = None

    # Scores
    safety_score: int  # 0-100
    condition_score: Optional[int] = None
    overall_score: int  # 0-100
    grade: str  # A+, A, B+, B, C+, C, D, F

    # Flagged items
    flagged_ingredients: Optional[List[Dict[str, Any]]] = None
    safe_ingredients: Optional[List[str]] = None

    # Recommendations
    recommendation: str
    care_tips: Optional[List[Dict[str, str]]] = None
    safer_alternative: Optional[Dict[str, Any]] = None

    # Metadata
    confidence: str
    analysis_type: str  # "ingredient", "material", "hybrid"
    personalized_notes: Optional[str] = None

    # Report
    report_id: str
    timestamp: str

class HealthCheck(BaseModel):
    status: str
    version: str
    claude_api: str

# ============================================
# CORE FUNCTIONS
# ============================================

def analyze_with_claude(image_base64: str, media_type: str) -> dict:
    """Send image to Claude Vision and get comprehensive analysis"""

    if not client:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    prompt = """Analyze this product/object image comprehensively.

TASK 1 - IDENTIFICATION:
Identify what this is: product name, brand, type, size/variant.

TASK 2 - CLASSIFICATION:
Determine the category:
- "consumable" = food, beverage, cosmetic, cleaning product, medicine (has ingredients)
- "container" = bottle, jar, tupperware, storage container (made of materials)
- "cookware" = pan, pot, utensil, bakeware (has coatings/materials)
- "baby_item" = bottles, toys, pacifiers (extra scrutiny needed)
- "other" = anything else

TASK 3 - INGREDIENTS OR MATERIALS:
- If CONSUMABLE: List all ingredients (from label if visible, or from your knowledge)
- If NON-CONSUMABLE: Identify what materials it's made of (plastic type, metal, glass, coatings)

TASK 4 - CONDITION ASSESSMENT:
Look at the ACTUAL ITEM in the photo:
- Is it new or used?
- Any visible wear, scratches, damage, discoloration?
- Any concerning observations?
- Estimated age/condition?

TASK 5 - RETURN JSON:
Return ONLY valid JSON in this exact format:
{
  "product_name": "Full product name",
  "brand": "Brand name",
  "product_type": "consumable|container|cookware|baby_item|other",

  "ingredients": ["ingredient1", "ingredient2"],
  "ingredients_source": "from_label|from_knowledge",

  "materials": [
    {"component": "main body", "material": "PET plastic", "notes": "recycling code #1"}
  ],

  "condition": {
    "overall": "new|good|fair|worn|damaged",
    "observations": ["visible scratching on surface", "discoloration on base"],
    "estimated_age": "2-3 years",
    "concerns": ["scratches may harbor bacteria", "microplastic shedding risk"]
  },

  "personalized_notes": "Specific observations about THIS particular item in the photo",

  "confidence": "high|medium|low"
}

IMPORTANT:
- Return ONLY the JSON, no other text
- Be thorough with condition assessment - look closely at the actual item
- List ALL ingredients you can identify (for consumables)
- Identify ALL materials and components (for non-consumables)
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text.strip()

        # Try to parse JSON (handle markdown code blocks if present)
        if response_text.startswith("```"):
            # Remove markdown code blocks
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)

        return json.loads(response_text)

    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Response was: {response_text}")
        raise HTTPException(status_code=500, detail=f"Failed to parse Claude response: {str(e)}")
    except Exception as e:
        print(f"Claude API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")


def score_ingredients(ingredients: List[str]) -> dict:
    """Score ingredients against toxicity database"""

    flagged = []
    safe = []
    total_score = 0
    max_severity = 0

    for ingredient in ingredients:
        ingredient_lower = ingredient.lower().strip()

        # Check for matches (including partial matches)
        matched = False
        for toxic_name, data in TOXICITY_DATABASE.items():
            if toxic_name in ingredient_lower or ingredient_lower in toxic_name:
                matched = True

                if data["score"] >= 4:  # Flag concerning ingredients
                    flagged.append({
                        "ingredient": ingredient,
                        "matched_as": toxic_name,
                        "hazard_score": data["score"],
                        "category": data["category"],
                        "source": data["source"],
                        "concerns": data["concerns"]
                    })
                    max_severity = max(max_severity, data["score"])
                else:
                    safe.append(ingredient)

                total_score += data["score"]
                break

        if not matched:
            # Unknown ingredient - give it a neutral score
            safe.append(ingredient)
            total_score += 2  # Slight penalty for unknown ingredients

    # Calculate final score (0-100, where 100 is safest)
    if len(ingredients) > 0:
        avg_score = total_score / len(ingredients)
        # Convert to 0-100 scale (inverted, so 100 = safest)
        final_score = max(0, min(100, int(100 - (avg_score * 10))))
    else:
        final_score = 50  # Unknown

    # Penalize for having any high-severity ingredients
    if max_severity >= 8:
        final_score = min(final_score, 30)
    elif max_severity >= 6:
        final_score = min(final_score, 50)

    return {
        "score": final_score,
        "flagged": flagged,
        "safe": safe
    }


def score_materials(materials: List[Dict]) -> Dict[str, Any]:
    """Score materials against MATERIAL_DATABASE"""
    scored_materials = []
    total_score = 0
    concerns = []

    for mat in materials:
        material_name = mat.get("material", "").lower()
        component = mat.get("component", "unknown")

        # Find in database (partial match)
        matched = None
        for key, data in MATERIAL_DATABASE.items():
            if key in material_name or material_name in key:
                matched = data
                break

        if matched:
            scored_materials.append({
                "component": component,
                "material": matched["full_name"],
                "recycling_code": matched["recycling_code"],
                "score": matched["score"],
                "concerns": matched["concerns"],
                "safe_for": matched["safe_for"],
                "avoid": matched["avoid"]
            })
            total_score += matched["score"]
            concerns.extend(matched["concerns"])
        else:
            scored_materials.append({
                "component": component,
                "material": mat.get("material", "Unknown"),
                "score": 50,
                "concerns": ["Unknown material - exercise caution"]
            })
            total_score += 50

    avg_score = total_score / len(materials) if materials else 50

    return {
        "score": int(avg_score),
        "materials": scored_materials,
        "all_concerns": list(set(concerns))
    }


def get_care_tips(product_type: str, materials: List[Dict] = None) -> List[Dict[str, str]]:
    """Generate care tips"""
    tips = []
    if product_type == "container":
        tips = [
            {"icon": "🚫", "tip": "Avoid dishwasher", "desc": "Hand wash with mild soap"},
            {"icon": "❄️", "tip": "No extreme temperatures", "desc": "Don't freeze or use with hot liquids"},
            {"icon": "☀️", "tip": "Store away from sunlight", "desc": "UV can degrade plastic"},
            {"icon": "🧽", "tip": "Use soft sponges only", "desc": "Abrasives cause scratches"},
            {"icon": "🔄", "tip": "Replace when worn", "desc": "Scratched containers shed microplastics"}
        ]
    elif product_type == "cookware":
        tips = [
            {"icon": "🔥", "tip": "Watch the heat", "desc": "Don't overheat non-stick coatings"},
            {"icon": "🥄", "tip": "Use wooden/silicone utensils", "desc": "Metal scratches coatings"},
            {"icon": "🧴", "tip": "Avoid harsh cleaners", "desc": "They can damage surfaces"},
            {"icon": "👀", "tip": "Inspect regularly", "desc": "Replace if coating is damaged"}
        ]
    return tips


def get_safer_alternative(product_type: str, materials: List[Dict] = None) -> Optional[Dict[str, Any]]:
    """Suggest safer alternative"""
    if product_type == "container" and materials:
        if any("plastic" in str(m).lower() for m in materials):
            return {
                "name": "Glass Container",
                "reason": "Glass doesn't leach chemicals, is dishwasher safe, and lasts longer",
                "grade": "A+",
                "score": 98
            }
    elif product_type == "cookware" and materials:
        if any("teflon" in str(m).lower() for m in materials):
            return {
                "name": "Cast Iron or Stainless Steel",
                "reason": "No chemical coatings to degrade, lasts generations",
                "grade": "A",
                "score": 95
            }
    return None


def calculate_grade(score: int) -> str:
    """Convert score to letter grade"""
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "B+"
    elif score >= 75:
        return "B"
    elif score >= 65:
        return "C+"
    elif score >= 55:
        return "C"
    elif score >= 35:
        return "D"
    else:
        return "F"


def generate_recommendation(grade: str, flagged: List, condition: Dict = None) -> str:
    """Generate recommendation"""
    if grade in ["A+", "A"]:
        recommendation = "This product appears to be safe with no significant toxic ingredients detected."
    elif grade in ["B+", "B"]:
        recommendation = "This product is relatively safe but contains some ingredients of mild concern."
    elif grade in ["C+", "C"]:
        recommendation = "This product contains some ingredients of moderate concern. Consider alternatives."
    elif grade == "D":
        recommendation = "This product contains several concerning ingredients. We recommend finding a safer alternative."
    else:
        recommendation = "This product contains highly toxic ingredients. We strongly recommend avoiding this product."

    # Add condition-specific advice
    if condition and condition.get("overall") in ["worn", "damaged"]:
        recommendation += " Additionally, the visible wear on this item increases safety risks."

    return recommendation


# ============================================
# V3 DATABASE ENRICHMENT & SCORING FUNCTIONS
# ============================================

def enrich_ingredients_with_database(ingredients_analysis: List[Dict]) -> List[Dict]:
    """
    Cross-reference Claude's ingredient analysis with V3 database
    Use HIGHER score for safety (more conservative approach)

    Args:
        ingredients_analysis: List of ingredient dicts from Claude

    Returns:
        Enriched list with database scores where applicable
    """
    enriched = []

    for ingredient in ingredients_analysis:
        ingredient_copy = ingredient.copy()
        ingredient_name = ingredient['name'].lower().strip()

        # Check database
        db_entry = TOXICITY_DATABASE.get(ingredient_name)

        if db_entry:
            claude_score = ingredient['hazard_score']
            db_score = db_entry['score']

            # Use HIGHER score (more conservative)
            if db_score > claude_score:
                ingredient_copy['hazard_score'] = db_score
                ingredient_copy['category'] = db_entry['category']
                ingredient_copy['concerns'] = db_entry.get('concerns', [])
                ingredient_copy['source'] = 'database'
            else:
                ingredient_copy['source'] = 'claude'
        else:
            # Novel ingredient not in database
            ingredient_copy['source'] = 'claude'

        enriched.append(ingredient_copy)

    return enriched


def calculate_ingredient_scores(ingredients_analysis: List[Dict]) -> Dict[str, Any]:
    """
    Calculate base safety score from ingredients with penalty system

    Formula:
    1. average_hazard = sum(scores) / count
    2. base_score = 100 - (average_hazard * 10)
    3. penalties = (count of scores >= 7) * 5 + (count of 4-6) * 2
    4. safety_score = base_score - penalties

    Args:
        ingredients_analysis: List of ingredient dicts with hazard_score

    Returns:
        Dict with average_hazard_score, base_score, penalty, safety_score
    """
    if not ingredients_analysis:
        return {
            'average_hazard_score': 0.0,
            'base_score': 100,
            'penalty': 0,
            'safety_score': 100
        }

    # Calculate average hazard
    total_hazard = sum(ing['hazard_score'] for ing in ingredients_analysis)
    count = len(ingredients_analysis)
    avg_hazard = total_hazard / count

    # Base score
    base_score = 100 - (avg_hazard * 10)

    # Calculate penalties
    high_concern_count = sum(1 for ing in ingredients_analysis if ing['hazard_score'] >= 7)
    moderate_count = sum(1 for ing in ingredients_analysis if 4 <= ing['hazard_score'] < 7)

    penalty = (high_concern_count * 5) + (moderate_count * 2)

    # Final safety score (before bonuses and condition)
    safety_score = max(0, base_score - penalty)

    return {
        'average_hazard_score': round(avg_hazard, 2),
        'base_score': int(base_score),
        'penalty': penalty,
        'safety_score': int(safety_score)
    }


def apply_positive_bonuses(score: int, positive_attributes: List[Dict]) -> int:
    """
    Apply positive bonuses from "X-free" claims
    +3 per claim, max +15 total

    Args:
        score: Current safety score
        positive_attributes: List of positive claim dicts

    Returns:
        Adjusted score with bonuses (capped at max)
    """
    if not positive_attributes:
        return score

    total_bonus = sum(attr.get('bonus_points', 3) for attr in positive_attributes)

    # Cap at +15
    total_bonus = min(total_bonus, 15)

    adjusted = score + total_bonus

    # Ensure within 0-100 range
    return max(0, min(100, adjusted))


def apply_condition_modifier(score: int, condition: Dict, product_type: str) -> int:
    """
    Apply condition modifier based on product type
    - Food/Water/Cosmetics/Cleaning/Supplements: 5% weight
    - Cookware: 15% weight (condition matters more)

    Args:
        score: Current score after ingredients and bonuses
        condition: Condition dict with score (0-100)
        product_type: Product category

    Returns:
        Final score with condition modifier
    """
    condition_score = condition.get('score', 100)

    # Determine weight based on product type
    if product_type.lower() == 'cookware':
        weight = 0.15
    else:
        weight = 0.05

    # Apply modifier
    modifier = int(condition_score * weight)
    adjusted = score + modifier

    # Clamp to 0-100
    return max(0, min(100, adjusted))


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.1.0",
        "claude_api": "connected" if client else "not configured"
    }


@app.get("/health", response_model=HealthCheck)
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.1.0",
        "claude_api": "connected" if client else "not configured"
    }


@app.post("/api/v1/scan", response_model=ScanResult)
async def scan_product(image: UploadFile = File(...)):
    """
    Scan a product image and get complete analysis.

    Supports:
    - Consumables (food, cosmetics, cleaning) → Ingredient analysis
    - Non-consumables (containers, cookware) → Material analysis
    - Condition assessment from visual inspection

    Returns comprehensive safety report with recommendations.
    """

    # Validate file type (more lenient for iOS compatibility)
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]

    # Log the content type for debugging
    print(f"Received image with content_type: {image.content_type}")

    if image.content_type and image.content_type.lower() not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type '{image.content_type}'. Allowed: {allowed_types}"
        )

    # Read and encode image
    image_data = await image.read()
    base64_image = base64.standard_b64encode(image_data).decode("utf-8")

    # Analyze with Claude Vision
    analysis = analyze_with_claude(base64_image, image.content_type)

    # Determine analysis type
    product_type = analysis.get("product_type", "unknown")

    if product_type == "consumable":
        # Score ingredients
        ingredients = analysis.get("ingredients", [])
        scoring = score_ingredients(ingredients)
        safety_score = scoring["score"]
        flagged_ingredients = scoring["flagged"]
        safe_ingredients = scoring["safe"]
        materials = None
        analysis_type = "ingredient"
    else:
        # Score materials
        materials_list = analysis.get("materials", [])
        scoring = score_materials(materials_list)
        safety_score = scoring["score"]
        flagged_ingredients = []
        safe_ingredients = []
        materials = scoring["materials"]
        analysis_type = "material"

    # Condition scoring
    condition = analysis.get("condition")
    condition_score = None
    if condition:
        condition_map = {
            "new": 100,
            "good": 85,
            "fair": 65,
            "worn": 45,
            "damaged": 20
        }
        condition_score = condition_map.get(condition.get("overall", "good"), 70)

    # Overall score (weighted: 70% safety, 30% condition)
    if condition_score is not None:
        overall_score = int(safety_score * 0.7 + condition_score * 0.3)
    else:
        overall_score = safety_score

    # Calculate grade
    grade = calculate_grade(overall_score)

    # Generate recommendation
    recommendation = generate_recommendation(grade, flagged_ingredients, condition)

    # Get care tips and alternatives
    care_tips = get_care_tips(product_type, materials)
    safer_alternative = get_safer_alternative(product_type, materials)

    # Generate unique report ID
    report_id = f"TC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex().upper()}"

    return ScanResult(
        product_name=analysis.get("product_name", "Unknown Product"),
        brand=analysis.get("brand"),
        product_type=product_type,
        ingredients=analysis.get("ingredients") if product_type == "consumable" else None,
        ingredients_source=analysis.get("ingredients_source"),
        materials=materials,
        condition=condition,
        safety_score=safety_score,
        condition_score=condition_score,
        overall_score=overall_score,
        grade=grade,
        flagged_ingredients=flagged_ingredients if flagged_ingredients else None,
        safe_ingredients=safe_ingredients if safe_ingredients else None,
        recommendation=recommendation,
        care_tips=care_tips if care_tips else None,
        safer_alternative=safer_alternative,
        confidence=analysis.get("confidence", "medium"),
        analysis_type=analysis_type,
        personalized_notes=analysis.get("personalized_notes"),
        report_id=report_id,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/scan/base64")
async def scan_product_base64(data: dict):
    """
    Alternative endpoint accepting base64 image directly.

    Body: {"image": "base64_string", "media_type": "image/jpeg"}
    """

    image_base64 = data.get("image")
    media_type = data.get("media_type", "image/jpeg")

    if not image_base64:
        raise HTTPException(status_code=400, detail="Missing 'image' field")

    # Remove data URL prefix if present
    if "base64," in image_base64:
        image_base64 = image_base64.split("base64,")[1]

    # Analyze with Claude Vision
    analysis = analyze_with_claude(image_base64, media_type)

    # Determine analysis type
    product_type = analysis.get("product_type", "unknown")

    if product_type == "consumable":
        # Score ingredients
        ingredients = analysis.get("ingredients", [])
        scoring = score_ingredients(ingredients)
        safety_score = scoring["score"]
        flagged_ingredients = scoring["flagged"]
        safe_ingredients = scoring["safe"]
        materials = None
        analysis_type = "ingredient"
    else:
        # Score materials
        materials_list = analysis.get("materials", [])
        scoring = score_materials(materials_list)
        safety_score = scoring["score"]
        flagged_ingredients = []
        safe_ingredients = []
        materials = scoring["materials"]
        analysis_type = "material"

    # Condition scoring
    condition = analysis.get("condition")
    condition_score = None
    if condition:
        condition_map = {
            "new": 100,
            "good": 85,
            "fair": 65,
            "worn": 45,
            "damaged": 20
        }
        condition_score = condition_map.get(condition.get("overall", "good"), 70)

    # Overall score (weighted: 70% safety, 30% condition)
    if condition_score is not None:
        overall_score = int(safety_score * 0.7 + condition_score * 0.3)
    else:
        overall_score = safety_score

    # Calculate grade
    grade = calculate_grade(overall_score)

    # Generate recommendation
    recommendation = generate_recommendation(grade, flagged_ingredients, condition)

    # Get care tips and alternatives
    care_tips = get_care_tips(product_type, materials)
    safer_alternative = get_safer_alternative(product_type, materials)

    # Generate unique report ID
    report_id = f"TC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex().upper()}"

    return {
        "product_name": analysis.get("product_name", "Unknown Product"),
        "brand": analysis.get("brand"),
        "product_type": product_type,
        "ingredients": analysis.get("ingredients") if product_type == "consumable" else None,
        "ingredients_source": analysis.get("ingredients_source"),
        "materials": materials,
        "condition": condition,
        "safety_score": safety_score,
        "condition_score": condition_score,
        "overall_score": overall_score,
        "grade": grade,
        "flagged_ingredients": flagged_ingredients if flagged_ingredients else None,
        "safe_ingredients": safe_ingredients if safe_ingredients else None,
        "recommendation": recommendation,
        "care_tips": care_tips if care_tips else None,
        "safer_alternative": safer_alternative,
        "confidence": analysis.get("confidence", "medium"),
        "analysis_type": analysis_type,
        "personalized_notes": analysis.get("personalized_notes"),
        "report_id": report_id,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/ingredient/{ingredient_name}")
async def lookup_ingredient(ingredient_name: str):
    """Look up a single ingredient in the toxicity database"""

    ingredient_lower = ingredient_name.lower().strip()

    # Direct match
    if ingredient_lower in TOXICITY_DATABASE:
        data = TOXICITY_DATABASE[ingredient_lower]
        return {
            "ingredient": ingredient_name,
            "found": True,
            "hazard_score": data["score"],
            "category": data["category"],
            "source": data["source"],
            "concerns": data["concerns"]
        }

    # Partial match
    for toxic_name, data in TOXICITY_DATABASE.items():
        if toxic_name in ingredient_lower or ingredient_lower in toxic_name:
            return {
                "ingredient": ingredient_name,
                "found": True,
                "matched_as": toxic_name,
                "hazard_score": data["score"],
                "category": data["category"],
                "source": data["source"],
                "concerns": data["concerns"]
            }

    return {
        "ingredient": ingredient_name,
        "found": False,
        "message": "Ingredient not found in toxicity database"
    }


@app.get("/api/v1/database/stats")
async def database_stats():
    """Get statistics about the toxicity database"""

    categories = {}
    for name, data in TOXICITY_DATABASE.items():
        cat = data["category"]
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    return {
        "total_ingredients": len(TOXICITY_DATABASE),
        "categories": categories,
        "high_hazard_count": sum(1 for d in TOXICITY_DATABASE.values() if d["score"] >= 7),
        "moderate_hazard_count": sum(1 for d in TOXICITY_DATABASE.values() if 4 <= d["score"] < 7),
        "low_hazard_count": sum(1 for d in TOXICITY_DATABASE.values() if d["score"] < 4),
        "total_materials": len(MATERIAL_DATABASE)
    }


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
