import pathlib
B = pathlib.Path('.')
p = B / 'Sources/Kumone/Features/Shared/iOS15NavLinkCompat.swift'
t = p.read_text(encoding='utf-8')

KEY = '''

private struct CompatPushKey: EnvironmentKey {
    static let defaultValue: ((AnyHashable) -> Void)? = nil
}

extension EnvironmentValues {
    var compatPush: ((AnyHashable) -> Void)? {
        get { self[CompatPushKey.self] }
        set { self[CompatPushKey.self] = newValue }
    }
}
'''

if 'CompatPushKey' not in t:
    t = t + KEY

# per-stack environment push (a global proxy is shared across tabs)
t = t.replace("""struct CompatNavigationLink<V: Hashable, Label: View>: View {
    let value: V
    let label: Label
""", """struct CompatNavigationLink<V: Hashable, Label: View>: View {
    let value: V
    let label: Label
    @Environment(\\.compatPush) private var compatPush
""")

t = t.replace("""struct CompatLabeledNavigationLink<V: Hashable>: View {
    let title: String
    let value: V
""", """struct CompatLabeledNavigationLink<V: Hashable>: View {
    let title: String
    let value: V
    @Environment(\\.compatPush) private var compatPush
""")

t = t.replace('                CompatNavProxy.shared.push?(AnyHashable(value))', '                compatPush?(AnyHashable(value))')
t = t.replace('            CompatNavProxy.shared.push?(AnyHashable(value))', '            compatPush?(AnyHashable(value))')

t = t.replace("""        .onAppear {
            CompatNavProxy.shared.push = { any in
                if let value = any.base as? PathValue {
                    path.wrappedValue.append(value)
                }
            }
        }""", """        .environment(\\.compatPush, { any in
            if let value = any.base as? PathValue {
                path.wrappedValue.append(value)
            }
        })
        .onAppear {
            CompatNavProxy.shared.push = { any in
                if let value = any.base as? PathValue {
                    path.wrappedValue.append(value)
                }
            }
        }""")

p.write_text(t, encoding='utf-8')
print('OK environment push wired')
