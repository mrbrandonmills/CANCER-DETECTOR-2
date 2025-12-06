# 🚀 Xcode Archive Instructions for TestFlight

## ⚠️ CRITICAL: Fix Xcode Path First

**Run this command in Terminal:**
```bash
sudo xcode-select --switch "/Volumes/Super Mastery/Xcode.app/Contents/Developer"
```

**Why**: Xcode is currently pointing to CommandLineTools instead of the full Xcode.app installation on your external drive.

---

## 📱 Archive & Upload Steps

### Step 1: Verify Xcode Path
After running the sudo command above, verify:
```bash
xcode-select -p
```
**Expected output**: `/Volumes/Super Mastery/Xcode.app/Contents/Developer`

---

### Step 2: Open Workspace (ALREADY OPEN)
The workspace is already open:
`/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/Runner.xcworkspace`

---

### Step 3: Select Build Target
In Xcode toolbar (top):
1. Click the device dropdown next to the Run/Stop buttons
2. Select **"Any iOS Device (arm64)"**

![Device Selection](https://docs-assets.developer.apple.com/published/b2e39da03b/rendered2x-1660075743.png)

---

### Step 4: Clean Build (Optional but Recommended)
**Product → Clean Build Folder** (or press ⌘+Shift+K)

---

### Step 5: Archive
**Product → Archive** (or press ⌘+Shift+B)

**What happens:**
- Xcode compiles in Release mode
- Creates archive with embedded provisioning
- Takes 2-5 minutes
- Progress shown in top toolbar

**Watch for:**
- ✅ Build succeeds (green checkmark)
- ✅ Archive Organizer opens automatically
- ❌ Build fails → Check error messages

---

### Step 6: Distribute to App Store Connect

When Archive Organizer opens:

1. **Select your archive** (should be top item)
   - Version: 4.0.0
   - Build: 1
   - Date: Today

2. **Click "Distribute App"** (blue button on right)

3. **Choose distribution method:**
   - Select: **"App Store Connect"**
   - Click: **Next**

4. **Upload or Export:**
   - Select: **"Upload"**
   - Click: **Next**

5. **Distribution options:**
   - ✅ Include bitcode for iOS content: **YES**
   - ✅ Upload your app's symbols: **YES**
   - Click: **Next**

6. **Automatic signing:**
   - Xcode will manage signing automatically
   - Click: **Next**

7. **Review contents:**
   - Verify: Version 4.0.0, Build 1
   - Verify: No warnings
   - Click: **Upload**

8. **Wait for upload:**
   - Progress bar shown
   - Takes 1-3 minutes
   - Success message appears

---

## ✅ After Upload

### In App Store Connect:
1. Go to https://appstoreconnect.apple.com
2. Select **"Cancer Detector"** app
3. Go to **TestFlight** tab
4. Wait 5-10 minutes for processing
5. Build will appear under **"iOS Builds"**
6. Add to **Internal Testing** or **External Testing**
7. Submit for beta review (if external)

---

## 🐛 Common Issues

### Issue: "No accounts with App Store Connect access"
**Fix**:
- Xcode → Settings → Accounts
- Add Apple ID with App Store Connect access
- Sign in and grant access

### Issue: "Provisioning profile doesn't match"
**Fix**:
- Signing & Capabilities tab in Xcode
- Uncheck "Automatically manage signing"
- Then re-check it
- Let Xcode recreate profiles

### Issue: "Archive is missing"
**Fix**:
- Make sure you selected "Any iOS Device (arm64)"
- If you select simulator, Archive option is disabled
- Clean build and try again

### Issue: "Build failed"
**Fix**:
- Read error messages carefully
- Common: Missing provisioning, wrong bundle ID
- Check: Signing & Capabilities tab for red errors

---

## 📊 Current App Configuration

**Bundle Identifier**: `com.yourdomain.cancerdetector` (verify in Xcode)
**Version**: 4.0.0
**Build**: 1
**Deployment Target**: iOS 14.0+
**Signing**: Automatic (managed by Xcode)

---

## 🎯 What Happens After Upload

1. **Processing** (5-10 minutes)
   - Apple validates the build
   - Symbols uploaded
   - dSYM files processed

2. **Build appears in TestFlight** (10-30 minutes)
   - Status: "Processing" → "Ready to Submit"
   - Can add internal testers immediately
   - External testers need beta review

3. **Internal Testing** (immediate)
   - Up to 100 internal testers
   - No review required
   - Install via TestFlight app
   - Instant updates

4. **External Testing** (1-2 day review)
   - Up to 10,000 external testers
   - Requires beta app review
   - Public link available
   - Feedback collection

---

## 🚀 V4 Features to Test

Once in TestFlight, verify:

1. **Scan a product** (use Cheez-Its or similar)
2. **Check tier capping**:
   - D-grade ingredients → score ≤49 ✅
   - F-grade ingredients → score ≤29 ✅

3. **Verify processing alerts**:
   - Ultra-processed foods show "🏭 ULTRA-PROCESSED" ✅

4. **Check hidden truths**:
   - Expandable cards for harmful ingredients ✅

5. **Corporate disclosure**:
   - Shows ownership (e.g., "Owned by Kellogg's") ✅

6. **Deep Research button**:
   - Shows "Premium feature coming soon" snackbar ✅

---

## 📝 Notes

- **First archive may take longer** (5-10 minutes)
- **Upload requires good internet** (50MB+ file)
- **Processing is automatic** (no action needed)
- **TestFlight link** generated after processing
- **100% test pass rate** before this build ✅

---

## 🆘 If You Get Stuck

**Check these in order:**
1. Xcode path fixed? (`xcode-select -p`)
2. Device target correct? (Any iOS Device, not simulator)
3. Signing configured? (Signing & Capabilities tab)
4. Apple ID added? (Xcode → Settings → Accounts)
5. Clean build? (Product → Clean Build Folder)

**Still stuck?**
- Screenshot the error
- Check error message carefully
- Most issues are signing-related

---

## ✅ Success Checklist

- [ ] Xcode path fixed (`sudo xcode-select --switch ...`)
- [ ] Workspace opened
- [ ] Device target: "Any iOS Device (arm64)"
- [ ] Archive created successfully
- [ ] Upload to App Store Connect completed
- [ ] Build appears in App Store Connect
- [ ] TestFlight processing complete
- [ ] Internal testing ready
- [ ] V4 features validated in TestFlight

---

**You're ready! Fix the Xcode path, then archive and upload.**

**All backend bugs fixed. All tests passing. Version 4.0.0 build 1 ready for the world! 🚀**
