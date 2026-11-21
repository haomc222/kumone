import pathlib, subprocess
B = pathlib.Path('.')
# PR #120's PlatformCompatibility.swift is an OLDER copy of an upstream file:
# restoring it from HEAD brings back PlatformImage/PlatformFont/PlatformView.
p = 'Sources/Kumone/Core/PlatformCompatibility.swift'
r = subprocess.run(['git', 'checkout', 'HEAD', '--', p], capture_output=True, text=True)
print('restore', p, '->', r.returncode, r.stderr.strip()[:200])

# PR's navigation refactor file depends on PR-only code; upstream has no such file.
q = B / 'Sources/Kumone/Features/CompatibilityNavigation.swift'
if q.exists():
    q.unlink()
    print('DEL', q)
print('done')
