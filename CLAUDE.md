# Cancer Detector v2.0

AI-powered product safety scanner for iOS that analyzes household products and provides instant cancer risk scores.

## Project Overview

**Version:** 3.0.0+1
**Status:** V3 Deployed - Ready for Production Testing
**Platform:** iOS (Flutter)
**Backend:** FastAPI V3.0.0 on Railway (Modular Prompts Architecture)
**AI Model:** Claude Sonnet 4 (claude-sonnet-4-20250514)

## Architecture

### Frontend: Flutter App
- **Language:** Dart
- **UI Framework:** Material Design 3 (Dark Theme)
- **Primary Color:** Purple (#8b5cf6)
- **Background:** Dark Blue (#0f172a)
- **Authentication:** Face ID / Touch ID via local_auth package
- **Storage:** Hive for local scan history
- **Networking:** HTTP package with multipart/form-data uploads

### Backend: FastAPI on Railway
- **URL:** https://cancer-detector-backend-production.up.railway.app
- **Framework:** FastAPI (Python)
- **AI Integration:** Anthropic Claude Vision API
- **Deployment:** Railway (automatic deploys from main branch)
- **Environment:** Python 3.11+

## Core Features

### 1. Product Scanning
- **Photo Capture:** Camera or gallery selection via image_picker
- **AI Analysis:** Claude Vision extracts product info, ingredients, and materials
- **No Barcode Required:** Visual identification of any household product

### 2. Safety Scoring System (V3)
- **Overall Score:** 0-100 (weighted: 95% ingredients + 5% condition)
- **Cookware Exception:** 85% ingredients + 15% condition (condition matters more)
- **Positive Bonuses:** +3 per "X-free" claim (max +15 total)
- **Letter Grades:** A+ through F
  - A+: 95-100 (Excellent)
  - A: 90-94 (Very Good)
  - A-: 85-89 (Good)
  - B+: 80-84 (Above Average)
  - F: 0-49 (Poor)

### 3. Product Analysis (V3)
- **6 Product Categories:** Food, Water, Cosmetics, Cookware, Cleaning, Supplements
- **Modular Prompts:** Category-specific analysis modules for specialized knowledge
- **Ingredient Analysis:** Against expanded toxicity database (296 ingredients)
- **Hazard Scoring:** Individual 0-10 hazard scores for each ingredient
- **Database Enrichment:** Uses HIGHER score (Claude vs Database) for conservative safety
- **Positive Attributes:** Recognition of "X-free" claims with bonus points
- **Condition Assessment:** Visual inspection for wear, damage, scratches (5% or 15% weight)
- **Personalized Notes:** Specific observations about photographed item

### 4. Results Display
- Safety grade with color-coded badge
- Flagged ingredients/materials with hazard levels
- Safe ingredients list
- Condition report with concerns
- Care tips for product longevity
- Safer alternative recommendations

## Technical Implementation

### API Integration

**Main Endpoint:** `POST /api/v1/scan`
```dart
// flutter_app/lib/services/api_service.dart

Future<ScanResult> scanImage(File imageFile) async {
  // Detect MIME type from file extension
  final mimeTypeString = lookupMimeType(imageFile.path) ?? 'image/jpeg';
  final mediaType = MediaType.parse(mimeTypeString);

  // Upload with explicit contentType
  request.files.add(await http.MultipartFile.fromPath(
    'image',
    imageFile.path,
    contentType: mediaType,
  ));
}
```

**Backend Processing:**
1. Validates image MIME type (image/jpeg, image/png, image/webp, image/gif)
2. Encodes image to base64
3. Sends to Claude Vision API with comprehensive prompt
4. Scores response against toxicity/material databases
5. Generates care tips and safer alternatives
6. Returns structured JSON response

### Data Models

**ScanResult** (flutter_app/lib/models/scan_result.dart)
```dart
class ScanResult {
  final bool success;
  final String? productName;
  final String? brand;
  final String? productType; // consumable | container | cookware | baby_item | other
  final List<String>? ingredients;
  final List<MaterialAnalysis>? materials;
  final ConditionData? condition;
  final int? safetyScore; // 0-100
  final int? conditionScore; // 0-100
  final int? overallScore; // 0-100
  final String? grade; // A+ | A | A- | ... | F
  final List<FlaggedIngredient>? flaggedIngredients;
  final List<CareTip>? careTips;
  final SaferAlternative? saferAlternative;
  // ... additional fields
}
```

### Databases

**TOXICITY_DATABASE** (backend/main.py)
- 103 ingredients across 14 categories
- Categories: carcinogen, endocrine_disruptor, respiratory_irritant, allergen, etc.
- Hazard scores: 1-10 (10 = most dangerous)

**MATERIAL_DATABASE** (backend/main.py)
- 18 materials: PET, HDPE, PVC, LDPE, PP, PS, PC, Teflon, Glass, etc.
- Safety scores: 0-100
- Concerns: microplastics, leaching, toxic fumes, BPA, etc.

## Recent Fixes

### MIME Type Detection Fix (Dec 1, 2025)
**Commit:** 57fb771

**Root Cause:**
- `MultipartFile.fromPath()` defaulted to `application/octet-stream`
- Backend rejected invalid content types
- Claude Vision API requires proper image MIME types

**Solution:**
1. Added `mime: ^1.0.4` package for MIME type detection
2. Added `http_parser: ^4.0.2` for MediaType parsing
3. Implemented `lookupMimeType()` to detect from file extension
4. Set `contentType` parameter explicitly in uploads
5. Fixed error handler to check both 'detail' (FastAPI) and 'error' fields

**Impact:** App now successfully uploads images and receives AI analysis

## Project Structure

```
CANCER DETECTOR VERSION 2 REBUILD/
├── backend/
│   ├── main.py                 # FastAPI backend v3.1.0
│   ├── requirements.txt        # Python dependencies
│   └── test_*.py               # Backend tests
├── flutter_app/
│   ├── lib/
│   │   ├── models/
│   │   │   └── scan_result.dart        # Data models
│   │   ├── screens/
│   │   │   ├── home_screen.dart        # Landing page
│   │   │   ├── scan_screen.dart        # Photo capture
│   │   │   ├── result_screen.dart      # Analysis display
│   │   │   └── history_screen.dart     # Past scans
│   │   ├── services/
│   │   │   └── api_service.dart        # Backend communication
│   │   └── main.dart                    # App entry point
│   ├── ios/
│   │   └── Runner.xcworkspace           # Xcode project
│   ├── pubspec.yaml                     # Flutter dependencies
│   └── README.md
├── main.py                     # Backend v3.1.0 (deployed)
├── CLAUDE.md                   # This file
└── README.md
```

## Dependencies

### Flutter (pubspec.yaml)
```yaml
dependencies:
  # UI
  flutter: sdk
  cupertino_icons: ^1.0.6
  google_fonts: ^6.1.0
  flutter_animate: ^4.3.0

  # Camera & Scanning
  camera: ^0.10.5+9
  mobile_scanner: ^3.5.5
  image_picker: ^1.0.7

  # HTTP & API
  http: ^1.2.0
  dio: ^5.4.0
  mime: ^1.0.4              # MIME type detection
  http_parser: ^4.0.2       # MediaType parsing

  # Storage
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  shared_preferences: ^2.2.2

  # Authentication
  local_auth: ^2.1.8

  # Utilities
  uuid: ^4.3.3
  intl: ^0.18.1
  connectivity_plus: ^5.0.2
```

### Backend (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
anthropic==0.42.0
python-multipart==0.0.6
pydantic==2.5.3
aiofiles==23.2.1
python-dotenv==1.0.0
pandas==2.1.4
```

## Environment Variables

### Backend (.env or Railway)
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...   # Required: Claude API key
PORT=8000                              # Optional: Server port
```

### Flutter
No environment variables required. API URL is hardcoded in `api_service.dart`:
```dart
static const String baseUrl = 'https://cancer-detector-backend-production.up.railway.app';
```

## Deployment

### Backend (Railway)
1. Connected to GitHub repository
2. Automatic deploys on push to main branch
3. Environment variables set in Railway dashboard
4. Buildpack: Python
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### iOS (TestFlight)
1. Open `flutter_app/ios/Runner.xcworkspace` in Xcode
2. Select **Product → Clean Build Folder** (⌘⇧K)
3. Select **Product → Build** (⌘B)
4. Select **Any iOS Device (arm64)** as target
5. Select **Product → Archive**
6. Distribute to App Store Connect for TestFlight

## Testing

### Manual Testing Checklist
- ✅ Photo capture from camera
- ✅ Photo selection from gallery
- ✅ Face ID authentication
- ✅ Scan consumables (food, cleaning products)
- ✅ Scan non-consumables (containers, cookware)
- ✅ Results display with grades
- ✅ Flagged ingredients/materials
- ✅ Care tips display
- ✅ Safer alternatives
- ✅ Scan history storage
- ✅ Error handling and messages

### Known Issues
- First scan may take 5-10 seconds (Claude API processing)
- Best results with clear, well-lit photos showing labels
- HEIC images automatically converted (iOS handles this)

## Future Improvements

### High Priority
- [ ] Add loading indicators during scan
- [ ] Implement retry mechanism for failed scans
- [ ] Add product search history
- [ ] Share results feature

### Medium Priority
- [ ] Offline mode with cached results
- [ ] User preferences for sensitivity levels
- [ ] Export scan reports as PDF
- [ ] Push notifications for recalled products

### Low Priority
- [ ] Dark/light theme toggle
- [ ] Multiple language support
- [ ] Barcode scanning as alternative
- [ ] Social features (share concerns)

## API Documentation

### Health Check
```http
GET /health
Response: { "status": "healthy", "version": "3.1.0", "claude_api": "connected" }
```

### Scan Product
```http
POST /api/v1/scan
Content-Type: multipart/form-data

Form Data:
  image: [File] (image/jpeg, image/png, image/webp, image/gif)

Response: {
  "success": true,
  "product_name": "Clorox Disinfecting Wipes",
  "brand": "Clorox",
  "product_type": "consumable",
  "ingredients": ["water", "sodium hypochlorite", ...],
  "safety_score": 45,
  "condition_score": 85,
  "overall_score": 57,
  "grade": "D+",
  "flagged_ingredients": [
    {
      "ingredient": "sodium hypochlorite",
      "hazard_score": 8,
      "category": "respiratory_irritant",
      "concerns": ["skin irritation", "respiratory issues"]
    }
  ],
  "care_tips": [...],
  "safer_alternative": {...}
}
```

### Lookup Ingredient
```http
GET /api/v1/ingredient/{name}
Response: { "name": "formaldehyde", "score": 10, "category": "carcinogen", ... }
```

### Database Stats
```http
GET /api/v1/database/stats
Response: { "total_ingredients": 103, "total_materials": 18, "categories": [...] }
```

## Development Workflow

### Starting Backend Locally
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Flutter App
```bash
cd flutter_app
flutter pub get
flutter run
# Or open in Xcode:
open ios/Runner.xcworkspace
```

### Testing API
```bash
# Health check
curl https://cancer-detector-backend-production.up.railway.app/health

# Scan image
curl -X POST https://cancer-detector-backend-production.up.railway.app/api/v1/scan \
  -F "image=@test_image.jpg"
```

## Troubleshooting

### "Invalid request" Error
**Cause:** Image content-type not set or invalid
**Solution:** Ensure using mime package with proper contentType parameter

### "Server error" 500
**Cause:** Claude API key missing or invalid
**Solution:** Check ANTHROPIC_API_KEY in Railway environment variables

### Face ID Not Working
**Cause:** Entitlements not configured
**Solution:** Check `Runner.entitlements` has Face ID usage description

### Build Fails in Xcode
**Cause:** Pods not installed
**Solution:** Run `cd ios && pod install`

## Contact & Support

**Developer:** Brandon Mills
**Repository:** Cancer Detector v2.0
**Backend:** https://cancer-detector-backend-production.up.railway.app
**Status:** Beta Testing Phase

---

*Last Updated: December 1, 2025*
*Version: 2.0.0+1*
*Backend: v3.1.0*
