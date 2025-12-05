# V3 Modular Prompt Architecture Design

**Version:** 3.0.0
**Date:** December 4, 2025
**Status:** Design Complete - Ready for Implementation
**Approach:** Hybrid (Phase 1: Lightweight → Phase 2+: Comprehensive)

---

## Executive Summary

This document defines the modular prompt architecture for Cancer Detector V3, representing a paradigm shift from condition-focused (V2: 70% safety + 30% condition) to **ingredient-focused analysis (V3: 95% ingredients + 5% condition)**.

**Key Innovation:** Product category specialization through modular prompts that leverage Claude's existing training knowledge without external research, enabling deep domain expertise across 6 comprehensive categories.

---

## Architecture Overview

### Modular Prompt System

```
┌─────────────────────────────────────────────────────────┐
│                     BASE_PROMPT                         │
│  - Core scoring philosophy (95/5 weight)                │
│  - JSON response structure                              │
│  - "X-free" positive bonus rules (+3 each, max +15)     │
│  - Condition weight context (5% food, 15% cookware)     │
└─────────────────────────────────────────────────────────┘
                            │
                            ↓
           ┌────────────────┴────────────────┐
           │   Product Type Detection         │
           │   (Single API Call - One Pass)   │
           └────────────────┬────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ↓                   ↓                   ↓
  ┌──────────┐        ┌──────────┐        ┌──────────┐
  │  FOOD    │        │  WATER   │        │ COSMETICS│
  │  MODULE  │        │  MODULE  │        │  MODULE  │
  └──────────┘        └──────────┘        └──────────┘
        ↓                   ↓                   ↓
  ┌──────────┐        ┌──────────┐        ┌──────────┐
  │ COOKWARE │        │ CLEANING │        │SUPPLEMENTS│
  │  MODULE  │        │  MODULE  │        │  MODULE  │
  └──────────┘        └──────────┘        └──────────┘
```

### Design Decision Matrix

| Factor | Modular | Standalone | Mega-Prompt |
|--------|---------|------------|-------------|
| **Maintainability** | ✅ Best | ❌ Worst | ⚠️ Medium |
| **Claude Clarity** | ✅ Good | ⚠️ Good | ❌ Risky |
| **Token Efficiency** | ✅ Good | ⚠️ Medium | ❌ Worst |
| **Testing** | ✅ Easy | ❌ Tedious | ⚠️ Medium |
| **Adding Categories** | ✅ Add Module | ❌ Rewrite All | ⚠️ Append |

**Winner:** Modular architecture

---

## Phase 1: Lightweight Modules (Ship Fast)

**Goal:** Get V3 to market quickly with solid foundation
**Timeline:** 2-3 weeks
**Module Size:** 100-150 words per category

### BASE_PROMPT (Core)

```python
BASE_PROMPT = """You are TrueCancer V3, an AI-powered product safety analyzer.

CORE PHILOSOPHY:
- Ingredients are 95% of safety (5% condition for food/cosmetics, 15% for cookware)
- Every ingredient gets 0-10 hazard score individually
- "X-free" claims are POSITIVE (add +3 each, max +15 total)
- Never flag positive attributes as hazards

SCORING FORMULA:
1. Calculate average ingredient hazard score
2. base_score = 100 - (average_hazard × 10)
3. Apply penalties: -5 per high concern (≥7), -2 per moderate (4-6)
4. Apply bonuses: +3 per "X-free" claim (max +15)
5. Apply condition modifier: 5% or 15% based on product type
6. Clamp to 0-100 range

RESPONSE FORMAT:
{
  "product_name": "string",
  "brand": "string",
  "product_type": "food|water|cosmetics|cookware|cleaning|supplements",
  "ingredients": {
    "analysis": [
      {
        "name": "ingredient_name",
        "hazard_score": 0-10,
        "category": "string",
        "concerns": ["array"],
        "is_safe": boolean
      }
    ],
    "average_hazard_score": float,
    "total_count": int
  },
  "positive_attributes": [
    {"claim": "BPA-free", "bonus_points": 3, "verified": true}
  ],
  "condition": {
    "rating": "new|good|fair|worn|damaged",
    "score": 0-100,
    "weight_percentage": 5 or 15,
    "concerns": ["array"]
  },
  "safety_score": 0-100,
  "condition_score": 0-100,
  "overall_score": 0-100,
  "grade": "A+|A|A-|B+|B|B-|C+|C|C-|D+|D|D-|F"
}

Now analyze based on product type...
"""
```

### FOOD_MODULE (Phase 1)

```python
FOOD_MODULE = """
FOOD-SPECIFIC PRIORITY INGREDIENTS:

HIGH CONCERN (scores 7-10):
- HFCS (high fructose corn syrup): 6
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
```

### WATER_MODULE (Phase 1)

```python
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

CONDITION WEIGHT: 5% (source/contaminants matter most)
"""
```

### COSMETICS_MODULE (Phase 1)

```python
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

EXPIRATION: Important for mascara, sunscreen, creams

CONDITION WEIGHT: 5% (ingredients matter most)
"""
```

### COOKWARE_MODULE (Phase 1)

```python
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
```

### CLEANING_MODULE (Phase 1)

```python
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

POSITIVE CLAIMS TO DETECT:
- "Plant-based" (+3)
- "Biodegradable" (+3)
- "Fragrance-free" (+3)
- "Non-toxic" (+3)

CONDITION WEIGHT: 5% (ingredients matter most)
"""
```

### SUPPLEMENTS_MODULE (Phase 1)

```python
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

POSITIVE CLAIMS TO DETECT:
- "Third-party tested" (+3)
- "USP verified" (+3)
- "Non-GMO" (+3)
- "Organic" (+3)

EXPIRATION: Critical - potency degrades

CONDITION WEIGHT: 5% (ingredients + testing matter most)
"""
```

---

## Phase 2: Comprehensive Enhancement (Data-Driven)

**Goal:** Enhance Water + Food modules based on user engagement
**Timeline:** 4-6 weeks after Phase 1 launch
**Module Size:** 400-600 words with deep expertise

### Example: WATER_MODULE (Phase 2 - Enhanced)

```python
WATER_MODULE_COMPREHENSIVE = """
WATER-SPECIFIC DEEP ANALYSIS:

SOURCE HIERARCHY (best to worst):
1. Spring water (natural aquifer source)
   - Look for source location claim (e.g., "Fiji Natural Artesian Water")
   - Score boost if verified source mentioned
2. Mineral water (naturally occurring minerals)
   - Check TDS (total dissolved solids) if visible
   - Higher TDS = more minerals (not necessarily bad)
3. Purified/filtered tap water
   - Reverse osmosis preferred over basic carbon filter
   - Note filtration method if claimed
4. Enhanced tap water
   - Dasani, Aquafina type (added minerals to tap water)
   - Not inherently bad but score lower than spring

FOREVER CHEMICALS (PFAS Family):
- PFOA (perfluorooctanoic acid): 10 - banned but legacy contamination
- PFOS (perfluorooctane sulfonate): 10 - extremely persistent
- GenX chemicals (newer PFAS): 9 - "safer" replacements still concerning
- Detection: Cannot be seen, taste, or smell
- Common sources: Industrial runoff, firefighting foam sites
- Health risks: Cancer, thyroid issues, immune suppression

MICROPLASTICS:
- Present in 93% of bottled water (2018 study)
- Size: 100 microns to 6.5mm particles
- Source: Bottle material degradation, environmental contamination
- Hazard score: 5 (ubiquitous, long-term effects unclear)
- Glass bottles eliminate this concern (+3 if noted)

BOTTLE MATERIAL SAFETY:
- PET (#1): 3 - Most common, antimony leaching possible when heated
- HDPE (#2): 2 - Safer, less leaching
- PVC (#3): 7 - Avoid (phthalates)
- LDPE (#4): 3 - Soft plastics, generally safe
- PP (#5): 2 - Safest plastic for bottles
- PS (#6): 6 - Avoid (styrene leaching)
- PC (#7): 6 - BPA risk unless labeled BPA-free
- Glass: 0 - Safest option

BRAND-SPECIFIC INSIGHTS:
- **Fiji**: Clean Artesian source, good mineral profile, glass available (premium score)
  - Concern: High carbon footprint from shipping
- **Evian**: French Alps source, generally tested clean, glass preferred
- **Dasani**: Coca-Cola brand, purified tap + minerals (not spring)
  - Ingredients typically include: water, magnesium sulfate, potassium chloride
- **Aquafina**: PepsiCo brand, purified tap water (PWS source)
- **Poland Spring**: Owned by Nestlé, spring sources in Maine
  - Controversy: Some sources may not be true springs
- **Smartwater**: Vapor-distilled + electrolytes, Glacéau brand
- **Essentia**: Ionized alkaline (pH 9.5+), purified + minerals
  - Note: Body regulates pH, alkaline claims debatable

CONTAMINANTS TO FLAG:
- Heavy metals: Lead (10), Arsenic (10), Mercury (10)
- Nitrates: 7 (agricultural runoff)
- Chlorine: 4 (disinfection byproduct, taste/odor)
- Fluoride: 3 (added for dental health, controversial)
- Bacteria (E. coli, coliform): 10 (immediate health risk)

POSITIVE CLAIMS:
- "BPA-free bottle" (+3)
- "Glass bottle" (+3)
- "Spring source verified" (+3)
- "NSF certified" (+3)
- "Tested for PFAS" (+3)

EXPIRATION:
- Water itself doesn't expire
- Plastic degradation over time increases leaching risk
- Note if bottle appears aged or stored in heat

CONDITION ASSESSMENT:
- Bottle integrity: Cracks allow bacterial contamination
- Dents/crushes may accelerate plastic leaching
- Heat exposure (left in car): Significantly increases antimony/BPA risk
- Cloudiness: Could indicate contamination or mineral precipitation

CONDITION WEIGHT: 5% (source and contaminants are primary)

SCORING EXAMPLE:
- Fiji in glass bottle, no visible damage:
  - Base ingredients (water): 0
  - Microplastics (glass eliminates): 0
  - Positive claims: +9 (glass, verified source, premium)
  - Condition: Perfect (100)
  - Overall: 95-100 (A+ range)

- Generic purified water in scratched PET bottle:
  - Base ingredients (tap source): 3
  - Microplastics: 5
  - PET material: 3
  - Condition concerns (scratches): 60
  - Average hazard: 3.7
  - Base: 100 - 37 = 63
  - Condition modifier: 63 + (60 × 0.05) = 66
  - Overall: 60-70 (C range)
"""
```

---

## Phase 3: Remaining Modules Enhancement

**Goal:** Bring Cosmetics, Cookware, Cleaning, Supplements to comprehensive level
**Timeline:** 8-12 weeks after Phase 1 launch
**Criteria:** Based on usage analytics and user feedback

---

## Implementation Strategy

### One-Pass Analysis Flow

```python
def build_prompt(product_type: str) -> str:
    """
    Construct single comprehensive prompt for one-pass analysis

    Args:
        product_type: One of ['food', 'water', 'cosmetics', 'cookware', 'cleaning', 'supplements']

    Returns:
        Complete prompt string combining BASE + category module
    """
    module_map = {
        'food': FOOD_MODULE,
        'water': WATER_MODULE,
        'cosmetics': COSMETICS_MODULE,
        'cookware': COOKWARE_MODULE,
        'cleaning': CLEANING_MODULE,
        'supplements': SUPPLEMENTS_MODULE
    }

    # Phase 1: Lightweight modules
    # Phase 2+: Swap in comprehensive modules for enhanced categories
    category_module = module_map.get(product_type, FOOD_MODULE)  # Default to food

    return f"{BASE_PROMPT}\n\n{category_module}"


async def analyze_product_v3(image_base64: str) -> dict:
    """
    Single-pass analysis: Claude identifies type AND analyzes comprehensively
    """
    # Step 1: Quick type detection (or use hybrid: detect first, then analyze)
    product_type = await detect_product_type(image_base64)  # Fast pre-check

    # Step 2: Build specialized prompt
    full_prompt = build_prompt(product_type)

    # Step 3: Single Claude API call
    response = await anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": full_prompt
                }
            ]
        }]
    )

    # Step 4: Parse and enrich with database
    analysis = json.loads(response.content[0].text)
    enriched = enrich_with_database(analysis)

    return enriched
```

### Database Enrichment Logic

```python
def enrich_with_database(claude_analysis: dict) -> dict:
    """
    Cross-reference Claude's ingredient analysis with V3 database
    Use HIGHER score for safety (more conservative)
    """
    for ingredient in claude_analysis['ingredients']['analysis']:
        db_entry = INGREDIENT_DATABASE.get(ingredient['name'].lower())

        if db_entry:
            # Use higher hazard score (more conservative)
            if db_entry['score'] > ingredient['hazard_score']:
                ingredient['hazard_score'] = db_entry['score']
                ingredient['category'] = db_entry['category']
                ingredient['concerns'] = db_entry.get('concerns', [])
                ingredient['source'] = 'database'  # Track enrichment source
            else:
                ingredient['source'] = 'claude'
        else:
            ingredient['source'] = 'claude'  # Novel ingredient

    return claude_analysis
```

---

## Quality Checks & Testing

### Phase 1 Testing Matrix

| Product Type | Test Case | Expected Grade | Validation |
|--------------|-----------|----------------|------------|
| **Food** | Organic apple, perfect condition | A+ (95-100) | Clean ingredients, +9 bonus |
| **Food** | Doritos (HFCS, Red 40, Yellow 6) | D (50-59) | Multiple moderate concerns |
| **Water** | Fiji glass bottle, pristine | A+ (95-100) | Premium source, glass, bonuses |
| **Water** | Generic tap in scratched PET | C (60-69) | Microplastics, PET, condition |
| **Cosmetics** | Paraben-free lotion, new | A (85-94) | Clean + bonus, minimal concerns |
| **Cosmetics** | Drugstore foundation (parabens, fragrance) | C+ (65-74) | Endocrine disruptors |
| **Cookware** | Scratched Teflon pan | F (0-49) | PFAS release, condition critical |
| **Cookware** | New cast iron skillet | A+ (95-100) | Safest material, perfect condition |
| **Cleaning** | Method plant-based cleaner | B+ (80-84) | Lower concern ingredients |
| **Cleaning** | Clorox bleach wipes | D+ (55-64) | Sodium hypochlorite, irritants |
| **Supplements** | Third-party tested vitamin D | A- (85-89) | Clean + verification bonus |
| **Supplements** | Generic multivitamin, proprietary blend | C (60-69) | Lack of transparency |

### Validation Criteria

**Critical Test:** HFCS in pristine bottle MUST score LOWER than water in scratched bottle
- HFCS bottle: Ingredient score 60, condition 100 → 62/100 (95% weight)
- Water scratched: Ingredient score 95, condition 60 → 92/100 (5% weight)
- ✅ Pass if HFCS < Water

**Positive Bonus Test:** BPA-free water bottle gets +3, NOT flagged as hazard
- Expected: `positive_attributes: [{"claim": "BPA-free", "bonus_points": 3}]`
- NOT expected: `flagged_ingredients: [{"name": "BPA-free", ...}]`

**Database Enrichment Test:** Claude says "Red 40: score 3", database says "score 5"
- Expected: Final score uses 5 (more conservative)
- Track: `ingredient.source = "database"`

---

## Deployment Phases

### Phase 1: Lightweight Launch (Weeks 1-2)

**Backend Changes:**
1. Update `main.py` to `main_v3.py` with modular prompt system
2. Add `build_prompt(product_type)` function
3. Implement database enrichment logic
4. Deploy to Railway (new `/api/v3/scan` endpoint)
5. Keep V2 endpoint alive for fallback

**Flutter Changes:**
1. Update `api_service.dart` to call `/api/v3/scan`
2. Parse new response structure (`ingredients.analysis` array)
3. Display `positive_attributes` with bonus points
4. Reorder UI: Ingredients first → Positive claims → Condition last
5. Add "Powered by V3" badge

**Testing:**
- Run all 12 test cases from matrix
- Verify scoring matches expectations
- Confirm positive bonuses working
- Check database enrichment

### Phase 2: Water + Food Enhancement (Weeks 4-6)

**Backend Changes:**
1. Swap `WATER_MODULE` for `WATER_MODULE_COMPREHENSIVE`
2. Swap `FOOD_MODULE` for `FOOD_MODULE_COMPREHENSIVE`
3. A/B test: Track engagement metrics (time on screen, shares)
4. Monitor Claude token usage (should stay under 4096)

**Flutter Changes:**
1. Add expandable sections for detailed ingredient explanations
2. Show "Enhanced Analysis" badge for Water/Food categories
3. Add brand-specific insights UI (if brand detected)

**Testing:**
- Verify comprehensive modules don't exceed token limits
- Check water brand recognition accuracy
- Validate food threshold flagging (sodium >600mg, sugar >10g)

### Phase 3: Full Enhancement (Weeks 8-12)

**Backend Changes:**
1. Enhance remaining 4 modules to comprehensive level
2. Add usage analytics to identify low-performing categories
3. Fine-tune scoring based on user feedback

**Flutter Changes:**
1. Unified "Deep Analysis" experience across all categories
2. Add comparison mode (scan multiple products side-by-side)
3. Export detailed reports

---

## Future: Deep Research Mode (Premium Feature)

**Trigger:** User opts into premium subscription
**Behavior:** Claude can use web search to access:
- Latest research papers on emerging contaminants
- Real-time recall databases
- Brand-specific lab test results
- Regulatory updates (FDA, EWG)

**Implementation:** Separate prompt + MCP server integration
- Reserved for post-V3 launch
- Pricing: $47/year (matching Oasis app analysis)

---

## Success Metrics

### Phase 1 (Lightweight)
- ✅ All test cases pass validation
- ✅ Average response time <5 seconds
- ✅ Token usage <4096 per scan
- ✅ Positive bonus system working (0 false flagged claims)
- ✅ Database enrichment >80% match rate

### Phase 2 (Water + Food Enhanced)
- ✅ User engagement +20% for Water/Food scans
- ✅ Brand recognition accuracy >90% for top 20 brands
- ✅ Zero "I don't understand this ingredient" support tickets
- ✅ Share rate +15% for A+ graded water/food

### Phase 3 (Full Enhancement)
- ✅ Unified experience across all 6 categories
- ✅ User retention +30% after first scan
- ✅ App Store rating >4.5 stars
- ✅ Ready for Deep Research Mode premium upsell

---

## Appendix: Module Quick Reference

| Module | Phase 1 Size | Phase 2+ Size | Priority Ingredients | Condition Weight |
|--------|--------------|---------------|---------------------|------------------|
| **Food** | 150 words | 500 words | HFCS, palm oil, BHA/BHT, artificial colors | 5% |
| **Water** | 120 words | 600 words | PFAS, microplastics, bottle type, brand | 5% |
| **Cosmetics** | 130 words | 450 words | Parabens, phthalates, fragrance, formaldehyde | 5% |
| **Cookware** | 140 words | 500 words | Teflon, PFAS, plastics, scratches/rust | 15% |
| **Cleaning** | 110 words | 400 words | Ammonia, chlorine, quats, fragrances | 5% |
| **Supplements** | 100 words | 450 words | Heavy metals, fillers, third-party testing | 5% |

---

**Document Version:** 1.0
**Last Updated:** December 4, 2025
**Next Review:** After Phase 1 launch (estimated 2 weeks)
**Approver:** Brandon Mills
**Implementation Lead:** Claude Code AI Assistant
