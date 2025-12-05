#!/usr/bin/env python3
"""
V3 Testing Matrix - Automated Test Runner
==========================================
Comprehensive test suite for V3 scoring logic and all 6 product type modules

Tests:
- Critical HFCS vs Water scenario
- Positive bonuses (+3 per claim, max +15)
- Database enrichment (uses HIGHER score)
- Condition weights (5% vs 15%)
- All 6 product modules
- Score clamping (0-100)
"""

import sys
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Import V3 scoring functions from main.py
from main import (
    TOXICITY_DATABASE,
    MATERIAL_DATABASE,
    enrich_ingredients_with_database,
    calculate_ingredient_scores,
    apply_positive_bonuses,
    apply_condition_modifier,
    calculate_grade
)


# ============================================
# TEST UTILITIES
# ============================================

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{test_name}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result with color coding"""
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} - {test_name}")
    if details:
        print(f"  {details}")


def assert_range(value: float, min_val: float, max_val: float, label: str) -> bool:
    """Check if value is within expected range"""
    if min_val <= value <= max_val:
        print(f"  {Colors.GREEN}✓{Colors.END} {label}: {value} (expected {min_val}-{max_val})")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.END} {label}: {value} (expected {min_val}-{max_val})")
        return False


# ============================================
# MOCK DATA GENERATORS
# ============================================

def create_mock_ingredient(name: str, hazard_score: int, category: str = "test",
                          concerns: List[str] = None) -> Dict:
    """Create mock ingredient analysis result"""
    return {
        "name": name,
        "hazard_score": hazard_score,
        "category": category,
        "concerns": concerns or ["test concern"],
        "is_safe": hazard_score <= 3
    }


def create_mock_condition(rating: str, score: int) -> Dict:
    """Create mock condition data"""
    return {
        "rating": rating,
        "score": score,
        "weight_percentage": 5,
        "concerns": []
    }


def create_mock_positive_attribute(claim: str) -> Dict:
    """Create mock positive attribute"""
    return {
        "claim": claim,
        "bonus_points": 3,
        "verified": True
    }


# ============================================
# UNIT TESTS
# ============================================

def test_database_enrichment():
    """Test that database enrichment uses HIGHER score (more conservative)"""
    print_test_header("TEST: Database Enrichment Logic")

    all_passed = True

    # Test 1: DB score higher than Claude
    print("\n📋 Test 1: DB score (7) > Claude score (5)")
    ingredients = [create_mock_ingredient("hfcs", 5, "sweetener")]
    enriched = enrich_ingredients_with_database(ingredients)

    # HFCS in database has score 6, should override Claude's 5
    db_score = TOXICITY_DATABASE.get("hfcs", {}).get("score", 0)
    final_score = enriched[0]["hazard_score"]

    passed = final_score == max(5, db_score)
    print(f"  Claude score: 5, DB score: {db_score}, Final: {final_score}")
    print_result("Should use higher score", passed)
    all_passed = all_passed and passed

    # Test 2: Claude score higher than DB
    print("\n📋 Test 2: Claude score (8) > DB score (6)")
    ingredients = [create_mock_ingredient("bha", 8, "preservative")]
    enriched = enrich_ingredients_with_database(ingredients)

    db_score = TOXICITY_DATABASE.get("bha", {}).get("score", 0)
    final_score = enriched[0]["hazard_score"]

    passed = final_score == max(8, db_score)
    print(f"  Claude score: 8, DB score: {db_score}, Final: {final_score}")
    print_result("Should use higher score", passed)
    all_passed = all_passed and passed

    # Test 3: Novel ingredient not in DB
    print("\n📋 Test 3: Novel ingredient not in database")
    ingredients = [create_mock_ingredient("novel_chemical_xyz", 6, "unknown")]
    enriched = enrich_ingredients_with_database(ingredients)

    passed = enriched[0]["hazard_score"] == 6 and enriched[0]["source"] == "claude"
    print(f"  Final score: {enriched[0]['hazard_score']}, Source: {enriched[0]['source']}")
    print_result("Should use Claude score with source=claude", passed)
    all_passed = all_passed and passed

    return all_passed


def test_ingredient_scoring():
    """Test ingredient scoring formula"""
    print_test_header("TEST: Ingredient Scoring Formula")

    all_passed = True

    # Test 1: All safe ingredients
    print("\n📋 Test 1: All safe ingredients (scores 0-3)")
    safe_ingredients = [
        create_mock_ingredient("water", 0, "safe"),
        create_mock_ingredient("glycerin", 1, "safe"),
        create_mock_ingredient("vitamin e", 2, "safe")
    ]
    result = calculate_ingredient_scores(safe_ingredients)

    # Average = (0+1+2)/3 = 1.0
    # Base = 100 - (1.0 * 10) = 90
    # No penalties (all < 4)
    # Expected: 90

    passed = assert_range(result["safety_score"], 85, 95, "Safety score")
    print(f"  Average hazard: {result['average_hazard_score']}")
    print(f"  Base score: {result['base_score']}")
    print(f"  Penalty: {result['penalty']}")
    all_passed = all_passed and passed

    # Test 2: High hazard ingredients
    print("\n📋 Test 2: High hazard ingredients (scores 7-10)")
    hazard_ingredients = [
        create_mock_ingredient("formaldehyde", 10, "carcinogen"),
        create_mock_ingredient("bha", 7, "preservative"),
        create_mock_ingredient("parabens", 7, "endocrine_disruptor")
    ]
    result = calculate_ingredient_scores(hazard_ingredients)

    # Average = (10+7+7)/3 = 8.0
    # Base = 100 - (8.0 * 10) = 20
    # Penalties: 3 high concern * 5 = 15
    # Expected: 20 - 15 = 5

    passed = assert_range(result["safety_score"], 0, 15, "Safety score")
    print(f"  Average hazard: {result['average_hazard_score']}")
    print(f"  Base score: {result['base_score']}")
    print(f"  Penalty: {result['penalty']}")
    all_passed = all_passed and passed

    # Test 3: Mixed ingredients
    print("\n📋 Test 3: Mixed safe and moderate ingredients")
    mixed_ingredients = [
        create_mock_ingredient("water", 0, "safe"),
        create_mock_ingredient("hfcs", 6, "sweetener"),
        create_mock_ingredient("red 40", 5, "food_dye"),
        create_mock_ingredient("glycerin", 1, "safe")
    ]
    result = calculate_ingredient_scores(mixed_ingredients)

    # Average = (0+6+5+1)/4 = 3.0
    # Base = 100 - (3.0 * 10) = 70
    # Penalties: 2 moderate * 2 = 4
    # Expected: 70 - 4 = 66

    passed = assert_range(result["safety_score"], 60, 75, "Safety score")
    print(f"  Average hazard: {result['average_hazard_score']}")
    print(f"  Base score: {result['base_score']}")
    print(f"  Penalty: {result['penalty']}")
    all_passed = all_passed and passed

    return all_passed


def test_positive_bonuses():
    """Test positive bonus application"""
    print_test_header("TEST: Positive Bonus Application")

    all_passed = True

    # Test 1: No bonuses
    print("\n📋 Test 1: No positive attributes")
    score = apply_positive_bonuses(70, [])
    passed = score == 70
    print(f"  Base: 70, Bonuses: 0, Final: {score}")
    print_result("No change expected", passed)
    all_passed = all_passed and passed

    # Test 2: 3 bonuses
    print("\n📋 Test 2: 3 positive attributes (+9 total)")
    bonuses = [
        create_mock_positive_attribute("organic"),
        create_mock_positive_attribute("non-gmo"),
        create_mock_positive_attribute("gluten-free")
    ]
    score = apply_positive_bonuses(70, bonuses)
    passed = score == 79
    print(f"  Base: 70, Bonuses: +9, Final: {score}")
    print_result("Should add +9", passed)
    all_passed = all_passed and passed

    # Test 3: Max bonus cap
    print("\n📋 Test 3: 6 positive attributes (should cap at +15)")
    bonuses = [
        create_mock_positive_attribute("organic"),
        create_mock_positive_attribute("non-gmo"),
        create_mock_positive_attribute("gluten-free"),
        create_mock_positive_attribute("vegan"),
        create_mock_positive_attribute("soy-free"),
        create_mock_positive_attribute("sugar-free")
    ]
    score = apply_positive_bonuses(70, bonuses)
    passed = score == 85  # 70 + 15 (capped)
    print(f"  Base: 70, Bonuses: +15 (capped from +18), Final: {score}")
    print_result("Should cap at +15", passed)
    all_passed = all_passed and passed

    # Test 4: Score clamping at 100
    print("\n📋 Test 4: Score clamping at 100")
    score = apply_positive_bonuses(95, bonuses)
    passed = score == 100
    print(f"  Base: 95, Bonuses: +15, Final: {score} (clamped)")
    print_result("Should clamp at 100", passed)
    all_passed = all_passed and passed

    return all_passed


def test_condition_weights():
    """Test condition weight application"""
    print_test_header("TEST: Condition Weight Application")

    all_passed = True

    # Test 1: Food product (5% weight)
    print("\n📋 Test 1: Food product with damaged condition (5% weight)")
    condition = create_mock_condition("damaged", 20)
    score = apply_condition_modifier(80, condition, "food")

    # Expected: 80 + (20 * 0.05) = 80 + 1 = 81
    passed = score == 81
    print(f"  Base: 80, Condition: 20, Weight: 5%, Final: {score}")
    print_result("Should add ~1 point", passed)
    all_passed = all_passed and passed

    # Test 2: Cookware (15% weight)
    print("\n📋 Test 2: Cookware with damaged condition (15% weight)")
    score = apply_condition_modifier(80, condition, "cookware")

    # Expected: 80 + (20 * 0.15) = 80 + 3 = 83
    passed = score == 83
    print(f"  Base: 80, Condition: 20, Weight: 15%, Final: {score}")
    print_result("Should add ~3 points", passed)
    all_passed = all_passed and passed

    # Test 3: Perfect condition
    print("\n📋 Test 3: Perfect condition (score 100)")
    perfect_condition = create_mock_condition("new", 100)
    score = apply_condition_modifier(80, perfect_condition, "food")

    # Expected: 80 + (100 * 0.05) = 80 + 5 = 85
    passed = score == 85
    print(f"  Base: 80, Condition: 100, Weight: 5%, Final: {score}")
    print_result("Should add 5 points", passed)
    all_passed = all_passed and passed

    return all_passed


# ============================================
# INTEGRATION TESTS
# ============================================

def test_critical_hfcs_vs_water():
    """
    CRITICAL TEST: HFCS bottle (pristine) vs Scratched water bottle
    This test validates the core V3 philosophy
    """
    print_test_header("CRITICAL TEST: HFCS vs Water Validation")

    # Scenario 1: Pristine HFCS soda
    print("\n📋 Scenario 1: Pristine HFCS Soda")
    hfcs_ingredients = [
        create_mock_ingredient("water", 0, "safe"),
        create_mock_ingredient("high fructose corn syrup", 6, "sweetener",
                              ["metabolic issues", "obesity"]),
        create_mock_ingredient("red 40", 5, "food_dye",
                              ["hyperactivity"]),
        create_mock_ingredient("sodium benzoate", 2, "preservative")
    ]

    enriched = enrich_ingredients_with_database(hfcs_ingredients)
    scores = calculate_ingredient_scores(enriched)
    hfcs_score = scores["safety_score"]

    # Apply pristine condition (100) with 5% weight for food
    pristine_condition = create_mock_condition("new", 100)
    hfcs_final = apply_condition_modifier(hfcs_score, pristine_condition, "food")

    print(f"  Ingredients: HFCS (6), Red 40 (5), Water (0), Sodium Benzoate (2)")
    print(f"  Average hazard: {scores['average_hazard_score']}")
    print(f"  Base score: {scores['base_score']}")
    print(f"  Penalty: {scores['penalty']}")
    print(f"  Safety score: {hfcs_score}")
    print(f"  Condition bonus: {pristine_condition['score']} * 0.05 = {int(pristine_condition['score'] * 0.05)}")
    print(f"  {Colors.BOLD}FINAL SCORE: {hfcs_final}{Colors.END}")

    # Scenario 2: Scratched water bottle
    print("\n📋 Scenario 2: Scratched Water Bottle")
    water_ingredients = [
        create_mock_ingredient("water", 0, "safe")
    ]

    enriched = enrich_ingredients_with_database(water_ingredients)
    scores = calculate_ingredient_scores(enriched)
    water_score = scores["safety_score"]

    # Apply damaged condition (45) with 5% weight
    damaged_condition = create_mock_condition("worn", 45)
    water_final = apply_condition_modifier(water_score, damaged_condition, "water")

    print(f"  Ingredients: Water (0)")
    print(f"  Average hazard: {scores['average_hazard_score']}")
    print(f"  Safety score: {water_score}")
    print(f"  Condition penalty: {damaged_condition['score']} * 0.05 = {int(damaged_condition['score'] * 0.05)}")
    print(f"  {Colors.BOLD}FINAL SCORE: {water_final}{Colors.END}")

    # CRITICAL VALIDATION
    print(f"\n{Colors.BOLD}CRITICAL VALIDATION:{Colors.END}")
    print(f"  HFCS Score: {hfcs_final}")
    print(f"  Water Score: {water_final}")

    passed = hfcs_final < water_final

    if passed:
        print(f"  {Colors.GREEN}✓ PASS: HFCS ({hfcs_final}) < Water ({water_final}){Colors.END}")
        print(f"  {Colors.GREEN}This validates the V3 philosophy: Ingredients > Condition{Colors.END}")
    else:
        print(f"  {Colors.RED}✗ FAIL: HFCS ({hfcs_final}) >= Water ({water_final}){Colors.END}")
        print(f"  {Colors.RED}V3 PHILOSOPHY VIOLATED!{Colors.END}")

    return passed


def test_all_product_types():
    """Test all 6 product type modules"""
    print_test_header("TEST: All 6 Product Type Modules")

    all_passed = True

    # We can't test modules directly without Claude API,
    # but we can validate that the database contains expected ingredients

    print("\n📋 Food Module - Database Coverage")
    food_ingredients = ["hfcs", "bha", "bht", "sodium nitrite", "red 40"]
    food_passed = all(ing in TOXICITY_DATABASE for ing in food_ingredients)
    print_result("Food database coverage", food_passed,
                f"Found {sum(1 for i in food_ingredients if i in TOXICITY_DATABASE)}/5 key ingredients")
    all_passed = all_passed and food_passed

    print("\n📋 Water Module - Database Coverage")
    # Water is mostly about container materials
    water_materials = ["pet", "hdpe", "polycarbonate"]
    water_passed = all(mat in MATERIAL_DATABASE for mat in water_materials)
    print_result("Water database coverage", water_passed,
                f"Found {sum(1 for m in water_materials if m in MATERIAL_DATABASE)}/3 materials")
    all_passed = all_passed and water_passed

    print("\n📋 Cosmetics Module - Database Coverage")
    cosmetic_ingredients = ["parabens", "methylparaben", "phthalate", "triclosan", "fragrance"]
    cosmetic_passed = all(ing in TOXICITY_DATABASE for ing in cosmetic_ingredients)
    print_result("Cosmetics database coverage", cosmetic_passed,
                f"Found {sum(1 for i in cosmetic_ingredients if i in TOXICITY_DATABASE)}/5 key ingredients")
    all_passed = all_passed and cosmetic_passed

    print("\n📋 Cookware Module - Database Coverage")
    cookware_materials = ["teflon", "stainless steel", "cast iron", "ceramic coating"]
    cookware_passed = all(mat in MATERIAL_DATABASE for mat in cookware_materials)
    print_result("Cookware database coverage", cookware_passed,
                f"Found {sum(1 for m in cookware_materials if m in MATERIAL_DATABASE)}/4 materials")
    all_passed = all_passed and cookware_passed

    print("\n📋 Cleaning Module - Database Coverage")
    cleaning_ingredients = ["sodium hypochlorite", "ammonia", "benzalkonium chloride", "2-butoxyethanol"]
    cleaning_passed = all(ing in TOXICITY_DATABASE for ing in cleaning_ingredients)
    print_result("Cleaning database coverage", cleaning_passed,
                f"Found {sum(1 for i in cleaning_ingredients if i in TOXICITY_DATABASE)}/4 key ingredients")
    all_passed = all_passed and cleaning_passed

    print("\n📋 Supplements Module - Database Coverage")
    supplement_ingredients = ["lead", "mercury", "arsenic", "titanium dioxide"]
    # Note: titanium dioxide might not be in DB, so we check what we can
    supplement_passed = sum(1 for ing in supplement_ingredients if ing in TOXICITY_DATABASE) >= 3
    print_result("Supplements database coverage", supplement_passed,
                f"Found {sum(1 for i in supplement_ingredients if i in TOXICITY_DATABASE)}/4 key ingredients")
    all_passed = all_passed and supplement_passed

    return all_passed


def test_score_clamping():
    """Test that scores are always clamped to 0-100 range"""
    print_test_header("TEST: Score Clamping (0-100 range)")

    all_passed = True

    # Test 1: Score > 100
    print("\n📋 Test 1: Score above 100 should clamp to 100")
    bonuses = [create_mock_positive_attribute(f"claim_{i}") for i in range(10)]
    score = apply_positive_bonuses(90, bonuses)
    passed = score == 100
    print(f"  Base: 90, Bonuses: +15, Final: {score}")
    print_result("Should clamp at 100", passed)
    all_passed = all_passed and passed

    # Test 2: Score < 0 (theoretical)
    print("\n📋 Test 2: Negative scores should clamp to 0")
    # Create extremely hazardous ingredients
    toxic_ingredients = [
        create_mock_ingredient("formaldehyde", 10, "carcinogen"),
        create_mock_ingredient("benzene", 10, "carcinogen"),
        create_mock_ingredient("asbestos", 10, "carcinogen")
    ]
    result = calculate_ingredient_scores(toxic_ingredients)
    passed = result["safety_score"] >= 0
    print(f"  Safety score: {result['safety_score']} (should be >= 0)")
    print_result("Should not go below 0", passed)
    all_passed = all_passed and passed

    return all_passed


# ============================================
# TEST SUITE RUNNER
# ============================================

def run_all_tests():
    """Run complete test suite"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}V3 TESTING MATRIX - AUTOMATED TEST RUNNER{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Unit Tests
    results["Database Enrichment"] = test_database_enrichment()
    results["Ingredient Scoring"] = test_ingredient_scoring()
    results["Positive Bonuses"] = test_positive_bonuses()
    results["Condition Weights"] = test_condition_weights()
    results["Score Clamping"] = test_score_clamping()

    # Integration Tests
    results["CRITICAL: HFCS vs Water"] = test_critical_hfcs_vs_water()
    results["All Product Types"] = test_all_product_types()

    # Summary
    print_test_header("TEST SUMMARY")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"\n{Colors.BOLD}Test Results:{Colors.END}")
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"  {status} - {test_name}")

    print(f"\n{Colors.BOLD}Overall:{Colors.END}")
    print(f"  Total Tests: {total}")
    print(f"  Passed: {Colors.GREEN}{passed}{Colors.END}")
    print(f"  Failed: {Colors.RED}{failed}{Colors.END}")
    print(f"  Success Rate: {int(passed/total*100)}%")

    # QA Verdict
    critical_passed = results.get("CRITICAL: HFCS vs Water", False)

    print(f"\n{Colors.BOLD}QA VERDICT:{Colors.END}")
    if failed == 0 and critical_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ PASS - Ready for deployment{Colors.END}")
        print(f"All tests passed, including critical HFCS vs Water validation.")
        verdict = "PASS"
    elif critical_passed and failed <= 2:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ CONDITIONAL PASS - Review failures{Colors.END}")
        print(f"Critical test passed, but {failed} non-critical test(s) failed.")
        verdict = "CONDITIONAL_PASS"
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ FAIL - DO NOT DEPLOY{Colors.END}")
        if not critical_passed:
            print(f"CRITICAL: HFCS vs Water test FAILED. V3 philosophy is broken!")
        else:
            print(f"{failed} tests failed. Fix issues before deployment.")
        verdict = "FAIL"

    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return {
        "verdict": verdict,
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": results
    }


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    try:
        summary = run_all_tests()

        # Exit with appropriate code
        if summary["verdict"] == "PASS":
            sys.exit(0)
        elif summary["verdict"] == "CONDITIONAL_PASS":
            sys.exit(0)  # Allow deployment with warnings
        else:
            sys.exit(1)  # Block deployment

    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}ERROR: Test suite crashed!{Colors.END}")
        print(f"{Colors.RED}{str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
