# Quick Start: TestFlight Submission Checklist

## 🔴 DO THIS FIRST (One-Time Setup)

Fix Xcode path:
```bash
sudo xcode-select --switch "/Volumes/Super Mastery/Xcode.app/Contents/Developer"
sudo xcodebuild -runFirstLaunch
flutter doctor -v  # Verify Xcode shows green checkmark
```

## 📱 TestFlight Submission (5 Steps)

### 1. Open Xcode Workspace
```bash
open "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/Runner.xcworkspace"
```

### 2. Configure Signing
- Runner project → Signing & Capabilities
- ✅ Automatically manage signing
- Team: Brandon Mills
- Bundle ID: com.example.cancerDetector

### 3. Select Device
- Top left dropdown → "Any iOS Device (arm64)"

### 4. Archive
- Product → Archive
- Wait 3-5 minutes

### 5. Upload
- Distribute App → App Store Connect → Upload
- Wait 5-15 minutes

## ✅ Verify
- https://appstoreconnect.apple.com
- TestFlight tab → Check for Build 2
- Add to test group → Invite testers

## 🆘 If Build Fails

Clean and rebuild:
```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"
flutter clean
flutter pub get
cd ios
pod install
```

Then try archiving again in Xcode.

## 📊 Current Configuration

- Version: 3.0.0 (Build 2)
- Bundle ID: com.example.cancerDetector
- Min iOS: 13.0
- Backend: Railway Production

## 📖 Full Guide

See `TESTFLIGHT_DEPLOYMENT_GUIDE.md` for detailed instructions.
