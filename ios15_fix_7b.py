import pathlib
B = pathlib.Path('.')
p = B / 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
EXT = """

extension View {
    @ViewBuilder
    func compatNoopToolbarBackground<A, B>(_ background: A, for bars: B) -> some View {
        self
    }

    @ViewBuilder
    func compatNoopToolbarBackground<A>(_ background: A) -> some View {
        self
    }
}
"""
if p.exists():
    t = p.read_text(encoding='utf-8')
    if 'compatNoopToolbarBackground' not in t:
        p.write_text(t + EXT, encoding='utf-8')
        print('OK noop toolbar background')
print('done')
