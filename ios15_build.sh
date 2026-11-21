#!/bin/bash
set -uo pipefail
export APP_NAME=Kumone

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

echo "=== apply iOS 15 patch ==="
python3 ios15_patch.py
echo "--- deployment targets ---"
grep -n 'iOS("|IPHONEOS_DEPLOYMENT_TARGET|iOS: "|\.iOS(\.v' Package.swift ios/KumoneIOSPackage/Package.swift ios/Config/Shared.xcconfig ios/project.yml 2>/dev/null || true

echo "=== build ==="
xcodebuild -workspace ios/KumoneIOS.xcworkspace -scheme KumoneIOS \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath "$RUNNER_TEMP/dd" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO \
  build > "$RUNNER_TEMP/build.log" 2>&1 || true

echo "--- first swift errors ---"
grep -E '\.swift:[0-9]+:[0-9]+: error:' "$RUNNER_TEMP/build.log" | head -80 || echo "(no swift errors matched)"
grep -E '\*\* BUILD (SUCCEEDED|FAILED) \*\*' "$RUNNER_TEMP/build.log" || echo "(no BUILD line)"

if grep -q 'error:' "$RUNNER_TEMP/build.log"; then
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
