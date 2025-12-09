"""
CANCER DETECTOR v3 - Claude Vision Edition
==========================================
ONE API. ONE CALL. DONE.

User takes photo → Claude identifies product + ingredients → Score → Report

No more:
- Google Vision OCR that doesn't search
- SerpApi that identifies but doesn't get ingredients  
- Open Food Facts that doesn't have household products
- EWG scraping that breaks

Just Claude Vision + Toxicity Database = Done.
"""

import os
import json
import base64
import re
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
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
# TOXICITY DATABASE (Built-in)
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
# FASTAPI APP
# ============================================

app = FastAPI(
    title="Cancer Detector API v3",
    description="Claude Vision + Toxicity Database = Simple & Working",
    version="3.0.0"
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
    brand: Optional[str]
    ingredients: List[str]
    ingredients_source: str  # "from_label" or "from_knowledge"
    confidence: str  # "high", "medium", "low"
    toxicity_score: int  # 0-100 (100 = safest)
    grade: str  # A, B, C, D, F
    flagged_ingredients: List[dict]
    safe_ingredients: List[str]
    recommendation: str

class HealthCheck(BaseModel):
    status: str
    version: str
    claude_api: str

# ============================================
# CORE FUNCTIONS
# ============================================

def analyze_with_claude(image_base64: str, media_type: str) -> dict:
    """Send image to Claude Vision and get product + ingredients"""
    
    if not client:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")
    
    prompt = """Analyze this product image carefully.

TASK 1 - IDENTIFY THE PRODUCT:
Look at the image and identify what product this is (brand, product name, size/variant if visible).

TASK 2 - EXTRACT OR RECALL INGREDIENTS:
- If you can see an ingredient label/list in the image, extract ALL ingredients exactly as written.
- If you only see the front of the product (no ingredient label visible), use your knowledge to provide the typical ingredients for this specific product.

TASK 3 - RETURN JSON:
Return ONLY a valid JSON object in this exact format:
{
  "product_name": "Full product name including brand",
  "brand": "Brand name only",
  "ingredients": ["ingredient 1", "ingredient 2", "ingredient 3"],
  "ingredients_source": "from_label" or "from_knowledge",
  "confidence": "high" or "medium" or "low",
  "notes": "Any relevant notes about the product or ingredients"
}

IMPORTANT:
- Return ONLY the JSON, no other text
- List ALL ingredients you can identify
- Be specific with chemical names when possible
- If you cannot identify the product at all, set confidence to "low"
"""

    try:
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
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
    
    # Calculate grade
    if final_score >= 90:
        grade = "A"
    elif final_score >= 75:
        grade = "B"
    elif final_score >= 55:
        grade = "C"
    elif final_score >= 35:
        grade = "D"
    else:
        grade = "F"
    
    # Generate recommendation
    if grade == "A":
        recommendation = "This product appears to be safe with no significant toxic ingredients detected."
    elif grade == "B":
        recommendation = "This product is relatively safe but contains some ingredients of mild concern."
    elif grade == "C":
        recommendation = "This product contains some ingredients of moderate concern. Consider alternatives."
    elif grade == "D":
        recommendation = "This product contains several concerning ingredients. We recommend finding a safer alternative."
    else:
        recommendation = "This product contains highly toxic ingredients. We strongly recommend avoiding this product."
    
    return {
        "score": final_score,
        "grade": grade,
        "flagged": flagged,
        "safe": safe,
        "recommendation": recommendation
    }


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "claude_api": "connected" if client else "not configured"
    }


@app.get("/health", response_model=HealthCheck)
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "claude_api": "connected" if client else "not configured"
    }


@app.post("/api/v1/scan", response_model=ScanResult)
async def scan_product(image: UploadFile = File(...)):
    """
    Scan a product image and get toxicity analysis.
    
    Upload an image of:
    - The front of a product (Claude will use knowledge)
    - The ingredient label (Claude will OCR it)
    - Both in one shot (best results)
    
    Returns product identification, ingredients, and toxicity score.
    """
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid image type. Allowed: {allowed_types}"
        )
    
    # Read and encode image
    image_data = await image.read()
    base64_image = base64.standard_b64encode(image_data).decode("utf-8")
    
    # Analyze with Claude Vision
    analysis = analyze_with_claude(base64_image, image.content_type)
    
    # Score the ingredients
    scoring = score_ingredients(analysis.get("ingredients", []))
    
    return ScanResult(
        product_name=analysis.get("product_name", "Unknown Product"),
        brand=analysis.get("brand"),
        ingredients=analysis.get("ingredients", []),
        ingredients_source=analysis.get("ingredients_source", "unknown"),
        confidence=analysis.get("confidence", "low"),
        toxicity_score=scoring["score"],
        grade=scoring["grade"],
        flagged_ingredients=scoring["flagged"],
        safe_ingredients=scoring["safe"],
        recommendation=scoring["recommendation"]
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
    
    # Score the ingredients
    scoring = score_ingredients(analysis.get("ingredients", []))
    
    return {
        "product_name": analysis.get("product_name", "Unknown Product"),
        "brand": analysis.get("brand"),
        "ingredients": analysis.get("ingredients", []),
        "ingredients_source": analysis.get("ingredients_source", "unknown"),
        "confidence": analysis.get("confidence", "low"),
        "toxicity_score": scoring["score"],
        "grade": scoring["grade"],
        "flagged_ingredients": scoring["flagged"],
        "safe_ingredients": scoring["safe"],
        "recommendation": scoring["recommendation"]
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
        "low_hazard_count": sum(1 for d in TOXICITY_DATABASE.values() if d["score"] < 4)
    }


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
