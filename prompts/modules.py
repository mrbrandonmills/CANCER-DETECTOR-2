"""
Category-specific modules for specialized product analysis
Phase 1: Lightweight (100-150 words per module)
"""

FOOD_MODULE = """
FOOD-SPECIFIC PRIORITY INGREDIENTS:

HIGH CONCERN (scores 7-10):
- HFCS (high fructose corn syrup): 7
- Palm oil: 5 (environmental + saturated fat)
- BHA, BHT: 7 (preservatives, potential carcinogens)
- Sodium nitrite: 7 (processed meats, carcinogen link)
- Artificial colors (Red 40, Yellow 5, Blue 1): 5-6

MODERATE CONCERN (scores 4-6):
- Natural flavors: 3 (vague, could contain allergens)
- Maltodextrin: 4 (refined, blood sugar spike)
- Refined oils (canola, soybean): 3-4

THRESHOLDS TO FLAG:
- Sodium: Flag if >600mg per serving
- Sugar: Flag if >10g per serving (added sugars)

COMMON ALLERGENS (always note):
- Tree nuts, peanuts, dairy, eggs, gluten, soy, shellfish

EXPIRATION: Critical for food - note freshness status

CONDITION WEIGHT: 5% (ingredients matter most)
"""

WATER_MODULE = """
WATER-SPECIFIC PRIORITY CONTAMINANTS:

FOREVER CHEMICALS (scores 9-10):
- PFAS (per/polyfluoroalkyl substances): 9
- PFOA, PFOS: 10

MICROPLASTICS & LEACHING (scores 5-7):
- Check bottle type: PET (#1) safer than PC (polycarbonate)
- Note if BPA-free claim present (+3 bonus)
- Microplastic concern for all bottled water: 5

SOURCE QUALITY HIERARCHY:
1. Spring water (natural source) - prefer if claimed
2. Mineral water (natural minerals)
3. Purified/filtered tap water
4. Regular tap water (brand-dependent)

BRAND AWARENESS:
- Note brand name for common brands (Fiji, Evian, Dasani, Aquafina)
- Dasani/Aquafina: Enhanced tap water (not spring)

BOTTLE SAFETY NOTES:
- Avoid reusing single-use bottles (bacterial growth risk)
- Glass bottles eliminate plastic leaching concerns entirely

CONDITION WEIGHT: 5% (source/contaminants matter most)
"""

COSMETICS_MODULE = """
COSMETICS-SPECIFIC PRIORITY INGREDIENTS:

ENDOCRINE DISRUPTORS (scores 7-10):
- Parabens (methylparaben, propylparaben): 7
- Phthalates (often in "fragrance"): 8
- Triclosan, Triclocarban: 8

FORMALDEHYDE RELEASERS (scores 8-9):
- DMDM hydantoin: 8
- Diazolidinyl urea: 8
- Quaternium-15: 8

FRAGRANCE CONCERNS (scores 4-6):
- "Fragrance" or "Parfum": 5 (can hide phthalates)
- Essential oils: 2-3 (natural but can irritate)

POSITIVE CLAIMS TO DETECT:
- "Paraben-free" (+3)
- "Phthalate-free" (+3)
- "Fragrance-free" (+3)
- "Hypoallergenic" (+3)
- "Dermatologist-tested" (+3)
- "Non-comedogenic" (+3)

ADDITIONAL CONCERNS:
- Sulfates (SLS, SLES): 4-5 (skin irritants, strip oils)
- Mineral oil, petrolatum: 3-4 (pore-clogging potential)
- Synthetic colors (FD&C, D&C): 5 (potential allergens)

EXPIRATION: Important for mascara, sunscreen, creams

CONDITION WEIGHT: 5% (ingredients matter most)
"""

COOKWARE_MODULE = """
COOKWARE-SPECIFIC PRIORITY MATERIALS:

FOREVER CHEMICALS (scores 8-10):
- Teflon, PTFE (non-stick coating): 7
- PFAS in any form: 9
- Scratched/damaged Teflon: 9 (releases particles)

PLASTIC CONCERNS (scores 4-7):
- PVC (#3): 7 (leaches phthalates)
- Polycarbonate (PC, #7): 6 (BPA risk)
- PET (#1), HDPE (#2): 3 (safer plastics)
- PP (#5): 2 (safest plastic)

SAFEST MATERIALS (scores 0-2):
- Glass: 0
- Stainless steel: 1
- Cast iron: 1
- Ceramic (lead-free): 1

CONDITION CRITICAL FOR COOKWARE:
- Scratches expose base metals or release particles
- Rust compromises safety
- Cracks in ceramic may leach

CONDITION WEIGHT: 15% (condition matters more for cookware)
"""

CLEANING_MODULE = """
CLEANING-SPECIFIC PRIORITY INGREDIENTS:

RESPIRATORY IRRITANTS (scores 7-10):
- Ammonia: 7
- Chlorine bleach (sodium hypochlorite): 8
- Quaternary ammonium compounds (quats): 7

CORROSIVE/TOXIC (scores 8-10):
- Sodium hydroxide (lye): 8
- Hydrochloric acid: 9
- Formaldehyde: 10

MODERATE CONCERN (scores 4-6):
- Artificial fragrances: 5
- Sodium lauryl sulfate (SLS): 4
- Phosphates: 5 (environmental)
- 2-Butoxyethanol: 6 (lung irritant, found in glass cleaners)
- Perchloroethylene (PERC): 7 (dry cleaning fluid, neurotoxin)

POSITIVE CLAIMS TO DETECT:
- "Plant-based" (+3)
- "Biodegradable" (+3)
- "Fragrance-free" (+3)
- "Non-toxic" (+3)
- "EPA Safer Choice" (+3)

SAFETY NOTES:
- Never mix bleach with ammonia (creates toxic chloramine gas)
- Ventilate when using strong cleaners to reduce inhalation exposure

CONDITION WEIGHT: 5% (ingredients matter most)
"""

SUPPLEMENTS_MODULE = """
SUPPLEMENTS-SPECIFIC CONSIDERATIONS:

REGULATORY CONTEXT:
- Supplements less regulated than food/drugs
- "Natural" does not mean safe
- Check for proprietary blends (lack transparency)

PRIORITY CONCERNS (scores vary):
- Heavy metals (lead, mercury, arsenic): 9-10
- Artificial fillers: 4-5
- Allergen-containing binders: 3-5
- Excess vitamins (fat-soluble A, D, E, K): 4-6
- Magnesium stearate (flow agent): 3 (generally safe but reduces absorption)
- Titanium dioxide (coating): 4 (potential nanoparticle concerns)

DOSAGE SAFETY:
- Check if dosages exceed RDA/safe upper limits
- Mega-doses can cause toxicity even with "natural" ingredients

POSITIVE CLAIMS TO DETECT:
- "Third-party tested" (+3)
- "USP verified" (+3)
- "Non-GMO" (+3)
- "Organic" (+3)
- "GMP certified" (+3)

EXPIRATION: Critical - potency degrades

CONDITION WEIGHT: 5% (ingredients + testing matter most)
"""


VALID_TYPES = {'food', 'water', 'cosmetics', 'cookware', 'cleaning', 'supplements'}


def build_prompt(product_type: str) -> str:
    """
    Construct single comprehensive prompt for one-pass analysis

    Args:
        product_type: One of ['food', 'water', 'cosmetics', 'cookware', 'cleaning', 'supplements']

    Returns:
        Complete prompt string combining BASE + category module
    """
    from .base_prompt import BASE_PROMPT

    if not isinstance(product_type, str):
        product_type = 'food'  # Safe default

    cleaned_type = product_type.lower().strip()

    if cleaned_type not in VALID_TYPES:
        cleaned_type = 'food'  # Safe default

    module_map = {
        'food': FOOD_MODULE,
        'water': WATER_MODULE,
        'cosmetics': COSMETICS_MODULE,
        'cookware': COOKWARE_MODULE,
        'cleaning': CLEANING_MODULE,
        'supplements': SUPPLEMENTS_MODULE
    }

    category_module = module_map[cleaned_type]
    return f"{BASE_PROMPT}\n\n{category_module}"
