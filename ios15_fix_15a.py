import pathlib, re, shutil
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# install the new navigation layer (overrides the earlier no-op fallbacks)
src = B / 'Sources/Kumone/Features/Shared'
a, b, c = B / 'ios15_navA.txt', B / 'ios15_navB.txt', B / 'ios15_navC.txt'
if a.exists() and b.exists() and c.exists():
    wr(src / 'iOS15NavCompat.swift', rd(a))
    wr(src / 'iOS15NavLinkCompat.swift', rd(b))
    wr(src / 'iOS15LegacyPush.swift', rd(c))
    print('OK nav layer installed')

# Theme: compatHiddenToolbarBackground's empty else returned EmptyView -> whole page blank
p = 'Sources/Kumone/DesignSystem/Theme.swift'
t = rd(p)
old = """        if #available(iOS 18.0, *) {
            toolbarBackgroundVisibility(.hidden, for: .automatic)
        } else {

        }"""
new = """        if #available(iOS 18.0, *) {
            toolbarBackgroundVisibility(.hidden, for: .automatic)
        } else {
            self
        }"""
if old in t:
    wr(p, t.replace(old, new, 1))
    print('OK theme empty else -> self')
elif 'compatHiddenToolbarBackground' in t:
    print('WARN theme pattern not matched')
print('done')
