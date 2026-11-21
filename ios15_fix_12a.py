import pathlib, re
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

p = 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
t = rd(p)
if 'static func seconds(' not in t:
    t = t.replace('''struct CompatDuration: Comparable {
    let t: TimeInterval''', '''struct CompatDuration: Comparable {
    static func seconds(_ value: Double) -> CompatDuration { CompatDuration(t: value) }
    static func milliseconds(_ value: Double) -> CompatDuration { CompatDuration(t: value / 1000) }
    let t: TimeInterval''')
    wr(p, t)
    print('OK duration factories')

# theme: drop the unavailable iOS-15 fallback call, leaving an empty else branch
p = 'Sources/Kumone/DesignSystem/Theme.swift'
t = rd(p)
t = t.replace('            compatNoopToolbarBackground(.hidden, for: .navigationBar)\n', '')
wr(p, t)
print('OK theme toolbar')

# any remaining Task.sleep(for: <identifier path>)
for f in B.rglob('*.swift'):
    if '.build' in str(f):
        continue
    t = rd(f)
    n = re.sub(r'Task\.sleep\(for: ([\w.]+)\)', r'Task.sleep(nanoseconds: UInt64(max(0, \1) * 1_000_000_000))', t)
    if n != t:
        wr(f, n)
        print('OK sleep', f.name)
print('done')
