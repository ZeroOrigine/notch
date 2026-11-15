#!/bin/bash
# Makes the Xcode project for Notch on iPhone/iPad and opens it.
cd "$(dirname "$0")"
LOG=ios_build_log.txt
echo "Started $(date)" > $LOG
if ! xcode-select -p 2>/dev/null | grep -q Xcode.app; then
  if [ -d /Applications/Xcode.app ]; then
    echo "Pointing tools to Xcode (asks for your Mac password)..."
    sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
  else
    echo "XCODE MISSING: install Xcode from the App Store first." | tee -a $LOG; read -p "Press Enter"; exit 1
  fi
fi
XG=xcodegen
if ! command -v xcodegen >/dev/null; then
  if [ ! -x ./tools/xcodegen/bin/xcodegen ]; then
    echo "Downloading XcodeGen..." | tee -a $LOG
    mkdir -p tools && curl -L -o tools/xg.zip https://github.com/yonaskolb/XcodeGen/releases/latest/download/xcodegen.zip >> $LOG 2>&1
    (cd tools && unzip -oq xg.zip) >> $LOG 2>&1
  fi
  XG=./tools/xcodegen/bin/xcodegen
fi
$XG generate >> $LOG 2>&1 || { echo "PROJECT FAILED" | tee -a $LOG; exit 1; }
echo "Checking the code compiles..." | tee -a $LOG
xcodebuild -project NotchiOS.xcodeproj -scheme Notch -destination 'generic/platform=iOS Simulator' -quiet build CODE_SIGNING_ALLOWED=NO > ios_errors.txt 2>&1
if grep -q "error:" ios_errors.txt; then echo "BUILD FAILED - see ios_errors.txt" | tee -a $LOG; else echo "BUILD OK" | tee -a $LOG; fi
open NotchiOS.xcodeproj
