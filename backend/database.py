"""
Database Models and Connection
==============================
PostgreSQL models for caching products, storing scans, and user scores.
Uses SQLAlchemy async for Railway PostgreSQL.
"""

import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    Text, JSON, ForeignKey, create_engine, Index
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import ARRAY

# Get database URL from environment (Railway provides this)
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert postgres:// to postgresql:// for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# For async, we need postgresql+asyncpg://
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

Base = declarative_base()


class CachedProduct(Base):
    """
    Cached product data from Open Food Facts / other sources.
    Avoids repeated API calls for the same products.
    """
    __tablename__ = "cached_products"
    
    id = Column(Integer, primary_key=True)
    barcode = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(500), nullable=False)
    brand = Column(String(255), nullable=True)
    
    # Ingredients
    ingredients_text = Column(Text, nullable=True)
    ingredients_list = Column(ARRAY(String), nullable=True)
    
    # Pre-calculated score (so we don't recalculate every time)
    cancer_score = Column(Integer, nullable=True)  # 0-100
    score_color = Column(String(20), nullable=True)  # green/yellow/orange/red
    worst_ingredient = Column(String(255), nullable=True)
    carcinogens_found = Column(ARRAY(String), nullable=True)
    
    # Metadata
    image_url = Column(String(1000), nullable=True)
    categories = Column(String(500), nullable=True)
    source = Column(String(50), nullable=True)  # openfoodfacts, serpapi, manual
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Search index
    search_name = Column(String(500), nullable=True)  # Lowercase for search


class UserScan(Base):
    """
    Record of each scan a user makes.
    Used for history and calculating overall user score.
    """
    __tablename__ = "user_scans"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), index=True, nullable=False)  # Firebase UID or device ID
    
    # Product info
    product_id = Column(Integer, ForeignKey("cached_products.id"), nullable=True)
    product_name = Column(String(500), nullable=False)
    
    # Score at time of scan
    cancer_score = Column(Integer, nullable=False)
    score_color = Column(String(20), nullable=False)
    
    # How they scanned it
    scan_method = Column(String(50), nullable=False)  # barcode, photo, manual
    
    # Timestamp
    scanned_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    product = relationship("CachedProduct", backref="scans")


class UserProfile(Base):
    """
    User profile with aggregated score.
    """
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Aggregated stats
    total_scans = Column(Integer, default=0)
    average_score = Column(Float, default=100.0)  # Starts at 100 (green)
    worst_product_name = Column(String(500), nullable=True)
    worst_product_score = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scan_at = Column(DateTime, nullable=True)


class IngredientReference(Base):
    """
    Reference table of known toxic ingredients.
    Pre-populated with ~500+ chemicals and their toxicity ratings.
    """
    __tablename__ = "ingredient_reference"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    name_lower = Column(String(255), index=True, nullable=False)  # For case-insensitive search
    
    # Toxicity rating 0-10
    toxicity_score = Column(Float, nullable=False, default=3.0)
    
    # Specific concerns
    is_carcinogen = Column(Boolean, default=False)
    is_endocrine_disruptor = Column(Boolean, default=False)
    is_allergen = Column(Boolean, default=False)
    is_irritant = Column(Boolean, default=False)
    
    # Category
    category = Column(String(100), nullable=True)  # preservative, fragrance, solvent, etc.
    
    # Additional info
    concerns = Column(ARRAY(String), nullable=True)
    safer_alternatives = Column(ARRAY(String), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Source of this data
    source = Column(String(100), nullable=True)  # prop65, iarc, eu-reach, etc.


# Create indexes for faster lookups
Index("idx_cached_products_search", CachedProduct.search_name)
Index("idx_user_scans_user_date", UserScan.user_id, UserScan.scanned_at)


# Database session management
async_engine = None
AsyncSessionLocal = None


async def init_db():
    """Initialize database connection and create tables."""
    global async_engine, AsyncSessionLocal
    
    if not ASYNC_DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")
    
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,  # Set True for SQL debugging
        pool_size=5,
        max_overflow=10
    )
    
    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database initialized successfully")


async def get_session() -> AsyncSession:
    """Get a database session."""
    if AsyncSessionLocal is None:
        await init_db()
    async with AsyncSessionLocal() as session:
        yield session


# Synchronous version for initial setup/migrations
def get_sync_engine():
    """Get synchronous engine for migrations."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")
    return create_engine(DATABASE_URL)


def create_tables_sync():
    """Create tables synchronously (for initial setup)."""
    engine = get_sync_engine()
    Base.metadata.create_all(engine)
    print("Tables created successfully")


if __name__ == "__main__":
    # Run this to create tables
    create_tables_sync()
