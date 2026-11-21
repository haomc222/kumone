import pathlib, re, shutil, subprocess
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

src = B / 'ios15_compat2.txt'
dst = B / 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
if src.exists():
    shutil.copyfile(src, dst)
    print('OK compat2 installed')

skip = {'iOS15NavCompat.swift', 'iOS15Shims.swift', 'iOS15CompatMore.swift'}
changed = 0
for f in B.rglob('*.swift'):
    if '.build' in str(f) or f.name in skip:
        continue
    t = rd(f)
    o = t
    t = t.replace('ContinuousClock', 'CompatClock')
    t = t.replace('ViewThatFits(', 'CompatViewThatFits(')
    t = t.replace('ViewThatFits {', 'CompatViewThatFits {')
    t = t.replace('.onGeometryChange(for:', '.compatOnGeometryChange(for:')
    t = re.sub(r'LabeledContent\(', 'CompatLabeledContent(', t)
    t = t.replace('.toolbarBackground(', '.compatNoopToolbarBackground(')
    if t != o:
        wr(f, t)
        changed += 1
print('files changed:', changed)

# repair SidebarView (line deletions left a dangling modifier chain)
p = 'Sources/Kumone/Features/SidebarView.swift'
subprocess.run(['git', 'checkout', 'HEAD', '--', p], capture_output=True, text=True)
t = rd(p)
lines = [ln for ln in t.split('\n') if not re.match(r'^\s*\.scrollContentBackground\(', ln)]
t = '\n'.join(lines)
wr(p, t)
print('OK sidebarview repaired')
