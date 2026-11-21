import pathlib, re, shutil
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# 1) install nav compat source
src = B / 'ios15_navcompat.txt'
dst = B / 'Sources/Kumone/Features/Shared/iOS15NavCompat.swift'
if src.exists():
    shutil.copyfile(src, dst)
    print('OK navcompat ->', dst)

# 2) navigation renames + unsupported modifier removal
nav_dest = re.compile(r'^\s*\.navigationDestination\(.*$')
changes = 0
for f in B.rglob('*.swift'):
    if '.build' in str(f) or f.name in ('iOS15NavCompat.swift', 'iOS15Shims.swift'):
        continue
    t = rd(f)
    o = t
    t = t.replace('NavigationStack(path:', 'CompatNavigationStack(path:')
    t = t.replace('NavigationStack {', 'CompatStack {')
    t = t.replace('NavigationLink(value:', 'CompatNavigationLink(value:')
    t = re.sub(r'NavigationLink\(\s*"([^"]*)"\s*,\s*value:', r'CompatLabeledNavigationLink("\1", value:', t)
    lines = [ln for ln in t.split('\n') if not nav_dest.match(ln)]
    t = '\n'.join(lines)
    if t != o:
        wr(f, t)
        changes += 1
print('files changed:', changes)

# 3) main-actor fixes for the renderer shim
shim = B / 'Sources/Kumone/Features/Shared/iOS15Shims.swift'
if shim.exists():
    t = rd(shim)
    t = t.replace('func renderViewToImage<V: View>', '@MainActor func renderViewToImage<V: View>')
    t = t.replace('private func legacyHostingImage<V: View>', '@MainActor private func legacyHostingImage<V: View>')
    wr(shim, t)
    print('OK shim mainactor')
c = B / 'Sources/Kumone/Features/Shared/CommentShareCard.swift'
if c.exists():
    t = rd(c)
    t = t.replace('    private func render() async {', '    @MainActor private func render() async {')
    wr(c, t)
    print('OK comment card mainactor')
