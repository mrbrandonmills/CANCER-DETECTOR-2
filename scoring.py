"""
Cancer Score Algorithm
======================
Calculates toxicity/cancer risk score from 0-100.
100 = Completely safe (green)
0 = Maximum concern (red)

The algorithm:
1. Look up each ingredient's toxicity rating from unified database
2. Weight by position (first ingredients = higher concentration)
3. Flag known carcinogens
4. Cap score based on worst ingredient (one bad ingredient tanks the score)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

# Import chemical lookup from unified database
try:
    from unified_database import lookup_chemical, get_chemical_toxicity_score, ChemicalInfo
except ImportError:
    # Fallback if running standalone
    ChemicalInfo = None
    def lookup_chemical(name): return None
    def get_chemical_toxicity_score(name): return 3.0

# Known carcinogens and high-concern chemicals
# Source: California Prop 65, IARC Group 1/2A, EU REACH
CARCINOGENS = {
    "formaldehyde", "benzene", "asbestos", "vinyl chloride",
    "ethylene oxide", "1,4-dioxane", "coal tar", "mineral oil",
    "crystalline silica", "wood dust", "nickel compounds",
    "chromium vi", "arsenic", "cadmium", "beryllium"
}

ENDOCRINE_DISRUPTORS = {
    "bpa", "bisphenol a", "phthalates", "dibutyl phthalate",
    "parabens", "methylparaben", "propylparaben", "butylparaben",
    "triclosan", "oxybenzone", "octinoxate", "resorcinol"
}

HIGH_CONCERN_CHEMICALS = {
    "sodium lauryl sulfate": 4,
    "sodium laureth sulfate": 4,
    "quaternium-15": 7,
    "dmdm hydantoin": 7,
    "imidazolidinyl urea": 6,
    "diazolidinyl urea": 6,
    "polyethylene glycol": 4,
    "peg-": 4,
    "propylene glycol": 3,
    "fragrance": 5,
    "parfum": 5,
    "synthetic fragrance": 6,
    "artificial color": 4,
    "fd&c": 4,
    "d&c": 4,
    "talc": 5,
    "aluminum": 4,
    "ammonia": 5,
    "chlorine": 6,
    "hydrochloric acid": 7,
    "phosphoric acid": 5,
    "sodium hypochlorite": 6,
    "bleach": 7,
    "quaternary ammonium": 5,
    "2-butoxyethanol": 6,
    "nonylphenol ethoxylate": 7,
    "diethanolamine": 6,
    "triethanolamine": 5,
    "cocamide dea": 6,
    "cocamide mea": 5,
}

# Safe/beneficial ingredients (score boost)
SAFE_INGREDIENTS = {
    "water", "aqua", "aloe vera", "coconut oil", "olive oil",
    "shea butter", "jojoba oil", "vitamin e", "tocopherol",
    "citric acid", "baking soda", "sodium bicarbonate",
    "essential oil", "plant extract", "vegetable glycerin"
}


@dataclass
class IngredientAnalysis:
    name: str
    toxicity_score: float  # 0-10, higher = more toxic
    is_carcinogen: bool
    is_endocrine_disruptor: bool
    concern_level: str  # "low", "moderate", "high", "critical"
    notes: Optional[str] = None


@dataclass 
class ProductScore:
    cancer_score: int  # 0-100, higher = safer
    color: str  # "green", "yellow", "orange", "red"
    worst_ingredient: Optional[str]
    carcinogen_count: int
    carcinogens_found: List[str]
    endocrine_disruptors_found: List[str]
    ingredient_breakdown: List[IngredientAnalysis]
    summary: str


def get_ingredient_toxicity(ingredient: str) -> float:
    """
    Returns toxicity score 0-10 for an ingredient.
    0 = completely safe
    10 = known carcinogen / maximum concern
    
    Uses unified database lookup first, then falls back to local lists.
    """
    # Try unified database first (has 500+ chemicals)
    score = get_chemical_toxicity_score(ingredient)
    if score != 3.0:  # 3.0 is the default "unknown" score
        return score
    
    # Fallback to local lists for common patterns
    ing_lower = ingredient.lower().strip()
    
    # Check carcinogens
    for carcinogen in CARCINOGENS:
        if carcinogen in ing_lower:
            return 10.0
    
    # Check endocrine disruptors
    for ed in ENDOCRINE_DISRUPTORS:
        if ed in ing_lower:
            return 8.0
    
    # Check known high-concern chemicals
    for chemical, score in HIGH_CONCERN_CHEMICALS.items():
        if chemical in ing_lower:
            return float(score)
    
    # Check safe ingredients
    for safe in SAFE_INGREDIENTS:
        if safe in ing_lower:
            return 1.0
    
    # Unknown ingredient - moderate default
    return 3.0


def analyze_ingredient(ingredient: str) -> IngredientAnalysis:
    """Analyze a single ingredient and return detailed breakdown."""
    ing_lower = ingredient.lower().strip()
    
    # Try unified database first
    chem_info = lookup_chemical(ingredient)
    
    if chem_info:
        toxicity = chem_info.toxicity_score
        is_carcinogen = chem_info.is_carcinogen
        is_ed = chem_info.is_endocrine_disruptor
        
        if toxicity >= 8:
            concern = "critical"
        elif toxicity >= 6:
            concern = "high"
        elif toxicity >= 4:
            concern = "moderate"
        else:
            concern = "low"
        
        notes = None
        if is_carcinogen:
            notes = f"Known/suspected carcinogen ({chem_info.source})"
        elif is_ed:
            notes = f"Potential endocrine disruptor ({chem_info.source})"
        elif chem_info.hazard_type:
            notes = chem_info.hazard_type
        
        return IngredientAnalysis(
            name=ingredient,
            toxicity_score=toxicity,
            is_carcinogen=is_carcinogen,
            is_endocrine_disruptor=is_ed,
            concern_level=concern,
            notes=notes
        )
    
    # Fallback to local analysis
    toxicity = get_ingredient_toxicity(ingredient)
    is_carcinogen = any(c in ing_lower for c in CARCINOGENS)
    is_ed = any(ed in ing_lower for ed in ENDOCRINE_DISRUPTORS)
    
    if toxicity >= 8:
        concern = "critical"
    elif toxicity >= 6:
        concern = "high"
    elif toxicity >= 4:
        concern = "moderate"
    else:
        concern = "low"
    
    notes = None
    if is_carcinogen:
        notes = "Known or suspected carcinogen"
    elif is_ed:
        notes = "Potential endocrine disruptor"
    
    return IngredientAnalysis(
        name=ingredient,
        toxicity_score=toxicity,
        is_carcinogen=is_carcinogen,
        is_endocrine_disruptor=is_ed,
        concern_level=concern,
        notes=notes
    )


def calculate_cancer_score(ingredients: List[str]) -> ProductScore:
    """
    Calculate the overall cancer/toxicity score for a product.
    
    Returns a score from 0-100:
    - 80-100: Green (safe)
    - 60-79: Yellow (some concerns)
    - 40-59: Orange (moderate concerns)
    - 0-39: Red (high concerns)
    """
    if not ingredients:
        return ProductScore(
            cancer_score=50,
            color="yellow",
            worst_ingredient=None,
            carcinogen_count=0,
            carcinogens_found=[],
            endocrine_disruptors_found=[],
            ingredient_breakdown=[],
            summary="No ingredients provided for analysis"
        )
    
    analyses = [analyze_ingredient(ing) for ing in ingredients]
    toxicity_scores = [a.toxicity_score for a in analyses]
    
    # Find carcinogens and EDs
    carcinogens = [a.name for a in analyses if a.is_carcinogen]
    eds = [a.name for a in analyses if a.is_endocrine_disruptor]
    
    # Weight by position (first ingredients are higher concentration)
    # Using 1/sqrt(position) weighting
    weights = [1.0 / ((i + 1) ** 0.5) for i in range(len(toxicity_scores))]
    total_weight = sum(weights)
    
    weighted_toxicity = sum(t * w for t, w in zip(toxicity_scores, weights)) / total_weight
    
    # Find worst ingredient
    worst_idx = toxicity_scores.index(max(toxicity_scores))
    worst_ingredient = ingredients[worst_idx]
    worst_score = toxicity_scores[worst_idx]
    
    # Cap based on worst ingredient
    # If you have a carcinogen, you can't score above 25
    if worst_score >= 9:
        max_allowed = 15
    elif worst_score >= 7:
        max_allowed = 35
    elif worst_score >= 5:
        max_allowed = 55
    else:
        max_allowed = 100
    
    # Convert 0-10 toxicity to 0-100 safety score (inverted)
    base_score = (10 - weighted_toxicity) * 10
    final_score = min(int(base_score), max_allowed)
    final_score = max(0, min(100, final_score))  # Clamp 0-100
    
    # Determine color
    if final_score >= 80:
        color = "green"
    elif final_score >= 60:
        color = "yellow"
    elif final_score >= 40:
        color = "orange"
    else:
        color = "red"
    
    # Generate summary
    if carcinogens:
        summary = f"⚠️ CRITICAL: Contains {len(carcinogens)} known/suspected carcinogen(s): {', '.join(carcinogens[:3])}"
    elif eds:
        summary = f"⚠️ WARNING: Contains {len(eds)} potential endocrine disruptor(s)"
    elif final_score < 40:
        summary = f"High toxicity concern. Worst ingredient: {worst_ingredient}"
    elif final_score < 60:
        summary = f"Moderate concerns found. Consider alternatives."
    elif final_score < 80:
        summary = f"Some minor concerns. Generally acceptable."
    else:
        summary = "✓ Low toxicity profile. This product appears relatively safe."
    
    return ProductScore(
        cancer_score=final_score,
        color=color,
        worst_ingredient=worst_ingredient,
        carcinogen_count=len(carcinogens),
        carcinogens_found=carcinogens,
        endocrine_disruptors_found=eds,
        ingredient_breakdown=analyses,
        summary=summary
    )


# Quick test
if __name__ == "__main__":
    # Test with Clorox-like ingredients
    test_ingredients = [
        "Water",
        "Alkyl Dimethyl Benzyl Ammonium Chloride",
        "Alkyl Polyglucoside",
        "Sodium Hypochlorite",  # Bleach - concerning
        "Fragrance",
        "Sodium Hydroxide"
    ]
    
    result = calculate_cancer_score(test_ingredients)
    print(f"Cancer Score: {result.cancer_score}/100 ({result.color.upper()})")
    print(f"Summary: {result.summary}")
    print(f"Worst Ingredient: {result.worst_ingredient}")
    if result.carcinogens_found:
        print(f"Carcinogens: {result.carcinogens_found}")
