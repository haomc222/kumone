import pathlib
B = pathlib.Path('.')
p = B / 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
t = p.read_text(encoding='utf-8')
anchor = """    static var now: CompatInstant { CompatInstant(t: ProcessInfo.processInfo.systemUptime) }
    let t: TimeInterval"""
done = """    static var now: CompatInstant { CompatInstant(t: ProcessInfo.processInfo.systemUptime) }
    let t: TimeInterval

    func duration(to other: CompatInstant) -> CompatDuration {
        CompatDuration(t: other.t - t)
    }"""
if 'func duration(to other: CompatInstant) -> CompatDuration {\n        CompatDuration(t: other.t - t)\n    }' in t:
    print('SKIP already applied')
elif anchor in t:
    p.write_text(t.replace(anchor, done, 1), encoding='utf-8')
    print('OK instant.duration inserted')
else:
    print('ANCHOR MISSING')
    for i, ln in enumerate(t.split('\n')[:40]):
        print(i + 1, ln)
