"""
V3 Modular Prompt System for Cancer Detector

Architecture:
- BASE_PROMPT: Core scoring philosophy (95% ingredients, 5% condition)
- Category Modules: Specialized domain knowledge (6 categories)
- build_prompt(): Combines BASE + module for one-pass analysis
"""

from .base_prompt import BASE_PROMPT
from .modules import (
    FOOD_MODULE,
    WATER_MODULE,
    COSMETICS_MODULE,
    COOKWARE_MODULE,
    CLEANING_MODULE,
    SUPPLEMENTS_MODULE,
    build_prompt
)

__all__ = [
    'BASE_PROMPT',
    'FOOD_MODULE',
    'WATER_MODULE',
    'COSMETICS_MODULE',
    'COOKWARE_MODULE',
    'CLEANING_MODULE',
    'SUPPLEMENTS_MODULE',
    'build_prompt'
]
