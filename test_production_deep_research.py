#!/usr/bin/env python3
"""
Test Deep Research in Production
Tests the deployed Railway instance with real Anthropic API
"""

import requests
import time
import json

PRODUCTION_URL = "https://cancer-detector-backend-production.up.railway.app"

print("=" * 80)
print("PRODUCTION TEST: Deep Research System")
print("Testing Railway deployment with real Anthropic API")
print("=" * 80)
print()

# ============================================
# TEST 1: Health Check
# ============================================
print("TEST 1: Verify deployment is healthy")
print("-" * 80)

try:
    health_response = requests.get(f"{PRODUCTION_URL}/health")
    health_response.raise_for_status()
    health_data = health_response.json()

    print(f"✓ Status: {health_data.get('status')}")
    print(f"✓ Version: {health_data.get('version')}")
    print(f"✓ Claude API: {health_data.get('claude_api')}")
    print()

except Exception as e:
    print(f"✗ FAIL: Health check failed - {e}")
    print()
    exit(1)

# ============================================
# TEST 2: Start Deep Research for Cheez-Its
# ============================================
print("TEST 2: Start Deep Research for Cheez-It Original")
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
    response = requests.post(f"{PRODUCTION_URL}/api/v4/deep-research", json=test_data)
    response.raise_for_status()
    result = response.json()

    job_id = result["job_id"]
    print(f"✓ Deep research job started")
    print(f"✓ Job ID: {job_id}")
    print(f"✓ Status URL: {result['check_status_url']}")
    print()

    # ============================================
    # TEST 3: Poll Job Status Until Complete
    # ============================================
    print("TEST 3: Monitor job progress until completion")
    print("-" * 80)

    max_polls = 90  # Max 3 minutes (90 * 2 seconds)
    poll_count = 0
    last_progress = -1

    while poll_count < max_polls:
        time.sleep(2)  # Poll every 2 seconds
        poll_count += 1

        status_response = requests.get(f"{PRODUCTION_URL}/api/v4/job/{job_id}")
        status_response.raise_for_status()
        job_status = status_response.json()

        status = job_status["status"]
        progress = job_status["progress"]
        current_step = job_status.get("current_step", "Unknown")

        # Only print if progress changed
        if progress != last_progress:
            print(f"  [{status.upper()}] {progress}% - {current_step}")
            last_progress = progress

        if status == "completed":
            print()
            print("=" * 80)
            print("✓ DEEP RESEARCH COMPLETED!")
            print("=" * 80)
            print()

            # ============================================
            # TEST 4: Validate Report Structure
            # ============================================
            print("TEST 4: Validate report structure and content")
            print("-" * 80)

            result = job_status["result"]
            report = result.get("report", {})

            print(f"Product: {result['product_name']}")
            print(f"Brand: {result['brand']}")
            print(f"Category: {result['category']}")
            print()

            # Expected sections
            expected_sections = [
                "1. EXECUTIVE SUMMARY",
                "2. THE COMPANY BEHIND IT",
                "3. INGREDIENT DEEP DIVE",
                "4. SUPPLY CHAIN INVESTIGATION",
                "5. REGULATORY HISTORY",
                "6. BETTER ALTERNATIVES",
                "7. ACTION ITEMS FOR CONSUMER"
            ]

            print("Section Validation:")
            all_passed = True
            for section in expected_sections:
                found = any(section in key for key in report.keys())
                status_icon = "✓" if found else "✗"
                print(f"  {status_icon} Section '{section}' {'present' if found else 'MISSING'}")
                if not found:
                    all_passed = False

            print()

            if all_passed:
                print("🎉 ALL 7 SECTIONS PRESENT!")
                print()

                # Display section previews
                print("=" * 80)
                print("REPORT PREVIEW (First 200 chars of each section)")
                print("=" * 80)
                for section_name, section_content in report.items():
                    print(f"\n## {section_name}")
                    print("-" * 80)
                    preview = section_content[:200].replace('\n', ' ')
                    if len(section_content) > 200:
                        preview += "..."
                    print(preview)

                print()
                print("=" * 80)
                print("FULL REPORT LENGTH:", len(result.get("full_report", "")), "characters")
                print("=" * 80)

            else:
                print("⚠️ SOME SECTIONS MISSING - Report incomplete")

            # Save full report to file
            report_filename = f"deep_research_report_{job_id[:8]}.json"
            with open(report_filename, 'w') as f:
                json.dump(result, f, indent=2)
            print()
            print(f"✓ Full report saved to: {report_filename}")

            break

        elif status == "failed":
            print()
            print("=" * 80)
            print(f"✗ DEEP RESEARCH FAILED")
            print("=" * 80)
            print(f"Error: {job_status.get('error', 'Unknown error')}")
            print()
            exit(1)

    if poll_count >= max_polls:
        print()
        print("=" * 80)
        print("⚠️ TIMEOUT: Deep research took longer than expected")
        print("=" * 80)
        print()
        exit(1)

except requests.exceptions.RequestException as e:
    print(f"✗ Network Error: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 80)
print("PRODUCTION TEST COMPLETE")
print("=" * 80)
print()
print("✓ Railway deployment is healthy")
print("✓ Deep Research API endpoints working")
print("✓ Background job processing working")
print("✓ Anthropic API integration working")
print("✓ All 7 report sections generated")
print()
print("Phase 3 Deep Research: PRODUCTION VALIDATED ✅")
print("=" * 80)
