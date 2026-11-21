import pathlib, re
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# 1) rebuild the merged shim from parts A + B (replaces the truncated compat3)
a = B / 'ios15_shimA.txt'
b = B / 'ios15_shimB.txt'
dst = B / 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
if a.exists() and b.exists():
    wr(dst, rd(a) + '\n' + rd(b))
    print('OK shim A+B ->', dst)

# 2) split view + navigation split renames
changed = 0
skip = {'iOS15Shims.swift', 'iOS15NavCompat.swift', 'iOS15CompatMore.swift'}
for f in B.rglob('*.swift'):
    if '.build' in str(f) or f.name in skip:
        continue
    t = rd(f)
    o = t
    t = t.replace('NavigationSplitViewVisibility', 'CompatSplitViewVisibility')
    t = t.replace('NavigationSplitView(columnVisibility:', 'CompatNavigationSplitView(columnVisibility:')
    t = t.replace('NavigationSplitView {', 'CompatNavigationSplitView {')
    lines = [ln for ln in t.split('\n')
             if not re.match(r'^\s*\.navigationSplitViewColumnWidth\(', ln)
             and not re.match(r'^\s*\.navigationSplitViewStyle\(', ln)]
    t = '\n'.join(lines)
    if t != o:
        wr(f, t)
        changed += 1
print('files changed:', changed)

# 3) MPNowPlayingSession availability
p = 'Sources/Kumone/Core/Player/NowPlayingManager.swift'
t = rd(p)
t = t.replace('    private var session: MPNowPlayingSession?',
              '    private var session: AnyObject?')
t = t.replace('        if let session { return session.nowPlayingInfoCenter }',
              '        if #available(iOS 16.0, *), let session = session as? MPNowPlayingSession {\n'
              '            return session.nowPlayingInfoCenter\n'
              '        }')
t = t.replace('''        if let avPlayer {
            let session = MPNowPlayingSession(players: [avPlayer])
            // We publish the full dictionary ourselves (elapsed time, queue
            // count, artwork), which the automatic publisher would omit.
            session.automaticallyPublishesNowPlayingInfo = false
            self.session = session
            session.becomeActiveIfPossible { _ in }
        }''', '''        if let avPlayer, #available(iOS 16.0, *) {
            let session = MPNowPlayingSession(players: [avPlayer])
            session.automaticallyPublishesNowPlayingInfo = false
            self.session = session
            session.becomeActiveIfPossible { _ in }
        }''')
wr(p, t)
print('OK nowplayingmanager')

# 4) Locale language availability
p = 'Sources/Kumone/Core/Models/Models.swift'
t = rd(p)
t = t.replace('''        Locale.current.language.languageCode?.identifier == "zh"''',
              '''        if #available(iOS 16.0, macOS 13.0, *) {
            return Locale.current.language.languageCode?.identifier == "zh"
        }
        return Locale.current.languageCode == "zh"''')
wr(p, t)
print('OK models locale')
print('done')
