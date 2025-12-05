"""
Cancer Detector API v2
======================
Clean, simple FastAPI backend.

Flow:
1. Photo → SerpAPI identifies product
2. Product name → Open Food Facts gets ingredients  
3. Ingredients → Scoring algorithm calculates cancer score
4. Return report to app

Endpoints:
- POST /api/scan/photo     - Scan from photo URL
- POST /api/scan/barcode   - Scan from barcode
- POST /api/scan/manual    - Manual ingredient entry
- GET  /api/product/{id}   - Get cached product
- GET  /api/user/{id}/history - User scan history
- GET  /api/user/{id}/score   - User overall score
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import base64
import uuid
from pathlib import Path

# Our modules
from scoring import calculate_cancer_score, ProductScore
from unified_database import (
    unified_product_search, 
    unified_barcode_lookup,
    lookup_chemical,
    ProductResult as ProductData
)
from serpapi_client import identify_product_from_image, LensResult

# Database (optional - works without it)
try:
    from database import init_db, get_session, AsyncSession, CachedProduct, UserScan, UserProfile
    from sqlalchemy import select, func
    HAS_DATABASE = True
except Exception:
    HAS_DATABASE = False
    print("⚠ Running without database - caching disabled")


# Initialize FastAPI
app = FastAPI(
    title="Cancer Detector API",
    description="Scan products and get toxicity/cancer risk scores",
    version="2.0.0"
)

# CORS - allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup uploads directory
upload_dir = Path("/tmp/uploads")
upload_dir.mkdir(exist_ok=True)


# ============== Request/Response Models ==============

class PhotoScanRequest(BaseModel):
    image_url: str = Field(..., description="Publicly accessible URL of product photo")
    user_id: Optional[str] = Field(None, description="User ID for history tracking")


class BarcodeScanRequest(BaseModel):
    barcode: str = Field(..., description="Product barcode (UPC/EAN)")
    user_id: Optional[str] = Field(None, description="User ID for history tracking")


class ManualEntryRequest(BaseModel):
    product_name: str = Field(..., description="Product name")
    ingredients: List[str] = Field(..., description="List of ingredients")
    user_id: Optional[str] = Field(None, description="User ID for history tracking")


class IngredientDetail(BaseModel):
    name: str
    toxicity_score: float
    concern_level: str
    is_carcinogen: bool
    notes: Optional[str] = None


class ScanResponse(BaseModel):
    success: bool
    product_name: Optional[str] = None
    brand: Optional[str] = None
    cancer_score: Optional[int] = None  # 0-100, higher = safer
    score_color: Optional[str] = None   # green/yellow/orange/red
    summary: Optional[str] = None
    worst_ingredient: Optional[str] = None
    carcinogen_count: int = 0
    carcinogens_found: List[str] = []
    ingredients: List[IngredientDetail] = []
    image_url: Optional[str] = None
    scan_method: Optional[str] = None
    error: Optional[str] = None
    manual_entry_needed: bool = False  # Signal user to enter ingredients manually
    identified_but_no_data: bool = False  # Product found but no ingredients in DB
    serpapi_identified: Optional[bool] = None  # Did SerpAPI identify the product?
    serpapi_confidence: Optional[float] = None  # Confidence level from SerpAPI


class UserScoreResponse(BaseModel):
    user_id: str
    overall_score: float  # 0-100
    score_color: str
    total_scans: int
    worst_product: Optional[str] = None
    worst_score: Optional[int] = None


class ScanHistoryItem(BaseModel):
    product_name: str
    cancer_score: int
    score_color: str
    scanned_at: datetime


# ============== Startup ==============

@app.on_event("startup")
async def startup():
    """Initialize database on startup (optional)."""
    if HAS_DATABASE:
        try:
            await init_db()
            print("✓ Database connected")
        except Exception as e:
            print(f"⚠ Database connection failed: {e}")
            print("  Running without database caching")
    else:
        print("⚠ Running without database (caching disabled)")


# ============== API Endpoints ==============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/images/{filename}")
async def serve_image(filename: str):
    """Serve uploaded images for SerpAPI."""
    file_path = Path("/tmp/uploads") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path)


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image and get a public URL.
    Saves temporarily for SerpAPI processing.
    """
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("/tmp/uploads")
        upload_dir.mkdir(exist_ok=True)

        # Generate unique filename
        file_ext = Path(file.filename).suffix or '.jpg'
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / filename

        # Save file temporarily
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        # Get public URL (Railway provides this via PORT env)
        # Construct public URL
        base_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "cancer-detector-backend-production.up.railway.app")
        public_url = f"https://{base_domain}/images/{filename}"

        return {
            "success": True,
            "image_url": public_url,
            "size": len(content),
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/scan/photo", response_model=ScanResponse)
async def scan_from_photo(
    request: PhotoScanRequest,
    background_tasks: BackgroundTasks
):
    """
    Scan a product from a photo.
    
    1. Send photo to SerpAPI Google Lens
    2. Get product identification
    3. Look up ingredients in Open Food Facts
    4. Calculate cancer score
    """
    # Step 1: Identify product from photo
    lens_result = await identify_product_from_image(request.image_url)

    if not lens_result.success:
        return ScanResponse(
            success=False,
            error=f"Could not identify product from photo. Try:\n• Scanning the barcode\n• Taking a clearer photo\n• Entering ingredients manually",
            scan_method="photo",
            serpapi_identified=False,
            manual_entry_needed=True
        )
    
    # Step 2: Search for product in databases
    product_data = None
    
    # Try searching by the identified name
    if lens_result.search_query:
        search_results = await unified_product_search(lens_result.search_query, limit=1)
        if search_results:
            product_data = search_results[0]
    
    # Step 3: If we have ingredients, calculate score
    if product_data and product_data.ingredients_list:
        score_result = calculate_cancer_score(product_data.ingredients_list)
        
        # Save scan to history if user_id provided
        if request.user_id:
            background_tasks.add_task(
                save_scan_to_history,
                request.user_id,
                product_data.name or lens_result.product_name,
                score_result,
                "photo"
            )
        
        return _build_response(
            product_data=product_data,
            score_result=score_result,
            scan_method="photo",
            fallback_name=lens_result.product_name
        )
    
    # Step 4: No ingredients found - return what we know
    product_display = lens_result.product_name or "your product"
    if lens_result.brand:
        product_display = f"{lens_result.brand} {lens_result.product_name}" if lens_result.product_name else lens_result.brand

    return ScanResponse(
        success=True,
        product_name=lens_result.product_name or "Product",
        brand=lens_result.brand,
        cancer_score=None,
        score_color="gray",
        summary=f"✓ Identified: {product_display}\n\nIngredients not in database. Please enter ingredients manually from the product label.",
        scan_method="photo",
        manual_entry_needed=True,
        identified_but_no_data=True,
        serpapi_identified=True,
        serpapi_confidence=lens_result.confidence if lens_result else 0.0,
        error=None  # Not an error - just missing data
    )


@app.post("/api/scan/barcode", response_model=ScanResponse)
async def scan_from_barcode(
    request: BarcodeScanRequest,
    background_tasks: BackgroundTasks
):
    """
    Scan a product by barcode.
    Fastest and most reliable method.
    """
    # Look up directly by barcode across all databases
    product_data = await unified_barcode_lookup(request.barcode)
    
    if not product_data.found:
        return ScanResponse(
            success=False,
            error="Product not found in database. Try photo scan or manual entry.",
            scan_method="barcode"
        )
    
    # Calculate score if we have ingredients
    if product_data.ingredients_list:
        score_result = calculate_cancer_score(product_data.ingredients_list)
        
        # Save to history
        if request.user_id:
            background_tasks.add_task(
                save_scan_to_history,
                request.user_id,
                product_data.name,
                score_result,
                "barcode"
            )
        
        return _build_response(
            product_data=product_data,
            score_result=score_result,
            scan_method="barcode"
        )
    
    return ScanResponse(
        success=True,
        product_name=product_data.name,
        brand=product_data.brand,
        image_url=product_data.image_url,
        cancer_score=None,
        score_color="gray",
        summary="Product found but no ingredients listed.",
        scan_method="barcode"
    )


@app.post("/api/scan/manual", response_model=ScanResponse)
async def scan_manual_entry(
    request: ManualEntryRequest,
    background_tasks: BackgroundTasks
):
    """
    Calculate score from manually entered ingredients.
    Used when database lookup fails.
    """
    if not request.ingredients:
        return ScanResponse(
            success=False,
            error="No ingredients provided",
            scan_method="manual"
        )
    
    score_result = calculate_cancer_score(request.ingredients)
    
    # Save to history
    if request.user_id:
        background_tasks.add_task(
            save_scan_to_history,
            request.user_id,
            request.product_name,
            score_result,
            "manual"
        )
    
    return ScanResponse(
        success=True,
        product_name=request.product_name,
        cancer_score=score_result.cancer_score,
        score_color=score_result.color,
        summary=score_result.summary,
        worst_ingredient=score_result.worst_ingredient,
        carcinogen_count=score_result.carcinogen_count,
        carcinogens_found=score_result.carcinogens_found,
        ingredients=[
            IngredientDetail(
                name=ing.name,
                toxicity_score=ing.toxicity_score,
                concern_level=ing.concern_level,
                is_carcinogen=ing.is_carcinogen,
                notes=ing.notes
            )
            for ing in score_result.ingredient_breakdown
        ],
        scan_method="manual"
    )


@app.get("/api/user/{user_id}/score", response_model=UserScoreResponse)
async def get_user_score(user_id: str):
    """
    Get user's overall cancer score based on all their scans.
    """
    # TODO: Implement with database
    # For now, return mock data
    return UserScoreResponse(
        user_id=user_id,
        overall_score=85.0,
        score_color="green",
        total_scans=0,
        worst_product=None,
        worst_score=None
    )


@app.get("/api/user/{user_id}/history", response_model=List[ScanHistoryItem])
async def get_user_history(user_id: str, limit: int = 50):
    """
    Get user's scan history.
    """
    # TODO: Implement with database
    return []


@app.get("/api/ingredient/{name}")
async def lookup_ingredient(name: str):
    """
    Look up toxicity info for a single ingredient.
    """
    from scoring import analyze_ingredient
    
    analysis = analyze_ingredient(name)
    
    return {
        "name": analysis.name,
        "toxicity_score": analysis.toxicity_score,
        "concern_level": analysis.concern_level,
        "is_carcinogen": analysis.is_carcinogen,
        "is_endocrine_disruptor": analysis.is_endocrine_disruptor,
        "notes": analysis.notes
    }


# ============== Helper Functions ==============

def _build_response(
    product_data: ProductData,
    score_result: ProductScore,
    scan_method: str,
    fallback_name: str = None
) -> ScanResponse:
    """Build the API response from product data and score."""
    
    return ScanResponse(
        success=True,
        product_name=product_data.name or fallback_name,
        brand=product_data.brand,
        cancer_score=score_result.cancer_score,
        score_color=score_result.color,
        summary=score_result.summary,
        worst_ingredient=score_result.worst_ingredient,
        carcinogen_count=score_result.carcinogen_count,
        carcinogens_found=score_result.carcinogens_found,
        ingredients=[
            IngredientDetail(
                name=ing.name,
                toxicity_score=ing.toxicity_score,
                concern_level=ing.concern_level,
                is_carcinogen=ing.is_carcinogen,
                notes=ing.notes
            )
            for ing in score_result.ingredient_breakdown
        ],
        image_url=product_data.image_url,
        scan_method=scan_method
    )


async def save_scan_to_history(
    user_id: str,
    product_name: str,
    score_result: ProductScore,
    scan_method: str
):
    """Save scan to user's history (background task)."""
    # TODO: Implement database save
    print(f"[HISTORY] User {user_id} scanned {product_name}: {score_result.cancer_score}/100")


# ============== Run Server ==============

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
