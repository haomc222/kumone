import pathlib
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# 1) FM's full-bleed backdrop leaks its expanded safe area into the shared ZStack,
#    which stretches the other tabs. Keep the gradient but stop ignoring safe area.
p = 'Sources/Kumone/Features/Pages/FMView.swift'
t = rd(p)
n = t.count('.ignoresSafeArea()')
if n:
    t = t.replace('            .ignoresSafeArea()\n', '')
    t = t.replace('.ignoresSafeArea()', '')
    wr(p, t)
    print('OK FM ignoresSafeArea removed:', n)
else:
    print('SKIP FM already clean')

# 2) clip each tab page so one page cannot paint outside its frame
p = 'Sources/Kumone/Features/IOSMainWindow.swift'
t = rd(p)
old = """        content()
            .opacity(selectedTab == tab ? 1 : 0)
            .allowsHitTesting(selectedTab == tab)
            .zIndex(selectedTab == tab ? 1 : 0)"""
new = """        content()
            .opacity(selectedTab == tab ? 1 : 0)
            .allowsHitTesting(selectedTab == tab)
            .zIndex(selectedTab == tab ? 1 : 0)
            .clipped()"""
if old in t and '.clipped()' not in t:
    wr(p, t.replace(old, new, 1))
    print('OK page clipped')
else:
    print('SKIP page clip')
print('done')
