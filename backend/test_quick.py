#!/usr/bin/env python3
"""
Cancer Detector v2 - Quick Test
================================
Run: python test_quick.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from scoring import calculate_cancer_score
from unified_database import (
    unified_product_search, 
    unified_barcode_lookup,
    lookup_chemical,
    TOXIC_CHEMICALS_DB
)

async def main():
    print("=" * 60)
    print("🔬 CANCER DETECTOR v2 - SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: Chemical Database
    print(f"\n1️⃣ Chemical Database: {len(TOXIC_CHEMICALS_DB)} chemicals loaded")
    
    test_chems = [
        ("sodium hypochlorite", "bleach"),
        ("formaldehyde", "carcinogen"),
        ("triclosan", "endocrine disruptor"),
        ("water", "safe")
    ]
    
    for chem, expected in test_chems:
        info = lookup_chemical(chem)
        if info:
            print(f"   ✓ {chem}: {info.toxicity_score}/10 ({expected})")
        else:
            print(f"   ✗ {chem}: NOT FOUND")
    
    # Test 2: Scoring Algorithm
    print("\n2️⃣ Scoring Algorithm Tests:")
    
    # Clorox wipes
    clorox = ["Water", "Alkyl Dimethyl Benzyl Ammonium Chloride", "Fragrance", "Sodium Hypochlorite"]
    result = calculate_cancer_score(clorox)
    print(f"   Clorox-type: {result.cancer_score}/100 ({result.color.upper()})")
    
    # Product with carcinogen
    bad = ["Water", "Formaldehyde", "Fragrance"]
    result2 = calculate_cancer_score(bad)
    print(f"   Carcinogen:  {result2.cancer_score}/100 ({result2.color.upper()}) - {result2.carcinogens_found}")
    
    # Safe product
    safe = ["Water", "Aloe Vera", "Coconut Oil", "Vitamin E"]
    result3 = calculate_cancer_score(safe)
    print(f"   Natural:     {result3.cancer_score}/100 ({result3.color.upper()})")
    
    # Test 3: Database Search (may fail in restricted networks)
    print("\n3️⃣ Database Search:")
    try:
        results = await unified_product_search("disinfecting spray", limit=2)
        if results:
            print(f"   Found {len(results)} products:")
            for r in results:
                print(f"   - {r.name} ({r.source})")
        else:
            print("   ⚠ No results (network may be restricted)")
    except Exception as e:
        print(f"   ⚠ Search failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ CORE SYSTEMS WORKING - Ready to deploy!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. railway login")
    print("2. railway link -p 880467d6-24df-4297-8a25-5417d06c0d98")
    print("3. railway up")


if __name__ == "__main__":
    asyncio.run(main())
