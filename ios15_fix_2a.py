import pathlib
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

LOCK = """

// MARK: - lock (replaces OSAllocatedUnfairLock, iOS 16+)

final class CompatLock<State>: @unchecked Sendable {
    private let lock = NSLock()
    private var state: State
    init(initialState: State) { state = initialState }
    func withLock<R>(_ body: (inout State) throws -> R) rethrows -> R {
        lock.lock()
        defer { lock.unlock() }
        return try body(&state)
    }
    func withLockUnchecked<R>(_ body: (inout State) throws -> R) rethrows -> R { try withLock(body) }
}
"""
shim = 'Sources/Kumone/Features/Shared/iOS15Shims.swift'
if (B / shim).exists() and 'class CompatLock' not in rd(shim):
    wr(shim, rd(shim) + LOCK)
    print('OK shim lock')

for p in ['Sources/Kumone/Core/API/Upstream.swift', 'Sources/Kumone/Core/Player/CDNHost.swift']:
    if (B / p).exists() and 'OSAllocatedUnfairLock' in rd(p):
        wr(p, rd(p).replace('OSAllocatedUnfairLock', 'CompatLock'))
        print('OK lock', p)

p = 'Sources/Kumone/Core/API/MusicAPI.swift'
if (B / p).exists():
    t = rd(p)
    n = t.replace('retryDelay: Duration = .milliseconds(400)', 'retryDelay: TimeInterval = 0.4')
    n = n.replace('try await Task.sleep(for: retryDelay)', 'try await Task.sleep(nanoseconds: UInt64(max(0, retryDelay) * 1_000_000_000))')
    if n != t:
        wr(p, n)
        print('OK musicapi sleep')
