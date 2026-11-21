import pathlib, re
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

def replace_struct(text, header, replacement):
    i = text.find(header)
    if i < 0:
        return text, False
    depth = 0
    j = i
    while j < len(text):
        ch = text[j]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                j += 1
                break
        j += 1
    return text[:i] + replacement + text[j:], True

WHOLE = '''private struct WholePointHeight<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content.fixedSize(horizontal: false, vertical: true)
    }
}'''

p = 'Sources/Kumone/Features/Shared/CommentShareCard.swift'
t = rd(p)
t, ok = replace_struct(t, 'private struct WholePointHeight: Layout {', WHOLE)
wr(p, t)
print('OK wholepointheight', ok)

RUBY = '''private struct RubyTextLayout<Content: View>: View {
    private let box: AttributedBox
    private let content: Content

    init(attributed: NSAttributedString, @ViewBuilder content: () -> Content) {
        box = AttributedBox(attributed)
        self.content = content()
    }

    var body: some View {
        let fitted = RubyAttributedString.fittedSize(box.string, width: .greatestFiniteMagnitude)
        content.frame(width: ceil(fitted.width), height: ceil(fitted.height))
    }
}'''

p = 'Sources/Kumone/DesignSystem/RubyText.swift'
t = rd(p)
t, ok = replace_struct(t, 'private struct RubyTextLayout: Layout {', RUBY)
wr(p, t)
print('OK rubytextlayout', ok)

# simple site fixes
p = 'Sources/Kumone/Core/Player/PlayerServiceIOS.swift'
t = rd(p).replace('lastPlaybackCheckpoint = .now', 'lastPlaybackCheckpoint = ProcessInfo.processInfo.systemUptime')
wr(p, t)

p = 'Sources/Kumone/Features/Player/LyricsScrollTracking.swift'
t = rd(p)
t = t.replace('private static let holdDuration: Duration = .seconds(3)', 'private static let holdDuration: TimeInterval = 3')
t = re.sub(r'Task\.sleep\(for: holdDuration\)', 'Task.sleep(nanoseconds: UInt64(max(0, holdDuration) * 1_000_000_000))', t)
wr(p, t)

p = 'Sources/Kumone/Features/Shared/SongCommentsView.swift'
t = rd(p).replace('return detent == .large', 'return true')
wr(p, t)

# bare toolbarBackground( (implicit self)
for f in B.rglob('*.swift'):
    if '.build' in str(f):
        continue
    t = rd(f)
    n = re.sub(r'(?<![.\w])toolbarBackground\(', 'compatNoopToolbarBackground(', t)
    if n != t:
        wr(f, n)
        print('OK toolbar bare', f.name)

# nav compat generic constraint + clock instant now
p = 'Sources/Kumone/Features/Shared/iOS15NavCompat.swift'
shutil = None
t = rd(p)
t = t.replace('struct CompatNavigationStack<PathValue, Content: View>: View {',
              'struct CompatNavigationStack<PathValue: Hashable, Content: View>: View {')
wr(p, t)
print('OK navcompat constraint')

p = 'Sources/Kumone/Features/Shared/iOS15CompatMore.swift'
t = rd(p)
if 'static var now' not in t:
    t = t.replace('''struct CompatInstant: Comparable {
    let t: TimeInterval''', '''struct CompatInstant: Comparable {
    static var now: CompatInstant { CompatInstant(t: ProcessInfo.processInfo.systemUptime) }
    let t: TimeInterval''')
    wr(p, t)
    print('OK instant now')
print('done')
