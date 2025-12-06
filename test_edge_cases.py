#!/usr/bin/env python3
"""
TrueCancer V4 - Edge Case Testing Suite
Validates all edge cases before TestFlight submission
"""

import sys
sys.path.append('.')
from main import calculate_v4_score
import json

print("=" * 80)
print("TRUECANCER V4 - EDGE CASE TESTING SUITE")
print("TestFlight Pre-Submission Validation")
print("=" * 80)
print()

# Track test results
tests_passed = 0
tests_failed = 0
test_results = []

def test(name, condition, details=""):
    """Helper function to track test results"""
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        status = "✓ PASS"
        test_results.append((name, True, details))
    else:
        tests_failed += 1
        status = "✗ FAIL"
        test_results.append((name, False, details))
    print(f"{status}: {name}")
    if details:
        print(f"  Details: {details}")
    return condition

# ============================================
# EDGE CASE 1: F-Grade Only Products
# ============================================
print("\n" + "=" * 80)
print("EDGE CASE 1: F-Grade Only Products (Should Cap at 29)")
print("=" * 80)

f_grade_product = {
    "product_name": "Toxic Soda",
    "brand": "BadCorp",
    "category": "food",
    "ingredients": [
        "aspartame",
        "sodium benzoate",
        "yellow 5",
        "red 40",
        "BHA",
        "TBHQ",
        "brominated vegetable oil"
    ]
}

try:
    result = calculate_v4_score(f_grade_product)
    test("F-grade product scores ≤29", result['overall_score'] <= 29, f"Score: {result['overall_score']}, Grade: {result['overall_grade']}")
    test("F-grade product gets F grade", result['overall_grade'] == 'F', f"Grade: {result['overall_grade']}")
except Exception as e:
    test("F-grade only product handling", False, str(e))

# ============================================
# EDGE CASE 2: Mixed Tier Products
# ============================================
print("\n" + "=" * 80)
print("EDGE CASE 2: Mixed Tier Products (Should Use Worst Tier)")
print("=" * 80)

mixed_tier_product = {
    "product_name": "Mixed Quality Cereal",
    "brand": "TestBrand",
    "category": "food",
    "ingredients": ["whole wheat", "organic oats", "sugar", "high fructose corn syrup", "BHA", "salt"]
}

try:
    result = calculate_v4_score(mixed_tier_product)
    test("Mixed tier uses worst tier (F)", result['overall_score'] <= 29, f"Score: {result['overall_score']}")
except Exception as e:
    test("Mixed tier product handling", False, str(e))

# ============================================
# EDGE CASE 3: Empty Lists
# ============================================
print("\n" + "=" * 80)
print("EDGE CASE 3: Empty Ingredient Lists")
print("=" * 80)

empty_product = {"product_name": "Empty Product", "brand": "TestBrand", "category": "food", "ingredients": []}

try:
    result = calculate_v4_score(empty_product)
    test("Empty product doesn't crash", 'overall_score' in result, f"Score: {result.get('overall_score', 'N/A')}")
except Exception as e:
    test("Empty ingredient list handling", False, str(e))

# ============================================
# EDGE CASE 4: Large Lists (100+)
# ============================================
print("\n" + "=" * 80)
print("EDGE CASE 4: Large Ingredient Lists (100+ items)")
print("=" * 80)

large_product = {"product_name": "Kitchen Sink", "brand": "Test", "category": "food", "ingredients": ["water", "salt"] * 60}

try:
    result = calculate_v4_score(large_product)
    test("Large product processes", 'overall_score' in result, f"Score: {result['overall_score']}, Ingredients: {len(large_product['ingredients'])}")
except Exception as e:
    test("Large ingredient list handling", False, str(e))

# ============================================
# EDGE CASE 5: Special Characters
# ============================================
print("\n" + "=" * 80)
print("EDGE CASE 5: Special Characters in Names")
print("=" * 80)

special_product = {"product_name": "Test™", "brand": "Test & Co.®", "category": "food", "ingredients": ["water (H₂O)", "salt [NaCl]"]}

try:
    result = calculate_v4_score(special_product)
    test("Special characters handled", 'overall_score' in result, f"Score: {result['overall_score']}")
except Exception as e:
    test("Special character handling", False, str(e))

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 80)
print("EDGE CASE TESTING - FINAL SUMMARY")
print("=" * 80)
print(f"\nTests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")

if tests_failed == 0:
    print("\n🎉 ALL EDGE CASE TESTS PASSED!")
else:
    print("\n⚠️ SOME TESTS FAILED")

print("\n" + "=" * 80)
print("EDGE CASE TESTING COMPLETE")
print("=" * 80)
