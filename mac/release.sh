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
echo "✓ Release ready: $(pwd)/NoTcH-OS-mac.zip"
