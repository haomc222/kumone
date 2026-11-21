import pathlib
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

src = B / 'ios15_glassbar.txt'
dst = B / 'Sources/Kumone/Features/GlassTabBar.swift'
if src.exists():
    wr(dst, rd(src))
    print('OK glass tab bar replaced')

p = 'Sources/Kumone/Features/IOSMainWindow.swift'
t = rd(p)
old = """            .padding(.bottom, 6)
        }
        .animation(AppAnimation.standard, value: player.hasCurrentTrack)"""
new = """            .padding(.bottom, 6)
            .frame(maxWidth: .infinity)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .animation(AppAnimation.standard, value: player.hasCurrentTrack)"""
if old in t:
    wr(p, t.replace(old, new, 1))
    print('OK tab interface width pinned')
else:
    print('SKIP tab interface pattern')
print('done')
