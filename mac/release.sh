#!/bin/zsh
# Build, sign, notarize and staple NoTcH OS, then make the download zip.
# Needs: a Developer ID identity in the keychain and a notarytool profile named "notch".
set -e
cd "$(dirname "$0")"
NOOPEN=1 ./build.sh
APP="NoTcH OS.app"
codesign --verify --deep --strict "$APP"
rm -f NoTcH-OS-mac.zip
ditto -c -k --keepParent "$APP" NoTcH-OS-mac.zip
echo "▸ Sending to Apple for notarization (usually 1-5 minutes)…"
xcrun notarytool submit NoTcH-OS-mac.zip --keychain-profile notch --wait
xcrun stapler staple "$APP"
rm -f NoTcH-OS-mac.zip
ditto -c -k --keepParent "$APP" NoTcH-OS-mac.zip
spctl -a -vv "$APP"
VER=$(defaults read "$(pwd)/$APP/Contents/Info" CFBundleShortVersionString)
BLD=$(defaults read "$(pwd)/$APP/Contents/Info" CFBundleVersion)
cp -f NoTcH-OS-mac.zip "NoTcH-OS-mac-$VER.zip"   # a fixed address per version, so the feed never points at a moving file
SHA=$(shasum -a 256 NoTcH-OS-mac.zip | cut -d" " -f1)
NOTES=${NOTES:-"New in $VER."}
cat > mac-update.json <<JSON
{"version":"$VER","build":$BLD,"url":"https://notch.zeroorigine.com/downloads/NoTcH-OS-mac-$VER.zip","sha256":"$SHA","notes":"$NOTES"}
JSON
echo "✓ Release ready: $(pwd)/NoTcH-OS-mac.zip and mac-update.json (version $VER, build $BLD)"
