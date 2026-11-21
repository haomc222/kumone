import pathlib
B = pathlib.Path('.')
p = B / 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
t = p.read_text(encoding='utf-8')
if 'func duration(to other: CompatInstant)' not in t:
    t = t.replace('''struct CompatInstant: Comparable {
    static var now: CompatInstant { CompatInstant(t: ProcessInfo.processInfo.systemUptime) }
    let t: TimeInterval''', '''struct CompatInstant: Comparable {
    static var now: CompatInstant { CompatInstant(t: ProcessInfo.processInfo.systemUptime) }
    let t: TimeInterval

    func duration(to other: CompatInstant) -> CompatDuration {
        CompatDuration(t: other.t - t)
    }''')
    p.write_text(t, encoding='utf-8')
    print('OK instant.duration')
else:
    print('SKIP already')
