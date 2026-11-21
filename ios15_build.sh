#!/bin/bash
set -uo pipefail
LOG="$RUNNER_TEMP/build.log"
COREFILES="Sources/Kumone/Core/Models/LyricsParser.swift Sources/Kumone/Core/Models/Models.swift Sources/Kumone/Core/Player/PlayerServiceIOS.swift Sources/Kumone/Core/Player/SleepTimer.swift Sources/Kumone/Core/Storage/AccountStore.swift Sources/Kumone/Core/Storage/SettingsManager.swift Sources/Kumone/Core/PlatformCompatibility.swift Sources/Kumone/Features/CompatibilityNavigation.swift"

echo "=== take PR #120 versions of the core (non-view) files ==="
git config user.email ci@ios15.local
git config user.name ios15-ci
git remote add pr120 https://github.com/Perfect9s/kumone.git 2>/dev/null || true
git fetch --no-tags pr120 fix/ios15-compatibility
git checkout FETCH_HEAD -- $COREFILES 2>&1 || echo "::warning::partial checkout"
git status --short | head -20

echo "=== base patch ==="
python3 ios15_patch.py

FIX=$(ls ios15_fix*.py 2>/dev/null | sort -V | tail -1)
if [ -n "$FIX" ]; then
  echo "=== round fix: $FIX ==="
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
  echo "=== ALL swift errors ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" | sed -E 's#^.*/kumone/kumone/##' | sort -u | head -200
  echo "=== error count by file ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" | sed -E 's#^.*/kumone/kumone/##' | awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -25
  echo "::error::编译失败，见 build-log"
  exit 1
fi

APP="$RUNNER_TEMP/dd/Build/Products/Release-iphoneos/KumoneIOS.app"
/usr/libexec/PlistBuddy -c "Print :MinimumOSVersion" "$APP/Info.plist"
if otool -L "$APP/KumoneIOS" | grep -qi CoreTransferable; then
  echo "::error::still links CoreTransferable"
  exit 1
fi
mkdir -p "$RUNNER_TEMP/payload/Payload" dist
cp -R "$APP" "$RUNNER_TEMP/payload/Payload/"
(cd "$RUNNER_TEMP/payload" && zip -qry "$GITHUB_WORKSPACE/dist/Kumone-ios15.ipa" Payload)
ls -la dist
exit 0
#!/bin/bash
set -uo pipefail
export APP_NAME=Kumone
LOG="$RUNNER_TEMP/build.log"

echo "=== take PR #120 additive files only ==="
git config user.email ci@ios15.local
git config user.name ios15-ci
git remote add pr120 https://github.com/Perfect9s/kumone.git 2>/dev/null || true
if git fetch --no-tags pr120 fix/ios15-compatibility; then
  git checkout FETCH_HEAD -- Sources/Kumone/Features/CompatibilityNavigation.swift Sources/Kumone/Core/PlatformCompatibility.swift 2>&1 || echo "::warning::additive checkout partial"
  git status --short | head -20
else
  echo "::warning::fetch PR120 failed"
fi

echo "=== base patch ==="
python3 ios15_patch.py

FIX=$(ls ios15_fix*.py 2>/dev/null | sort -V | tail -1)
if [ -n "$FIX" ]; then
  echo "=== round fix: $FIX ==="
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
  echo "=== context (first 12 sites) ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" \
    | sed -E 's#^.*/kumone/kumone/##' | awk -F: '{print $1":"$2}' | sort -u | head -12 \
    | while IFS=: read -r file line; do
        [ -f "$file" ] || continue
        if [ "$line" -gt 6 ]; then start=$((line - 6)); else start=1; fi
        end=$((line + 6))
        echo "----- $file ($start-$end) -----"
        sed -n "$start,$end p" "$file" | awk -v s="$start" '{ printf "%d| %s\n", NR + s - 1, $0 }'
      done
  echo "::error::编译失败，见 build-log"
  exit 1
fi

echo "=== verify + package ==="
APP="$RUNNER_TEMP/dd/Build/Products/Release-iphoneos/KumoneIOS.app"
/usr/libexec/PlistBuddy -c "Print :MinimumOSVersion" "$APP/Info.plist"
if otool -L "$APP/KumoneIOS" | grep -qi CoreTransferable; then
  echo "::error::still links CoreTransferable"
  exit 1
fi
mkdir -p "$RUNNER_TEMP/payload/Payload" dist
cp -R "$APP" "$RUNNER_TEMP/payload/Payload/"
(cd "$RUNNER_TEMP/payload" && zip -qry "$GITHUB_WORKSPACE/dist/Kumone-ios15.ipa" Payload)
ls -la dist
exit 0
#!/bin/bash
set -uo pipefail
export APP_NAME=Kumone
LOG="$RUNNER_TEMP/build.log"

echo "=== merge PR #120 (iOS 15 compatibility) ==="
git config user.email ci@ios15.local
git config user.name ios15-ci
git remote add pr120 https://github.com/Perfect9s/kumone.git 2>/dev/null || true
if git fetch --no-tags pr120 fix/ios15-compatibility; then
  git cherry-pick -X theirs FETCH_HEAD || {
    echo "::warning::cherry-pick 有冲突，按 PR 侧解决并提交"
    git status --short | head -50
    git add -A
    git commit -m "wip: pr120 conflicts" || true
  }
else
  echo "::warning::拉取 PR #120 失败，跳过合并"
fi
git log --oneline -3

echo "=== apply base patch ==="
python3 ios15_patch.py

FIX=$(ls -t ios15_fix*.py 2>/dev/null | head -1)
if [ -n "$FIX" ]; then
  echo "=== apply round fix: $FIX ==="
  python3 "$FIX"
fi

echo "--- deployment targets ---"
grep -nE 'iOS\(|IPHONEOS_DEPLOYMENT_TARGET|iOS: ' Package.swift ios/KumoneIOSPackage/Package.swift ios/Config/Shared.xcconfig ios/project.yml 2>/dev/null

echo "=== build ==="
xcodebuild -workspace ios/KumoneIOS.xcworkspace -scheme KumoneIOS \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath "$RUNNER_TEMP/dd" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  build > "$LOG" 2>&1

grep -E '\*\* BUILD (SUCCEEDED|FAILED) \*\*' "$LOG"

if grep -q 'error:' "$LOG"; then
  echo "=== swift errors ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" | sed -E 's#^.*/kumone/kumone/##' | sort -u | head -40
  echo "=== full dumps of syntax-broken files ==="
  grep -E 'unexpected conditional compilation block terminator|extraneous|expected .}. at end' "$LOG" \
    | sed -E 's#^.*/kumone/kumone/##' | awk -F: '{print $1}' | sort -u | head -3 \
    | while read -r file; do
        [ -f "$file" ] || continue
        echo "===== BEGIN $file ====="
        cat -n "$file"
        echo "===== END $file ====="
      done
  echo "::error::编译失败，完整日志见 build-log artifact"
  exit 1
fi

echo "=== verify + package ==="
APP="$RUNNER_TEMP/dd/Build/Products/Release-iphoneos/KumoneIOS.app"
/usr/libexec/PlistBuddy -c "Print :MinimumOSVersion" "$APP/Info.plist"
xcrun vtool -show-build "$APP/KumoneIOS" | head -20
if otool -L "$APP/KumoneIOS" | grep -qi CoreTransferable; then
  echo "::error::仍链接 CoreTransferable，iOS 15 上会在 dyld 阶段中止"
  exit 1
fi
mkdir -p "$RUNNER_TEMP/payload/Payload" dist
cp -R "$APP" "$RUNNER_TEMP/payload/Payload/"
(cd "$RUNNER_TEMP/payload" && zip -qry "$GITHUB_WORKSPACE/dist/Kumone-ios15.ipa" Payload)
ls -la dist
exit 0
#!/bin/bash
set -uo pipefail
export APP_NAME=Kumone
LOG="$RUNNER_TEMP/build.log"

echo "=== merge PR #120 (iOS 15 compatibility) ==="
git config user.email ci@ios15.local
git config user.name ios15-ci
git remote add pr120 https://github.com/Perfect9s/kumone.git 2>/dev/null || true
if git fetch --no-tags pr120 fix/ios15-compatibility; then
  git cherry-pick -X theirs FETCH_HEAD || {
    echo "::warning::cherry-pick 有冲突，按 PR 侧解决并提交"
    git status --short | head -50
    git add -A
    git commit -m "wip: pr120 conflicts" || true
  }
else
  echo "::warning::拉取 PR #120 失败，跳过合并步骤"
fi
git log --oneline -3

echo "=== apply base patch ==="
python3 ios15_patch.py

if [ -f ios15_fix.py ]; then
  echo "=== apply round fix ==="
  python3 ios15_fix.py
fi

echo "--- deployment targets ---"
grep -nE 'iOS\(|IPHONEOS_DEPLOYMENT_TARGET|iOS: ' Package.swift ios/KumoneIOSPackage/Package.swift ios/Config/Shared.xcconfig ios/project.yml 2>/dev/null || true

echo "=== build ==="
xcodebuild -workspace ios/KumoneIOS.xcworkspace -scheme KumoneIOS \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath "$RUNNER_TEMP/dd" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  build > "$LOG" 2>&1 || true

grep -E '\*\* BUILD (SUCCEEDED|FAILED) \*\*' "$LOG" || echo "(no BUILD line)"

if grep -q 'error:' "$LOG"; then
  echo "=== swift errors ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" | sed -E 's#^.*/kumone/kumone/##' | sort -u | head -40
  echo "=== full dumps of syntax-broken files ==="
  grep -E 'unexpected conditional compilation block terminator|extraneous|expected .}. at end' "$LOG" \
    | sed -E 's#^.*/kumone/kumone/##' | awk -F: '{print $1}' | sort -u | head -3 \
    | while read -r file; do
        [ -f "$file" ] || continue
        echo "===== BEGIN $file ====="
        cat -n "$file"
        echo "===== END $file ====="
      done
  echo "::error::编译失败，完整日志见 build-log artifact"
  exit 1
fi

echo "=== verify + package ==="
APP="$RUNNER_TEMP/dd/Build/Products/Release-iphoneos/KumoneIOS.app"
/usr/libexec/PlistBuddy -c "Print :MinimumOSVersion" "$APP/Info.plist"
xcrun vtool -show-build "$APP/KumoneIOS" | head -20 || true
if otool -L "$APP/KumoneIOS" | grep -qi CoreTransferable; then
  echo "::error::仍链接 CoreTransferable，iOS 15 上会在 dyld 阶段中止"
  exit 1
fi
mkdir -p "$RUNNER_TEMP/payload/Payload" dist
cp -R "$APP" "$RUNNER_TEMP/payload/Payload/"
(cd "$RUNNER_TEMP/payload" && zip -qry "$GITHUB_WORKSPACE/dist/Kumone-ios15.ipa" Payload)
ls -la dist
#!/bin/bash
set -uo pipefail
export APP_NAME=Kumone
LOG="$RUNNER_TEMP/build.log"

echo "=== merge PR #120 (iOS 15 compatibility) ==="
git config user.email ci@ios15.local
git config user.name ios15-ci
git remote add pr120 https://github.com/Perfect9s/kumone.git 2>/dev/null || true
if git fetch --no-tags pr120 fix/ios15-compatibility; then
  git cherry-pick -X theirs FETCH_HEAD || {
    echo "::warning::cherry-pick 有冲突，按 PR 侧解决并提交"
    git status --short | head -50
    git add -A
    git commit -m "wip: pr120 conflicts" || true
  }
else
  echo "::warning::拉取 PR #120 失败，跳过合并步骤"
fi
git log --oneline -3

echo "=== apply base patch ==="
python3 ios15_patch.py

if [ -f ios15_fix.py ]; then
  echo "=== apply round fix ==="
  python3 ios15_fix.py
fi

echo "--- deployment targets ---"
grep -nE 'iOS\(|IPHONEOS_DEPLOYMENT_TARGET|iOS: ' Package.swift ios/KumoneIOSPackage/Package.swift ios/Config/Shared.xcconfig ios/project.yml 2>/dev/null || true

echo "=== build ==="
xcodebuild -workspace ios/KumoneIOS.xcworkspace -scheme KumoneIOS \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath "$RUNNER_TEMP/dd" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  build > "$LOG" 2>&1 || true

grep -E '\*\* BUILD (SUCCEEDED|FAILED) \*\*' "$LOG" || echo "(no BUILD line)"

if grep -q 'error:' "$LOG"; then
  echo "=== swift errors ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" | sed -E 's#^.*/kumone/kumone/##' | sort -u | head -30
  echo "=== context dumps ==="
  grep -E '\.swift:[0-9]+:[0-9]+: error:' "$LOG" \
    | sed -E 's#^.*/kumone/kumone/##' \
    | awk -F: '{print $1":"$2}' | sort -u | head -10 \
    | while IFS=: read -r file line; do
        [ -f "$file" ] || continue
        if [ "$line" -gt 14 ]; then start=$((line - 14)); else start=1; fi
        end=$((line + 14))
        echo "----- $file  (lines $start-$end) -----"
        sed -n "$start,$end p" "$file" | awk -v s="$start" '{ printf "%d| %s\n", NR + s - 1, $0 }'
      done
  echo "::error::编译失败，完整日志见 build-log artifact"
  exit 1
fi

echo "=== verify + package ==="
APP="$RUNNER_TEMP/dd/Build/Products/Release-iphoneos/KumoneIOS.app"
/usr/libexec/PlistBuddy -c "Print :MinimumOSVersion" "$APP/Info.plist"
xcrun vtool -show-build "$APP/KumoneIOS" | head -20 || true
if otool -L "$APP/KumoneIOS" | grep -qi CoreTransferable; then
  echo "::error::仍链接 CoreTransferable，iOS 15 上会在 dyld 阶段中止"
  exit 1
fi
mkdir -p "$RUNNER_TEMP/payload/Payload" dist
cp -R "$APP" "$RUNNER_TEMP/payload/Payload/"
(cd "$RUNNER_TEMP/payload" && zip -qry "$GITHUB_WORKSPACE/dist/Kumone-ios15.ipa" Payload)
ls -la dist
