import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import (
    TOXICITY_DATABASE,
    enrich_ingredients_with_database,
    calculate_ingredient_scores,
    apply_positive_bonuses,
    apply_condition_modifier
)


def test_enrichment_uses_higher_score():
    """Verify enrichment uses HIGHER score (more conservative)"""
    claude_analysis = [
        {"name": "red 40", "hazard_score": 3, "category": "color", "concerns": []}
    ]

    enriched = enrich_ingredients_with_database(claude_analysis)

    # Database has Red 40 at score 5, should use that
    assert enriched[0]['hazard_score'] == 5
    assert enriched[0]['source'] == 'database'


def test_enrichment_keeps_claude_if_higher():
    """Verify enrichment keeps Claude's score if higher than database"""
    claude_analysis = [
        {"name": "formaldehyde", "hazard_score": 10, "category": "carcinogen", "concerns": []}
    ]

    enriched = enrich_ingredients_with_database(claude_analysis)

    # Claude says 10, database might say 9 - keep 10
    assert enriched[0]['hazard_score'] >= 9
    assert enriched[0]['source'] in ['claude', 'database']


def test_enrichment_tracks_novel_ingredients():
    """Verify novel ingredients not in database are marked as Claude-sourced"""
    claude_analysis = [
        {"name": "novel_ingredient_xyz", "hazard_score": 4, "category": "unknown", "concerns": []}
    ]

    enriched = enrich_ingredients_with_database(claude_analysis)

    assert enriched[0]['source'] == 'claude'
    assert enriched[0]['hazard_score'] == 4


def test_calculate_ingredient_scores():
    """Verify scoring algorithm: base = 100 - (avg_hazard * 10) - penalties"""
    ingredients_analysis = [
        {"name": "water", "hazard_score": 0, "is_safe": True},
        {"name": "sugar", "hazard_score": 3, "is_safe": True},
        {"name": "HFCS", "hazard_score": 6, "is_safe": False},
    ]

    result = calculate_ingredient_scores(ingredients_analysis)

    # Average: (0 + 3 + 6) / 3 = 3.0
    # Base: 100 - (3.0 * 10) = 70
    # Penalties: 1 moderate (score 6): -2
    # Expected: 70 - 2 = 68
    assert result['average_hazard_score'] == 3.0
    assert result['base_score'] == 70
    assert result['penalty'] == 2
    assert result['safety_score'] == 68


def test_apply_positive_bonuses_caps_at_15():
    """Verify positive bonuses cap at +15"""
    score = 70
    positive_attributes = [
        {"claim": "BPA-free", "bonus_points": 3, "verified": True},
        {"claim": "organic", "bonus_points": 3, "verified": True},
        {"claim": "non-GMO", "bonus_points": 3, "verified": True},
        {"claim": "paraben-free", "bonus_points": 3, "verified": True},
        {"claim": "phthalate-free", "bonus_points": 3, "verified": True},
        {"claim": "fragrance-free", "bonus_points": 3, "verified": True},  # 6th claim
    ]

    adjusted = apply_positive_bonuses(score, positive_attributes)

    # 6 claims * 3 = 18, but capped at 15
    assert adjusted == 70 + 15  # 85


def test_apply_condition_modifier_food():
    """Verify condition modifier is 5% for food"""
    score = 80
    condition = {"score": 60, "rating": "fair"}
    product_type = "food"

    adjusted = apply_condition_modifier(score, condition, product_type)

    # 80 + (60 * 0.05) = 80 + 3 = 83
    assert adjusted == 83


def test_apply_condition_modifier_cookware():
    """Verify condition modifier is 15% for cookware"""
    score = 80
    condition = {"score": 60, "rating": "fair"}
    product_type = "cookware"

    adjusted = apply_condition_modifier(score, condition, product_type)

    # 80 + (60 * 0.15) = 80 + 9 = 89
    assert adjusted == 89


def test_critical_test_hfcs_vs_water_scratched():
    """CRITICAL: HFCS in pristine bottle MUST score LOWER than water in scratched bottle"""
    # HFCS bottle scenario
    hfcs_ingredients = [
        {"name": "water", "hazard_score": 0, "is_safe": True},
        {"name": "HFCS", "hazard_score": 6, "is_safe": False},
    ]
    hfcs_condition = {"score": 100, "rating": "new"}
    hfcs_result = calculate_ingredient_scores(hfcs_ingredients)
    hfcs_score = apply_condition_modifier(hfcs_result['safety_score'], hfcs_condition, "food")

    # Water scratched scenario
    water_ingredients = [
        {"name": "water", "hazard_score": 0, "is_safe": True},
    ]
    water_condition = {"score": 60, "rating": "worn"}
    water_result = calculate_ingredient_scores(water_ingredients)
    water_score = apply_condition_modifier(water_result['safety_score'], water_condition, "water")

    # HFCS must score LOWER than water
    assert hfcs_score < water_score, f"HFCS ({hfcs_score}) should be < Water ({water_score})"


def test_penalty_boundaries():
    """Verify penalty thresholds are correct at boundaries"""
    # Score 3: No penalty (low concern)
    low = [{"name": "sugar", "hazard_score": 3, "is_safe": True}]
    result = calculate_ingredient_scores(low)
    assert result['penalty'] == 0, "Score 3 should have 0 penalty"

    # Score 4: Moderate penalty (-2)
    moderate_low = [{"name": "sls", "hazard_score": 4, "is_safe": False}]
    result = calculate_ingredient_scores(moderate_low)
    assert result['penalty'] == 2, "Score 4 should have -2 penalty"

    # Score 6: Still moderate (-2, not -5)
    moderate_high = [{"name": "hfcs", "hazard_score": 6, "is_safe": False}]
    result = calculate_ingredient_scores(moderate_high)
    assert result['penalty'] == 2, "Score 6 should have -2 penalty, not -5"

    # Score 7: High penalty (-5, not -2)
    high = [{"name": "bha", "hazard_score": 7, "is_safe": False}]
    result = calculate_ingredient_scores(high)
    assert result['penalty'] == 5, "Score 7 should have -5 penalty"
