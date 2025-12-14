"""
CANCER DETECTOR v3.1 - ADVANCED EDITION
========================================
Complete Analysis System: Ingredients + Materials + Condition Assessment

Features:
- Consumable products (food, cosmetics, cleaning) → Ingredient analysis
- Non-consumables (containers, cookware, items) → Material analysis
- Condition assessment from visual inspection
- Care tips and safer alternatives
- Comprehensive scoring system
"""

import os
import json
import base64
import re
import uuid
import asyncio
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
import anthropic
import asyncpg
from jinja2 import Environment, FileSystemLoader
# Reportlab for PDF generation (pure Python, no system deps)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s:     %(message)s')
logger = logging.getLogger(__name__)

# V3 Modular Prompts
from prompts import build_prompt

# ============================================
# CONFIGURATION
# ============================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not set!")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# ============================================
# POSTGRES DATABASE SETUP (V4 Caching)
# ============================================

db_pool = None

async def init_db():
    """Initialize Postgres connection pool on startup"""
    global db_pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("⚠️ DATABASE_URL not set - caching disabled")
        return

    try:
        db_pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10)
        logger.info("✅ Postgres connected for V4 caching")

        # V4 Caching: Create cached_products table (persistent across deployments)
        # Uses CREATE TABLE IF NOT EXISTS to preserve cached scans across deployments
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_products (
                    id SERIAL PRIMARY KEY,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    product_name VARCHAR(255),
                    brand VARCHAR(255),
                    data JSONB NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Create indexes for performance (IF NOT EXISTS to avoid errors on existing indexes)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cached_products_key ON cached_products(cache_key)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cached_products_updated ON cached_products(updated_at)
            """)
        logger.info("✅ Cached_products table ready for persistent V4 scan storage")

        # Create cached_deep_research table for persistent Deep Research storage
        # Uses CREATE TABLE IF NOT EXISTS to preserve cached research across deployments
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_deep_research (
                    id SERIAL PRIMARY KEY,
                    cache_key VARCHAR(255) UNIQUE NOT NULL,
                    product_name VARCHAR(255),
                    brand VARCHAR(255),
                    category VARCHAR(255),
                    report JSONB NOT NULL,
                    full_report TEXT,
                    pdf_bytes BYTEA,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cached_deep_research_key
                ON cached_deep_research(cache_key)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cached_deep_research_updated
                ON cached_deep_research(updated_at)
            """)
        logger.info("✅ Cached_deep_research table ready for persistent storage")
    except Exception as e:
        logger.error(f"❌ Postgres connection failed: {e}")
        db_pool = None

async def close_db():
    """Close Postgres connection pool on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Postgres connection closed")

# ============================================
# TOXICITY DATABASE (103 ingredients)
# ============================================

# Hazard ratings: 0 = safe, 10 = extremely hazardous
TOXICITY_DATABASE = {
    # ========== KNOWN CARCINOGENS (IARC Group 1) ==========
    "formaldehyde": {"score": 10, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["cancer", "respiratory irritation"]},
    "benzene": {"score": 10, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["leukemia", "blood cancer"]},
    "asbestos": {"score": 10, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["mesothelioma", "lung cancer"]},
    "1,4-dioxane": {"score": 9, "category": "carcinogen", "source": "IARC Group 2B", "concerns": ["cancer", "organ toxicity"]},
    "ethylene oxide": {"score": 10, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["cancer", "reproductive harm"]},

    # ========== ENDOCRINE DISRUPTORS ==========
    "triclosan": {"score": 8, "category": "endocrine_disruptor", "source": "EPA", "concerns": ["hormone disruption", "antibiotic resistance"]},
    "triclocarban": {"score": 8, "category": "endocrine_disruptor", "source": "EPA", "concerns": ["hormone disruption"]},
    "bisphenol a": {"score": 8, "category": "endocrine_disruptor", "source": "FDA", "concerns": ["hormone disruption", "reproductive harm"]},
    "bpa": {"score": 8, "category": "endocrine_disruptor", "source": "FDA", "concerns": ["hormone disruption", "reproductive harm"]},
    "phthalate": {"score": 7, "category": "endocrine_disruptor", "source": "EPA", "concerns": ["hormone disruption", "reproductive harm"]},
    "dibutyl phthalate": {"score": 8, "category": "endocrine_disruptor", "source": "Prop 65", "concerns": ["reproductive harm"]},
    "dehp": {"score": 8, "category": "endocrine_disruptor", "source": "Prop 65", "concerns": ["reproductive harm"]},
    "parabens": {"score": 5, "category": "endocrine_disruptor", "source": "EU SCCS", "concerns": ["weak hormone disruption"]},
    "methylparaben": {"score": 4, "category": "endocrine_disruptor", "source": "EU SCCS", "concerns": ["weak hormone disruption"]},
    "propylparaben": {"score": 5, "category": "endocrine_disruptor", "source": "EU SCCS", "concerns": ["hormone disruption"]},
    "butylparaben": {"score": 6, "category": "endocrine_disruptor", "source": "EU SCCS", "concerns": ["hormone disruption"]},
    "oxybenzone": {"score": 6, "category": "endocrine_disruptor", "source": "EWG", "concerns": ["hormone disruption", "coral reef damage"]},

    # ========== QUATERNARY AMMONIUM COMPOUNDS (Cleaning Products) ==========
    "benzalkonium chloride": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["asthma", "skin irritation", "antibiotic resistance"]},
    "alkyl dimethyl benzyl ammonium chloride": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["asthma", "skin irritation"]},
    "quaternary ammonium": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["asthma", "skin irritation"]},
    "didecyl dimethyl ammonium chloride": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["respiratory irritation"]},
    "alkyl dimethyl ethylbenzyl ammonium chloride": {"score": 6, "category": "respiratory_irritant", "source": "EPA", "concerns": ["asthma"]},
    "cetrimonium chloride": {"score": 4, "category": "irritant", "source": "CIR", "concerns": ["skin irritation"]},

    # ========== CHLORINE COMPOUNDS ==========
    "sodium hypochlorite": {"score": 5, "category": "irritant", "source": "EPA", "concerns": ["respiratory irritation", "skin burns", "toxic fumes when mixed"]},
    "chlorine": {"score": 6, "category": "irritant", "source": "EPA", "concerns": ["respiratory irritation", "toxic fumes"]},
    "chlorine dioxide": {"score": 5, "category": "irritant", "source": "EPA", "concerns": ["respiratory irritation"]},
    "hypochlorous acid": {"score": 3, "category": "irritant", "source": "EPA", "concerns": ["mild irritation"]},

    # ========== SOLVENTS ==========
    "2-butoxyethanol": {"score": 6, "category": "solvent", "source": "EPA", "concerns": ["liver damage", "kidney damage", "narcosis"]},
    "ethylene glycol": {"score": 7, "category": "solvent", "source": "EPA", "concerns": ["kidney damage", "toxic if ingested"]},
    "methanol": {"score": 7, "category": "solvent", "source": "EPA", "concerns": ["blindness", "organ damage"]},
    "isopropyl alcohol": {"score": 2, "category": "solvent", "source": "EPA", "concerns": ["mild irritation"]},
    "ethanol": {"score": 1, "category": "solvent", "source": "EPA", "concerns": ["minimal"]},
    "denatured alcohol": {"score": 2, "category": "solvent", "source": "EPA", "concerns": ["drying"]},
    "acetone": {"score": 3, "category": "solvent", "source": "EPA", "concerns": ["irritation", "drying"]},
    "toluene": {"score": 7, "category": "solvent", "source": "Prop 65", "concerns": ["reproductive harm", "neurological damage"]},
    "xylene": {"score": 6, "category": "solvent", "source": "EPA", "concerns": ["neurological effects"]},
    "perchloroethylene": {"score": 8, "category": "solvent", "source": "IARC Group 2A", "concerns": ["probable carcinogen", "neurological effects"]},

    # ========== FRAGRANCES & PRESERVATIVES ==========
    "fragrance": {"score": 5, "category": "undisclosed", "source": "EWG", "concerns": ["allergies", "undisclosed chemicals", "potential hormone disruptors"]},
    "parfum": {"score": 5, "category": "undisclosed", "source": "EWG", "concerns": ["allergies", "undisclosed chemicals"]},
    "synthetic fragrance": {"score": 5, "category": "undisclosed", "source": "EWG", "concerns": ["allergies", "undisclosed chemicals"]},
    "dmdm hydantoin": {"score": 7, "category": "preservative", "source": "EWG", "concerns": ["formaldehyde releaser", "allergies"]},
    "quaternium-15": {"score": 7, "category": "preservative", "source": "EWG", "concerns": ["formaldehyde releaser", "allergies"]},
    "imidazolidinyl urea": {"score": 6, "category": "preservative", "source": "EWG", "concerns": ["formaldehyde releaser"]},
    "diazolidinyl urea": {"score": 6, "category": "preservative", "source": "EWG", "concerns": ["formaldehyde releaser"]},
    "bronopol": {"score": 6, "category": "preservative", "source": "EU", "concerns": ["formaldehyde releaser", "nitrosamine formation"]},
    "methylisothiazolinone": {"score": 7, "category": "preservative", "source": "EU", "concerns": ["severe allergies", "neurotoxicity"]},
    "methylchloroisothiazolinone": {"score": 7, "category": "preservative", "source": "EU", "concerns": ["severe allergies"]},
    "phenoxyethanol": {"score": 3, "category": "preservative", "source": "CIR", "concerns": ["mild irritation"]},
    "sodium benzoate": {"score": 2, "category": "preservative", "source": "FDA", "concerns": ["benzene formation with vitamin C"]},
    "potassium sorbate": {"score": 1, "category": "preservative", "source": "FDA", "concerns": ["minimal"]},

    # ========== SURFACTANTS ==========
    "sodium lauryl sulfate": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["skin irritation", "drying"]},
    "sls": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["skin irritation"]},
    "sodium laureth sulfate": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["potential 1,4-dioxane contamination"]},
    "sles": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["potential contamination"]},
    "cocamidopropyl betaine": {"score": 2, "category": "surfactant", "source": "CIR", "concerns": ["rare allergies"]},
    "lauramine oxide": {"score": 3, "category": "surfactant", "source": "EPA", "concerns": ["mild irritation"]},
    "ammonium lauryl sulfate": {"score": 4, "category": "surfactant", "source": "CIR", "concerns": ["irritation"]},

    # ========== HEAVY METALS & CONTAMINANTS ==========
    "lead": {"score": 10, "category": "heavy_metal", "source": "CDC", "concerns": ["neurotoxicity", "developmental harm"]},
    "mercury": {"score": 10, "category": "heavy_metal", "source": "CDC", "concerns": ["neurotoxicity"]},
    "arsenic": {"score": 10, "category": "heavy_metal", "source": "IARC Group 1", "concerns": ["cancer", "organ damage"]},
    "cadmium": {"score": 9, "category": "heavy_metal", "source": "IARC Group 1", "concerns": ["cancer", "kidney damage"]},
    "chromium vi": {"score": 10, "category": "heavy_metal", "source": "IARC Group 1", "concerns": ["lung cancer"]},
    "thimerosal": {"score": 5, "category": "preservative", "source": "FDA", "concerns": ["mercury-based"]},

    # ========== PETROLEUM DERIVATIVES ==========
    "mineral oil": {"score": 3, "category": "petroleum", "source": "CIR", "concerns": ["contamination concerns", "comedogenic"]},
    "petrolatum": {"score": 3, "category": "petroleum", "source": "CIR", "concerns": ["contamination concerns if unrefined"]},
    "petroleum": {"score": 4, "category": "petroleum", "source": "EU", "concerns": ["contamination"]},
    "paraffin": {"score": 3, "category": "petroleum", "source": "CIR", "concerns": ["contamination concerns"]},
    "coal tar": {"score": 9, "category": "carcinogen", "source": "IARC Group 1", "concerns": ["cancer"]},

    # ========== AMMONIA & BASES ==========
    "ammonia": {"score": 5, "category": "irritant", "source": "EPA", "concerns": ["respiratory irritation", "toxic fumes"]},
    "ammonium hydroxide": {"score": 5, "category": "irritant", "source": "EPA", "concerns": ["burns", "respiratory irritation"]},
    "sodium hydroxide": {"score": 5, "category": "caustic", "source": "EPA", "concerns": ["burns", "corrosive"]},
    "potassium hydroxide": {"score": 5, "category": "caustic", "source": "EPA", "concerns": ["burns", "corrosive"]},

    # ========== ACIDS ==========
    "hydrochloric acid": {"score": 6, "category": "caustic", "source": "EPA", "concerns": ["burns", "toxic fumes"]},
    "phosphoric acid": {"score": 4, "category": "acid", "source": "EPA", "concerns": ["irritation"]},
    "sulfuric acid": {"score": 7, "category": "caustic", "source": "EPA", "concerns": ["severe burns"]},
    "citric acid": {"score": 1, "category": "acid", "source": "FDA", "concerns": ["minimal"]},
    "lactic acid": {"score": 1, "category": "acid", "source": "FDA", "concerns": ["minimal"]},

    # ========== ARTIFICIAL COLORS & FOOD ADDITIVES ==========
    "red 40": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity in children", "allergic reactions"]},
    "allura red": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity in children"]},
    "yellow 5": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity", "allergies"]},
    "tartrazine": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity", "allergies"]},
    "yellow 6": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity", "allergies"]},
    "sunset yellow": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["hyperactivity"]},
    "blue 1": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["allergic reactions"]},
    "brilliant blue": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["allergies"]},
    "blue 2": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["allergies"]},
    "green 3": {"score": 5, "category": "food_dye", "source": "FDA", "concerns": ["allergies"]},
    "bha": {"score": 7, "category": "preservative", "source": "IARC Group 2B", "concerns": ["possible carcinogen", "endocrine disruption"]},
    "butylated hydroxyanisole": {"score": 7, "category": "preservative", "source": "IARC Group 2B", "concerns": ["possible carcinogen"]},
    "bht": {"score": 7, "category": "preservative", "source": "IARC Group 3", "concerns": ["possible endocrine disruption"]},
    "butylated hydroxytoluene": {"score": 7, "category": "preservative", "source": "IARC Group 3", "concerns": ["endocrine concerns"]},
    "hfcs": {"score": 6, "category": "sweetener", "source": "FDA", "concerns": ["metabolic issues", "obesity", "diabetes risk"]},
    "high fructose corn syrup": {"score": 6, "category": "sweetener", "source": "FDA", "concerns": ["metabolic issues", "obesity"]},
    "sodium nitrite": {"score": 7, "category": "preservative", "source": "IARC Group 2A", "concerns": ["forms carcinogenic nitrosamines", "processed meat risk"]},
    "sodium nitrate": {"score": 6, "category": "preservative", "source": "IARC Group 2A", "concerns": ["converts to nitrite", "cancer risk"]},
    "msg": {"score": 3, "category": "flavor_enhancer", "source": "FDA", "concerns": ["headaches in sensitive individuals", "allergies"]},
    "monosodium glutamate": {"score": 3, "category": "flavor_enhancer", "source": "FDA", "concerns": ["headaches", "allergies"]},
    "tbhq": {"score": 6, "category": "preservative", "source": "FDA", "concerns": ["vision problems", "DNA damage in studies"]},
    "tertiary butylhydroquinone": {"score": 6, "category": "preservative", "source": "FDA", "concerns": ["vision problems"]},

    # ========== SAFE INGREDIENTS ==========
    "water": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "aqua": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "glycerin": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "vegetable glycerin": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "aloe vera": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "aloe barbadensis": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "coconut oil": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "shea butter": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "jojoba oil": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "vitamin e": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "tocopherol": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "baking soda": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "sodium bicarbonate": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "vinegar": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "acetic acid": {"score": 1, "category": "safe", "source": "FDA", "concerns": []},
    "hydrogen peroxide": {"score": 2, "category": "oxidizer", "source": "FDA", "concerns": ["irritation at high concentrations"]},
    "sodium chloride": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "salt": {"score": 0, "category": "safe", "source": "FDA", "concerns": []},
    "essential oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["possible allergies"]},
    "lavender oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["possible allergies"]},
    "tea tree oil": {"score": 2, "category": "safe", "source": "FDA", "concerns": ["possible allergies", "hormone effects in children"]},
    "eucalyptus oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["possible allergies"]},
    "lemon oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["photosensitivity"]},
    "orange oil": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["photosensitivity"]},
    "sodium carbonate": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["mild irritation"]},
    "washing soda": {"score": 1, "category": "safe", "source": "FDA", "concerns": ["mild irritation"]},
}

# ============================================
# MATERIAL DATABASE
# ============================================

MATERIAL_DATABASE = {
    # === PLASTICS ===
    "pet": {
        "full_name": "Polyethylene Terephthalate",
        "recycling_code": "#1",
        "score": 75,
        "concerns": ["microplastics when scratched", "antimony leaching potential"],
        "safe_for": ["cold beverages", "single use"],
        "avoid": ["hot liquids", "reuse when scratched", "dishwasher"]
    },
    "hdpe": {
        "full_name": "High-Density Polyethylene",
        "recycling_code": "#2",
        "score": 90,
        "concerns": ["minimal"],
        "safe_for": ["food storage", "beverages", "reuse"],
        "avoid": ["very high heat"]
    },
    "pvc": {
        "full_name": "Polyvinyl Chloride",
        "recycling_code": "#3",
        "score": 30,
        "concerns": ["phthalates", "dioxins", "lead stabilizers", "chlorine"],
        "safe_for": ["non-food applications only"],
        "avoid": ["food contact", "heating", "children's products"]
    },
    "ldpe": {
        "full_name": "Low-Density Polyethylene",
        "recycling_code": "#4",
        "score": 85,
        "concerns": ["minimal"],
        "safe_for": ["food storage bags", "squeeze bottles"],
        "avoid": ["high heat"]
    },
    "pp": {
        "full_name": "Polypropylene",
        "recycling_code": "#5",
        "score": 95,
        "concerns": ["minimal"],
        "safe_for": ["microwave", "food storage", "hot liquids"],
        "avoid": []
    },
    "polypropylene": {
        "full_name": "Polypropylene",
        "recycling_code": "#5",
        "score": 95,
        "concerns": ["minimal"],
        "safe_for": ["microwave", "food storage", "hot liquids"],
        "avoid": []
    },
    "ps": {
        "full_name": "Polystyrene",
        "recycling_code": "#6",
        "score": 40,
        "concerns": ["styrene leaching", "possible carcinogen", "not recyclable"],
        "safe_for": ["cold items only", "single use"],
        "avoid": ["hot food", "fatty foods", "microwave", "reuse"]
    },
    "polycarbonate": {
        "full_name": "Polycarbonate",
        "recycling_code": "#7",
        "score": 35,
        "concerns": ["BPA leaching", "hormone disruption"],
        "safe_for": ["nothing if contains BPA"],
        "avoid": ["food contact", "baby bottles", "heating"]
    },

    # === GLASS ===
    "glass": {
        "full_name": "Glass",
        "recycling_code": "♻",
        "score": 98,
        "concerns": ["breakage"],
        "safe_for": ["everything", "microwave", "dishwasher", "hot liquids"],
        "avoid": ["dropping"]
    },
    "borosilicate glass": {
        "full_name": "Borosilicate Glass",
        "recycling_code": "♻",
        "score": 99,
        "concerns": ["none"],
        "safe_for": ["everything", "extreme temperatures", "oven safe"],
        "avoid": []
    },

    # === METALS ===
    "stainless steel": {
        "full_name": "Stainless Steel",
        "recycling_code": "♻",
        "score": 95,
        "concerns": ["nickel leaching for sensitive individuals"],
        "safe_for": ["food storage", "cooking", "beverages"],
        "avoid": ["highly acidic foods for extended time"]
    },
    "aluminum": {
        "full_name": "Aluminum",
        "recycling_code": "♻",
        "score": 70,
        "concerns": ["acidic food reaction", "potential alzheimer's link debated"],
        "safe_for": ["dry goods", "beverages in cans"],
        "avoid": ["acidic foods", "scratched surfaces"]
    },
    "cast iron": {
        "full_name": "Cast Iron",
        "recycling_code": "♻",
        "score": 90,
        "concerns": ["iron leaching (usually beneficial)"],
        "safe_for": ["cooking", "high heat"],
        "avoid": ["acidic foods for long periods", "soap"]
    },

    # === COATINGS ===
    "teflon": {
        "full_name": "PTFE (Polytetrafluoroethylene)",
        "recycling_code": "N/A",
        "score": 50,
        "concerns": ["PFOA (legacy)", "toxic fumes when overheated", "microplastics when scratched"],
        "safe_for": ["low-medium heat cooking when intact"],
        "avoid": ["high heat >500°F", "metal utensils", "use when scratched"]
    },
    "ceramic coating": {
        "full_name": "Ceramic Non-Stick Coating",
        "recycling_code": "N/A",
        "score": 80,
        "concerns": ["durability", "may contain nanoparticles"],
        "safe_for": ["low-medium heat cooking"],
        "avoid": ["high heat", "metal utensils"]
    },

    # === SILICONE ===
    "silicone": {
        "full_name": "Food-Grade Silicone",
        "recycling_code": "N/A",
        "score": 85,
        "concerns": ["quality varies", "may contain fillers in cheap versions"],
        "safe_for": ["baking", "food storage", "microwave", "freezer"],
        "avoid": ["direct flame", "cheap unbranded versions"]
    },

    # === WOOD/BAMBOO ===
    "bamboo": {
        "full_name": "Bamboo",
        "recycling_code": "♻",
        "score": 80,
        "concerns": ["melamine binders in some products", "mold if not dried"],
        "safe_for": ["utensils", "cutting boards"],
        "avoid": ["dishwasher", "soaking", "products with melamine"]
    },
    "wood": {
        "full_name": "Natural Wood",
        "recycling_code": "♻",
        "score": 85,
        "concerns": ["mold if not dried", "finishes may contain chemicals"],
        "safe_for": ["utensils", "cutting boards"],
        "avoid": ["dishwasher", "soaking"]
    }
}

# ============================================
# V4 TIER SYSTEM DATABASES
# ============================================

# TIER 1: 🔴 RED (Grade F) - AVOID
# These trigger automatic score caps (cannot score above C/49)
TIER_1_AVOID = {
    # IARC Group 1 Carcinogens
    "processed meat": {"grade": "F", "reason": "IARC Group 1 carcinogen (same category as tobacco)", "hidden_truth": "ractopamine"},
    "sodium nitrite": {"grade": "F", "reason": "Forms carcinogenic nitrosamines, linked to colorectal cancer"},
    "sodium nitrate": {"grade": "F", "reason": "Converts to nitrite, carcinogenic in processed meats"},

    # Banned Globally, Allowed in US
    "ractopamine": {"grade": "F", "reason": "BANNED in 168 countries including EU, China, Russia. Still in 60-80% of US pork.", "hidden_truth": "ractopamine"},
    "potassium bromate": {"grade": "F", "reason": "IARC Group 2B carcinogen. BANNED in EU, Canada, China, Japan, Brazil. Still in US bread.", "hidden_truth": "potassium bromate"},
    "brominated vegetable oil": {"grade": "F", "reason": "BANNED in EU, Japan, India. Builds up in body tissue. FDA finally banned 2024.", "hidden_truth": "brominated_vegetable_oil"},
    "azodicarbonamide": {"grade": "F", "reason": "BANNED in EU, Australia. Breaks down to carcinogenic semicarbazide. Used in US bread.", "hidden_truth": "azodicarbonamide"},
    "red 3": {"grade": "F", "reason": "FDA acknowledged carcinogen in 1990. BANNED in cosmetics. Still allowed in food.", "hidden_truth": "red_3"},

    # Known Endocrine Disruptors
    "bha": {"grade": "F", "reason": "IARC Group 2B carcinogen. BANNED in EU for infant food. Endocrine disruptor.", "hidden_truth": "BHA"},
    "butylated hydroxyanisole": {"grade": "F", "reason": "IARC Group 2B carcinogen. BANNED in EU for infant food.", "hidden_truth": "BHA"},
    "bht": {"grade": "F", "reason": "Potential carcinogen. Banned in UK, Japan, Romania. Linked to behavioral issues in children.", "hidden_truth": "BHT"},
    "butylated hydroxytoluene": {"grade": "F", "reason": "Potential carcinogen. Banned in UK, Japan, Romania.", "hidden_truth": "BHT"},

    # Trans Fats
    "partially hydrogenated": {"grade": "F", "reason": "Artificial trans fat. No safe level. FDA banned 2018 but loopholes remain.", "hidden_truth": "partially_hydrogenated"},
}

# TIER 2: 🟠 ORANGE (Grade D) - LIMIT
TIER_2_LIMIT = {
    # IARC Group 2B
    "aspartame": {"grade": "D", "reason": "IARC classified as 'possibly carcinogenic' July 2023"},
    "red 40": {"grade": "D", "reason": "Requires warning label in EU. Linked to hyperactivity in children."},
    "allura red": {"grade": "D", "reason": "Same as Red 40. Requires warning label in EU."},
    "yellow 5": {"grade": "D", "reason": "Requires warning label in EU. Contains benzidine (carcinogen)."},
    "tartrazine": {"grade": "D", "reason": "Same as Yellow 5. Requires warning label in EU."},
    "yellow 6": {"grade": "D", "reason": "Requires warning label in EU. Linked to adrenal tumors."},
    "sunset yellow": {"grade": "D", "reason": "Same as Yellow 6. Requires warning label in EU."},
    "caramel color": {"grade": "D", "reason": "Class IV caramel contains 4-MEI, linked to cancer in animal studies."},

    # GRAS Exploited
    "titanium dioxide": {"grade": "D", "reason": "BANNED in EU food since 2022. Still allowed in US. DNA damage concerns."},
    "propylparaben": {"grade": "D", "reason": "Endocrine disruptor. BANNED in EU food. Still in US products."},

    # Processing Markers
    "high fructose corn syrup": {"grade": "D", "reason": "Ultra-processed marker. Linked to obesity, diabetes, fatty liver."},
    "hfcs": {"grade": "D", "reason": "Ultra-processed marker. Linked to obesity, diabetes, fatty liver."},
    "maltodextrin": {"grade": "D", "reason": "High glycemic (105-136). Spikes blood sugar faster than table sugar."},
    "dextrose": {"grade": "D", "reason": "Industrial corn sugar. Glycemic index of 100."},

    # Problematic Additives
    "carrageenan": {"grade": "D", "reason": "Inflammatory. May cause gastrointestinal issues. Some countries restrict."},
    "sodium benzoate": {"grade": "D", "reason": "Can form benzene (carcinogen) when combined with vitamin C."},
    "polysorbate 80": {"grade": "D", "reason": "Emulsifier linked to gut microbiome disruption and inflammation."},
    "tbhq": {"grade": "D", "reason": "Petroleum-based preservative. Possible carcinogen. Banned in Japan and some EU countries."},
    "tertiary butylhydroquinone": {"grade": "D", "reason": "Petroleum-based preservative. Vision problems, DNA damage in studies."},
}

# TIER 3: 🟡 YELLOW (Grade C) - CAUTION
TIER_3_CAUTION = {
    "palm oil": {"grade": "C", "reason": "High saturated fat. Major deforestation driver. Often from unethical sources."},
    "soybean oil": {"grade": "C", "reason": "Usually from GMO industrial farms. High omega-6 (inflammatory)."},
    "corn syrup": {"grade": "C", "reason": "Refined sugar from industrial corn. Empty calories."},
    "modified food starch": {"grade": "C", "reason": "Ultra-processed. Often from GMO corn. May contain processing chemicals."},
    "modified starch": {"grade": "C", "reason": "Ultra-processed. Often from GMO corn. May contain processing chemicals."},
    "mono and diglycerides": {"grade": "C", "reason": "May contain trans fats. Loophole in trans fat labeling."},
    "monoglycerides": {"grade": "C", "reason": "May contain trans fats. Loophole in trans fat labeling."},
    "diglycerides": {"grade": "C", "reason": "May contain trans fats. Loophole in trans fat labeling."},
    "soy lecithin": {"grade": "C", "reason": "Usually GMO. Highly processed extraction."},
    "citric acid": {"grade": "C", "reason": "Usually manufactured from GMO corn mold, not citrus."},
    "xanthan gum": {"grade": "C", "reason": "May cause digestive issues in some people."},
    "natural flavors": {"grade": "C", "reason": "Can contain up to 100 different chemicals, undisclosed", "hidden_truth": "natural_flavors"},
    "artificial flavors": {"grade": "C", "reason": "Synthetic chemicals, undisclosed components"},
    "msg": {"grade": "C", "reason": "Flavor enhancer. Headaches in sensitive individuals, allergies."},
    "monosodium glutamate": {"grade": "C", "reason": "Flavor enhancer. Headaches in sensitive individuals, allergies."},
}

# TIER 4: 🟢 GREEN (Grade A/B) - SAFE
TIER_4_SAFE = {
    # Whole Foods
    "whole wheat flour": {"grade": "A", "reason": "Minimally processed whole grain."},
    "whole grain": {"grade": "A", "reason": "Minimally processed, nutrient-rich."},
    "olive oil": {"grade": "A", "reason": "Heart-healthy monounsaturated fats."},
    "butter": {"grade": "B", "reason": "Natural dairy fat. Better than processed alternatives."},
    "sea salt": {"grade": "B", "reason": "Minimally processed. Contains trace minerals."},
    "salt": {"grade": "B", "reason": "Minimal processing."},
    "cane sugar": {"grade": "B", "reason": "Less processed than HFCS. Use in moderation."},
    "water": {"grade": "A", "reason": "Essential, no concerns."},
    "aqua": {"grade": "A", "reason": "Essential, no concerns."},

    # Certified
    "organic": {"grade": "A", "bonus": True, "reason": "No synthetic pesticides. Better farming practices."},
    "non-gmo verified": {"grade": "A", "bonus": True, "reason": "Verified non-GMO."},
    "non-gmo": {"grade": "A", "bonus": True, "reason": "Non-GMO."},
    "fair trade": {"grade": "A", "bonus": True, "reason": "Ethical sourcing verified."},
    "usda organic": {"grade": "A", "bonus": True, "reason": "Certified organic, no synthetic pesticides."},

    # Safe Ingredients
    "glycerin": {"grade": "A", "reason": "Safe, natural humectant."},
    "vegetable glycerin": {"grade": "A", "reason": "Safe, natural humectant."},
    "vitamin e": {"grade": "A", "reason": "Antioxidant, beneficial."},
    "tocopherol": {"grade": "A", "reason": "Vitamin E, antioxidant."},
    "baking soda": {"grade": "A", "reason": "Safe, natural."},
    "sodium bicarbonate": {"grade": "A", "reason": "Safe, natural."},
    "vinegar": {"grade": "A", "reason": "Safe, natural preservative."},
    "acetic acid": {"grade": "B", "reason": "Safe, natural acid."},
}

# ============================================
# V4 CORPORATE PENALTIES DATABASE
# ============================================

CORPORATE_PENALTIES = {
    "Nestlé": {
        "penalty": -15,
        "brands": ["Gerber", "DiGiorno", "Stouffer's", "Hot Pockets", "Lean Cuisine",
                   "Coffee-Mate", "Carnation", "Häagen-Dazs", "Dreyer's", "Nestle"],
        "notable_brands": ["Lean Cuisine", "Hot Pockets", "DiGiorno", "Gerber"],
        "issues": [
            "Baby formula marketing violations (WHO code)",
            "Child labor in cocoa supply chain",
            "Water extraction from drought areas",
            "Microplastics contamination scandals"
        ]
    },
    "PepsiCo": {
        "penalty": -12,
        "brands": ["Quaker", "Frito-Lay", "Tropicana", "Gatorade", "Naked Juice",
                   "Sabra", "Siete Foods", "Poppi", "Pepsi", "Lay's", "Doritos"],
        "notable_brands": ["Naked Juice", "Tropicana", "Doritos", "Pepsi"],
        "issues": [
            "$9M settlement for 'all natural' GMO fraud (Naked Juice)",
            "Lobbying against soda taxes",
            "Plastic pollution (4th worst polluter globally)"
        ]
    },
    "Kraft Heinz": {
        "penalty": -12,
        "brands": ["Oscar Mayer", "Lunchables", "Velveeta", "Philadelphia",
                   "Jell-O", "Kool-Aid", "Maxwell House", "Capri Sun", "Kraft", "Heinz"],
        "notable_brands": ["Lunchables", "Oscar Mayer", "Velveeta", "Kool-Aid"],
        "issues": [
            "Named in SF lawsuit (Dec 2025) for 'tobacco playbook' tactics",
            "Heavy lobbying against food safety regulations",
            "Ultra-processed foods marketed to children"
        ]
    },
    "General Mills": {
        "penalty": -10,
        "brands": ["Annie's", "Cascadian Farm", "Lärabar", "Nature Valley",
                   "Cheerios", "Lucky Charms", "Yoplait", "Häagen-Dazs"],
        "notable_brands": ["Annie's Organic", "Cascadian Farm", "Lucky Charms", "Yoplait"],
        "issues": [
            "Glyphosate residues in Cheerios products",
            "Owns 'healthy' brands while selling sugary cereals",
            "Lobbied against GMO labeling"
        ]
    },
    "Kellogg's": {
        "penalty": -10,
        "brands": ["Kashi", "MorningStar Farms", "Bear Naked", "RXBar",
                   "Pringles", "Cheez-It", "Pop-Tarts", "Eggo", "Kellogg"],
        "notable_brands": ["Kashi", "MorningStar Farms", "Pop-Tarts", "Cheez-It"],
        "issues": [
            "Named in SF lawsuit for ultra-processed foods",
            "Bought 'healthy' brands to capture health-conscious consumers",
            "High sugar products marketed with health claims"
        ]
    },
    "Mars": {
        "penalty": -10,
        "brands": ["M&M's", "Snickers", "Skittles", "Twix", "Uncle Ben's",
                   "Pedigree", "Whiskas", "Mars"],
        "notable_brands": ["M&M's", "Snickers", "Skittles", "Twix"],
        "issues": [
            "Named in SF lawsuit",
            "Child labor in cocoa supply chain",
            "Artificial dyes with EU warning requirements"
        ]
    },
    "Mondelez": {
        "penalty": -10,
        "brands": ["Oreo", "Chips Ahoy", "Ritz", "Triscuit", "Wheat Thins",
                   "Cadbury", "Toblerone", "Philadelphia"],
        "notable_brands": ["Oreo", "Triscuit", "Cadbury", "Philadelphia"],
        "issues": [
            "Named in SF lawsuit",
            "Spun off from Kraft to avoid US regulations",
            "Child labor in cocoa supply chain"
        ]
    },
    "Coca-Cola": {
        "penalty": -12,
        "brands": ["Minute Maid", "Simply", "Honest Tea", "vitaminwater",
                   "Fairlife", "Topo Chico", "Costa Coffee", "Coca-Cola", "Coke"],
        "notable_brands": ["Honest Tea", "vitaminwater", "Coca-Cola", "Minute Maid"],
        "issues": [
            "Named in SF lawsuit",
            "$7M+ annual lobbying",
            "Deceptive marketing of 'vitamin' water (settled lawsuit)",
            "Plastic pollution (world's #1 polluter)"
        ]
    },
    "ConAgra": {
        "penalty": -10,
        "brands": ["Healthy Choice", "Marie Callender's", "Hunt's", "PAM",
                   "Slim Jim", "Chef Boyardee", "Banquet", "ConAgra"],
        "notable_brands": ["Healthy Choice", "Marie Callender's", "Slim Jim", "Chef Boyardee"],
        "issues": [
            "Named in SF lawsuit",
            "Ironic naming of 'Healthy Choice' ultra-processed meals",
            "Lobbied against country of origin labeling"
        ]
    },
    "Unilever": {
        "penalty": -8,
        "brands": ["Ben & Jerry's", "Hellmann's", "Knorr", "Lipton",
                   "Breyers", "Magnum", "Talenti", "Unilever"],
        "notable_brands": ["Ben & Jerry's", "Hellmann's", "Breyers", "Magnum"],
        "issues": [
            "Palm oil sourcing controversies",
            "Owns ethical brands while selling processed foods",
            "Deforestation supply chain links"
        ]
    },
}

# ============================================
# V4 NOVA ULTRA-PROCESSING MARKERS
# ============================================

NOVA_4_MARKERS = [
    "high fructose corn syrup",
    "hfcs",
    "maltodextrin",
    "hydrogenated",
    "partially hydrogenated",
    "isolated protein",
    "modified starch",
    "modified food starch",
    "interesterified",
    "hydrolysed",
    "hydrolyzed",
    "artificial flavor",
    "natural flavor",  # Often masks ultra-processing
    "emulsifier",
    "humectant",
    "flavor enhancer",
    "colors",
    "dyes",
    "artificial color",
    "anti-caking",
    "bulking agent",
    "carbonating",
    "foaming",
    "gelling agent",
    "glazing agent",
    # Industrial processing markers
    "enriched",  # Enriched flour - refined and re-fortified
    "refined",  # Refined oils, flours
    "bleached",  # Bleached flour
    # Preservatives (often indicate ultra-processing)
    "tbhq",
    "bha",
    "bht",
    "sodium benzoate",
    "potassium sorbate",
    "calcium propionate",
    # Artificial colors (FD&C colors)
    "yellow 5",
    "yellow 6",
    "red 40",
    "red 3",
    "blue 1",
    "blue 2",
    "caramel color",
    # Sweeteners
    "corn syrup",
    "invert sugar",
    "glucose syrup",
    "dextrose",
    "maltose",
]

# ============================================
# V4 HIDDEN TRUTHS DATABASE
# ============================================

HIDDEN_TRUTHS = {
    "ractopamine": """
🚨 HIDDEN TRUTH: Ractopamine is a growth drug fed to 60-80% of American pigs to add
lean muscle quickly before slaughter. It's BANNED in 168 countries including the
entire European Union, China, Taiwan, and Russia due to cardiovascular risks.
The US allows it because Elanco (manufacturer) lobbied successfully. When you
buy conventional pork products, you're likely consuming residues of a drug most
of the world considers too dangerous for food animals.
    """,

    "potassium bromate": """
🚨 HIDDEN TRUTH: Potassium bromate makes bread rise higher and look whiter.
It's classified as a Group 2B carcinogen (possibly carcinogenic to humans) by
the World Health Organization. It's BANNED in the EU, UK, Canada, Brazil,
China, and Japan. California requires cancer warnings on products containing it.
The FDA asked bakers to "voluntarily" stop using it in 1991 - but never banned it.
    """,

    "GRAS_unknown": """
⚠️ HIDDEN TRUTH: This ingredient was likely self-certified as "safe" by the
manufacturer through the GRAS loophole. Since 2000, 98.7% of new food chemicals
were approved this way - WITHOUT FDA review. Companies hire their own experts
to rubber-stamp safety. The FDA has no idea what's in most processed foods.
    """,

    "natural_flavors": """
⚠️ HIDDEN TRUTH: "Natural flavors" can contain up to 100 different chemicals.
Companies don't have to disclose what's in them. They may include solvents,
emulsifiers, and preservatives. "Natural" doesn't mean safe - arsenic is natural too.
The only difference from "artificial flavors" is the original source material.
    """,

    "BHA": """
🚨 HIDDEN TRUTH: BHA (Butylated Hydroxyanisole) is classified as a Group 2B carcinogen
by the World Health Organization - meaning "possibly carcinogenic to humans."
It's BANNED in baby food throughout the EU due to endocrine disruption risks.
Studies show it causes tumors in rats. Yet the FDA allows it in cereals, chips,
and processed meats because food industry lobbying convinced them the benefits
outweigh the risks. Japan banned it outright. The UK doesn't want it in baby food.
But in America, it's in your breakfast cereal.
    """,

    "BHT": """
🚨 HIDDEN TRUTH: BHT (Butylated Hydroxytoluene) is banned in Japan, Romania, Sweden,
and Australia due to cancer concerns. Research links it to behavioral problems in
children and liver damage. It's structurally similar to BHA (also banned in many
countries). Food companies use it to prevent fats from going rancid - essentially
prioritizing shelf life over your health. The FDA allows it because proving
definitive harm in humans is nearly impossible when you can't run 20-year
controlled studies on people. So they let it slide.
    """,

    "brominated_vegetable_oil": """
🚨 HIDDEN TRUTH: Brominated Vegetable Oil (BVO) was FINALLY banned by the FDA in
2024 after 50+ years of use in sports drinks and sodas. Why so long? Because
it took decades for enough evidence to pile up showing it accumulates in body
tissue and causes neurological problems. The EU banned it years earlier.
Japan banned it. India banned it. But Pepsi and Coca-Cola lobbied hard to
keep it in the US market. If you bought Gatorade or Mountain Dew before 2024,
you consumed a banned substance.
    """,

    "azodicarbonamide": """
🚨 HIDDEN TRUTH: Azodicarbonamide is BANNED in the EU and Australia. When heated,
it breaks down into semicarbazide - a carcinogen. It's the same chemical used
to make yoga mats and shoe soles. Yet it's legal in US bread because it makes
dough easier to work with. When Subway got called out for using it in 2014,
they quietly removed it. But many bakeries still use it. The World Health
Organization linked it to asthma in factory workers. The FDA's response?
"It's generally recognized as safe." By who? The bread industry.
    """,

    "red_3": """
🚨 HIDDEN TRUTH: The FDA acknowledged Red 3 as a carcinogen in 1990. They BANNED
it in cosmetics and externally applied drugs that same year. But they left it
legal in FOOD because removing it would be "too disruptive" to the food industry.
You read that right - banned on your skin, allowed in your stomach. It causes
thyroid tumors in rats. It's in candy, cake frosting, and maraschino cherries.
The FDA has been "reviewing" it for 30+ years while you eat it. California
finally banned it in 2023. The rest of the US? Still waiting.
    """,

    "partially_hydrogenated": """
🚨 HIDDEN TRUTH: Artificial trans fats (partially hydrogenated oils) have NO SAFE LEVEL
according to the American Heart Association. The FDA technically "banned" them in 2018...
except they didn't. Loopholes allow up to 0.5g per serving to be labeled as "0g trans fat."
Food companies just shrink serving sizes. And "fully hydrogenated" oils (which contain
different harmful fats) are still legal. Trans fats increase bad cholesterol, decrease
good cholesterol, and cause inflammation. The WHO estimates they cause 500,000+ deaths
per year globally. But food industry lobbying ensured the "ban" has more holes than
swiss cheese.
    """,
}

# Ultra-Processing Truth (shown when 5+ NOVA markers detected)
ULTRA_PROCESSED_TRUTH = """
🏭 ULTRA-PROCESSED FOOD ALERT

This product contains {count} ultra-processing markers.

📊 THE SCIENCE: A 2019 NIH study locked 20 people in a metabolic ward
and fed them ultra-processed OR unprocessed diets with IDENTICAL calories,
sugar, fat, and nutrients. Result: Ultra-processed group ate 508 MORE
calories per day and gained 2 pounds in 2 weeks. The unprocessed group
lost 2 pounds.

🧠 WHY IT MATTERS: Ultra-processed foods are engineered to override
your brain's satiety signals. They're designed to be addictive. This
isn't about willpower - it's about food engineering.

📈 HEALTH RISKS LINKED TO ULTRA-PROCESSED FOODS:
• 12-29% increased cancer risk
• 62% increased mortality risk
• 50% increased depression risk
• 15% increased diabetes risk

These effects occur REGARDLESS of individual ingredient toxicity.
"""

# Monoculture Truth (shown when 3+ monoculture ingredients detected)
MONOCULTURE_TRUTH = """
🌾 INDUSTRIAL AGRICULTURE ALERT

This product likely contains ingredients from industrial monoculture farms.

WHY THIS MATTERS:
• Monocultures destroy biodiversity
• Force small farmers to grow single crops
• Concentrate wealth in mega-corporations
• Deplete soil nutrients
• Require massive pesticide use
• Often located near low-income communities (environmental racism)

COMMON MONOCULTURE INGREDIENTS:
• Corn (syrup, starch, oil, dextrose, maltodextrin)
• Soy (lecithin, oil, protein isolate)
• Palm oil (linked to rainforest destruction)

🌱 BETTER CHOICE: Look for products with:
• USDA Organic certification
• Fair Trade certification
• "Single origin" or named farm sources
• B-Corp certified companies
"""

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="Cancer Detector API v3.1 - ADVANCED",
    description="Complete Analysis: Ingredients + Materials + Condition Assessment",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Jinja2 templates for PDF generation
TEMPLATES_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

# ============================================
# STARTUP/SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_db()

# ============================================
# MODELS
# ============================================

class ScanResult(BaseModel):
    product_name: str
    brand: Optional[str] = None
    product_type: str  # "consumable", "container", "cookware", "baby_item", "other"

    # For consumables
    ingredients: Optional[List[str]] = None
    ingredients_source: Optional[str] = None

    # For non-consumables
    materials: Optional[List[Dict[str, Any]]] = None

    # Condition analysis
    condition: Optional[Dict[str, Any]] = None

    # Scores
    safety_score: int  # 0-100
    condition_score: Optional[int] = None
    overall_score: int  # 0-100
    grade: str  # A+, A, B+, B, C+, C, D, F

    # Flagged items
    flagged_ingredients: Optional[List[Dict[str, Any]]] = None
    safe_ingredients: Optional[List[str]] = None

    # Recommendations
    recommendation: str
    care_tips: Optional[List[Dict[str, str]]] = None
    safer_alternative: Optional[Dict[str, Any]] = None

    # Metadata
    confidence: str
    analysis_type: str  # "ingredient", "material", "hybrid"
    personalized_notes: Optional[str] = None

    # Report
    report_id: str
    timestamp: str

class HealthCheck(BaseModel):
    status: str
    version: str
    claude_api: str

# ============================================
# V4 PHASE 3: DEEP RESEARCH MODELS
# ============================================

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DeepResearchRequest(BaseModel):
    product_name: str
    brand: Optional[str] = None
    category: str
    ingredients: List[str]

class DeepResearchJob(BaseModel):
    job_id: str
    status: JobStatus
    progress: int  # 0-100
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

# In-memory job store (use Redis/DB in production)
DEEP_RESEARCH_JOBS: Dict[str, DeepResearchJob] = {}

# ============================================
# DEEP RESEARCH PROMPT
# ============================================

DEEP_RESEARCH_PROMPT_TEMPLATE = """You are TrueCancer's Deep Research Agent. The user has requested a comprehensive investigation of this product:

**Product**: {product_name}
**Brand**: {brand}
**Category**: {category}
**Ingredients**: {ingredients}

Your task is to generate a comprehensive report with SEVEN sections. Be direct, honest, and hedge toward consumer protection. The user deserves to know what companies don't want them to know.

## 1. EXECUTIVE SUMMARY
One concise paragraph: Should this person buy this product? Why or why not? Be direct and honest.

## 2. THE COMPANY BEHIND IT
- Parent company ownership chain (if any)
- Corporate history and major controversies
- Lobbying activities and political spending (if known)
- Recent lawsuits, settlements, or regulatory actions
- Overall corporate ethics assessment

## 3. INGREDIENT DEEP DIVE
For each concerning ingredient identified:
- Full scientific/chemical name
- What it does in this product (functional purpose)
- Key health research findings (cite studies when possible)
- Regulatory status globally (banned where? allowed where?)
- Why it's allowed in the US despite concerns

## 4. SUPPLY CHAIN INVESTIGATION
- Where key ingredients are likely sourced
- Known suppliers and their practices (if information available)
- Labor condition concerns (if documented)
- Environmental impact of production
- Monoculture vs. sustainable farming assessment

## 5. REGULATORY HISTORY
- FDA warning letters (if any)
- Product recalls (if any)
- FTC advertising complaints or enforcement
- State-level regulatory actions
- Note if no significant regulatory issues found

## 6. BETTER ALTERNATIVES
List 3-5 alternative products that:
- Score higher on TrueCancer safety metrics
- Are genuinely healthier (not just marketing)
- Are ethically sourced when possible
- Are reasonably priced and accessible
- Explain WHY each is better

## 7. ACTION ITEMS FOR CONSUMER
What can the consumer do right now?
- Immediate substitutes they can buy today
- Specific brands to support instead
- How to read labels to avoid similar issues
- Resources for learning more about this topic
- One simple action step they can take

IMPORTANT GUIDELINES:
- Be factual and cite sources when making claims
- If information is not available, say so clearly
- Distinguish between documented facts vs. reasonable concerns
- Avoid fear-mongering but don't minimize real risks
- Give actionable advice, not just information
- Remember: Consumer protection over corporate reputation

Generate the complete report now:"""

# ============================================
# CORE FUNCTIONS
# ============================================

def analyze_with_claude(image_base64: str, media_type: str) -> dict:
    """Send image to Claude Vision and get comprehensive analysis"""

    if not client:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    prompt = """Analyze this product/object image comprehensively.

TASK 1 - IDENTIFICATION:
Identify what this is: product name, brand, type, size/variant.

TASK 2 - CLASSIFICATION:
Determine the category:
- "consumable" = food, beverage, cosmetic, cleaning product, medicine (has ingredients)
- "container" = bottle, jar, tupperware, storage container (made of materials)
- "cookware" = pan, pot, utensil, bakeware (has coatings/materials)
- "baby_item" = bottles, toys, pacifiers (extra scrutiny needed)
- "other" = anything else

TASK 3 - INGREDIENTS OR MATERIALS:
- If CONSUMABLE: List all ingredients (from label if visible, or from your knowledge)
- If NON-CONSUMABLE: Identify what materials it's made of (plastic type, metal, glass, coatings)

TASK 4 - CONDITION ASSESSMENT:
Look at the ACTUAL ITEM in the photo:
- Is it new or used?
- Any visible wear, scratches, damage, discoloration?
- Any concerning observations?
- Estimated age/condition?

TASK 5 - RETURN JSON:
Return ONLY valid JSON in this exact format:
{
  "product_name": "Full product name",
  "brand": "Brand name",
  "product_type": "consumable|container|cookware|baby_item|other",

  "ingredients": ["ingredient1", "ingredient2"],
  "ingredients_source": "from_label|from_knowledge",

  "materials": [
    {"component": "main body", "material": "PET plastic", "notes": "recycling code #1"}
  ],

  "condition": {
    "overall": "new|good|fair|worn|damaged",
    "observations": ["visible scratching on surface", "discoloration on base"],
    "estimated_age": "2-3 years",
    "concerns": ["scratches may harbor bacteria", "microplastic shedding risk"]
  },

  "personalized_notes": "Specific observations about THIS particular item in the photo",

  "confidence": "high|medium|low"
}

IMPORTANT:
- Return ONLY the JSON, no other text
- Be thorough with condition assessment - look closely at the actual item
- List ALL ingredients you can identify (for consumables)
- Identify ALL materials and components (for non-consumables)
"""

    try:
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text.strip()

        # Try to parse JSON (handle markdown code blocks if present)
        if response_text.startswith("```"):
            # Remove markdown code blocks
            response_text = re.sub(r'^```json?\n?', '', response_text)
            response_text = re.sub(r'\n?```$', '', response_text)

        return json.loads(response_text)

    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Response was: {response_text}")
        raise HTTPException(status_code=500, detail=f"Failed to parse Claude response: {str(e)}")
    except Exception as e:
        print(f"Claude API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")


def score_ingredients(ingredients: List[str]) -> dict:
    """Score ingredients against toxicity database"""

    flagged = []
    safe = []
    total_score = 0
    max_severity = 0

    for ingredient in ingredients:
        ingredient_lower = ingredient.lower().strip()

        # Check for matches (including partial matches)
        matched = False
        for toxic_name, data in TOXICITY_DATABASE.items():
            if toxic_name in ingredient_lower or ingredient_lower in toxic_name:
                matched = True

                if data["score"] >= 4:  # Flag concerning ingredients
                    flagged.append({
                        "ingredient": ingredient,
                        "matched_as": toxic_name,
                        "hazard_score": data["score"],
                        "category": data["category"],
                        "source": data["source"],
                        "concerns": data["concerns"]
                    })
                    max_severity = max(max_severity, data["score"])
                else:
                    safe.append(ingredient)

                total_score += data["score"]
                break

        if not matched:
            # Unknown ingredient - give it a neutral score
            safe.append(ingredient)
            total_score += 2  # Slight penalty for unknown ingredients

    # Calculate final score (0-100, where 100 is safest)
    if len(ingredients) > 0:
        avg_score = total_score / len(ingredients)
        # Convert to 0-100 scale (inverted, so 100 = safest)
        final_score = max(0, min(100, int(100 - (avg_score * 10))))
    else:
        final_score = 50  # Unknown

    # Penalize for having any high-severity ingredients
    if max_severity >= 8:
        final_score = min(final_score, 30)
    elif max_severity >= 6:
        final_score = min(final_score, 50)

    return {
        "score": final_score,
        "flagged": flagged,
        "safe": safe
    }


def score_materials(materials: List[Dict]) -> Dict[str, Any]:
    """Score materials against MATERIAL_DATABASE"""
    scored_materials = []
    total_score = 0
    concerns = []

    for mat in materials:
        material_name = mat.get("material", "").lower()
        component = mat.get("component", "unknown")

        # Find in database (partial match)
        matched = None
        for key, data in MATERIAL_DATABASE.items():
            if key in material_name or material_name in key:
                matched = data
                break

        if matched:
            scored_materials.append({
                "component": component,
                "material": matched["full_name"],
                "recycling_code": matched["recycling_code"],
                "score": matched["score"],
                "concerns": matched["concerns"],
                "safe_for": matched["safe_for"],
                "avoid": matched["avoid"]
            })
            total_score += matched["score"]
            concerns.extend(matched["concerns"])
        else:
            scored_materials.append({
                "component": component,
                "material": mat.get("material", "Unknown"),
                "score": 50,
                "concerns": ["Unknown material - exercise caution"]
            })
            total_score += 50

    avg_score = total_score / len(materials) if materials else 50

    return {
        "score": int(avg_score),
        "materials": scored_materials,
        "all_concerns": list(set(concerns))
    }


def get_care_tips(product_type: str, materials: List[Dict] = None) -> List[Dict[str, str]]:
    """Generate care tips"""
    tips = []
    if product_type == "container":
        tips = [
            {"icon": "🚫", "tip": "Avoid dishwasher", "desc": "Hand wash with mild soap"},
            {"icon": "❄️", "tip": "No extreme temperatures", "desc": "Don't freeze or use with hot liquids"},
            {"icon": "☀️", "tip": "Store away from sunlight", "desc": "UV can degrade plastic"},
            {"icon": "🧽", "tip": "Use soft sponges only", "desc": "Abrasives cause scratches"},
            {"icon": "🔄", "tip": "Replace when worn", "desc": "Scratched containers shed microplastics"}
        ]
    elif product_type == "cookware":
        tips = [
            {"icon": "🔥", "tip": "Watch the heat", "desc": "Don't overheat non-stick coatings"},
            {"icon": "🥄", "tip": "Use wooden/silicone utensils", "desc": "Metal scratches coatings"},
            {"icon": "🧴", "tip": "Avoid harsh cleaners", "desc": "They can damage surfaces"},
            {"icon": "👀", "tip": "Inspect regularly", "desc": "Replace if coating is damaged"}
        ]
    return tips


def get_safer_alternative(product_type: str, materials: List[Dict] = None) -> Optional[Dict[str, Any]]:
    """Suggest safer alternative"""
    if product_type == "container" and materials:
        if any("plastic" in str(m).lower() for m in materials):
            return {
                "name": "Glass Container",
                "reason": "Glass doesn't leach chemicals, is dishwasher safe, and lasts longer",
                "grade": "A+",
                "score": 98
            }
    elif product_type == "cookware" and materials:
        if any("teflon" in str(m).lower() for m in materials):
            return {
                "name": "Cast Iron or Stainless Steel",
                "reason": "No chemical coatings to degrade, lasts generations",
                "grade": "A",
                "score": 95
            }
    return None


def calculate_grade(score: int) -> str:
    """Convert score to letter grade"""
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "B+"
    elif score >= 75:
        return "B"
    elif score >= 65:
        return "C+"
    elif score >= 55:
        return "C"
    elif score >= 35:
        return "D"
    else:
        return "F"


def generate_recommendation(grade: str, flagged: List, condition: Dict = None) -> str:
    """Generate recommendation"""
    if grade in ["A+", "A"]:
        recommendation = "This product appears to be safe with no significant toxic ingredients detected."
    elif grade in ["B+", "B"]:
        recommendation = "This product is relatively safe but contains some ingredients of mild concern."
    elif grade in ["C+", "C"]:
        recommendation = "This product contains some ingredients of moderate concern. Consider alternatives."
    elif grade == "D":
        recommendation = "This product contains several concerning ingredients. We recommend finding a safer alternative."
    else:
        recommendation = "This product contains highly toxic ingredients. We strongly recommend avoiding this product."

    # Add condition-specific advice
    if condition and condition.get("overall") in ["worn", "damaged"]:
        recommendation += " Additionally, the visible wear on this item increases safety risks."

    return recommendation


# ============================================
# V3 DATABASE ENRICHMENT & SCORING FUNCTIONS
# ============================================

def enrich_ingredients_with_database(ingredients_analysis: List[Dict]) -> List[Dict]:
    """
    Cross-reference Claude's ingredient analysis with V3 database
    Use HIGHER score for safety (more conservative approach)

    Args:
        ingredients_analysis: List of ingredient dicts from Claude

    Returns:
        Enriched list with database scores where applicable
    """
    enriched = []

    for ingredient in ingredients_analysis:
        # Validate required fields exist
        if 'name' not in ingredient or 'hazard_score' not in ingredient:
            continue  # Skip malformed ingredients

        ingredient_copy = ingredient.copy()
        ingredient_name = ingredient['name'].lower().strip()

        # Check database
        db_entry = TOXICITY_DATABASE.get(ingredient_name)

        if db_entry:
            claude_score = ingredient['hazard_score']
            db_score = db_entry['score']

            # Use HIGHER score (more conservative)
            if db_score > claude_score:
                ingredient_copy['hazard_score'] = db_score
                ingredient_copy['category'] = db_entry['category']
                ingredient_copy['concerns'] = db_entry.get('concerns', [])
                ingredient_copy['source'] = 'database'
            else:
                ingredient_copy['source'] = 'claude'
        else:
            # Novel ingredient not in database
            ingredient_copy['source'] = 'claude'

        enriched.append(ingredient_copy)

    return enriched


def calculate_ingredient_scores(ingredients_analysis: List[Dict]) -> Dict[str, Any]:
    """
    Calculate base safety score from ingredients with penalty system

    Formula:
    1. average_hazard = sum(scores) / count
    2. base_score = 100 - (average_hazard * 10)
    3. penalties = (count of scores >= 7) * 5 + (count of 4-6) * 2
    4. safety_score = base_score - penalties

    Args:
        ingredients_analysis: List of ingredient dicts with hazard_score

    Returns:
        Dict with average_hazard_score, base_score, penalty, safety_score
    """
    if not ingredients_analysis:
        return {
            'average_hazard_score': 0.0,
            'base_score': 100,
            'penalty': 0,
            'safety_score': 100
        }

    # Calculate average hazard
    total_hazard = sum(ing['hazard_score'] for ing in ingredients_analysis)
    count = len(ingredients_analysis)
    avg_hazard = total_hazard / count

    # Base score
    base_score = 100 - (avg_hazard * 10)

    # Calculate penalties
    high_concern_count = sum(1 for ing in ingredients_analysis if ing['hazard_score'] >= 7)
    moderate_count = sum(1 for ing in ingredients_analysis if 4 <= ing['hazard_score'] < 7)

    penalty = (high_concern_count * 5) + (moderate_count * 2)

    # Final safety score (before bonuses and condition)
    safety_score = max(0, base_score - penalty)

    return {
        'average_hazard_score': round(avg_hazard, 2),
        'base_score': int(base_score),
        'penalty': penalty,
        'safety_score': int(safety_score)
    }


def apply_positive_bonuses(score: int, positive_attributes: List[Dict]) -> int:
    """
    Apply positive bonuses from "X-free" claims
    +3 per claim, max +15 total

    Args:
        score: Current safety score
        positive_attributes: List of positive claim dicts

    Returns:
        Adjusted score with bonuses (capped at max)
    """
    if not positive_attributes:
        return score

    total_bonus = sum(attr.get('bonus_points', 3) for attr in positive_attributes)

    # Cap at +15
    total_bonus = min(total_bonus, 15)

    adjusted = score + total_bonus

    # Ensure within 0-100 range
    return max(0, min(100, adjusted))


def apply_condition_modifier(score: int, condition: Dict, product_type: str) -> int:
    """
    Apply condition modifier based on product type
    - Food/Water/Cosmetics/Cleaning/Supplements: 5% weight
    - Cookware: 15% weight (condition matters more)

    Args:
        score: Current score after ingredients and bonuses
        condition: Condition dict with score (0-100)
        product_type: Product category

    Returns:
        Final score with condition modifier
    """
    condition_score = condition.get('score', 100)

    # Determine weight based on product type
    if product_type.lower() == 'cookware':
        weight = 0.15
    else:
        weight = 0.05

    # Apply modifier
    modifier = int(condition_score * weight)
    adjusted = score + modifier

    # Clamp to 0-100
    return max(0, min(100, adjusted))


# ============================================
# V4 SCORING FUNCTIONS
# ============================================

def calculate_v4_score(product_data: dict) -> dict:
    """
    TrueCancer V4 Scoring Algorithm

    4-Dimension Scoring:
    - Ingredient Safety: 40% weight
    - Processing Level: 25% weight
    - Corporate Ethics: 20% weight
    - Supply Chain: 15% weight

    Args:
        product_data: Dict with 'ingredients', 'brand', etc.

    Returns:
        {
            "overall_score": 0-100,
            "overall_grade": "A+" to "F",
            "dimension_scores": {...},
            "ingredients_graded": [...],
            "alerts": [],
            "hidden_truths": []
        }
    """

    base_score = 75  # Start neutral
    ingredients = product_data.get("ingredients", [])
    brand = product_data.get("brand", "").lower()

    # ========== 1. INGREDIENT SAFETY (40% weight) ==========
    ingredient_scores = []
    ingredients_graded = []
    alerts = []
    hidden_truths = []

    for ingredient in ingredients:
        ing_lower = ingredient.lower()
        ingredient_data = None
        grade = "C"  # Default unknown
        score = 60
        reason = "Unknown - not in safety database. May have bypassed FDA review via GRAS loophole."
        color = "#facc15"  # Yellow
        hidden_truth_key = "GRAS_unknown"

        # Check Tier 1 (F grade, red)
        for key, data in TIER_1_AVOID.items():
            if key in ing_lower:
                grade = "F"
                score = 0
                reason = data["reason"]
                color = "#ef4444"
                hidden_truth_key = data.get("hidden_truth")
                alerts.append(f"🔴 AVOID: {ingredient}")
                ingredient_data = data
                break

        # Check Tier 2 (D grade, orange) if not already matched
        if not ingredient_data:
            for key, data in TIER_2_LIMIT.items():
                if key in ing_lower:
                    grade = "D"
                    score = 35
                    reason = data["reason"]
                    color = "#f97316"
                    alerts.append(f"🟠 LIMIT: {ingredient}")
                    ingredient_data = data
                    hidden_truth_key = None
                    break

        # Check Tier 3 (C grade, yellow) if not already matched
        if not ingredient_data:
            for key, data in TIER_3_CAUTION.items():
                if key in ing_lower:
                    grade = "C"
                    score = 55
                    reason = data["reason"]
                    color = "#facc15"
                    hidden_truth_key = data.get("hidden_truth")
                    ingredient_data = data
                    break

        # Check Tier 4 (A/B grade, green) if not already matched
        if not ingredient_data:
            for key, data in TIER_4_SAFE.items():
                if key in ing_lower:
                    grade = data["grade"]
                    score = 95 if grade == "A" else 80
                    reason = data["reason"]
                    color = "#22c55e" if grade == "A" else "#4ade80"
                    ingredient_data = data
                    hidden_truth_key = None
                    break

        # Add hidden truth if applicable
        if hidden_truth_key and hidden_truth_key in HIDDEN_TRUTHS:
            if HIDDEN_TRUTHS[hidden_truth_key] not in hidden_truths:
                hidden_truths.append(HIDDEN_TRUTHS[hidden_truth_key])

        ingredient_scores.append(score)
        ingredients_graded.append({
            "name": ingredient,
            "grade": grade,
            "color": color,
            "reason": reason,
            "hazard_score": score,  # ✅ Add hazard score for Flutter
            "hidden_truth": HIDDEN_TRUTHS.get(hidden_truth_key) if hidden_truth_key else None  # ✅ Add hidden truth
        })

    # Sort ingredients worst-first (F → D → C → B → A)
    grade_order = {"F": 0, "D": 1, "C": 2, "B": 3, "A": 4}
    ingredients_graded.sort(key=lambda x: grade_order.get(x["grade"], 2))

    # Calculate ingredient safety score
    if ingredient_scores:
        ingredient_safety_score = sum(ingredient_scores) / len(ingredient_scores)
    else:
        ingredient_safety_score = 50

    # ========== 2. PROCESSING LEVEL (25% weight) ==========
    nova_markers_found = 0
    for ing in ingredients:
        ing_lower = ing.lower()
        for marker in NOVA_4_MARKERS:
            if marker in ing_lower:
                nova_markers_found += 1
                break  # Count each ingredient once

    if nova_markers_found >= 5:
        processing_score = 20  # Ultra-processed
        hidden_truths.append(ULTRA_PROCESSED_TRUTH.format(count=nova_markers_found))
        alerts.append(f"🏭 ULTRA-PROCESSED: {nova_markers_found} processing markers detected")
    elif nova_markers_found >= 3:
        processing_score = 40
        alerts.append(f"⚠️ HIGHLY PROCESSED: {nova_markers_found} processing markers")
    elif nova_markers_found >= 1:
        processing_score = 60
    else:
        processing_score = 90  # Minimally processed

    # ========== 3. CORPORATE ETHICS (20% weight) ==========
    corporate_score = 70  # Default
    parent_company = None
    corporate_disclosure = None

    for parent, data in CORPORATE_PENALTIES.items():
        # Check if brand matches any of the parent company's brands
        if any(b.lower() in brand for b in data["brands"]):
            corporate_score = 70 + data["penalty"]  # Apply penalty
            parent_company = parent
            alerts.append(f"📍 OWNED BY: {parent}")

            # Build corporate disclosure object
            corporate_disclosure = {
                "parent_company": parent,
                "issues": data["issues"],
                "notable_brands": data.get("notable_brands", []),
                "penalty_applied": data["penalty"]
            }

            # Add corporate truth with notable brands
            issues_text = "\n".join(f"• {issue}" for issue in data["issues"])
            notable_brands_text = ", ".join(data.get("notable_brands", [])[:4])
            corporate_truth = f"""
📍 CORPORATE OWNERSHIP ALERT

{product_data.get('brand', 'This product')} is owned by {parent}.

⚠️ PARENT COMPANY ISSUES:
{issues_text}

💡 DID YOU KNOW?
{parent} also makes: {notable_brands_text}
The same company selling you this product also profits from ultra-processed foods.
This is the "healthy brand + junk food" business model.
            """
            hidden_truths.append(corporate_truth)
            break

    # Ensure score stays in 0-100 range
    corporate_score = max(0, min(100, corporate_score))

    # ========== 4. SUPPLY CHAIN (15% weight) ==========
    supply_chain_score = 50  # Default unknown

    # Check for positive certifications
    product_str = str(product_data).lower()
    for cert in ["organic", "fair trade", "non-gmo", "rainforest alliance", "b-corp", "usda organic"]:
        if cert in product_str:
            supply_chain_score += 10

    # Check for monoculture ingredients
    monoculture_keywords = ["corn", "soy", "palm", "canola"]
    monoculture_count = 0
    for ing in ingredients:
        ing_lower = ing.lower()
        for keyword in monoculture_keywords:
            if keyword in ing_lower:
                monoculture_count += 1
                break  # Count each ingredient once

    if monoculture_count >= 3:
        supply_chain_score -= 15
        hidden_truths.append(MONOCULTURE_TRUTH)
        alerts.append(f"🌾 MONOCULTURE ALERT: {monoculture_count} industrial ingredients")

    supply_chain_score = max(0, min(100, supply_chain_score))

    # ========== CALCULATE OVERALL SCORE ==========
    overall_score = (
        ingredient_safety_score * 0.40 +
        processing_score * 0.25 +
        corporate_score * 0.20 +
        supply_chain_score * 0.15
    )

    # Apply score caps based on worst ingredient tier
    # F-grade ingredients → cap at 29 (cannot be better than F)
    # D-grade ingredients → cap at 49 (cannot be better than D)
    # C-grade ingredients → cap at 69 (cannot be better than C)
    has_f_grade = any(ing["grade"] == "F" for ing in ingredients_graded)
    has_d_grade = any(ing["grade"] == "D" for ing in ingredients_graded)
    has_c_grade = any(ing["grade"] == "C" for ing in ingredients_graded)

    if has_f_grade:
        overall_score = min(overall_score, 29)  # Cannot be better than F
        if "⚖️ SCORE CAPPED" not in str(alerts):
            alerts.append("⚖️ SCORE CAPPED: Product cannot score above F due to F-grade ingredients")
    elif has_d_grade:
        overall_score = min(overall_score, 49)  # Cannot be better than D
        if "⚖️ SCORE CAPPED" not in str(alerts):
            alerts.append("⚖️ SCORE CAPPED: Product cannot score above D due to D-grade ingredients")
    elif has_c_grade:
        overall_score = min(overall_score, 69)  # Cannot be better than C
        if "⚖️ SCORE CAPPED" not in str(alerts):
            alerts.append("⚖️ SCORE CAPPED: Product cannot score above C due to C-grade ingredients")

    overall_score = max(0, min(100, round(overall_score)))

    # ========== DETERMINE GRADE ==========
    if overall_score >= 95:
        grade = "A+"
    elif overall_score >= 85:
        grade = "A"
    elif overall_score >= 70:
        grade = "B"
    elif overall_score >= 50:
        grade = "C"
    elif overall_score >= 30:
        grade = "D"
    else:
        grade = "F"

    return {
        "overall_score": overall_score,
        "overall_grade": grade,
        "dimension_scores": {
            "ingredient_safety": round(ingredient_safety_score),
            "processing_level": round(processing_score),
            "corporate_ethics": round(corporate_score),
            "supply_chain": round(supply_chain_score)
        },
        "ingredients_graded": ingredients_graded,
        "alerts": alerts,
        "hidden_truths": hidden_truths,
        "parent_company": parent_company,
        "corporate_disclosure": corporate_disclosure
    }


# ============================================
# V4 PHASE 3: JOB HELPER FUNCTIONS (In-Memory)
# ============================================

def save_job(job_id: str, job_data: dict):
    """Save job to in-memory store"""
    DEEP_RESEARCH_JOBS[job_id] = DeepResearchJob(**job_data)

def get_job(job_id: str) -> dict | None:
    """Retrieve job from in-memory store"""
    job = DEEP_RESEARCH_JOBS.get(job_id)
    return job.dict() if job else None

def update_job_progress(job_id: str, progress: int, current_step: str):
    """Update job progress"""
    job_data = get_job(job_id)
    if job_data:
        job_data["progress"] = progress
        job_data["current_step"] = current_step
        save_job(job_id, job_data)

def complete_job(job_id: str, result: dict):
    """Mark job as completed with full report"""
    job_data = get_job(job_id)
    if job_data:
        job_data["status"] = JobStatus.COMPLETED.value
        job_data["progress"] = 100
        job_data["current_step"] = "Complete"
        job_data["result"] = result
        job_data["completed_at"] = datetime.utcnow().isoformat()
        save_job(job_id, job_data)

def fail_job(job_id: str, error: str):
    """Mark job as failed with error message"""
    job_data = get_job(job_id)
    if job_data:
        job_data["status"] = JobStatus.FAILED.value
        job_data["error"] = error
        job_data["completed_at"] = datetime.utcnow().isoformat()
        save_job(job_id, job_data)

# ============================================
# V4 PHASE 3: DEEP RESEARCH BACKGROUND TASK
# ============================================

async def process_deep_research(job_id: str, request_data: DeepResearchRequest, cache_key: str = None):
    """
    Background task that processes deep research requests.
    Updates job status and progress in Redis (with in-memory fallback).
    Saves result to Postgres cache for persistent storage.
    """
    try:
        # Step 1: Mark as processing
        update_job_progress(job_id, 10, "Preparing comprehensive analysis...")
        await asyncio.sleep(1)  # Simulate processing

        # Step 2: Format ingredients list
        update_job_progress(job_id, 20, "Analyzing ingredients database...")
        ingredients_str = ", ".join(request_data.ingredients)
        await asyncio.sleep(1)

        # Step 3: Build research prompt
        update_job_progress(job_id, 30, "Researching corporate ownership...")
        research_prompt = DEEP_RESEARCH_PROMPT_TEMPLATE.format(
            product_name=request_data.product_name,
            brand=request_data.brand or "Unknown",
            category=request_data.category,
            ingredients=ingredients_str
        )
        await asyncio.sleep(1)

        # Step 4: Call Claude API
        update_job_progress(job_id, 50, "Investigating supply chain...")

        if not client:
            raise Exception("Anthropic API key not configured")

        await asyncio.sleep(2)  # Simulate API call delay

        update_job_progress(job_id, 70, "Checking regulatory history...")

        # Call Claude for deep research
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=8000,  # Comprehensive report needs more tokens
            temperature=0.3,  # Lower temp for factual research
            messages=[{
                "role": "user",
                "content": research_prompt
            }]
        )

        await asyncio.sleep(1)

        # Step 5: Parse response
        update_job_progress(job_id, 85, "Finding better alternatives...")

        report_text = response.content[0].text

        await asyncio.sleep(1)

        # Step 6: Format report
        update_job_progress(job_id, 95, "Generating recommendations...")

        # Parse sections (simple parsing - can be enhanced)
        sections = {}
        current_section = None
        current_content = []

        for line in report_text.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        # Step 7: Complete job
        result = {
            "product_name": request_data.product_name,
            "brand": request_data.brand,
            "category": request_data.category,
            "report": sections,
            "full_report": report_text,
            "generated_at": datetime.utcnow().isoformat()
        }
        complete_job(job_id, result)

        # Step 8: Save to persistent cache for future instant retrieval
        if cache_key:
            await save_deep_research_to_cache(
                cache_key=cache_key,
                product_name=request_data.product_name,
                brand=request_data.brand or "Unknown",
                category=request_data.category,
                report=sections,
                full_report=report_text
            )
            logger.info(f"[DEEP RESEARCH] Saved to persistent cache: {cache_key}")

    except Exception as e:
        # Mark job as failed
        print(f"Deep research error for {job_id}: {e}")
        fail_job(job_id, str(e))


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.2.0",
        "claude_api": "connected" if client else "not configured"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.2.0",
        "v3_ready": True,
        "claude_api": "connected" if client else "not configured",
        "modular_prompts": True,
        "categories": ["food", "water", "cosmetics", "cookware", "cleaning", "supplements"]
    }


@app.post("/api/v1/scan", response_model=ScanResult)
async def scan_product(image: UploadFile = File(...)):
    """
    Scan a product image and get complete analysis.

    Supports:
    - Consumables (food, cosmetics, cleaning) → Ingredient analysis
    - Non-consumables (containers, cookware) → Material analysis
    - Condition assessment from visual inspection

    Returns comprehensive safety report with recommendations.
    """

    # Validate file type (more lenient for iOS compatibility)
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]

    # Log the content type for debugging
    print(f"Received image with content_type: {image.content_type}")

    if image.content_type and image.content_type.lower() not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type '{image.content_type}'. Allowed: {allowed_types}"
        )

    # Read and encode image
    image_data = await image.read()
    base64_image = base64.standard_b64encode(image_data).decode("utf-8")

    # Analyze with Claude Vision
    analysis = analyze_with_claude(base64_image, image.content_type)

    # Determine analysis type
    product_type = analysis.get("product_type", "unknown")

    if product_type == "consumable":
        # Score ingredients
        ingredients = analysis.get("ingredients", [])
        scoring = score_ingredients(ingredients)
        safety_score = scoring["score"]
        flagged_ingredients = scoring["flagged"]
        safe_ingredients = scoring["safe"]
        materials = None
        analysis_type = "ingredient"
    else:
        # Score materials
        materials_list = analysis.get("materials", [])
        scoring = score_materials(materials_list)
        safety_score = scoring["score"]
        flagged_ingredients = []
        safe_ingredients = []
        materials = scoring["materials"]
        analysis_type = "material"

    # Condition scoring
    condition = analysis.get("condition")
    condition_score = None
    if condition:
        condition_map = {
            "new": 100,
            "good": 85,
            "fair": 65,
            "worn": 45,
            "damaged": 20
        }
        condition_score = condition_map.get(condition.get("overall", "good"), 70)

    # Overall score (weighted: 70% safety, 30% condition)
    if condition_score is not None:
        overall_score = int(safety_score * 0.7 + condition_score * 0.3)
    else:
        overall_score = safety_score

    # Calculate grade
    grade = calculate_grade(overall_score)

    # Generate recommendation
    recommendation = generate_recommendation(grade, flagged_ingredients, condition)

    # Get care tips and alternatives
    care_tips = get_care_tips(product_type, materials)
    safer_alternative = get_safer_alternative(product_type, materials)

    # Generate unique report ID
    report_id = f"TC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex().upper()}"

    return ScanResult(
        product_name=analysis.get("product_name", "Unknown Product"),
        brand=analysis.get("brand"),
        product_type=product_type,
        ingredients=analysis.get("ingredients") if product_type == "consumable" else None,
        ingredients_source=analysis.get("ingredients_source"),
        materials=materials,
        condition=condition,
        safety_score=safety_score,
        condition_score=condition_score,
        overall_score=overall_score,
        grade=grade,
        flagged_ingredients=flagged_ingredients if flagged_ingredients else None,
        safe_ingredients=safe_ingredients if safe_ingredients else None,
        recommendation=recommendation,
        care_tips=care_tips if care_tips else None,
        safer_alternative=safer_alternative,
        confidence=analysis.get("confidence", "medium"),
        analysis_type=analysis_type,
        personalized_notes=analysis.get("personalized_notes"),
        report_id=report_id,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/scan/base64")
async def scan_product_base64(data: dict):
    """
    Alternative endpoint accepting base64 image directly.

    Body: {"image": "base64_string", "media_type": "image/jpeg"}
    """

    image_base64 = data.get("image")
    media_type = data.get("media_type", "image/jpeg")

    if not image_base64:
        raise HTTPException(status_code=400, detail="Missing 'image' field")

    # Remove data URL prefix if present
    if "base64," in image_base64:
        image_base64 = image_base64.split("base64,")[1]

    # Analyze with Claude Vision
    analysis = analyze_with_claude(image_base64, media_type)

    # Determine analysis type
    product_type = analysis.get("product_type", "unknown")

    if product_type == "consumable":
        # Score ingredients
        ingredients = analysis.get("ingredients", [])
        scoring = score_ingredients(ingredients)
        safety_score = scoring["score"]
        flagged_ingredients = scoring["flagged"]
        safe_ingredients = scoring["safe"]
        materials = None
        analysis_type = "ingredient"
    else:
        # Score materials
        materials_list = analysis.get("materials", [])
        scoring = score_materials(materials_list)
        safety_score = scoring["score"]
        flagged_ingredients = []
        safe_ingredients = []
        materials = scoring["materials"]
        analysis_type = "material"

    # Condition scoring
    condition = analysis.get("condition")
    condition_score = None
    if condition:
        condition_map = {
            "new": 100,
            "good": 85,
            "fair": 65,
            "worn": 45,
            "damaged": 20
        }
        condition_score = condition_map.get(condition.get("overall", "good"), 70)

    # Overall score (weighted: 70% safety, 30% condition)
    if condition_score is not None:
        overall_score = int(safety_score * 0.7 + condition_score * 0.3)
    else:
        overall_score = safety_score

    # Calculate grade
    grade = calculate_grade(overall_score)

    # Generate recommendation
    recommendation = generate_recommendation(grade, flagged_ingredients, condition)

    # Get care tips and alternatives
    care_tips = get_care_tips(product_type, materials)
    safer_alternative = get_safer_alternative(product_type, materials)

    # Generate unique report ID
    report_id = f"TC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex().upper()}"

    return {
        "product_name": analysis.get("product_name", "Unknown Product"),
        "brand": analysis.get("brand"),
        "product_type": product_type,
        "ingredients": analysis.get("ingredients") if product_type == "consumable" else None,
        "ingredients_source": analysis.get("ingredients_source"),
        "materials": materials,
        "condition": condition,
        "safety_score": safety_score,
        "condition_score": condition_score,
        "overall_score": overall_score,
        "grade": grade,
        "flagged_ingredients": flagged_ingredients if flagged_ingredients else None,
        "safe_ingredients": safe_ingredients if safe_ingredients else None,
        "recommendation": recommendation,
        "care_tips": care_tips if care_tips else None,
        "safer_alternative": safer_alternative,
        "confidence": analysis.get("confidence", "medium"),
        "analysis_type": analysis_type,
        "personalized_notes": analysis.get("personalized_notes"),
        "report_id": report_id,
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# V4 RESEARCH FUNCTIONS (NEW ARCHITECTURE)
# ============================================

async def research_product(product_name: str, brand: str, category: str, visible_ingredients: list) -> dict:
    """
    V4 NEW ARCHITECTURE: Claude researches the product using its knowledge base.
    This is the BRAIN of V4 - Claude synthesizes real safety data.

    Args:
        product_name: Product name from vision
        brand: Brand name from vision
        category: Product category
        visible_ingredients: Any ingredients read from label (may be empty)

    Returns:
        Complete V4 analysis with grades, scores, hidden truths, corporate info
    """

    research_prompt = f"""You are TrueCancer's product safety researcher. Research this product thoroughly using your knowledge base.

PRODUCT: {product_name}
BRAND: {brand}
CATEGORY: {category}
VISIBLE INGREDIENTS (from label): {visible_ingredients if visible_ingredients else "None visible - research THIS SPECIFIC PRODUCT's known ingredients"}

YOUR TASK:
1. **IDENTIFY INGREDIENTS FOR THIS EXACT PRODUCT** (not category assumptions):
   - Research ingredients for THIS SPECIFIC product/brand combination
   - ✅ RIGHT: "Cheez-It Original contains TBHQ" (you know this specific product)
   - ❌ WRONG: "Crackers typically contain preservatives" (category assumption)
   - EXAMPLE: Cathedral City Cheddar has NO annatto - don't assume because "most cheddar" does
   - If visible_ingredients provided, verify and supplement with your knowledge of THIS product
   - You have vast knowledge - if you identify "Coca-Cola Classic", you KNOW its real ingredients

   **ANTI-HALLUCINATION RULE**: Research the SPECIFIC PRODUCT, never fall back to "products like this usually contain..."

   **IF YOU CANNOT VERIFY INGREDIENTS** after thorough research of this exact product:
   - Set report_completeness below 80 to indicate partial data
   - Add to alerts: "📋 INCOMPLETE: Could not verify full ingredient list - consider Deep Research"
   - You may request: "Please scan the ingredient label for complete analysis"

2. **GRADE EACH INGREDIENT** using this exact system:
   - **F (Red)**: IARC Group 1 carcinogens, banned in EU, known endocrine disruptors (formaldehyde, BHA, parabens)
   - **D (Orange)**: IARC 2B possible carcinogens, requires EU warnings, GRAS-exploited (TBHQ, artificial colors, sodium nitrite)
   - **C (Yellow)**: Processed ingredients, GMO-derived, environmental concerns (HFCS, palm oil, "natural flavors")
   - **B (Green)**: Minimally processed, minor concerns (canola oil, sugar, cornstarch)
   - **A (Green)**: Whole foods, certified organic, no concerns (water, organic wheat, sea salt)

3. **RESEARCH PARENT COMPANY**:
   - Who owns this brand? (e.g., Kellogg's owns Cheez-Its, Clorox Company owns Clorox)
   - Any EPA fines, lawsuits, settlements, controversies?
   - Part of Big 10 conglomerates? (Nestlé, PepsiCo, Kraft Heinz, General Mills, Kellogg's, Mars, Mondelez, Coca-Cola, ConAgra, Unilever)

4. **GENERATE HIDDEN TRUTHS** - what consumers should know that's NOT on the label:
   - Specific dollar amounts of fines/settlements
   - Which countries have banned ingredients
   - GRAS loopholes exploited
   - Corporate ownership connections
   - Environmental impacts
   - **FOR CLEAN PRODUCTS**: Also generate POSITIVE truths celebrating good choices:
     - "💚 CLEAN CHOICE: [Brand] uses only [X] simple ingredients"
     - "🏅 GOOD RECORD: No FDA warnings, recalls, or major lawsuits on record"
     - "🌱 SUSTAINABLE: [Positive environmental/ethical practice]"

5. **DETERMINE EXPOSURE TYPE** (EU SCCS retention factor context):
   Based on the product category, classify exposure type:
   - **"leave_on"**: Lotions, moisturizers, deodorants, sunscreens, makeup, serums - 100% body retention
   - **"rinse_off"**: Shampoos, conditioners, body wash, face wash, hand soap - ~1% retention (rinsed away)
   - **"oral_rinse"**: Toothpaste, mouthwash - ~0.1% retention (spit out)
   - **"ingested"**: Food, beverages, supplements, vitamins - 100% internal exposure
   - **"spray_inhalation"**: Hairspray, aerosol sprays, air fresheners - inhalation + skin contact
   - **"household"**: Cleaning products, laundry detergent - minimal direct body contact

6. **CALCULATE DIMENSION SCORES** (0-100):
   - **ingredient_safety**: Average of all ingredient scores (F=0, D=35, C=55, B=80, A=95)
   - **processing_level**: 90 if whole foods, 60 if processed, 30 if ultra-processed
   - **corporate_ethics**: 70 baseline, subtract 10-30 for each major controversy/fine
   - **supply_chain**: 50 default, +10 for organic/fair trade, -10 for monoculture crops

7. **CALCULATE OVERALL SCORE**:
   - Formula: (ingredient_safety × 0.40) + (processing_level × 0.25) + (corporate_ethics × 0.20) + (supply_chain × 0.15)
   - CRITICAL: If ANY F-grade ingredient exists, cap overall_score at 49 max
   - If ANY D-grade ingredient exists and no F, cap at 69 max

8. **DETERMINE OVERALL GRADE**:
   - A+ (95-100), A (85-94), B (70-84), C (50-69), D (30-49), F (0-29)

RETURN THIS EXACT JSON (no markdown, no extra text):
{{
  "product_name": "{product_name}",
  "brand": "{brand}",
  "category": "{category}",
  "overall_score": <number 0-100>,
  "overall_grade": "<letter grade>",
  "dimension_scores": {{
    "ingredient_safety": <0-100>,
    "processing_level": <0-100>,
    "corporate_ethics": <0-100>,
    "supply_chain": <0-100>
  }},
  "ingredients_graded": [
    {{
      "name": "<ingredient name>",
      "grade": "<F/D/C/B/A>",
      "hazard_score": <0-100 where F=0-29, D=30-49, C=50-69, B=70-84, A=85-100>,
      "description": "<why this grade - max 150 chars>",
      "tier": <1 for F, 2 for D, 3 for C, 4 for B/A>
    }}
  ],
  "alerts": [
    "🔴 AVOID: <F-grade ingredient>",
    "🟠 LIMIT: <D-grade ingredient>",
    "🏭 ULTRA-PROCESSED: <count> processing markers",
    "📍 OWNED BY: <parent company>",
    "🟢 CLEAN FORMULA: All verified ingredients grade B or higher",
    "🟡 NEEDS IMPROVEMENT: Consider [substitute] for cleaner option",
    "📋 INCOMPLETE: <if report_completeness below 80>"
  ],
  "hidden_truths": [
    "💊 HIDDEN TRUTH: <specific fact with numbers/dates/countries>",
    "📍 CORPORATE OWNERSHIP: <parent company details>",
    "⚖️ LEGAL ISSUES: <specific fines/lawsuits with dollar amounts>",
    "💚 CLEAN CHOICE: <positive fact for clean products>",
    "🏅 GOOD RECORD: <positive corporate fact if applicable>"
  ],
  "corporate_disclosure": {{
    "parent_company": "<name or null>",
    "penalty_applied": <number like -10, -20, -30>,
    "issues": "<specific controversies, lawsuits, EPA fines with dates and amounts OR 'No major controversies found'>"
  }},
  "suggested_substitute": {{
    "should_suggest": <true if overall_grade is C/D/F, false for A/B>,
    "product_name": "<specific 95%+ match B/A grade alternative, or null if A/B grade>",
    "brand": "<brand of substitute, or null>",
    "why_better": "<one sentence reason, or null>",
    "expected_grade": "<B or A, or null>"
  }},
  "exposure_context": {{
    "exposure_type": "<leave_on|rinse_off|oral_rinse|ingested|spray_inhalation|household>",
    "retention_note": "<1-2 sentence explanation of how much actually enters body based on product type>"
  }},
  "report_completeness": <0-100 percentage of how complete this report is>,
  "needs_deeper_research": <true if report_completeness below 80, false otherwise>,
  "deeper_research_reason": "<explanation if incomplete, or null if complete>"
}}

CRITICAL RULES:
- Sort ingredients_graded by hazard_score DESCENDING (worst first)
- Be specific in hidden_truths (include dates, dollar amounts, country names)
- If you don't know an ingredient's safety, grade it C with "Insufficient safety data"
- ALWAYS return valid JSON with all required fields
- Do NOT invent ingredients based on category assumptions - only include what you KNOW is in THIS EXACT product
- For cleaning products, include both active AND inactive ingredients you know about
- For C/D/F grades, ALWAYS suggest a 95%+ match substitute that grades B or A (same category, same use case)
- For A/B grades, generate POSITIVE alerts and hidden_truths celebrating the clean choice
- report_completeness should be 80+ for acceptable report; below 80 triggers needs_deeper_research
- This scan becomes the CANONICAL database entry - accuracy is critical for all future users who scan this product
"""

    try:
        # Call Claude API for research
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": research_prompt
            }]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Remove markdown if present
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        # Find JSON object
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)

            # Normalize arrays (fix Claude returning strings instead of arrays)
            if isinstance(result.get('alerts'), str):
                result['alerts'] = [result['alerts']] if result['alerts'] else []
            if isinstance(result.get('hidden_truths'), str):
                result['hidden_truths'] = [result['hidden_truths']] if result['hidden_truths'] else []
            if isinstance(result.get('ingredients_graded'), str):
                result['ingredients_graded'] = []

            # Ensure arrays exist (defensive)
            if 'alerts' not in result or result['alerts'] is None:
                result['alerts'] = []
            if 'hidden_truths' not in result or result['hidden_truths'] is None:
                result['hidden_truths'] = []
            if 'ingredients_graded' not in result or result['ingredients_graded'] is None:
                result['ingredients_graded'] = []

            logger.info(f"[V4 RESEARCH] Successfully researched {product_name}: {len(result.get('ingredients_graded', []))} ingredients, score={result.get('overall_score')}")
            return result
        else:
            raise ValueError("No JSON found in research response")

    except Exception as e:
        logger.error(f"[V4 RESEARCH ERROR] {str(e)}")
        # Return fallback response
        return {
            "product_name": product_name,
            "brand": brand,
            "category": category,
            "overall_score": 50,
            "overall_grade": "C",
            "dimension_scores": {
                "ingredient_safety": 50,
                "processing_level": 50,
                "corporate_ethics": 50,
                "supply_chain": 50
            },
            "ingredients_graded": [],
            "alerts": ["⚠️ Research temporarily unavailable"],
            "hidden_truths": [],
            "corporate_disclosure": None
        }


def normalize_cache_key(brand: str, product_name: str) -> str:
    """
    Normalize product name for consistent cache keys.
    Removes variants, scents, sizes to match same base product.
    """
    import re

    # Lowercase and strip
    brand_clean = brand.lower().strip()
    name_clean = product_name.lower().strip()

    # Remove common variant descriptors (scents, sizes, etc.)
    variant_patterns = [
        r'\s*-\s*.*$',  # Everything after dash
        r'\s+lemon.*',
        r'\s+fresh.*',
        r'\s+original.*',
        r'\s+crisp.*',
        r'\s+clean.*',
        r'\s+lavender.*',
        r'\s+citrus.*',
        r'\s+unscented.*',
        r'\s+\d+\s*(oz|ml|ct|count|pack).*',  # Sizes
        r'\s+value.*',
        r'\s+family.*',
        r'\s+travel.*',
    ]

    for pattern in variant_patterns:
        name_clean = re.sub(pattern, '', name_clean, flags=re.IGNORECASE)

    # Remove special characters except spaces
    name_clean = re.sub(r'[^\w\s]', '', name_clean)

    # Collapse multiple spaces
    name_clean = re.sub(r'\s+', ' ', name_clean).strip()
    brand_clean = re.sub(r'[^\w\s]', '', brand_clean)
    brand_clean = re.sub(r'\s+', ' ', brand_clean).strip()

    return f"{brand_clean}:{name_clean}"


# ============================================
# DEEP RESEARCH CACHING FUNCTIONS
# ============================================

async def get_cached_deep_research(cache_key: str) -> dict | None:
    """
    Check if deep research exists in Postgres cache.
    Returns cached result if found (no TTL - deep research is permanent).
    """
    global db_pool
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            cached = await conn.fetchrow("""
                SELECT report, full_report, product_name, brand, category, created_at
                FROM cached_deep_research
                WHERE cache_key = $1
            """, cache_key)
            if cached:
                logger.info(f"[DEEP RESEARCH CACHE HIT] {cache_key}")
                return {
                    "product_name": cached["product_name"],
                    "brand": cached["brand"],
                    "category": cached["category"],
                    "report": json.loads(cached["report"]),
                    "full_report": cached["full_report"],
                    "generated_at": cached["created_at"].isoformat(),
                    "cached": True
                }
    except Exception as e:
        logger.error(f"[DEEP RESEARCH CACHE ERROR] {e}")
    return None


async def save_deep_research_to_cache(
    cache_key: str,
    product_name: str,
    brand: str,
    category: str,
    report: dict,
    full_report: str
) -> bool:
    """
    Save deep research result to Postgres cache.
    Uses ON CONFLICT to handle race conditions.
    """
    global db_pool
    if not db_pool:
        return False
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO cached_deep_research
                    (cache_key, product_name, brand, category, report, full_report, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                ON CONFLICT (cache_key) DO UPDATE SET
                    report = EXCLUDED.report,
                    full_report = EXCLUDED.full_report,
                    updated_at = NOW()
            """, cache_key, product_name, brand, category, json.dumps(report), full_report)
            logger.info(f"[DEEP RESEARCH CACHED] {cache_key}")
            return True
    except Exception as e:
        logger.error(f"[DEEP RESEARCH CACHE SAVE ERROR] {e}")
        return False


async def get_cached_pdf_bytes(cache_key: str) -> bytes | None:
    """
    Check if PDF bytes exist in cache for this research.
    Returns PDF bytes if found, None otherwise.
    """
    global db_pool
    if not db_pool:
        return None
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT pdf_bytes FROM cached_deep_research
                WHERE cache_key = $1 AND pdf_bytes IS NOT NULL
            """, cache_key)
            if result and result["pdf_bytes"]:
                logger.info(f"[PDF CACHE HIT] {cache_key}")
                return result["pdf_bytes"]
    except Exception as e:
        logger.error(f"[PDF CACHE ERROR] {e}")
    return None


async def save_pdf_bytes_to_cache(cache_key: str, pdf_bytes: bytes) -> bool:
    """
    Save generated PDF bytes to cache for future instant retrieval.
    """
    global db_pool
    if not db_pool:
        return False
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE cached_deep_research
                SET pdf_bytes = $1, updated_at = NOW()
                WHERE cache_key = $2
            """, pdf_bytes, cache_key)
            logger.info(f"[PDF CACHED] {cache_key}")
            return True
    except Exception as e:
        logger.error(f"[PDF CACHE SAVE ERROR] {e}")
        return False


async def get_product_analysis(product_name: str, brand: str, category: str, visible_ingredients: list) -> dict:
    """
    V4 NEW ARCHITECTURE: Check cache first, research if needed, cache the result.

    Uses Postgres cached_products table for 7-day caching.
    """
    global db_pool

    # Create normalized cache key for consistent matching
    cache_key = normalize_cache_key(brand, product_name)
    logger.info(f"[V4 CACHE KEY] Normalized: {cache_key} (from '{brand}':'{product_name}')")

    # Check Postgres cache (7-day TTL)
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                cached = await conn.fetchrow("""
                    SELECT data, updated_at
                    FROM cached_products
                    WHERE cache_key = $1 AND updated_at > NOW() - INTERVAL '7 days'
                """, cache_key)

                if cached:
                    logger.info(f"[V4 CACHE HIT] {cache_key}")
                    return json.loads(cached["data"])
        except Exception as e:
            logger.warning(f"[V4 CACHE CHECK ERROR] {str(e)}")

    # Cache miss - research the product
    logger.info(f"[V4 CACHE MISS] {cache_key} - researching with Claude...")

    result = await research_product(product_name, brand, category, visible_ingredients)

    # Save to cache
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cached_products (cache_key, product_name, brand, data, updated_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (cache_key) DO UPDATE SET
                        data = $4,
                        updated_at = NOW()
                """, cache_key, product_name, brand, json.dumps(result))
            logger.info(f"[V4 CACHE SAVED] {cache_key}")
        except Exception as e:
            logger.warning(f"[V4 CACHE SAVE ERROR] {str(e)}")

    return result


# ============================================
# V4 SCAN ENDPOINT
# ============================================

@app.post("/api/v4/scan")
async def scan_product_v4(image: UploadFile = File(...)):
    """
    V4 Product Safety Scanner with 4-Dimension Scoring

    Consumer-protective scoring with:
    - Ingredient Safety (40%)
    - Processing Level (25%)
    - Corporate Ethics (20%)
    - Supply Chain (15%)

    Returns hidden truths, corporate ownership, and tiered ingredient grading.
    """
    # FIRST LINE - PROVE FUNCTION IS CALLED
    logger.info(f"[V4 SCAN START] Received image: {image.filename}, type: {image.content_type}")

    # Validate content type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type: {image.content_type}. Allowed: {', '.join(allowed_types)}"
        )

    try:
        # Read and encode image
        image_data = await image.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # V4 NEW ARCHITECTURE: Vision only identifies product, doesn't need ingredients
        vision_prompt = """Look at this product image and extract basic identification:

1. product_name: The exact product name from the package
2. brand: The brand/manufacturer name
3. category: One of [food, beverage, cleaning, cosmetics, household, supplement, cookware, other]
4. visible_ingredients: Any ingredients you can clearly read (may be empty - that's OK)

Return ONLY valid JSON (no markdown, no extra text):
{
  "product_name": "...",
  "brand": "...",
  "category": "...",
  "visible_ingredients": []
}

IMPORTANT: If you cannot read ingredients clearly, return empty array - that's completely fine. Your main job is to identify the product."""

        # Step 1: Vision extracts product identification (NOT ingredients)
        vision_message = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image.content_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": vision_prompt
                    }
                ]
            }]
        )

        # Parse vision response
        vision_text = vision_message.content[0].text
        logger.info(f"[V4 VISION RESPONSE] {vision_text[:500]}")

        # Extract JSON
        json_start = vision_text.find('{')
        json_end = vision_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            vision_json = vision_text[json_start:json_end]
            vision_data = json.loads(vision_json)
        else:
            raise HTTPException(status_code=500, detail="Failed to parse vision response")

        logger.info(f"[V4 VISION] Product: {vision_data.get('product_name')}, Brand: {vision_data.get('brand')}, Category: {vision_data.get('category')}")

        # Step 2: Get full analysis (cache or research)
        analysis = await get_product_analysis(
            product_name=vision_data.get("product_name", "Unknown Product"),
            brand=vision_data.get("brand", "Unknown Brand"),
            category=vision_data.get("category", "other"),
            visible_ingredients=vision_data.get("visible_ingredients", [])
        )

        # Generate unique report ID
        report_id = f"V4-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex().upper()}"

        # Build final response
        response = {
            "success": True,
            "version": "4.2.0",
            **analysis,  # Include all research results
            "report_id": report_id,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"[V4 COMPLETE] {analysis['product_name']}: Score={analysis['overall_score']}, Grade={analysis['overall_grade']}, Ingredients={len(analysis.get('ingredients_graded', []))}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"V4 scan error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/api/v1/ingredient/{ingredient_name}")
async def lookup_ingredient(ingredient_name: str):
    """Look up a single ingredient in the toxicity database"""

    ingredient_lower = ingredient_name.lower().strip()

    # Direct match
    if ingredient_lower in TOXICITY_DATABASE:
        data = TOXICITY_DATABASE[ingredient_lower]
        return {
            "ingredient": ingredient_name,
            "found": True,
            "hazard_score": data["score"],
            "category": data["category"],
            "source": data["source"],
            "concerns": data["concerns"]
        }

    # Partial match
    for toxic_name, data in TOXICITY_DATABASE.items():
        if toxic_name in ingredient_lower or ingredient_lower in toxic_name:
            return {
                "ingredient": ingredient_name,
                "found": True,
                "matched_as": toxic_name,
                "hazard_score": data["score"],
                "category": data["category"],
                "source": data["source"],
                "concerns": data["concerns"]
            }

    return {
        "ingredient": ingredient_name,
        "found": False,
        "message": "Ingredient not found in toxicity database"
    }


@app.get("/api/v1/database/stats")
async def database_stats():
    """Get statistics about the toxicity database"""

    categories = {}
    for name, data in TOXICITY_DATABASE.items():
        cat = data["category"]
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    return {
        "total_ingredients": len(TOXICITY_DATABASE),
        "categories": categories,
        "high_hazard_count": sum(1 for d in TOXICITY_DATABASE.values() if d["score"] >= 7),
        "moderate_hazard_count": sum(1 for d in TOXICITY_DATABASE.values() if 4 <= d["score"] < 7),
        "low_hazard_count": sum(1 for d in TOXICITY_DATABASE.values() if d["score"] < 4),
        "total_materials": len(MATERIAL_DATABASE)
    }


# ============================================
# V3 API ENDPOINT
# ============================================

@app.post("/api/v3/scan")
async def scan_product_v3(image: UploadFile = File(...)):
    """
    V3 Product Safety Scanner with Modular Prompts

    Paradigm shift: 95% ingredient-focused, 5% condition-focused
    Uses category-specific modules for specialized analysis
    """

    if not client:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    try:
        # Validate content type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Expected image/*, got {image.content_type}"
            )

        # Read and encode image
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # Step 1: Use modular prompt (default to 'food' for Phase 1)
        # TODO: Implement type detection in future
        product_type = "food"
        full_prompt = build_prompt(product_type)

        # Step 2: Single Claude API call with modular prompt
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image.content_type,
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": full_prompt
                        }
                    ]
                }
            ]
        )

        # Step 3: Parse Claude's response
        analysis_text = response.content[0].text

        # Extract JSON from response (Claude may wrap in markdown)
        if "```json" in analysis_text:
            json_start = analysis_text.find("```json") + 7
            json_end = analysis_text.find("```", json_start)
            analysis_text = analysis_text[json_start:json_end].strip()
        elif "```" in analysis_text:
            # Handle plain ``` without json
            json_start = analysis_text.find("```") + 3
            json_end = analysis_text.find("```", json_start)
            analysis_text = analysis_text[json_start:json_end].strip()

        claude_analysis = json.loads(analysis_text)

        # Step 4: Enrich ingredients with database
        if 'ingredients' in claude_analysis and 'analysis' in claude_analysis['ingredients']:
            enriched_ingredients = enrich_ingredients_with_database(
                claude_analysis['ingredients']['analysis']
            )
            claude_analysis['ingredients']['analysis'] = enriched_ingredients

            # Recalculate scores with enriched data
            scoring_result = calculate_ingredient_scores(enriched_ingredients)

            # Apply positive bonuses
            safety_with_bonuses = apply_positive_bonuses(
                scoring_result['safety_score'],
                claude_analysis.get('positive_attributes', [])
            )

            # Apply condition modifier
            final_score = apply_condition_modifier(
                safety_with_bonuses,
                claude_analysis.get('condition', {'score': 100}),
                claude_analysis.get('product_type', 'food')
            )

            # Update scores in response
            claude_analysis['safety_score'] = scoring_result['safety_score']
            claude_analysis['overall_score'] = final_score

            # Calculate grade
            claude_analysis['grade'] = calculate_grade(final_score)

        # Add success flag
        claude_analysis['success'] = True

        # Return V3 response
        return claude_analysis

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================
# V4 PHASE 3: DEEP RESEARCH ENDPOINTS
# ============================================

@app.post("/api/v4/deep-research")
async def start_deep_research(
    request: DeepResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a deep research job for comprehensive product investigation.
    Returns job_id for tracking progress.

    This is a premium feature that generates a 7-section report including:
    - Executive summary
    - Corporate ownership investigation
    - Ingredient deep dive
    - Supply chain analysis
    - Regulatory history
    - Better alternatives
    - Action items
    """

    # Check cache first for instant retrieval
    cache_key = normalize_cache_key(request.brand or "", request.product_name)
    logger.info(f"[DEEP RESEARCH] Checking cache for: {cache_key}")

    cached_result = await get_cached_deep_research(cache_key)
    if cached_result:
        # Cache hit! Return immediately with completed status
        logger.info(f"[DEEP RESEARCH] Cache hit - returning instantly")
        job_id = f"cached_{cache_key}"  # Synthetic job ID for cached results

        # Create completed job object for cached results
        job_data = {
            "job_id": job_id,
            "status": JobStatus.COMPLETED.value,
            "progress": 100,
            "current_step": "Report ready (cached)",
            "created_at": cached_result["generated_at"],
            "result": cached_result,
            "error": None,
            "completed_at": cached_result["generated_at"]
        }
        save_job(job_id, job_data)

        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Deep research report available (cached).",
            "check_status_url": f"/api/v4/job/{job_id}",
            "cached": True
        }

    # Cache miss - generate new research
    logger.info(f"[DEEP RESEARCH] Cache miss - starting new research job")

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Create job tracking object
    job_data = {
        "job_id": job_id,
        "status": JobStatus.PENDING.value,
        "progress": 0,
        "current_step": "Initializing deep research...",
        "created_at": datetime.utcnow().isoformat(),
        "result": None,
        "error": None,
        "completed_at": None
    }

    # Save to in-memory store
    save_job(job_id, job_data)

    # Start background task (also pass cache_key for saving later)
    background_tasks.add_task(process_deep_research, job_id, request, cache_key)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Deep research initiated. Use the job_id to check progress.",
        "check_status_url": f"/api/v4/job/{job_id}"
    }


@app.get("/api/v4/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Check the status of a deep research job.

    Returns:
    - Job status (pending/processing/completed/failed)
    - Progress percentage (0-100)
    - Current step description
    - Result (when completed)
    - Error message (if failed)
    """

    job_data = get_job(job_id)

    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    return job_data


def generate_deep_research_pdf_reportlab(result: dict, generated_at_formatted: str, buffer: BytesIO) -> bytes:
    """
    Generate Deep Research PDF using reportlab (pure Python, no system deps).

    This replaces WeasyPrint which had version incompatibility issues on Railway.
    Reportlab works reliably across all Python environments.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, white, red, orange, green, gray
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    import re

    # Extract data
    product_name = result.get("product_name", "Unknown Product")
    brand = result.get("brand", "")
    category = result.get("category", "Unknown")
    report = result.get("report", {})
    full_report = result.get("full_report", "")

    # DEBUG: Log what we received
    logger.info(f"[PDF DEBUG] Result keys: {list(result.keys())}")
    logger.info(f"[PDF DEBUG] Report type: {type(report)}, keys: {list(report.keys()) if isinstance(report, dict) else 'NOT A DICT'}")
    logger.info(f"[PDF DEBUG] Full report length: {len(full_report) if full_report else 0}")

    # Section name mapping - Claude returns numbered sections, map to readable titles
    # Sections from prompt: "1. EXECUTIVE SUMMARY", "2. THE COMPANY BEHIND IT", etc.
    section_order = [
        ("EXECUTIVE SUMMARY", "Executive Summary"),
        ("THE COMPANY BEHIND IT", "The Company Behind It"),
        ("INGREDIENT DEEP DIVE", "Ingredient Deep Dive"),
        ("SUPPLY CHAIN INVESTIGATION", "Supply Chain Investigation"),
        ("REGULATORY HISTORY", "Regulatory History"),
        ("BETTER ALTERNATIVES", "Better Alternatives"),
        ("ACTION ITEMS FOR CONSUMER", "Action Items for Consumer"),
    ]

    # Helper to find section content by partial match
    def get_section_content(key_pattern):
        for section_key, content in report.items():
            if key_pattern.upper() in section_key.upper():
                return content
        return None

    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Custom styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=6,
        textColor=HexColor('#1a1a2e'),
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#1a1a2e'),
        spaceBefore=20,
        spaceAfter=10,
        borderPadding=5
    )

    subsection_style = ParagraphStyle(
        'Subsection',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=HexColor('#333333'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#333333'),
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#333333'),
        leftIndent=20,
        spaceAfter=4
    )

    # Build document content
    story = []

    # Header
    story.append(Paragraph("TrueCancer Deep Research Report", title_style))
    story.append(Spacer(1, 6))

    # Product info
    product_display = f"<b>{product_name}</b>"
    if brand:
        product_display += f" by {brand}"
    story.append(Paragraph(product_display, subtitle_style))
    story.append(Paragraph(f"Category: {category} | Generated: {generated_at_formatted}", subtitle_style))
    story.append(Spacer(1, 20))

    # Helper to escape HTML special characters for reportlab
    def escape_html(text):
        if not text:
            return ""
        text = str(text)
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text

    # Helper to convert markdown text to paragraphs
    def add_markdown_content(content_text, story):
        if not content_text:
            return

        lines = content_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue

            # Handle markdown bullet points
            if line.startswith('- ') or line.startswith('* '):
                bullet_text = escape_html(line[2:])
                # Handle bold in bullet points
                bullet_text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', bullet_text)
                story.append(Paragraph(f"• {bullet_text}", bullet_style))
            # Handle subsections (### )
            elif line.startswith('### '):
                sub_title = escape_html(line[4:])
                story.append(Paragraph(sub_title, subsection_style))
            # Regular text
            else:
                text = escape_html(line)
                # Convert markdown bold
                text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
                story.append(Paragraph(text, body_style))

    # Process each section in order
    for key_pattern, display_title in section_order:
        content = get_section_content(key_pattern)
        if content:
            story.append(Paragraph(display_title, section_header_style))
            add_markdown_content(content, story)
            story.append(Spacer(1, 10))

    # If no sections were found, use full_report as fallback
    if not any(get_section_content(key) for key, _ in section_order):
        if full_report:
            story.append(Paragraph("Full Research Report", section_header_style))
            add_markdown_content(full_report, story)
            story.append(Spacer(1, 10))

    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#999999'),
        alignment=TA_CENTER
    )
    story.append(Paragraph("Generated by TrueCancer V4 - Deep Research Engine", footer_style))
    story.append(Paragraph("This report is for educational purposes only. Consult healthcare professionals for medical advice.", footer_style))

    # Build PDF
    doc.build(story)
    return buffer.getvalue()


@app.get("/api/v4/deep-research/{job_id}/pdf")
async def get_deep_research_pdf(job_id: str):
    """
    Generate and return PDF for a completed deep research job.

    Server-side PDF generation eliminates iOS memory crashes from
    client-side dart_pdf widget tree building.

    Caches PDF bytes in database for instant retrieval on subsequent requests.

    Returns: PDF file as binary stream
    """
    # Get job data
    job_data = get_job(job_id)

    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_data.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job_data.get('status')}"
        )

    result = job_data.get("result")
    if not result:
        raise HTTPException(status_code=500, detail="No result data found")

    # Generate cache key for PDF lookup
    cache_key = normalize_cache_key(result.get("brand", ""), result.get("product_name", ""))

    # Create filename (needed for both cached and fresh PDFs)
    product_name_safe = re.sub(r'[^\w\s-]', '', result.get("product_name", "Report"))
    product_name_safe = re.sub(r'\s+', '_', product_name_safe)[:50]
    filename = f"TrueCancer_Report_{product_name_safe}.pdf"

    # Check PDF cache first for instant retrieval
    cached_pdf = await get_cached_pdf_bytes(cache_key)
    if cached_pdf:
        logger.info(f"[PDF] Cache hit - returning cached PDF for {cache_key}")
        return StreamingResponse(
            BytesIO(cached_pdf),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    # Cache miss - generate fresh PDF using reportlab
    try:
        # Parse generated_at for formatting
        generated_at = result.get("generated_at", datetime.utcnow().isoformat())
        try:
            dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            generated_at_formatted = dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            generated_at_formatted = generated_at

        # Generate PDF with reportlab (pure Python, no system deps)
        pdf_buffer = BytesIO()
        pdf_bytes = generate_deep_research_pdf_reportlab(
            result=result,
            generated_at_formatted=generated_at_formatted,
            buffer=pdf_buffer
        )

        logger.info(f"[PDF] Generated fresh PDF for job {job_id}: {filename} ({len(pdf_bytes)} bytes)")

        # Save PDF bytes to cache for future instant retrieval
        await save_pdf_bytes_to_cache(cache_key, pdf_bytes)

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"[PDF] Generation error for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@app.delete("/api/v4/admin/cleanup-jobs")
async def cleanup_old_jobs():
    """
    Manual cleanup endpoint for in-memory jobs.

    Jobs are stored in memory and cleared on server restart.
    """
    DEEP_RESEARCH_JOBS.clear()
    return {
        "message": "In-memory job store cleared",
        "storage": "in-memory"
    }


@app.post("/api/admin/cache/wipe-pdf")
async def wipe_pdf_cache(admin_key: str = Header(None, alias="admin-key")):
    """
    Admin endpoint to wipe only cached PDF bytes, forcing PDF regeneration.
    Keeps research data intact.
    """
    global db_pool

    admin_secret = os.getenv("ADMIN_SECRET")
    if not admin_secret:
        raise HTTPException(status_code=500, detail="ADMIN_SECRET not configured")

    if not admin_key or admin_key != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute("UPDATE cached_deep_research SET pdf_bytes = NULL")
            count = int(result.split()[-1]) if result else 0

        logger.info(f"[ADMIN] PDF cache cleared: {count} PDFs will regenerate on next request")

        return {
            "status": "success",
            "message": "PDF cache cleared. PDFs will regenerate with latest code on next request.",
            "cleared": count
        }

    except Exception as e:
        logger.error(f"[ADMIN] PDF cache wipe failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF cache wipe failed: {str(e)}")


@app.post("/api/admin/cache/wipe")
async def wipe_cache(admin_key: str = Header(None, alias="admin-key")):
    """
    Admin endpoint to wipe all cached data for fresh start.

    Use this when:
    - Prompt architecture changes require fresh research
    - Before production launch
    - Testing new scoring algorithms
    - After major Claude model updates

    Requires admin-key header with ADMIN_SECRET environment variable.
    """
    global db_pool

    # Check admin authorization
    admin_secret = os.getenv("ADMIN_SECRET")
    if not admin_secret:
        raise HTTPException(status_code=500, detail="ADMIN_SECRET not configured")

    if not admin_key or admin_key != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin key")

    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        async with db_pool.acquire() as conn:
            # Wipe V4 scan cache
            products_result = await conn.execute("DELETE FROM cached_products")
            products_count = int(products_result.split()[-1]) if products_result else 0

            # Wipe Deep Research cache
            research_result = await conn.execute("DELETE FROM cached_deep_research")
            research_count = int(research_result.split()[-1]) if research_result else 0

        # Clear in-memory job store
        DEEP_RESEARCH_JOBS.clear()

        logger.info(f"[ADMIN] Cache wiped: {products_count} products, {research_count} research reports")

        return {
            "status": "success",
            "message": "All caches wiped. Next scans will use fresh research.",
            "cleared": {
                "cached_products": products_count,
                "cached_deep_research": research_count,
                "in_memory_jobs": "cleared"
            }
        }

    except Exception as e:
        logger.error(f"[ADMIN] Cache wipe failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache wipe failed: {str(e)}")


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
