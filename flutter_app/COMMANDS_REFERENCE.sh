#!/bin/bash

# =============================================================================
# TRUECANCER V4 - TESTFLIGHT DEPLOYMENT COMMANDS REFERENCE
# =============================================================================
# This file contains all commands you might need for TestFlight deployment.
# Copy and paste these commands into Terminal as needed.
# =============================================================================

# -----------------------------------------------------------------------------
# CRITICAL: FIX XCODE PATH (DO THIS FIRST!)
# -----------------------------------------------------------------------------

# Set Xcode developer directory
sudo xcode-select --switch "/Volumes/Super Mastery/Xcode.app/Contents/Developer"

# Run Xcode first launch
sudo xcodebuild -runFirstLaunch

# Verify Xcode is properly configured
flutter doctor -v

# Check Xcode version
xcodebuild -version

# -----------------------------------------------------------------------------
# OPEN XCODE WORKSPACE
# -----------------------------------------------------------------------------

# Open the correct workspace (NOT the .xcodeproj!)
open "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/Runner.xcworkspace"

# -----------------------------------------------------------------------------
# FLUTTER COMMANDS (If you need to rebuild)
# -----------------------------------------------------------------------------

# Navigate to project
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"

# Clean project
flutter clean

# Get dependencies
flutter pub get

# Check for issues
flutter analyze

# Check Flutter doctor
flutter doctor -v

# -----------------------------------------------------------------------------
# COCOAPODS COMMANDS (If you need to reinstall dependencies)
# -----------------------------------------------------------------------------

# Navigate to iOS directory
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios"

# Deintegrate CocoaPods (clean slate)
pod deintegrate

# Install CocoaPods dependencies
pod install

# Update CocoaPods
pod update

# Go back to project root
cd ..

# -----------------------------------------------------------------------------
# VERIFY BUILD CONFIGURATION
# -----------------------------------------------------------------------------

# Check Flutter build configuration
cat "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/Flutter/Generated.xcconfig"

# Check pubspec version
cat "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/pubspec.yaml" | grep version

# Check bundle identifier
grep -A 2 "PRODUCT_BUNDLE_IDENTIFIER" "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/Runner.xcodeproj/project.pbxproj" | head -5

# -----------------------------------------------------------------------------
# TROUBLESHOOTING: COMPLETE REBUILD
# -----------------------------------------------------------------------------

# If everything is broken, run this sequence:
cd "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app"
flutter clean
rm -rf ios/Pods
rm -rf ios/.symlinks
rm ios/Podfile.lock
flutter pub get
cd ios
pod install
cd ..
flutter doctor -v

# Then open Xcode and try archiving again

# -----------------------------------------------------------------------------
# VIEW DOCUMENTATION
# -----------------------------------------------------------------------------

# Open deployment guide in default text editor
open "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/BRANDON_START_HERE.md"

# View deployment summary
cat "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/DEPLOYMENT_SUMMARY.txt"

# Open full guide
open "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/TESTFLIGHT_DEPLOYMENT_GUIDE.md"

# -----------------------------------------------------------------------------
# CHECK APP ASSETS
# -----------------------------------------------------------------------------

# List app icons
ls -lh "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/Runner/Assets.xcassets/AppIcon.appiconset"

# Check Info.plist
cat "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/ios/Runner/Info.plist"

# Check API endpoint
grep -r "baseUrl" "/Volumes/Super Mastery/CANCER DETECTOR VERSION 2 REBUILD/flutter_app/lib" --include="*.dart"

# -----------------------------------------------------------------------------
# VERSION MANAGEMENT
# -----------------------------------------------------------------------------

# To increment build number, edit pubspec.yaml:
# Change: version: 3.0.0+2
# To:     version: 3.0.0+3 (increment the number after +)
# Then run: flutter clean && flutter pub get

# -----------------------------------------------------------------------------
# APP STORE CONNECT
# -----------------------------------------------------------------------------

# Open App Store Connect in browser:
# https://appstoreconnect.apple.com

# TestFlight direct link (after login):
# https://appstoreconnect.apple.com/apps/{YOUR_APP_ID}/testflight

# =============================================================================
# END OF COMMANDS REFERENCE
# =============================================================================
