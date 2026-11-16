# Notch for Android

A Trusted Web Activity that opens https://notch.zeroorigine.com/app/ full screen.
Package: com.zeroorigine.notch. Min Android 7 (API 24), target API 36.

## Build

    export ANDROID_HOME=/path/to/android-sdk    # needs platforms;android-36 and build-tools;35.0.0
    export NOTCH_KEYSTORE=/path/to/upload.p12   # upload key, never committed
    export NOTCH_KEYPASS_FILE=/path/to/upload.pass
    ./gradlew bundleRelease                     # app/build/outputs/bundle/release/app-release.aab

Bump versionCode in app/build.gradle and twa-manifest.json for every Play upload.

The site's /.well-known/assetlinks.json must list both SHA-256 fingerprints:
the upload key and the Play App Signing key (Play Console, Setup, App signing).
