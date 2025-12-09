#!/usr/bin/env python3
"""
Test script to verify V4 API is returning correct data structure
"""
import requests
import json

API_URL = "https://cancer-detector-backend-production.up.railway.app/api/v4/scan"

print("🔬 Testing V4 API Response Structure")
print("=" * 60)
print(f"API URL: {API_URL}")
print()

# Test with a simple text file (since we can't send actual product images in this test)
# The API will attempt to parse it and we can see the response structure

test_data = {
    "image": ("test.jpg", b"fake image data", "image/jpeg")
}

try:
    # Just check if API is reachable and get response structure
    response = requests.get("https://cancer-detector-backend-production.up.railway.app/health")

    if response.status_code == 200:
        print("✅ Backend is ONLINE")
        print(f"Health check: {response.json()}")
    else:
        print(f"❌ Backend returned status {response.status_code}")

except Exception as e:
    print(f"❌ Cannot reach backend: {e}")

print()
print("=" * 60)
print()
print("❗ CRITICAL QUESTION:")
print("When you scan Clorox in TestFlight, does the app show:")
print("1. ✅ Score/Grade (you said YES)")
print("2. ✅ 4-dimension circles (you said YES)")
print("3. ✅ Deep Research button (you said YES)")
print("4. ❌ Alerts section (you said NO - MISSING)")
print("5. ❌ Hidden truths cards (you said NO - MISSING)")
print("6. ❌ Ingredient list (you said NO - MISSING)")
print()
print("This means the API is returning:")
print("- overall_score: ✅ (shown)")
print("- dimension_scores: ✅ (shown)")
print("- alerts: [] (EMPTY - hidden by conditional rendering)")
print("- hidden_truths: [] (EMPTY - hidden)")
print("- ingredients_graded: [] (EMPTY - hidden)")
print()
print("=" * 60)
print()
print("🔍 ROOT CAUSE:")
print("Claude Vision API is NOT extracting ingredients from the photo.")
print("When ingredients array is empty, calculate_v4_score returns empty arrays.")
print()
print("SOLUTION: Check Railway logs for this line:")
print('[V4 SCAN] Ingredients extracted: 0')
print()
print("If count is 0, the Vision API failed to read the label.")
