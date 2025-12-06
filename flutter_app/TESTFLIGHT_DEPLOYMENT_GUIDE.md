# TrueCancer V4 TestFlight Deployment Guide

**Version:** 3.0.0 (Build 2)
**Date:** December 5, 2025
**Prepared By:** DevOps Engineer

---

## ✅ PRE-DEPLOYMENT CHECKLIST (COMPLETED)

All preparation work has been completed:

- [x] Flutter environment verified (v3.35.7)
- [x] Project cleaned (`flutter clean`)
- [x] Dependencies installed (`flutter pub get`)
- [x] Version incremented to 3.0.0+2 in `pubspec.yaml`
- [x] CocoaPods dependencies installed
- [x] App icons verified (all sizes present)
- [x] Permissions configured in Info.plist
- [x] Backend API URL confirmed (Railway production)

---

## 🚨 CRITICAL STEP: FIX XCODE CONFIGURATION

**Before you can build for iOS, you MUST fix the Xcode path.**

### Current Issue
Xcode is installed at: `/Volumes/Super Mastery/Xcode.app`
But the system is pointing to: `/Library/Developer/CommandLineTools`

### Fix Command
Open Terminal and run:

```bash
sudo xcode-select --switch "/Volumes/Super Mastery/Xcode.app/Contents/Developer"
```

You'll be prompted for your password. After entering it, run:

```bash
sudo xcodebuild -runFirstLaunch
```

### Verify the Fix
Run this command to confirm:

```bash
flutter doctor -v
```

You should now see a green checkmark [✓] next to "Xcode - develop for iOS and macOS"

---

## 📱 STEP-BY-STEP TESTFLIGHT SUBMISSION

### Step 1: Open Xcode Workspace

**IMPORTANT:** Always open the `.xcworkspace` file, NOT the `.xcodeproj` file!

```bash
open "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/Runner.xcworkspace"
```

Or manually navigate to:
- Path: `/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/`
- Double-click: `Runner.xcworkspace`

---

### Step 2: Configure Signing & Capabilities

1. **Select the Runner Project**
   - In the left sidebar (Project Navigator), click on the blue "Runner" icon at the top

2. **Select the Runner Target**
   - Under "TARGETS" in the middle pane, select "Runner"

3. **Go to Signing & Capabilities Tab**
   - Click the "Signing & Capabilities" tab at the top

4. **Configure Signing**
   - ✅ Check "Automatically manage signing"
   - Team: Select "Brandon Mills" (or your Apple Developer team)
   - Bundle Identifier: Should show `com.example.cancerDetector`

   **⚠️ IMPORTANT:** If this is your first time deploying to TestFlight, you may need to update the bundle identifier to match your App Store Connect app. Check App Store Connect for the correct bundle ID.

5. **Verify Provisioning Profile**
   - Status should show: "Xcode Managed Profile"
   - If you see errors, click "Download Manual Profiles" in Xcode Preferences > Accounts

---

### Step 3: Select Build Target

At the top left of Xcode, next to the Play/Stop buttons:

1. Click on the device selector dropdown
2. Select: **"Any iOS Device (arm64)"**

**DO NOT select a simulator** - TestFlight requires a real device build!

---

### Step 4: Archive the Build

1. **Start the Archive**
   - Menu Bar → Product → Archive
   - Or press: `⌘ + B` to build first, then Product → Archive

2. **Wait for Build to Complete**
   - This typically takes 3-5 minutes
   - You'll see build progress in the top center of Xcode
   - Do NOT interrupt the process

3. **Build Success**
   - When complete, the Organizer window will open automatically
   - You should see your archive listed with:
     - App name: "cancer_detector"
     - Version: 3.0.0 (2)
     - Date/Time of archive

---

### Step 5: Distribute to App Store Connect

In the Organizer window that opened:

1. **Select Your Archive**
   - Click on the archive you just created (should be at the top)

2. **Click "Distribute App"**
   - Blue button on the right side

3. **Select Distribution Method**
   - Choose: **"App Store Connect"**
   - Click "Next"

4. **Select Destination**
   - Choose: **"Upload"**
   - Click "Next"

5. **Distribution Options**
   - App Thinning: None (default)
   - Rebuild from Bitcode: ✅ (checked)
   - Include symbols: ✅ (checked)
   - Click "Next"

6. **Re-sign the App**
   - Automatically manage signing: ✅ (checked)
   - Click "Next"

7. **Review Info.plist**
   - Xcode will show you the app information
   - Verify:
     - Bundle ID: com.example.cancerDetector
     - Version: 3.0.0
     - Build: 2
   - Click "Upload"

8. **Wait for Upload**
   - This takes 5-15 minutes depending on internet speed
   - You'll see a progress bar
   - When complete, you'll see "Upload Successful"

---

### Step 6: Verify in App Store Connect

1. **Go to App Store Connect**
   - Open: https://appstoreconnect.apple.com
   - Sign in with your Apple Developer account

2. **Navigate to Your App**
   - Click "My Apps"
   - Select your app (or create a new app if this is first time)

3. **Go to TestFlight Tab**
   - Click the "TestFlight" tab at the top

4. **Check Build Status**
   - Under "iOS Builds", look for Build 2
   - Initial status: "Processing" (this takes 5-15 minutes)
   - Wait for status to change to: "Ready to Submit" or "Ready to Test"

5. **Add to Test Group**
   - Once processing is complete
   - Click on your build
   - Click "Groups" section
   - Add to "App Store Connect Users" or create a new internal test group

6. **Add Testers**
   - In the test group, click "Testers"
   - Click the "+" button
   - Add email addresses of testers (including yourself!)
   - Save

7. **Send Invitations**
   - Testers will receive an email with TestFlight download link
   - They can install the app via TestFlight app

---

## 🔧 TROUBLESHOOTING COMMON ISSUES

### Issue: "No such module 'Flutter'"

**Solution:**
```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios"
pod deintegrate
pod install
```

Then restart Xcode.

---

### Issue: "Signing for 'Runner' requires a development team"

**Solution:**
1. Xcode → Preferences (⌘ + ,)
2. Accounts tab
3. Click your Apple ID
4. Click "Download Manual Profiles"
5. Try archiving again

---

### Issue: "Application not configured for iOS"

**Solution:**
This is usually because Xcode path is not set correctly. Run:

```bash
sudo xcode-select --switch "/Volumes/Super Mastery/Xcode.app/Contents/Developer"
sudo xcodebuild -runFirstLaunch
```

Then try again.

---

### Issue: "Build failed" with errors

**Solution:**
1. Clean the build folder:
   - Xcode → Product → Clean Build Folder (⌘ + Shift + K)

2. Clean Flutter:
```bash
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"
flutter clean
flutter pub get
cd ios
pod install
```

3. Restart Xcode and try again

---

### Issue: "Provisioning profile doesn't include signing certificate"

**Solution:**
1. Xcode → Preferences → Accounts
2. Select your Apple ID
3. Select your team
4. Click "Download Manual Profiles"
5. Wait for profiles to download
6. Try archiving again

---

### Issue: "Archive is invalid - Version must be incremented"

**Solution:**
Open `pubspec.yaml` and increment the build number:

```yaml
version: 3.0.0+3  # Increment the number after the +
```

Then run:
```bash
flutter clean
flutter pub get
```

And archive again in Xcode.

---

## 📋 POST-UPLOAD CHECKLIST

After uploading to TestFlight:

- [ ] Build appears in App Store Connect
- [ ] Status changes from "Processing" to "Ready to Test"
- [ ] Build added to internal testing group
- [ ] Testers added and invitations sent
- [ ] Testers receive email with TestFlight link
- [ ] Confirm testers can install and launch app
- [ ] Test critical features:
  - [ ] Barcode scanning works
  - [ ] Photo upload works
  - [ ] API calls to backend succeed
  - [ ] Results display correctly
  - [ ] No crashes on startup

---

## 🎯 APP INFORMATION

**Bundle Identifier:** com.example.cancerDetector
**App Display Name:** Cancer Detector
**Version:** 3.0.0
**Build Number:** 2
**Minimum iOS Version:** 13.0
**Backend API:** https://cancer-detector-backend-production.up.railway.app

**Permissions Required:**
- Camera (for scanning)
- Photo Library (for selecting images)
- Face ID / Touch ID (for security)

---

## 📊 BUILD VERIFICATION

All pre-flight checks passed:

✅ **Flutter Doctor Status:**
```
Flutter version: 3.35.7
Dart version: 3.9.2
CocoaPods version: 1.16.2
```

✅ **Dependencies Installed:**
- 23 total pods installed
- All Flutter packages resolved
- No dependency conflicts

✅ **App Configuration:**
- App icons: Present (all sizes)
- Launch screen: Configured
- Info.plist: All permissions set
- API endpoint: Production Railway

✅ **Code Quality:**
- No debug prints in release mode
- All assets bundled
- Production API URL configured

---

## 🆘 NEED HELP?

If you encounter issues not covered in this guide:

1. **Check Xcode Console**
   - View → Debug Area → Show Debug Area
   - Look for red error messages

2. **Check Flutter Logs**
   ```bash
   cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"
   flutter analyze
   ```

3. **Verify Xcode Version**
   ```bash
   xcodebuild -version
   ```

4. **Re-run Flutter Doctor**
   ```bash
   flutter doctor -v
   ```

---

## 🚀 NEXT STEPS AFTER TESTFLIGHT

Once testers confirm the app works:

1. **Prepare App Store Submission**
   - Create app listing in App Store Connect
   - Add screenshots
   - Write app description
   - Set pricing
   - Fill out compliance forms

2. **Submit for Review**
   - Select the TestFlight build
   - Submit for App Store review
   - Wait for approval (typically 1-3 days)

3. **Release!**
   - Once approved, release to App Store
   - Monitor for crashes and user feedback

---

**Good luck with your TestFlight submission! 🎉**
