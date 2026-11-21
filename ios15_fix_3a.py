import pathlib, re
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# drop PR files that depend on PR-only refactors
for p in ['Sources/Kumone/Features/CompatibilityNavigation.swift',
          'Sources/Kumone/Core/PlatformCompatibility.swift']:
    f = B / p
    if f.exists():
        f.unlink()
        print('DEL', p)

# global sweeps
sleep_sec = re.compile(r'Task\.sleep\(for: \.seconds\((\d+(?:\.\d+)?)\)\)')
sleep_ms = re.compile(r'Task\.sleep\(for: \.milliseconds\((\d+(?:\.\d+)?)\)\)')
for f in B.rglob('*.swift'):
    if '.build' in str(f):
        continue
    t = rd(f)
    o = t
    t = t.replace('OSAllocatedUnfairLock', 'CompatLock')
    t = sleep_sec.sub(lambda m: 'Task.sleep(nanoseconds: UInt64(%s * 1_000_000_000))' % m.group(1), t)
    t = sleep_ms.sub(lambda m: 'Task.sleep(nanoseconds: UInt64(%s * 1_000_000))' % m.group(1), t)
    if t != o:
        wr(f, t)

# PlayerServiceIOS clock
p = 'Sources/Kumone/Core/Player/PlayerServiceIOS.swift'
if (B / p).exists():
    t = rd(p)
    t = t.replace('private var lastPlaybackCheckpoint = ContinuousClock.now',
                  'private var lastPlaybackCheckpoint = ProcessInfo.processInfo.systemUptime')
    t = t.replace('self.lastPlaybackCheckpoint.duration(to: .now) >= .seconds(20)',
                  'ProcessInfo.processInfo.systemUptime - self.lastPlaybackCheckpoint >= 20')
    wr(p, t)
    print('OK playerservice clock')

# DownloadManager Duration -> TimeInterval
p = 'Sources/Kumone/Core/Storage/DownloadManager.swift'
if (B / p).exists():
    t = rd(p)
    t = t.replace('private let retrySleep: (Duration) async throws -> Void',
                  'private let retrySleep: (TimeInterval) async throws -> Void')
    t = t.replace('retrySleep: @escaping (Duration) async throws -> Void = { try await Task.sleep(for: $0) }',
                  'retrySleep: @escaping (TimeInterval) async throws -> Void = { try await Task.sleep(nanoseconds: UInt64(max(0, $0) * 1_000_000_000)) }')
    t = t.replace('let delays: [Duration] = [.seconds(1), .seconds(2), .seconds(4)]',
                  'let delays: [TimeInterval] = [1, 2, 4]')
    t = re.sub(r'\.seconds\((\d+(?:\.\d+)?)\)', r'\1', t)
    wr(p, t)
    print('OK downloadmanager durations')
print('done')
