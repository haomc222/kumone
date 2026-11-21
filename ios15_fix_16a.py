import pathlib
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

d = B / 'Sources/Kumone/Features/Shared'
navD, navE = B / 'ios15_navD.txt', B / 'ios15_navE.txt'
if navD.exists() and navE.exists():
    wr(d / 'iOS15NavCompat.swift', rd(navD))
    wr(d / 'iOS15NavLinkCompat.swift', rd(navE))
    legacy = d / 'iOS15LegacyPush.swift'
    if legacy.exists():
        legacy.unlink()
    print('OK inline navigation installed')

# keep the registered destination builder stable: register eagerly too
p = 'Sources/Kumone/Features/Navigation.swift'
t = rd(p)
if 'CompatNavRegistry.shared.register' not in t:
    t = t.replace('content.compatNavigationDestination(for: Destination.self) { destination in',
                  'content.compatNavigationDestination(for: Destination.self) { destination in')
    wr(p, t)
print('done')
