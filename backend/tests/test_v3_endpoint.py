import pytest
import sys
from pathlib import Path
import base64
import httpx
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.mark.asyncio
async def test_v3_health_check():
    """Verify health endpoint shows V3 support"""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # Verify V3 readiness flags
        assert "v3_ready" in data
        assert data["v3_ready"] is True
        assert "modular_prompts" in data
        assert data["modular_prompts"] is True


@pytest.mark.asyncio
async def test_v3_scan_endpoint_exists():
    """Verify /api/v3/scan endpoint is registered"""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Try to POST to the endpoint without a file
        # A 404 means endpoint doesn't exist
        # 422 or 500 means endpoint exists but has validation/config issues
        response = await client.post("/api/v3/scan")
        # Should not be 404 (Not Found) - endpoint exists
        assert response.status_code != 404


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping integration test"
)
async def test_v3_scan_with_modular_prompt():
    """Integration test: V3 scan uses modular prompt system

    This test requires ANTHROPIC_API_KEY to be set.
    Skip with: pytest -m "not integration"
    """
    # Create a test image (1x1 pixel PNG)
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    test_image_bytes = base64.b64decode(test_image_base64)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Upload via multipart/form-data
        files = {'image': ('test.png', test_image_bytes, 'image/png')}
        response = await client.post("/api/v3/scan", files=files)

        # Should succeed with API key
        assert response.status_code == 200
        data = response.json()

        # Verify V3 response structure
        assert 'success' in data
        assert 'ingredients' in data
        assert 'analysis' in data['ingredients']
        assert 'positive_attributes' in data
        assert 'condition' in data
        assert 'safety_score' in data
        assert 'overall_score' in data
