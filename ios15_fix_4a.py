import pathlib, re
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

SHIM_EXTRA = """

// MARK: - iOS 15 form style

extension View {
    @ViewBuilder
    func compatFormStyleGrouped() -> some View {
        if #available(iOS 16.0, macOS 13.0, *) {
            self.formStyle(.grouped)
        } else {
            self
        }
    }
}
"""
shim = B / 'Sources/Kumone/Features/Shared/iOS15Shims.swift'
if shim.exists():
    t = rd(shim)
    if 'compatFormStyleGrouped' not in t:
        wr(shim, t + SHIM_EXTRA)
        print('OK shim formStyle')

DROP = [
    r'^\s*\.presentationDetents\(.*$',
    r'^\s*\.presentationDragIndicator\(.*$',
    r'^\s*\.contentTransition\(.*$',
    r'^\s*\.menuOrder\(.*$',
    r'^\s*\.scrollIndicators\(.*$',
    r'^\s*\.scrollDismissesKeyboard\(.*$',
    r'^\s*\.toolbarBackground\(.*$',
    r'^\s*\.scrollContentBackground\(.*$',
]
drop_re = [re.compile(p) for p in DROP]

changed = 0
for f in B.rglob('*.swift'):
    if '.build' in str(f) or 'iOS15Shims.swift' in str(f):
        continue
    src = rd(f)
    lines = src.split('\n')
    out = []
    removed = 0
    for ln in lines:
        if any(r.match(ln) for r in drop_re):
            removed += 1
            continue
        out.append(ln)
    t = '\n'.join(out)
    t = t.replace('.formStyle(.grouped)', '.compatFormStyleGrouped()')
    if t != src:
        wr(f, t)
        changed += 1
        print('OK', f, 'removed', removed)
print('files changed:', changed)
