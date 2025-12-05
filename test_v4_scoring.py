#!/usr/bin/env python3
"""
Test V4 Scoring with Cheez-Its Example
Expected: D grade (~34.65 overall score)
"""

import sys
sys.path.append('.')

from main import calculate_v4_score

# Cheez-Its ingredient list (from V4 architecture doc)
cheezits_data = {
    "product_name": "Cheez-It Original",
    "brand": "Kellogg's",
    "category": "food",
    "ingredients": [
        "enriched flour",
        "vegetable oil",
        "cheese",
        "salt",
        "paprika",
        "yeast",
        "paprika extract color",
        "soy lecithin",
        "tbhq",           # F-grade
        "yellow 5",       # D-grade
        "yellow 6",       # D-grade
        "high fructose corn syrup",  # D-grade
        "palm oil",       # C-grade
        "maltodextrin",   # NOVA marker
        "modified food starch",  # NOVA marker
        "natural flavor"  # NOVA marker
    ]
}

print("=" * 60)
print("TESTING V4 SCORING: Cheez-It Original")
print("=" * 60)
print()

# Run V4 scoring
results = calculate_v4_score(cheezits_data)

# Display results
print(f"📊 OVERALL SCORE: {results['overall_score']}/100")
print(f"📝 OVERALL GRADE: {results['overall_grade']}")
print()

print("🎯 DIMENSION SCORES:")
for dimension, score in results['dimension_scores'].items():
    dimension_name = dimension.replace('_', ' ').title()
    print(f"  {dimension_name}: {score}/100")
print()

print(f"🔴 ALERTS ({len(results['alerts'])}):")
for alert in results['alerts']:
    print(f"  • {alert}")
print()

print(f"📚 HIDDEN TRUTHS ({len(results['hidden_truths'])}):")
for truth in results['hidden_truths']:
    preview = truth.split('\n')[0][:70] + "..."
    print(f"  • {preview}")
print()

print(f"🏢 PARENT COMPANY: {results.get('parent_company', 'None detected')}")
print()

print("🧪 INGREDIENT BREAKDOWN (Worst-First):")
for ing in results['ingredients_graded']:
    grade_emoji = {
        "F": "🔴",
        "D": "🟠",
        "C": "🟡",
        "B": "🟢",
        "A": "🟢"
    }.get(ing['grade'], "⚪")

    print(f"  {grade_emoji} [{ing['grade']}] {ing['name']}")
    print(f"      Reason: {ing['reason'][:80]}...")
print()

# Validation
print("=" * 60)
print("✅ VALIDATION")
print("=" * 60)
expected_grade = "D"
expected_score_range = (30, 40)  # Should be ~34.65

print(f"Expected Grade: {expected_grade}")
print(f"Actual Grade: {results['overall_grade']}")
print(f"✓ PASS" if results['overall_grade'] == expected_grade else "✗ FAIL")
print()

print(f"Expected Score Range: {expected_score_range[0]}-{expected_score_range[1]}")
print(f"Actual Score: {results['overall_score']}")
in_range = expected_score_range[0] <= results['overall_score'] <= expected_score_range[1]
print(f"✓ PASS" if in_range else "✗ FAIL")
print()

# Check key features
checks = [
    ("TBHQ detected as D-grade", any("tbhq" in ing['name'].lower() and ing['grade'] == 'D' for ing in results['ingredients_graded'])),
    ("Kellogg's penalty applied", results.get('parent_company') == 'Kellogg\'s'),
    ("Corporate alert present", any("OWNED BY" in alert for alert in results['alerts'])),
    ("Score capped at D grade", results['overall_score'] <= 49),
    ("Processing detected", any("PROCESSED" in alert for alert in results['alerts'])),
    ("Hidden truth shown", len(results['hidden_truths']) > 0)
]

print("🔍 FEATURE CHECKS:")
for check_name, passed in checks:
    status = "✓" if passed else "✗"
    print(f"  {status} {check_name}")

print()
print("=" * 60)
all_passed = results['overall_grade'] == expected_grade and in_range and all(c[1] for c in checks)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
else:
    print("⚠️ SOME TESTS FAILED")
print("=" * 60)
