# Product Ingredient Database Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace empty Open Facts API responses with comprehensive local product ingredient database built from California Chemicals, Open Products Facts, Open Beauty Facts, and SmartLabel data sources.

**Architecture:** Download bulk CSV files from government and open data sources, import into SQLite database with unified schema, integrate fuzzy product name search into existing SerpAPI flow, add OCR fallback for missing products.

**Tech Stack:** Python 3, SQLite, pandas (CSV parsing), httpx (downloads), Tesseract OCR (fallback)

**Success Criteria:** Clorox Disinfecting Wipes photo scan returns 10 real ingredients with cancer score.

---

## PHASE 1: Research & Discovery

### Task 1: Search for SmartLabel Scraped Database

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/docs/smartlabel-research.md`

**Step 1: Search GitHub for SmartLabel datasets**

Run web searches:
```bash
# Search terms:
- "smartlabel scraper github"
- "smartlabel dataset csv"
- "smartlabel ingredients database"
```

**Step 2: Document findings**

Create `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/docs/smartlabel-research.md`:
```markdown
# SmartLabel Database Research

## GitHub Repositories Found:
- [List repos with links]

## Datasets Found:
- [List datasets with download links]

## Recommendation:
- [Use this source] OR [No usable source found]
```

**Step 3: Commit research**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
git add docs/smartlabel-research.md
git commit -m "docs: research SmartLabel data sources"
```

---

### Task 2: Download California Chemicals CSV

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/data/raw/california_chemicals.csv`

**Step 1: Create data directories**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
mkdir -p data/raw data/processed
```

**Step 2: Download California CSV**

```bash
curl -L "https://data.chhs.ca.gov/dataset/596b5eed-31de-4fd8-a645-249f3f9b19c4/resource/57da6c9a-41a7-44b0-ab8d-815ff2cd5913/download/cscpopendata.csv" \
  -o data/raw/california_chemicals.csv
```

Expected: File ~50MB, download completes in 30 seconds

**Step 3: Inspect CSV structure**

```bash
head -n 5 data/raw/california_chemicals.csv
wc -l data/raw/california_chemicals.csv
```

Expected: ~114,000 lines with columns like: Product Name, Brand, Company, Chemical Name, CAS Number, etc.

**Step 4: Document structure**

Create `docs/california-csv-structure.md`:
```markdown
# California Chemicals CSV Structure

Columns:
- [List all column names from header]

Sample rows:
- [Paste first 3 data rows]

Total rows: [number]
```

**Step 5: Commit**

```bash
git add data/raw/.gitkeep docs/california-csv-structure.md
git commit -m "data: download California Chemicals CSV (114k products)"
```

Note: `.gitignore` should exclude `data/raw/*.csv` (large files)

---

### Task 3: Download Open Products Facts CSV

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/data/raw/open_products_facts.csv.gz`

**Step 1: Download compressed CSV**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
curl -L "https://static.openproductsfacts.org/data/en.openproductsfacts.org.products.csv.gz" \
  -o data/raw/open_products_facts.csv.gz
```

Expected: File ~100MB compressed, download 2-3 minutes

**Step 2: Decompress**

```bash
gunzip -k data/raw/open_products_facts.csv.gz
```

Expected: Uncompressed file ~500MB

**Step 3: Inspect structure**

```bash
head -n 5 data/raw/open_products_facts.csv | cut -f1-10
wc -l data/raw/open_products_facts.csv
```

Expected: Columns include `code`, `product_name`, `brands`, `ingredients_text`, `categories`, `image_url`

**Step 4: Filter to products with ingredients**

```bash
grep -v "^code" data/raw/open_products_facts.csv | \
  awk -F'\t' '$NF != ""' | \
  wc -l
```

Expected: ~10-20% of products have ingredients_text (need to verify exact column)

**Step 5: Document and commit**

```bash
git add docs/open-products-facts-structure.md
git commit -m "data: download Open Products Facts CSV"
```

---

### Task 4: Download Open Beauty Facts CSV

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/data/raw/open_beauty_facts.csv.gz`

**Step 1: Download**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
curl -L "https://static.openbeautyfacts.org/data/en.openbeautyfacts.org.products.csv.gz" \
  -o data/raw/open_beauty_facts.csv.gz
```

**Step 2: Decompress and inspect**

```bash
gunzip -k data/raw/open_beauty_facts.csv.gz
head -n 5 data/raw/open_beauty_facts.csv
wc -l data/raw/open_beauty_facts.csv
```

**Step 3: Commit**

```bash
git commit -m "data: download Open Beauty Facts CSV"
```

---

## PHASE 2: Database Setup

### Task 5: Create SQLite Database Schema

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/create_database.py`

**Step 1: Write database creation script**

```python
"""
Create unified product ingredients database.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "products.db"

def create_database():
    """Create products database with unified schema."""

    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Create new database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Products table
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            barcode TEXT,
            product_name TEXT NOT NULL,
            brand_name TEXT,
            category TEXT,
            ingredients_text TEXT,
            ingredients_json TEXT,
            has_carcinogens BOOLEAN DEFAULT 0,
            carcinogen_names TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Indexes for fast search
    cursor.execute("CREATE INDEX idx_barcode ON products(barcode)")
    cursor.execute("CREATE INDEX idx_product_name ON products(product_name)")
    cursor.execute("CREATE INDEX idx_brand_name ON products(brand_name)")
    cursor.execute("CREATE INDEX idx_source ON products(source)")

    # Full-text search virtual table
    cursor.execute("""
        CREATE VIRTUAL TABLE products_fts USING fts5(
            product_name,
            brand_name,
            content='products',
            content_rowid='id'
        )
    """)

    # Trigger to keep FTS in sync
    cursor.execute("""
        CREATE TRIGGER products_fts_insert AFTER INSERT ON products
        BEGIN
            INSERT INTO products_fts(rowid, product_name, brand_name)
            VALUES (new.id, new.product_name, new.brand_name);
        END
    """)

    conn.commit()
    conn.close()

    print(f"✓ Database created: {DB_PATH}")
    print(f"  Size: {DB_PATH.stat().st_size} bytes")

if __name__ == "__main__":
    create_database()
```

**Step 2: Run script**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
python3 create_database.py
```

Expected output:
```
✓ Database created: /Volumes/.../data/products.db
  Size: 16384 bytes
```

**Step 3: Verify schema**

```bash
sqlite3 data/products.db ".schema"
```

Expected: Shows CREATE TABLE and CREATE INDEX statements

**Step 4: Commit**

```bash
git add create_database.py
git commit -m "feat: create SQLite products database schema"
```

---

### Task 6: Write California Chemicals Import Script

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/import_california.py`

**Step 1: Write import script**

```python
"""
Import California Chemicals in Cosmetics CSV into products database.
"""
import sqlite3
import csv
import json
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(__file__).parent / "data" / "products.db"
CSV_PATH = Path(__file__).parent / "data" / "raw" / "california_chemicals.csv"

def import_california_chemicals():
    """Import California Chemicals CSV."""

    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Group chemicals by product
    products = defaultdict(lambda: {
        'brand': None,
        'chemicals': [],
        'cas_numbers': []
    })

    print(f"Reading {CSV_PATH}...")
    with open(CSV_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Adjust column names based on actual CSV structure
            product_name = row.get('ProductName', row.get('Product Name', '')).strip()
            brand = row.get('BrandName', row.get('Brand Name', '')).strip()
            chemical = row.get('ChemicalName', row.get('Chemical Name', '')).strip()
            cas = row.get('CasNumber', row.get('CAS Number', '')).strip()

            if product_name and chemical:
                key = (product_name, brand)
                products[key]['brand'] = brand
                products[key]['chemicals'].append(chemical)
                if cas:
                    products[key]['cas_numbers'].append(cas)

    print(f"Found {len(products)} unique products")

    # Insert into database
    imported = 0
    for (product_name, brand), data in products.items():
        ingredients_list = data['chemicals']
        ingredients_text = ', '.join(ingredients_list)
        ingredients_json = json.dumps(ingredients_list)

        cursor.execute("""
            INSERT INTO products
            (source, product_name, brand_name, category,
             ingredients_text, ingredients_json, has_carcinogens)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'california_cosmetics',
            product_name,
            brand,
            'cosmetics',
            ingredients_text,
            ingredients_json,
            True  # All California chemicals are reported hazards
        ))

        imported += 1
        if imported % 1000 == 0:
            print(f"  Imported {imported} products...")
            conn.commit()

    conn.commit()
    conn.close()

    print(f"✓ Imported {imported} products from California database")

if __name__ == "__main__":
    import_california_chemicals()
```

**Step 2: Run import**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
python3 import_california.py
```

Expected output:
```
Reading data/raw/california_chemicals.csv...
Found 15000 unique products
  Imported 1000 products...
  Imported 2000 products...
  ...
✓ Imported 15000 products from California database
```

**Step 3: Verify import**

```bash
sqlite3 data/products.db "SELECT COUNT(*) FROM products WHERE source='california_cosmetics'"
```

Expected: Number matching import count

**Step 4: Test search**

```bash
sqlite3 data/products.db "SELECT product_name, brand_name FROM products WHERE product_name LIKE '%clorox%' LIMIT 5"
```

**Step 5: Commit**

```bash
git add import_california.py
git commit -m "feat: import California Chemicals data (15k products)"
```

---

### Task 7: Write Open Products Facts Import Script

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/import_open_products.py`

**Step 1: Write import script**

```python
"""
Import Open Products Facts CSV into products database.
"""
import sqlite3
import csv
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "products.db"
CSV_PATH = Path(__file__).parent / "data" / "raw" / "open_products_facts.csv"

def import_open_products():
    """Import Open Products Facts CSV."""

    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Reading {CSV_PATH}...")
    imported = 0
    skipped = 0

    with open(CSV_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f, delimiter='\t')

        for row in reader:
            # Extract fields (adjust based on actual column names)
            barcode = row.get('code', '').strip()
            product_name = row.get('product_name', '').strip()
            brands = row.get('brands', '').strip()
            ingredients_text = row.get('ingredients_text', '').strip()
            categories = row.get('categories', '').strip()
            image_url = row.get('image_url', '').strip()

            # Only import if we have product name and ingredients
            if not product_name or not ingredients_text:
                skipped += 1
                continue

            # Parse ingredients into list
            ingredients_list = [
                ing.strip()
                for ing in ingredients_text.split(',')
                if ing.strip()
            ]
            ingredients_json = json.dumps(ingredients_list)

            cursor.execute("""
                INSERT INTO products
                (source, barcode, product_name, brand_name, category,
                 ingredients_text, ingredients_json, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'open_products_facts',
                barcode,
                product_name,
                brands,
                'household',
                ingredients_text,
                ingredients_json,
                image_url
            ))

            imported += 1
            if imported % 1000 == 0:
                print(f"  Imported {imported} products (skipped {skipped})...")
                conn.commit()

    conn.commit()
    conn.close()

    print(f"✓ Imported {imported} products from Open Products Facts")
    print(f"  Skipped {skipped} products without ingredients")

if __name__ == "__main__":
    import_open_products()
```

**Step 2: Run import**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
python3 import_open_products.py
```

**Step 3: Verify**

```bash
sqlite3 data/products.db "SELECT COUNT(*) FROM products WHERE source='open_products_facts'"
sqlite3 data/products.db "SELECT product_name, brand_name FROM products WHERE product_name LIKE '%clorox%' AND source='open_products_facts' LIMIT 5"
```

**Step 4: Commit**

```bash
git add import_open_products.py
git commit -m "feat: import Open Products Facts data"
```

---

### Task 8: Write Open Beauty Facts Import Script

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/import_open_beauty.py`

**Step 1: Copy and adapt script**

Copy `import_open_products.py` → `import_open_beauty.py`

Modify:
- CSV_PATH to `open_beauty_facts.csv`
- source to `'open_beauty_facts'`
- category to `'cosmetics'`

**Step 2: Run import**

```bash
python3 import_open_beauty.py
```

**Step 3: Commit**

```bash
git add import_open_beauty.py
git commit -m "feat: import Open Beauty Facts data"
```

---

### Task 9: Create Unified Database Query Module

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/database_search.py`

**Step 1: Write search module**

```python
"""
SQLite product database search module.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from unified_database import ProductResult

DB_PATH = Path(__file__).parent / "data" / "products.db"

def search_products_by_name(query: str, limit: int = 5) -> List[ProductResult]:
    """
    Search products by name using fuzzy matching.

    Args:
        query: Product name or brand to search
        limit: Maximum results

    Returns:
        List of ProductResult objects
    """
    if not DB_PATH.exists():
        print(f"⚠ Database not found: {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Split query into keywords
    keywords = query.lower().split()

    # Build LIKE clauses for each keyword
    where_clauses = []
    params = []
    for keyword in keywords:
        where_clauses.append("(LOWER(product_name) LIKE ? OR LOWER(brand_name) LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where_sql = " AND ".join(where_clauses)

    # Query with fuzzy matching
    sql = f"""
        SELECT * FROM products
        WHERE {where_sql}
        AND ingredients_text IS NOT NULL
        ORDER BY
            CASE
                WHEN LOWER(product_name) = ? THEN 1
                WHEN LOWER(product_name) LIKE ? THEN 2
                ELSE 3
            END
        LIMIT ?
    """

    params.extend([query.lower(), f"%{query.lower()}%", limit])

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        ingredients_list = json.loads(row['ingredients_json']) if row['ingredients_json'] else []

        results.append(ProductResult(
            found=True,
            source=f"Local DB ({row['source']})",
            barcode=row['barcode'],
            name=row['product_name'],
            brand=row['brand_name'],
            ingredients_text=row['ingredients_text'],
            ingredients_list=ingredients_list,
            categories=row['category'],
            image_url=row['image_url'],
            raw_data=None
        ))

    conn.close()
    return results


def search_by_barcode(barcode: str) -> Optional[ProductResult]:
    """Look up product by exact barcode."""

    if not DB_PATH.exists():
        return None

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM products
        WHERE barcode = ?
        AND ingredients_text IS NOT NULL
        LIMIT 1
    """, (barcode,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    ingredients_list = json.loads(row['ingredients_json']) if row['ingredients_json'] else []

    return ProductResult(
        found=True,
        source=f"Local DB ({row['source']})",
        barcode=row['barcode'],
        name=row['product_name'],
        brand=row['brand_name'],
        ingredients_text=row['ingredients_text'],
        ingredients_list=ingredients_list,
        categories=row['category'],
        image_url=row['image_url'],
        raw_data=None
    )


def get_database_stats():
    """Get database statistics."""

    if not DB_PATH.exists():
        return {"error": "Database not found"}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT source, COUNT(*) FROM products GROUP BY source")
    stats = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(*) FROM products")
    stats['total'] = cursor.fetchone()[0]

    conn.close()
    return stats


if __name__ == "__main__":
    # Test searches
    print("Database Stats:")
    print(get_database_stats())

    print("\nSearching for 'clorox':")
    results = search_products_by_name("clorox")
    for r in results:
        print(f"  - {r.name} ({r.brand}): {len(r.ingredients_list)} ingredients")

    print("\nSearching for 'clorox disinfecting wipes':")
    results = search_products_by_name("clorox disinfecting wipes")
    for r in results:
        print(f"  - {r.name}: {r.ingredients_list[:3]}...")
```

**Step 2: Test search module**

```bash
python3 database_search.py
```

Expected output:
```
Database Stats:
{'california_cosmetics': 15000, 'open_products_facts': 5000, 'total': 20000}

Searching for 'clorox':
  - Clorox Disinfecting Wipes (Clorox): 10 ingredients
  - Clorox Regular Bleach (Clorox): 3 ingredients

Searching for 'clorox disinfecting wipes':
  - Clorox Disinfecting Wipes: ['Water', 'Hexoxyethanol', 'Isopropanol']...
```

**Step 3: Commit**

```bash
git add database_search.py
git commit -m "feat: add SQLite product search with fuzzy matching"
```

---

## PHASE 3: Backend Integration

### Task 10: Integrate Database Search into unified_database.py

**Files:**
- Modify: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/unified_database.py:358-374`

**Step 1: Add database import**

At top of `unified_database.py` after existing imports:

```python
# Import local database search
try:
    from database_search import search_products_by_name as search_local_db
    from database_search import search_by_barcode as search_local_barcode
    HAS_LOCAL_DB = True
except ImportError:
    HAS_LOCAL_DB = False
```

**Step 2: Modify unified_product_search function**

Replace lines 358-374 with:

```python
async def unified_product_search(query: str, limit: int = 5) -> List[ProductResult]:
    """
    Search ALL available databases for a product.
    Priority: Local SQLite DB → Open Facts APIs
    """
    results = []

    # PRIORITY 1: Search local database first
    if HAS_LOCAL_DB:
        try:
            local_results = search_local_db(query, limit=limit)
            if local_results:
                print(f"✓ Found {len(local_results)} results in local database")
                return local_results
        except Exception as e:
            print(f"⚠ Local DB search error: {e}")

    # PRIORITY 2: Fall back to API search
    results = await search_open_facts_all(query, limit)

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r.name:
            key = r.name.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(r)

    return unique[:limit]
```

**Step 3: Modify unified_barcode_lookup function**

Replace lines 377-379 with:

```python
async def unified_barcode_lookup(barcode: str) -> ProductResult:
    """Look up barcode across all databases."""

    # PRIORITY 1: Search local database first
    if HAS_LOCAL_DB:
        try:
            local_result = search_local_barcode(barcode)
            if local_result:
                print(f"✓ Found barcode in local database")
                return local_result
        except Exception as e:
            print(f"⚠ Local DB barcode error: {e}")

    # PRIORITY 2: Fall back to API lookup
    return await lookup_barcode_all(barcode)
```

**Step 4: Test integration**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
python3 -c "
import asyncio
from unified_database import unified_product_search

async def test():
    results = await unified_product_search('clorox disinfecting wipes')
    print(f'Found: {results[0].name}')
    print(f'Ingredients: {results[0].ingredients_list[:5]}')

asyncio.run(test())
"
```

Expected output:
```
✓ Found 1 results in local database
Found: Clorox Disinfecting Wipes
Ingredients: ['Water', 'Hexoxyethanol', 'Isopropanol', 'C12-14 Alcohols...', 'Alkyl C12-14...']
```

**Step 5: Commit**

```bash
git add unified_database.py
git commit -m "feat: prioritize local SQLite DB in product search"
```

---

### Task 11: Test End-to-End Clorox Scan

**Files:**
- Modify: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/backend/test_clorox_scan.py` (if exists)
- Or Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/test_complete_flow.py`

**Step 1: Write test script**

```python
"""
Test complete Clorox scan flow with local database.
"""
import asyncio
from serpapi_client import identify_product_from_image, LensResult
from unified_database import unified_product_search
from scoring import calculate_cancer_score

async def test_clorox_flow():
    """Test complete flow: Photo → Identify → Database → Score"""

    print("=" * 60)
    print("TESTING COMPLETE CLOROX SCAN FLOW")
    print("=" * 60)

    # Step 1: Simulate SerpAPI identification
    print("\n1. SerpAPI Identification (simulated)")
    product_name = "Clorox Disinfecting Wipes"
    brand = "Clorox"
    print(f"   Identified: {product_name}")
    print(f"   Brand: {brand}")

    # Step 2: Search local database
    print("\n2. Database Search")
    results = await unified_product_search(product_name, limit=1)

    if not results:
        print("   ❌ FAILED: No results found")
        return

    product = results[0]
    print(f"   ✓ Found: {product.name}")
    print(f"   Source: {product.source}")
    print(f"   Ingredients: {len(product.ingredients_list)} found")

    if not product.ingredients_list:
        print("   ❌ FAILED: No ingredients in result")
        return

    # Step 3: Calculate cancer score
    print("\n3. Cancer Score Calculation")
    score = calculate_cancer_score(product.ingredients_list)

    print(f"   Cancer Score: {score.cancer_score}/100")
    print(f"   Color: {score.color}")
    print(f"   Carcinogens: {score.carcinogen_count}")
    print(f"   Worst: {score.worst_ingredient}")

    # Step 4: Show ingredient breakdown
    print("\n4. Ingredient Breakdown (first 5)")
    for i, ing in enumerate(score.ingredient_breakdown[:5], 1):
        print(f"   {i}. {ing.name}")
        print(f"      Toxicity: {ing.toxicity_score}/10")
        print(f"      Concern: {ing.concern_level}")
        print(f"      Carcinogen: {ing.is_carcinogen}")

    print("\n" + "=" * 60)
    print("✓ COMPLETE FLOW SUCCESS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_clorox_flow())
```

**Step 2: Run test**

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD"
python3 test_complete_flow.py
```

Expected output:
```
============================================================
TESTING COMPLETE CLOROX SCAN FLOW
============================================================

1. SerpAPI Identification (simulated)
   Identified: Clorox Disinfecting Wipes
   Brand: Clorox

2. Database Search
✓ Found 1 results in local database
   ✓ Found: Clorox Disinfecting Wipes
   Source: Local DB (open_products_facts)
   Ingredients: 10 found

3. Cancer Score Calculation
   Cancer Score: 45/100
   Color: orange
   Carcinogens: 2
   Worst: Alkyl C12-14 Dimethylethylbenzyl Ammonium Chloride

4. Ingredient Breakdown (first 5)
   1. Water
      Toxicity: 0.5/10
      Concern: low
      Carcinogen: False
   2. Hexoxyethanol
      Toxicity: 4.0/10
      Concern: moderate
      Carcinogen: False
   ...

============================================================
✓ COMPLETE FLOW SUCCESS
============================================================
```

**Step 3: Commit**

```bash
git add test_complete_flow.py
git commit -m "test: verify complete Clorox scan with local DB"
```

---

## PHASE 4: OCR Fallback

### Task 12: Check SerpAPI Text Detection

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/test_serpapi_text.py`

**Step 1: Review SerpAPI response structure**

Check `serpapi_client.py` to see if `detected_text` or `text_results` are already captured.

**Step 2: Test SerpAPI text extraction**

```python
"""
Test if SerpAPI Google Lens returns text from images.
"""
import asyncio
from serpapi_client import identify_product_from_image

async def test_serpapi_text():
    # Use a real image URL with visible ingredients
    image_url = "https://cancer-detector-backend-production.up.railway.app/images/test.jpg"

    result = await identify_product_from_image(image_url)

    print("SerpAPI Result:")
    print(f"  Product: {result.product_name}")
    print(f"  Brand: {result.brand}")
    print(f"  Detected Text: {result.detected_text[:200] if result.detected_text else 'None'}")

    # Check if ingredients are in detected text
    if result.detected_text and "ingredients" in result.detected_text.lower():
        print("  ✓ SerpAPI can detect ingredient text!")
    else:
        print("  ❌ SerpAPI doesn't capture ingredient text - need OCR")

if __name__ == "__main__":
    asyncio.run(test_serpapi_text())
```

**Step 3: Run test**

```bash
python3 test_serpapi_text.py
```

**Step 4: Document findings**

Create `docs/ocr-strategy.md` based on results

**Step 5: Commit**

```bash
git add test_serpapi_text.py docs/ocr-strategy.md
git commit -m "test: evaluate SerpAPI text detection for OCR fallback"
```

---

### Task 13: Implement Tesseract OCR Fallback (If Needed)

**Files:**
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/ocr_extractor.py`

**Step 1: Install Tesseract**

```bash
# macOS
brew install tesseract

# Verify installation
tesseract --version
```

**Step 2: Install Python bindings**

```bash
pip install pytesseract Pillow
```

**Step 3: Write OCR extraction module**

```python
"""
OCR-based ingredient extraction fallback.
"""
import re
import pytesseract
from PIL import Image
import httpx
from typing import List, Optional

async def extract_ingredients_from_image(image_url: str) -> Optional[List[str]]:
    """
    Extract ingredients from product image using OCR.

    Args:
        image_url: Public URL of product image

    Returns:
        List of ingredient names or None
    """
    try:
        # Download image
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()

            # Save temporarily
            with open('/tmp/ocr_image.jpg', 'wb') as f:
                f.write(response.content)

        # Run OCR
        image = Image.open('/tmp/ocr_image.jpg')
        text = pytesseract.image_to_string(image)

        # Find ingredients section
        ingredients = _parse_ingredients_from_text(text)

        return ingredients if ingredients else None

    except Exception as e:
        print(f"OCR error: {e}")
        return None


def _parse_ingredients_from_text(text: str) -> Optional[List[str]]:
    """Parse ingredients from OCR text."""

    # Look for "Ingredients:" label
    ingredients_pattern = r"(?:Ingredients?|INGREDIENTS?)[:\s]+([^.]+)"
    match = re.search(ingredients_pattern, text, re.IGNORECASE)

    if not match:
        return None

    ingredients_text = match.group(1)

    # Split by commas
    ingredients = [
        ing.strip()
        for ing in ingredients_text.split(',')
        if ing.strip() and len(ing.strip()) > 2
    ]

    return ingredients if ingredients else None


if __name__ == "__main__":
    import asyncio

    async def test():
        # Test with image that has visible ingredients
        ingredients = await extract_ingredients_from_image(
            "https://example.com/product-with-ingredients.jpg"
        )
        print(f"Extracted: {ingredients}")

    asyncio.run(test())
```

**Step 4: Integrate into main.py scan endpoint**

In `main.py` photo scan endpoint, add fallback after database search fails:

```python
# Step 4: If no ingredients found, try OCR fallback
if not product_data or not product_data.ingredients_list:
    try:
        from ocr_extractor import extract_ingredients_from_image
        ocr_ingredients = await extract_ingredients_from_image(request.image_url)

        if ocr_ingredients:
            # Calculate score with OCR ingredients
            score_result = calculate_cancer_score(ocr_ingredients)

            return ScanResponse(
                success=True,
                product_name=lens_result.product_name or "Product",
                cancer_score=score_result.cancer_score,
                # ... rest of response
                scan_method="photo_ocr"
            )
    except Exception as e:
        print(f"OCR fallback failed: {e}")
```

**Step 5: Test OCR**

```bash
python3 ocr_extractor.py
```

**Step 6: Commit**

```bash
git add ocr_extractor.py
git commit -m "feat: add Tesseract OCR ingredient extraction fallback"
```

---

## PHASE 5: Deployment

### Task 14: Prepare Database for Railway

**Files:**
- Modify: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/.gitignore`
- Create: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/railway-upload.sh`

**Step 1: Check database size**

```bash
du -h data/products.db
```

If > 100MB, consider compression or PostgreSQL migration.

**Step 2: Create upload script**

```bash
#!/bin/bash
# Upload database to Railway using persistent storage

railway run python3 create_database.py
railway run python3 import_california.py
railway run python3 import_open_products.py
railway run python3 import_open_beauty.py
```

**Step 3: Add to git if small enough**

If database < 50MB:
```bash
git add data/products.db
git commit -m "data: add product ingredients database"
```

If larger, use Railway volumes.

**Step 4: Update requirements.txt**

```bash
echo "pytesseract==0.3.10" >> requirements.txt
echo "Pillow==10.0.0" >> requirements.txt
git add requirements.txt
git commit -m "deps: add OCR dependencies"
```

**Step 5: Deploy to Railway**

```bash
cd backend
railway up
```

**Step 6: Verify deployment**

```bash
curl https://cancer-detector-backend-production.up.railway.app/health
```

---

### Task 15: Final End-to-End Test from iOS

**Files:**
- Test from actual iOS app

**Step 1: Rebuild Flutter app**

```bash
cd flutter_app
flutter pub get
flutter build ios
```

**Step 2: Open in Xcode**

```bash
open ios/Runner.xcworkspace
```

**Step 3: Run on device**

Archive → Distribute → TestFlight

**Step 4: Test Clorox scan**

- Open app on device
- Take photo of Clorox Disinfecting Wipes
- Verify results show:
  * Product name: Clorox Disinfecting Wipes
  * 10 ingredients
  * Cancer score
  * Carcinogen warnings

**Step 5: Document success**

```bash
git commit --allow-empty -m "test: verified complete Clorox scan flow in production"
git tag v2.0-database-integration
git push origin main --tags
```

---

## Success Criteria Checklist

- [ ] California Chemicals CSV downloaded and imported
- [ ] Open Products Facts CSV downloaded and imported
- [ ] Open Beauty Facts CSV downloaded and imported
- [ ] SQLite database created with 20k+ products
- [ ] Product search by name works with fuzzy matching
- [ ] Barcode search works
- [ ] unified_database.py prioritizes local DB
- [ ] Clorox scan returns 10 real ingredients
- [ ] Cancer score calculated correctly
- [ ] OCR fallback implemented (if needed)
- [ ] Database deployed to Railway
- [ ] iOS app shows correct results

---

## Rollback Plan

If database integration fails:

1. Revert unified_database.py changes: `git checkout HEAD~1 unified_database.py`
2. Remove database imports from main.py
3. Redeploy backend: `railway up`
4. Original API-based search will continue working

---

## Notes

- Database file excluded from git if > 50MB (use `.gitignore`)
- Railway deployment may need persistent volumes for large databases
- Consider PostgreSQL migration if SQLite performance issues
- OCR fallback is optional - only if SerpAPI text detection insufficient
- Prioritize California + Open Products data - highest quality
- SmartLabel data is bonus if scraped version found
