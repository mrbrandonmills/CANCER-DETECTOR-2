#!/usr/bin/env python3
"""
Test V4 Phase 2: Hidden Truths Expansion & Corporate Disclosures
Tests new hidden truth paragraphs and corporate disclosure with notable brands
"""

import sys
sys.path.append('.')

from main import calculate_v4_score

print("=" * 80)
print("V4 PHASE 2 TESTING: Hidden Truths & Corporate Disclosures")
print("=" * 80)
print()

# ============================================
# TEST 1: F-GRADE INGREDIENT WITH BHA
# ============================================
print("TEST 1: Product with BHA (F-grade ingredient)")
print("-" * 80)

test1_data = {
    "product_name": "Rice Krispies Treats",
    "brand": "Kellogg's",
    "category": "food",
    "ingredients": ["rice", "sugar", "BHA", "corn syrup"]
}

results1 = calculate_v4_score(test1_data)

print(f"✓ Product: {test1_data['product_name']}")
print(f"✓ Overall Score: {results1['overall_score']}/100 (Grade: {results1['overall_grade']})")
print(f"✓ Alerts: {len(results1['alerts'])} total")
for alert in results1['alerts']:
    print(f"  • {alert}")
print()

# Check for BHA hidden truth
bha_truth_found = any("BHA" in truth and "Group 2B carcinogen" in truth for truth in results1['hidden_truths'])
print(f"✓ BHA Hidden Truth: {'FOUND ✓' if bha_truth_found else 'MISSING ✗'}")
print()

# Check corporate disclosure
if results1.get('corporate_disclosure'):
    disclosure = results1['corporate_disclosure']
    print(f"✓ Corporate Disclosure:")
    print(f"  Parent Company: {disclosure['parent_company']}")
    print(f"  Penalty Applied: {disclosure['penalty_applied']} points")
    print(f"  Issues: {len(disclosure['issues'])} total")
    print(f"  Notable Brands: {', '.join(disclosure['notable_brands'])}")
else:
    print("✗ Corporate Disclosure: MISSING")
print()
print()

# ============================================
# TEST 2: PRODUCT WITH RED 3
# ============================================
print("TEST 2: Product with Red 3 (FDA-acknowledged carcinogen)")
print("-" * 80)

test2_data = {
    "product_name": "Maraschino Cherries",
    "brand": "Generic",
    "category": "food",
    "ingredients": ["cherries", "corn syrup", "red 3", "citric acid"]
}

results2 = calculate_v4_score(test2_data)

print(f"✓ Product: {test2_data['product_name']}")
print(f"✓ Overall Score: {results2['overall_score']}/100 (Grade: {results2['overall_grade']})")
print()

# Check for Red 3 hidden truth
red3_truth_found = any("Red 3" in truth and "carcinogen in 1990" in truth for truth in results2['hidden_truths'])
print(f"✓ Red 3 Hidden Truth: {'FOUND ✓' if red3_truth_found else 'MISSING ✗'}")
if red3_truth_found:
    print("  Preview: FDA banned in cosmetics but still allowed in food...")
print()

# Check for F-grade detection
has_f_grade = any(ing['grade'] == 'F' for ing in results2['ingredients_graded'])
print(f"✓ F-Grade Detected: {'YES ✓' if has_f_grade else 'NO ✗'}")
print(f"✓ Score Capped: {'YES ✓' if results2['overall_score'] <= 49 else 'NO ✗'}")
print()
print()

# ============================================
# TEST 3: GENERAL MILLS PRODUCT (HEALTHY BRAND)
# ============================================
print("TEST 3: Annie's Organic (owned by General Mills)")
print("-" * 80)

test3_data = {
    "product_name": "Annie's Organic Mac & Cheese",
    "brand": "Annie's",
    "category": "food",
    "ingredients": ["organic pasta", "organic cheddar", "salt"]
}

results3 = calculate_v4_score(test3_data)

print(f"✓ Product: {test3_data['product_name']}")
print(f"✓ Brand: {test3_data['brand']}")
print(f"✓ Overall Score: {results3['overall_score']}/100 (Grade: {results3['overall_grade']})")
print()

# Check corporate disclosure
if results3.get('corporate_disclosure'):
    disclosure = results3['corporate_disclosure']
    print(f"✓ CORPORATE DISCLOSURE WORKING:")
    print(f"  Parent: {disclosure['parent_company']}")
    print(f"  Notable Brands (Did You Know): {', '.join(disclosure['notable_brands'])}")
    print(f"  Shows healthy/junk contrast: {'YES ✓' if 'Lucky Charms' in str(disclosure['notable_brands']) else 'NO ✗'}")

    # Check for corporate truth in hidden_truths
    corporate_truth_found = any("CORPORATE OWNERSHIP" in truth and disclosure['parent_company'] in truth
                                 for truth in results3['hidden_truths'])
    print(f"  Corporate Truth Paragraph: {'FOUND ✓' if corporate_truth_found else 'MISSING ✗'}")
else:
    print("✗ CORPORATE DISCLOSURE: MISSING (Expected General Mills)")
print()
print()

# ============================================
# TEST 4: PARTIALLY HYDROGENATED OILS (TRANS FATS)
# ============================================
print("TEST 4: Product with Partially Hydrogenated Oils")
print("-" * 80)

test4_data = {
    "product_name": "Oreo Cookies",
    "brand": "Oreo",
    "category": "food",
    "ingredients": ["sugar", "flour", "partially hydrogenated soybean oil", "cocoa"]
}

results4 = calculate_v4_score(test4_data)

print(f"✓ Product: {test4_data['product_name']}")
print(f"✓ Overall Score: {results4['overall_score']}/100 (Grade: {results4['overall_grade']})")
print()

# Check for trans fat hidden truth
trans_fat_truth_found = any("trans fats" in truth.lower() and "NO SAFE LEVEL" in truth
                            for truth in results4['hidden_truths'])
print(f"✓ Trans Fat Hidden Truth: {'FOUND ✓' if trans_fat_truth_found else 'MISSING ✗'}")
print()

# Check Mondelez disclosure
if results4.get('corporate_disclosure'):
    print(f"✓ Parent Company: {results4['corporate_disclosure']['parent_company']}")
    print(f"  (Expected: Mondelez)")
print()
print()

# ============================================
# PHASE 2 VALIDATION SUMMARY
# ============================================
print("=" * 80)
print("PHASE 2 VALIDATION SUMMARY")
print("=" * 80)

checks = [
    ("BHA hidden truth displays correctly", bha_truth_found),
    ("Red 3 hidden truth displays correctly", red3_truth_found),
    ("Trans fat hidden truth displays correctly", trans_fat_truth_found),
    ("Corporate disclosure includes parent company", results3.get('corporate_disclosure') is not None),
    ("Corporate disclosure includes notable brands",
     len(results3.get('corporate_disclosure', {}).get('notable_brands', [])) > 0 if results3.get('corporate_disclosure') else False),
    ("Corporate disclosure includes issues list",
     len(results3.get('corporate_disclosure', {}).get('issues', [])) > 0 if results3.get('corporate_disclosure') else False),
    ("Corporate disclosure includes penalty amount",
     results3.get('corporate_disclosure', {}).get('penalty_applied') is not None if results3.get('corporate_disclosure') else False),
    ("F-grade ingredients trigger score cap", results2['overall_score'] <= 49),
]

print()
all_passed = all(check[1] for check in checks)

for check_name, passed in checks:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {check_name}")

print()
print("=" * 80)
if all_passed:
    print("🎉 ALL PHASE 2 TESTS PASSED!")
else:
    print("⚠️ SOME PHASE 2 TESTS FAILED")
print("=" * 80)

# Display one full corporate disclosure example
print()
print("EXAMPLE CORPORATE DISCLOSURE OUTPUT:")
print("-" * 80)
if results3.get('corporate_disclosure'):
    disclosure = results3['corporate_disclosure']
    print(f"Parent Company: {disclosure['parent_company']}")
    print(f"Penalty Applied: {disclosure['penalty_applied']} points")
    print()
    print("Issues:")
    for issue in disclosure['issues']:
        print(f"  • {issue}")
    print()
    print(f"Notable Brands: {', '.join(disclosure['notable_brands'])}")
    print()
    print("Hidden Truth Paragraph:")
    corporate_truths = [t for t in results3['hidden_truths'] if "CORPORATE OWNERSHIP" in t]
    if corporate_truths:
        print(corporate_truths[0][:300] + "...")
print("=" * 80)
