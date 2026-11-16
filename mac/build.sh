#!/bin/zsh
# Builds "NoTcH OS.app" next to this script. Needs Xcode Command Line Tools (xcode-select --install).
# 1) runs unit tests, 2) builds for Apple chips and Intel, 3) joins them into one universal app.
cd "$(dirname "$0")"
SRC=(Notch.swift Features.swift Settings.swift MainWindow.swift Core.swift Tools.swift Brains.swift Insight.swift)
: > build_errors.txt

echo "▸ Running tests…"
swiftc -parse-as-library -swift-version 5 Core.swift tests/CoreTests.swift -o core_tests 2>> build_errors.txt && ./core_tests > test_results.txt 2>&1
TEST_OK=$?
cat test_results.txt
if [ $TEST_OK -ne 0 ]; then echo "✗ Tests failed. See test_results.txt / build_errors.txt"; exit 1; fi

echo "▸ Compiling Notch (Apple chips)…"
swiftc -O -parse-as-library -swift-version 5 -target arm64-apple-macos13.0 $SRC -o Notch_arm64 2>> build_errors.txt || { grep -E "error" build_errors.txt | head -40; echo "✗ Build failed (arm64)"; exit 1; }
echo "▸ Compiling Notch (Intel)…"
swiftc -O -parse-as-library -swift-version 5 -target x86_64-apple-macos13.0 $SRC -o Notch_x86 2>> build_errors.txt || { grep -E "error" build_errors.txt | head -40; echo "✗ Build failed (x86_64)"; exit 1; }
lipo -create Notch_arm64 Notch_x86 -output Notch_bin && rm -f Notch_arm64 Notch_x86

pkill -x Notch 2>/dev/null
APP="NoTcH OS.app"
rm -rf Notch.app   # old name
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp -f AppIcon.icns "$APP/Contents/Resources/AppIcon.icns" 2>/dev/null
mv -f Notch_bin "$APP/Contents/MacOS/Notch"
cp -f Info.plist "$APP/Contents/Info.plist"
codesign --force --sign - "$APP" >/dev/null 2>&1
touch "$APP"
lipo -archs "$APP/Contents/MacOS/Notch" > build_archs.txt
echo "✓ Built $APP ($(cat build_archs.txt))"
open "$APP"
echo "✓ NoTcH OS is running. Hover the notch or press ⌥⌘G."
