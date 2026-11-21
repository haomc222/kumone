import pathlib, re, subprocess
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# restore the file broken by line-wise .navigationDestination deletion
p = 'Sources/Kumone/Features/Pages/SettingsView.swift'
subprocess.run(['git', 'checkout', 'HEAD', '--', p], capture_output=True, text=True)
t = rd(p)
t = t.replace('NavigationStack(path:', 'CompatNavigationStack(path:')
t = t.replace('NavigationStack {', 'CompatStack {')
t = t.replace('NavigationLink(value:', 'CompatNavigationLink(value:')
t = re.sub(r'NavigationLink\(\s*"([^"]*)"\s*,\s*value:', r'CompatLabeledNavigationLink("\1", value:', t)
t = t.replace('.navigationDestination(for:', '.compatNavigationDestination(for:')
t = t.replace('.formStyle(.grouped)', '.compatFormStyleGrouped()')
t = '\n'.join(ln for ln in t.split('\n') if not re.match(r'^\s*\.presentationDetents?\(', ln))
wr(p, t)
print('OK settingsview restored + reapplied')

nav = B / 'Sources/Kumone/Features/Shared/iOS15NavCompat.swift'
EXT = """

extension View {
    @ViewBuilder
    func compatNavigationDestination<D: Hashable, C: View>(
        for data: D.Type,
        @ViewBuilder destination: @escaping (D) -> C
    ) -> some View {
        if #available(iOS 16.0, macOS 13.0, *) {
            self.navigationDestination(for: data, destination: destination)
        } else {
            self
        }
    }
}
"""
if nav.exists():
    t = rd(nav)
    if 'compatNavigationDestination' not in t:
        wr(nav, t + EXT)
        print('OK navcompat extension')
print('done')
