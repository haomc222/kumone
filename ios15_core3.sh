#!/bin/bash
set -uo pipefail
export APP_NAME=Kumone
LOG="$RUNNER_TEMP/build.log"

echo "=== take PR #120's additive files only (no 3-way merge of view files) ==="
git config user.email ci@ios15.local
git config user.name ios15-ci
git remote add pr120 https://github.com/Perfect9s/kumone.git 2>/dev/null || true
if git fetch --no-tags pr120 fix/ios15-compatibility; then
  git checkout FETCH_HEAD -- \
    Sources/Kumone/Features/CompatibilityNavigation.swift \
    Sources/Kumone/Core/PlatformCompatibility.swift 2>&1 || echo "::warning::additive checkout partially failed"
  git status --short | head -20
else
  echo "::warning::拉取 PR #120 失败"
fi

echo "=== apply base patch ==="
python3 ios15_patch.py

FIX=$(ls ios15_fix*.py 2>/dev/null | sort -V | tail -1)
if [ -n "$FIX" ]; then
  echo "=== apply round fix: $FIX ==="
  python3 "$FIX"
fi

echo "=== build ==="
xcodebuild -workspace ios/KumoneIOS.xcworkspace -scheme KumoneIOS \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath "$RUNNER_TEMP/dd" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  build > "$LOG" 2>&1

grep -E '\*\* BUILD (SUCCEEDED|FAILED) \*\*' "$LOG"

if grep -q 'error:' "$LOG"; then
  echo "=== swift errors (unique) ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" | sed -E 's#^.*/kumone/kumone/##' | sort -u | head -60
  echo "=== context (first 12 error sites) ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" \
    | sed -E 's#^.*/kumone/kumone/##' | awk -F: '{print $1":"$2}' | sort -u | head -12 \
    | while IFS=: read -r file line; do
        [ -f "$file" ] || continue
        if [ "$line" -gt 6 ]; then start=$((line - 6)); else start=1; fi
        end=$((line + 6))
        echo "----- $file ($start-$end) -----"
        sed -n "$start,$end p" "$file" | awk -v s="$start" '{ printf "%d| %s\n", NR + s - 1, $0 }'
      done
  echo "::error::编译失败，完整日志见 build-log artifact"
  exit 1
fi

echo "=== verify + package ==="
APP="$RUNNER_TEMP/dd/Build/Products/Release-iphoneos/KumoneIOS.app"
/usr/libexec/PlistBuddy -c "Print :MinimumOSVersion" "$APP/Info.plist"
if otool -L "$APP/KumoneIOS" | grep -qi CoreTransferable; then
  echo "::error::仍链接 CoreTransferable，iOS 15 上会在 dyld 阶段中止"
  exit 1
fi
mkdir -p "$RUNNER_TEMP/payload/Payload" dist
cp -R "$APP" "$RUNNER_TEMP/payload/Payload/"
(cd "$RUNNER_TEMP/payload" && zip -qry "$GITHUB_WORKSPACE/dist/Kumone-ios15.ipa" Payload)
ls -la dist
exit 0
