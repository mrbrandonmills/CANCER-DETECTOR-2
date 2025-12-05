import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompts.base_prompt import BASE_PROMPT
from prompts.modules import (
    FOOD_MODULE,
    WATER_MODULE,
    COSMETICS_MODULE,
    COOKWARE_MODULE,
    CLEANING_MODULE,
    SUPPLEMENTS_MODULE,
    build_prompt
)


def test_base_prompt_contains_core_philosophy():
    """Verify BASE_PROMPT has 95/5 weight philosophy"""
    assert "95%" in BASE_PROMPT
    assert "ingredients" in BASE_PROMPT.lower()
    assert "condition" in BASE_PROMPT.lower()


def test_base_prompt_contains_positive_bonus_rules():
    """Verify BASE_PROMPT explains +3 bonuses, max +15"""
    assert "+3" in BASE_PROMPT or "bonus" in BASE_PROMPT.lower()
    assert "15" in BASE_PROMPT or "max" in BASE_PROMPT.lower()


def test_food_module_contains_hfcs():
    """Verify FOOD_MODULE flags HFCS"""
    assert "hfcs" in FOOD_MODULE.lower() or "high fructose" in FOOD_MODULE.lower()


def test_water_module_contains_pfas():
    """Verify WATER_MODULE flags PFAS"""
    assert "pfas" in WATER_MODULE.lower()


def test_build_prompt_combines_base_and_module():
    """Verify build_prompt() concatenates BASE + category module"""
    food_prompt = build_prompt("food")
    assert BASE_PROMPT in food_prompt
    assert FOOD_MODULE in food_prompt

    water_prompt = build_prompt("water")
    assert BASE_PROMPT in water_prompt
    assert WATER_MODULE in water_prompt


def test_build_prompt_defaults_to_food():
    """Verify unknown product type defaults to food module"""
    unknown_prompt = build_prompt("unknown_type")
    assert FOOD_MODULE in unknown_prompt


def test_build_prompt_handles_all_product_types():
    """Verify all 6 product types return correct modules"""
    types = ['food', 'water', 'cosmetics', 'cookware', 'cleaning', 'supplements']
    for ptype in types:
        prompt = build_prompt(ptype)
        assert BASE_PROMPT in prompt
        assert len(prompt) > len(BASE_PROMPT)


def test_build_prompt_case_insensitive():
    """Verify case-insensitive matching"""
    assert build_prompt('FOOD') == build_prompt('food')
    assert build_prompt('Water') == build_prompt('water')


def test_build_prompt_handles_invalid_type():
    """Verify invalid types default to food"""
    invalid_prompt = build_prompt('invalid_type')
    assert FOOD_MODULE in invalid_prompt
