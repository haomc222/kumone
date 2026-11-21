import pathlib, re
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

shim = B / 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
if shim.exists():
    t = rd(shim)
    if 'typealias Instant' not in t:
        t = t.replace('''struct CompatClock {
    var now: CompatInstant''', '''struct CompatClock {
    typealias Instant = CompatCompatInstantAlias
    var now: CompatInstant''')
        t = t.replace('typealias Instant = CompatCompatInstantAlias', 'typealias Instant = CompatInstant')
        wr(shim, t)
        print('OK clock aliases')

skip = {'iOS15Shims.swift', 'iOS15NavCompat.swift', 'iOS15CompatMore.swift'}
changed = 0
for f in B.rglob('*.swift'):
    if '.build' in str(f) or f.name in skip:
        continue
    t = rd(f)
    o = t
    t = t.replace('.navigationDestination(for:', '.compatNavigationDestination(for:')
    t = t.replace('LabeledContent {', 'CompatLabeledContent {')
    t = t.replace('.toolbarBackground(for:', '.compatNoopToolbarBackground(for:')
    # non-literal sleeps
    t = re.sub(r'Task\.sleep\(for: \.seconds\(([A-Za-z_][A-Za-z0-9_.]*)\)\)',
               r'Task.sleep(nanoseconds: UInt64(max(0, \1) * 1_000_000_000))', t)
    t = re.sub(r'Task\.sleep\(for: \.milliseconds\(([A-Za-z_][A-Za-z0-9_.]*)\)\)',
               r'Task.sleep(nanoseconds: UInt64(max(0, \1) * 1_000_000))', t)
    if t != o:
        wr(f, t)
        changed += 1
print('files changed:', changed)

# PlayerServiceIOS leftover .now
p = 'Sources/Kumone/Core/Player/PlayerServiceIOS.swift'
t = rd(p)
lines = t.split('\n')
for i, ln in enumerate(lines):
    if '.now' in ln and 'ProcessInfo' not in ln:
        ln2 = ln.replace('lastPlaybackCheckpoint.now', 'ProcessInfo.processInfo.systemUptime')
        lines[i] = ln2
t = '\n'.join(lines)
wr(p, t)
print('OK playerservice .now sweep')

# SongCommentsView: drop PresentationDetent usage lines
p = 'Sources/Kumone/Features/Shared/SongCommentsView.swift'
if (B / p).exists():
    t = rd(p)
    lines = [ln for ln in t.split('\n') if 'PresentationDetent' not in ln and not re.match(r'^\s*\.presentationDetents?\(', ln)]
    wr(p, '\n'.join(lines))
    print('OK songcomments detents')
print('done')
