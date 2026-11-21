import pathlib, re
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

p = 'Sources/Kumone/DesignSystem/Theme.swift'
t = rd(p)
marker = 'func compatHiddenToolbarBackground() -> some View {'
i = t.find(marker)
if i < 0:
    print('MISSING function')
else:
    depth = 0
    j = t.index('{', i)
    start = j
    while j < len(t):
        if t[j] == '{':
            depth += 1
        elif t[j] == '}':
            depth -= 1
            if depth == 0:
                break
        j += 1
    block = t[start:j + 1]
    fixed = re.sub(r'\} else \{\s*\}', '} else {\n            self\n        }', block)
    if fixed != block:
        wr(p, t[:start] + fixed + t[j + 1:])
        print('OK compatHiddenToolbarBackground else -> self')
    else:
        print('SKIP already fine')

for f in B.rglob('*.swift'):
    if '.build' in str(f):
        continue
    for n, ln in enumerate(rd(f).split('\n'), 1):
        if re.search(r'\} else \{\s*\}', ln):
            print('EMPTY ELSE', f.name, n)
print('done')
