import pathlib, re
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# 1) ProposedViewSize backport type
shim = B / 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
if shim.exists():
    t = rd(shim)
    if 'CompatProposedViewSize' not in t:
        t += """

struct CompatProposedViewSize {
    var width: CGFloat?
    var height: CGFloat?

    init(width: CGFloat? = nil, height: CGFloat? = nil) {
        self.width = width
        self.height = height
    }

    init(_ size: CGSize) {
        self.width = size.width
        self.height = size.height
    }

    init(replacing proposal: CompatProposedViewSize) {
        self = proposal
    }
}
"""
        wr(shim, t)
        print('OK proposed view size type')

def drop_block(lines, start_re):
    out = []
    i = 0
    removed = 0
    while i < len(lines):
        ln = lines[i]
        if re.match(start_re, ln):
            depth = 0
            j = i
            while j < len(lines):
                depth += lines[j].count('{') - lines[j].count('}')
                j += 1
                if depth <= 0:
                    break
            i = j
            removed += 1
            continue
        out.append(ln)
        i += 1
    return out, removed

skip = {'iOS15Shims.swift', 'iOS15NavCompat.swift', 'iOS15CompatMore.swift'}
changed = 0
for f in B.rglob('*.swift'):
    if '.build' in str(f) or f.name in skip:
        continue
    t = rd(f)
    o = t
    t = t.replace('ProposedViewSize', 'CompatProposedViewSize').replace('CompatCompatProposedViewSize', 'CompatProposedViewSize')
    if t != o:
        wr(f, t)
        changed += 1
print('proposal rename files:', changed)

# 2) toolbar content builders (buildIf/buildEither are iOS 16) -> drop toolbar blocks
for p in ['Sources/Kumone/Features/Detail/PlaylistDetailView.swift',
          'Sources/Kumone/Features/MainWindow.swift',
          'Sources/Kumone/Features/Detail/AlbumDetailView.swift',
          'Sources/Kumone/Features/Pages/LibraryPages.swift']:
    if not (B / p).exists():
        continue
    lines = rd(p).split('\n')
    lines, n1 = drop_block(lines, r'^\s*\.toolbar \{')
    lines, n2 = drop_block(lines, r'^\s*\.toolbar\(')
    wr(p, '\n'.join(lines))
    print('OK toolbar dropped', p, n1, n2)
print('done')
