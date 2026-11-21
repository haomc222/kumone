#!/bin/bash
set -uo pipefail
LOG="$RUNNER_TEMP/build.log"

git config user.email ci@ios15.local
git config user.name ios15-ci
git remote add pr120 https://github.com/Perfect9s/kumone.git 2>/dev/null || true
echo "=== PR120 additive files ==="
git fetch --no-tags pr120 fix/ios15-compatibility && git checkout FETCH_HEAD -- Sources/Kumone/Features/CompatibilityNavigation.swift Sources/Kumone/Core/PlatformCompatibility.swift

VERSION=$(cat ios15_version.txt 2>/dev/null | tr -d '[:space:]')
[ -n "$VERSION" ] || VERSION=0.3.37
BUILD_NUMBER=$(git rev-list --count HEAD)
echo "VERSION=$VERSION BUILD=$BUILD_NUMBER"

echo "=== base patch + round fixes ==="
python3 ios15_patch.py
for f in $(ls ios15_fix*.py 2>/dev/null | sort -V); do echo "--- $f ---"; python3 "$f"; done

echo "=== build ==="
xcodebuild -workspace ios/KumoneIOS.xcworkspace -scheme KumoneIOS \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath "$RUNNER_TEMP/dd" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  MARKETING_VERSION="$VERSION" CURRENT_PROJECT_VERSION="$BUILD_NUMBER" \
  build > "$LOG" 2>&1

grep -E '\*\* BUILD (SUCCEEDED|FAILED) \*\*' "$LOG"
if grep -q 'error:' "$LOG"; then
  echo "=== swift errors ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" | sed -E 's#^.*/kumone/kumone/##' | sort -u | head -50
  echo "=== count by file ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" | sed -E 's#^.*/kumone/kumone/##' | awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20
  exit 1
fi

APP="$RUNNER_TEMP/dd/Build/Products/Release-iphoneos/KumoneIOS.app"
echo "--- bundle version ---"
/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$APP/Info.plist"
/usr/libexec/PlistBuddy -c "Print :MinimumOSVersion" "$APP/Info.plist"
if otool -L "$APP/KumoneIOS" | grep -qi CoreTransferable; then
  echo "::error::still links CoreTransferable"
  exit 1
fi
mkdir -p "$RUNNER_TEMP/payload/Payload" dist
cp -R "$APP" "$RUNNER_TEMP/payload/Payload/"
(cd "$RUNNER_TEMP/payload" && zip -qry "$GITHUB_WORKSPACE/dist/Kumone-ios15-$VERSION.ipa" Payload)
ls -la dist
exit 0
