#!/usr/bin/env python3
"""
Test V4 Phase 3: Deep Research System
Tests async job queue and comprehensive report generation
"""

import requests
import time
import json

# Test against local server
BASE_URL = "http://localhost:8000"

print("=" * 80)
print("V4 PHASE 3 TESTING: Deep Research System")
print("=" * 80)
print()

# ============================================
# TEST 1: Cheez-Its Deep Research
# ============================================
print("TEST 1: Starting Deep Research for Cheez-It Original")
print("-" * 80)

test_data = {
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
        "tbhq",
        "yellow 5",
        "yellow 6",
        "high fructose corn syrup"
    ]
}

try:
    # Start deep research
    response = requests.post(f"{BASE_URL}/api/v4/deep-research", json=test_data)
    response.raise_for_status()
    result = response.json()

    job_id = result["job_id"]
    print(f"✓ Deep research job started")
    print(f"✓ Job ID: {job_id}")
    print(f"✓ Status URL: {result['check_status_url']}")
    print()

    # Poll job status
    print("Polling job status...")
    print()

    max_polls = 60  # Max 60 seconds
    poll_count = 0

    while poll_count < max_polls:
        time.sleep(2)  # Wait 2 seconds between polls
        poll_count += 1

        status_response = requests.get(f"{BASE_URL}/api/v4/job/{job_id}")
        status_response.raise_for_status()
        job_status = status_response.json()

        status = job_status["status"]
        progress = job_status["progress"]
        current_step = job_status.get("current_step", "Unknown")

        print(f"  [{status.upper()}] {progress}% - {current_step}")

        if status == "completed":
            print()
            print("✓ Deep research COMPLETED!")
            print()

            # Display report
            result = job_status["result"]
            print("=" * 80)
            print("DEEP RESEARCH REPORT")
            print("=" * 80)
            print(f"Product: {result['product_name']}")
            print(f"Brand: {result['brand']}")
            print(f"Category: {result['category']}")
            print()

            # Display sections
            report = result.get("report", {})
            for section_name, section_content in report.items():
                print(f"\n## {section_name}")
                print("-" * 80)
                # Show first 300 characters of each section
                preview = section_content[:300]
                if len(section_content) > 300:
                    preview += "..."
                print(preview)
                print()

            # Validation checks
            print("=" * 80)
            print("VALIDATION CHECKS")
            print("=" * 80)
            expected_sections = [
                "1. EXECUTIVE SUMMARY",
                "2. THE COMPANY BEHIND IT",
                "3. INGREDIENT DEEP DIVE",
                "4. SUPPLY CHAIN INVESTIGATION",
                "5. REGULATORY HISTORY",
                "6. BETTER ALTERNATIVES",
                "7. ACTION ITEMS FOR CONSUMER"
            ]

            all_passed = True
            for section in expected_sections:
                found = any(section in key for key in report.keys())
                status = "✓ PASS" if found else "✗ FAIL"
                print(f"{status}: Section '{section}' present")
                if not found:
                    all_passed = False

            print()
            if all_passed:
                print("🎉 ALL SECTIONS PRESENT!")
            else:
                print("⚠️ SOME SECTIONS MISSING")
            print("=" * 80)

            break

        elif status == "failed":
            print()
            print(f"✗ Deep research FAILED")
            print(f"Error: {job_status.get('error', 'Unknown error')}")
            break

    if poll_count >= max_polls:
        print()
        print("⚠️ TIMEOUT: Deep research took longer than expected")

except requests.exceptions.RequestException as e:
    print(f"✗ Network Error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
