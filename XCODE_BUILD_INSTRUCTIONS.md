# Quick Guide: Building iOS App with Xcode

## Prerequisites

### 1. Install Xcode (First Time Only)
1. Open **App Store** on your Mac
2. Search for **"Xcode"**
3. Click **Get** (15GB+ download, may take 30+ minutes)
4. Once installed, open Xcode and accept license agreement

### 2. Configure Xcode Command Line Tools
```bash
# Point xcode-select to full Xcode installation
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer

# Run first-time setup
sudo xcodebuild -runFirstLaunch

# Verify installation
xcodebuild -version
```

Expected output:
```
Xcode 15.x
Build version 15Xxx
```

### 3. Verify Flutter Configuration
```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"
flutter doctor -v
```

You should see:
```
✓ Flutter
✓ Xcode (now with checkmark)
✓ CocoaPods
```

---

## Building the App

### Method 1: Flutter Build (Easiest for Testing)

```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"

# Build release version for iOS
flutter build ios --release --no-codesign
```

Build will take 3-5 minutes. Output:
```
Built /path/to/build/ios/iphoneos/Runner.app
```

**Note:** `--no-codesign` skips code signing for now. You'll sign it in Xcode before installing on device.

---

### Method 2: Xcode Archive (For App Store Submission)

#### Step 1: Open Project in Xcode
```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"
open ios/Runner.xcworkspace
```

**Important:** Always open `.xcworkspace`, NOT `.xcodeproj`

#### Step 2: Configure Code Signing
1. In Xcode, select **Runner** project in left sidebar
2. Select **Runner** target
3. Go to **Signing & Capabilities** tab
4. Check **"Automatically manage signing"**
5. Select your **Team** (Apple ID)
   - If no team, click "Add Account" and sign in with Apple ID
   - Free accounts work for testing (7-day installs)

#### Step 3: Select Build Target
1. In Xcode toolbar, click the device dropdown (next to Run button)
2. Select **"Any iOS Device (arm64)"**
   - Do NOT select a simulator
   - This creates a build for real devices

#### Step 4: Clean and Build
1. **Product → Clean Build Folder** (⌘⇧K)
2. Wait for cleaning to complete
3. **Product → Archive**
4. Wait 5-10 minutes for archive to build

#### Step 5: Export Archive
1. When build completes, Organizer window opens automatically
2. Select your archive from the list
3. Click **"Distribute App"**
4. Choose **"Development"** (for personal device testing)
5. Click **"Next"** through the wizard
6. Choose signing options (usually automatic)
7. Click **"Export"**
8. Save the .ipa file to a location you remember

---

## Installing on Your iPhone/iPad

### Prerequisites
- iPhone/iPad with iOS 13.0 or later
- USB cable to connect device to Mac
- Device must be registered in your Apple Developer account

### Method 1: Via Xcode Devices Window

1. **Connect your device** via USB cable
2. **Unlock your device** and trust the computer if prompted
3. In Xcode: **Window → Devices and Simulators** (⌘⇧2)
4. Select your device from left sidebar
5. In the "Installed Apps" section, click the **+** button
6. Navigate to `build/ios/iphoneos/Runner.app`
7. Click **Open** to install

### Method 2: Via Finder (macOS Catalina+)

1. Connect device via USB
2. Open **Finder**
3. Select your device in sidebar
4. Drag the `Runner.app` to the device window
5. Wait for installation to complete

### Method 3: Via Xcode Run (Simplest)

1. Connect device via USB
2. In Xcode, select your device from the device dropdown
3. Click the **Run** button (▶️) or press ⌘R
4. App will build and install automatically
5. Launch app on device

---

## Trusting the App (Required for Free Accounts)

After installation, the app won't open immediately. You need to trust the developer certificate:

1. On your iOS device, open **Settings**
2. Go to **General → VPN & Device Management**
3. Under "Developer App", tap your Apple ID
4. Tap **"Trust [Your Apple ID]"**
5. Confirm by tapping **"Trust"**
6. Now you can open the app

**Note:** Apps installed with free accounts expire after 7 days and need to be reinstalled.

---

## Troubleshooting

### "Unable to install app"
**Cause:** Device not registered or provisioning issue
**Fix:**
1. Connect device to Mac
2. In Xcode: Window → Devices and Simulators
3. Ensure device appears and shows "Connected"
4. Try installing again

### "Code signing error"
**Cause:** No team selected or certificate issue
**Fix:**
1. Xcode → Preferences → Accounts
2. Add your Apple ID if not present
3. Select your team in Signing & Capabilities
4. Click "Download Manual Profiles" if needed

### "Build failed with error"
**Cause:** Various compilation issues
**Fix:**
```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"
flutter clean
cd ios
pod deintegrate
pod install
cd ..
flutter build ios --release --no-codesign
```

### App crashes on launch
**Cause:** Permissions not configured or backend unreachable
**Fix:**
1. Check device has internet connection
2. Grant camera and photo library permissions
3. Check console logs in Xcode for errors

### "Could not find developer disk image"
**Cause:** Xcode version too old for your iOS version
**Fix:**
1. Update Xcode to latest version
2. Download iOS support files for your iOS version
3. Restart Xcode and try again

---

## Quick Reference Commands

```bash
# Navigate to project
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"

# Clean build
flutter clean

# Install dependencies
flutter pub get

# Install iOS pods
cd ios && pod install && cd ..

# Build for iOS
flutter build ios --release --no-codesign

# Open in Xcode
open ios/Runner.xcworkspace

# Check Flutter status
flutter doctor -v
```

---

## Testing the App

Once installed, test these features:

### Basic Functionality
1. **Launch app** - Should show home screen
2. **Grant permissions** - Camera and photos
3. **Scan barcode** - Point at product barcode
4. **Take photo** - Capture ingredient label
5. **View results** - Check toxicity scores
6. **View history** - See past scans

### V3 Features to Verify
1. **Ingredient list** displays with toxicity scores
2. **Health concerns** section shows relevant warnings
3. **Top toxic ingredients** highlighted
4. **Product score** calculation accurate
5. **Carcinogenic flags** appear when present
6. **Recommendations** provided based on analysis

### Backend Connectivity
- App should connect to: `https://cancer-detector-backend-production.up.railway.app`
- Check network status indicator
- Try with WiFi and cellular data
- Test offline handling

---

## Upgrading to Paid Developer Account

If you want longer-lasting installs and App Store distribution:

1. Visit https://developer.apple.com/programs/
2. Click **"Enroll"**
3. Pay $99/year
4. Complete enrollment (may take 24-48 hours)
5. Benefits:
   - 1-year app installs (not 7 days)
   - TestFlight for beta testing
   - App Store distribution
   - 100 TestFlight testers
   - Advanced app capabilities

---

## Next Steps After Installation

1. **Test all features** thoroughly on device
2. **Check performance** (should be smooth 60fps)
3. **Verify backend** responses are correct
4. **Test edge cases** (no internet, invalid images, etc.)
5. **Get feedback** from test users
6. **Fix any issues** discovered
7. **Prepare for App Store** submission (if desired)

---

## App Store Submission (Optional)

When ready to publish:

1. Create app in App Store Connect
2. Fill in app metadata (description, screenshots, etc.)
3. Create archive in Xcode (Product → Archive)
4. Upload to App Store Connect
5. Submit for review
6. Typical review time: 1-3 days
7. Once approved, app goes live on App Store

---

## Support Resources

- **Flutter Docs:** https://docs.flutter.dev/deployment/ios
- **Xcode Help:** https://developer.apple.com/xcode/
- **App Store Connect:** https://appstoreconnect.apple.com/
- **Apple Developer Forums:** https://developer.apple.com/forums/

---

**App Version:** 3.0.0+1
**Backend:** https://cancer-detector-backend-production.up.railway.app
**API Version:** V3 (Modular Prompts)
**Last Updated:** December 5, 2025
