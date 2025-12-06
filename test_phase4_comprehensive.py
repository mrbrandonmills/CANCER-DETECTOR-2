#!/usr/bin/env python3
"""
Phase 4 Comprehensive Production Testing
Tests all V4 features on Railway deployment
"""

import requests
import json
import time

PRODUCTION_URL = "https://cancer-detector-backend-production.up.railway.app"

print("=" * 80)
print("PHASE 4 COMPREHENSIVE PRODUCTION TESTING")
print("Testing all V4 features on Railway deployment")
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
# TEST SUITE 1: Health & Infrastructure
# ============================================
print("\n" + "=" * 80)
print("TEST SUITE 1: Health & Infrastructure")
print("=" * 80)

try:
    health_response = requests.get(f"{PRODUCTION_URL}/health")
    health_data = health_response.json()

    test("Health endpoint accessible", health_response.status_code == 200)
    test("Status is healthy", health_data.get('status') == 'healthy')
    test("Claude API connected", health_data.get('claude_api') == 'connected')
    test("Version is 3.0.0+", health_data.get('version') >= '3.0.0')
    test("V3 endpoints ready", health_data.get('v3_ready') == True)
    test("Modular prompts enabled", health_data.get('modular_prompts') == True)

except Exception as e:
    test("Health endpoint accessible", False, str(e))

# ============================================
# TEST SUITE 2: Deep Research (Phase 3)
# ============================================
print("\n" + "=" * 80)
print("TEST SUITE 2: Deep Research (Phase 3)")
print("=" * 80)

try:
    # Start deep research job
    dr_request = {
        "product_name": "Test Product",
        "brand": "Test Brand",
        "category": "food",
        "ingredients": ["water", "salt"]
    }

    dr_response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=dr_request)
    dr_data = dr_response.json()

    test("Deep Research endpoint exists", dr_response.status_code == 200)
    test("Job ID returned", "job_id" in dr_data)
    test("Status URL provided", "check_status_url" in dr_data)

    if "job_id" in dr_data:
        job_id = dr_data["job_id"]

        # Check job status
        time.sleep(2)
        status_response = requests.get(f"{PRODUCTION_URL}/api/v4/job/{job_id}")
        status_data = status_response.json()

        test("Job status endpoint works", status_response.status_code == 200)
        test("Job tracking working", status_data.get('status') in ['pending', 'processing', 'completed'])
        test("Progress tracking present", 'progress' in status_data)
        test("Current step shown", 'current_step' in status_data)

        # Monitor until completion (max 60 seconds)
        max_polls = 30
        poll_count = 0
        completed = False

        while poll_count < max_polls and not completed:
            time.sleep(2)
            poll_response = requests.get(f"{PRODUCTION_URL}/api/v4/job/{job_id}")
            poll_data = poll_response.json()

            if poll_data.get('status') == 'completed':
                completed = True
                result = poll_data.get('result', {})
                report = result.get('report', {})

                # Validate report structure
                expected_sections = [
                    "1. EXECUTIVE SUMMARY",
                    "2. THE COMPANY BEHIND IT",
                    "3. INGREDIENT DEEP DIVE",
                    "4. SUPPLY CHAIN INVESTIGATION",
                    "5. REGULATORY HISTORY",
                    "6. BETTER ALTERNATIVES",
                    "7. ACTION ITEMS FOR CONSUMER"
                ]

                sections_found = sum(1 for section in expected_sections if any(section in key for key in report.keys()))

                test("Deep Research completes", True)
                test("All 7 report sections present", sections_found == 7, f"{sections_found}/7 sections found")
                test("Full report generated", len(result.get('full_report', '')) > 1000)

            elif poll_data.get('status') == 'failed':
                test("Deep Research completes", False, f"Failed: {poll_data.get('error')}")
                break

            poll_count += 1

        if not completed and poll_count >= max_polls:
            test("Deep Research completes in time", False, "Timeout after 60 seconds")

except Exception as e:
    test("Deep Research system working", False, str(e))

# ============================================
# TEST SUITE 3: V4 Scoring Validation
# ============================================
print("\n" + "=" * 80)
print("TEST SUITE 3: V4 Scoring Validation")
print("=" * 80)

# Import local scoring function for validation
import sys
sys.path.append('.')
from main import calculate_v4_score

# Test Cheez-Its (should be D, not A+)
cheezits_data = {
    "product_name": "Cheez-It Original",
    "brand": "Kellogg's",
    "category": "food",
    "ingredients": [
        "enriched flour", "vegetable oil", "cheese", "salt", "paprika", "yeast",
        "tbhq", "yellow 5", "yellow 6", "high fructose corn syrup", "palm oil"
    ]
}

try:
    cheezits_result = calculate_v4_score(cheezits_data)

    test("Cheez-Its scores D (not A+)", cheezits_result['overall_grade'] == 'D',
         f"Grade: {cheezits_result['overall_grade']}, Score: {cheezits_result['overall_score']}")
    test("Score capped due to D-grade ingredients", cheezits_result['overall_score'] <= 49)
    test("D-grade ingredients detected", any(ing['grade'] == 'D' for ing in cheezits_result['ingredients_graded']))
    test("Corporate ownership detected", 'parent_company' in cheezits_result)
    test("Kellogg's penalty applied", cheezits_result.get('parent_company') == "Kellogg's")
    test("Processing alerts present", any('PROCESSED' in alert for alert in cheezits_result['alerts']))

except Exception as e:
    test("V4 scoring working", False, str(e))

# ============================================
# TEST SUITE 4: Hidden Truths (Phase 2)
# ============================================
print("\n" + "=" * 80)
print("TEST SUITE 4: Hidden Truths (Phase 2)")
print("=" * 80)

# Test BHA (F-grade with hidden truth)
bha_data = {
    "product_name": "Rice Krispies Treats",
    "brand": "Kellogg's",
    "category": "food",
    "ingredients": ["enriched flour", "sugar", "BHA", "corn syrup"]
}

try:
    bha_result = calculate_v4_score(bha_data)

    test("BHA detected as F-grade", any("BHA" in ing['name'] and ing['grade'] == 'F' for ing in bha_result['ingredients_graded']))
    test("BHA hidden truth shown", any("BHA" in str(truth) or "TBHQ" in str(truth) for truth in bha_result['hidden_truths']))
    test("F-grade ingredient caps score", bha_result['overall_score'] <= 49)
    test("Score cap alert present", any("SCORE CAPPED" in alert or "cannot score above" in alert.lower() for alert in bha_result['alerts']))

except Exception as e:
    test("Hidden truths working", False, str(e))

# ============================================
# TEST SUITE 5: Corporate Disclosures (Phase 2)
# ============================================
print("\n" + "=" * 80)
print("TEST SUITE 5: Corporate Disclosures (Phase 2)")
print("=" * 80)

# Test Annie's (owned by General Mills)
annies_data = {
    "product_name": "Annie's Organic Mac & Cheese",
    "brand": "Annie's",
    "category": "food",
    "ingredients": ["organic pasta", "cheese", "butter", "salt"]
}

try:
    annies_result = calculate_v4_score(annies_data)

    test("Corporate ownership detected", 'parent_company' in annies_result)
    test("General Mills ownership shown", annies_result.get('parent_company') == "General Mills")
    test("Corporate disclosure present", 'corporate_disclosure' in annies_result)

    if 'corporate_disclosure' in annies_result:
        disclosure = annies_result['corporate_disclosure']
        test("Notable brands included", 'notable_brands' in disclosure)
        test("Parent issues listed", 'issues' in disclosure and len(disclosure['issues']) > 0)
        test("Penalty amount shown", 'penalty_applied' in disclosure)

except Exception as e:
    test("Corporate disclosures working", False, str(e))

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"\nTests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
print()

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED!")
    print()
    print("✅ V4 Phase 1: Core Scoring System - WORKING")
    print("✅ V4 Phase 2: Hidden Truths & Corporate Disclosures - WORKING")
    print("✅ V4 Phase 3: Deep Research System - WORKING")
    print("✅ V4 Phase 4: Production Validation - COMPLETE")
else:
    print("⚠️ SOME TESTS FAILED")
    print("\nFailed Tests:")
    for name, passed, details in test_results:
        if not passed:
            print(f"  ✗ {name}")
            if details:
                print(f"    {details}")

print("\n" + "=" * 80)
print("PHASE 4 TESTING COMPLETE")
print("=" * 80)
