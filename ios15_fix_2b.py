import pathlib
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

LRC = r'''    static func parseLRC(_ lrc: String) -> [(time: TimeInterval, text: String)] {
        var result: [(TimeInterval, String)] = []
        let timeTag = try! NSRegularExpression(pattern: "\\[(\\d+):(\\d+)(?:[.:](\\d+))?\\]")
        for rawLine in lrc.components(separatedBy: .newlines) {
            let line = rawLine.trimmingCharacters(in: .whitespaces)
            guard !line.isEmpty else { continue }
            let ns = line as NSString
            let full = NSRange(location: 0, length: ns.length)
            let matches = timeTag.matches(in: line, range: full)
            guard let last = matches.last else { continue }
            let content = ns.substring(from: last.range.location + last.range.length)
                .trimmingCharacters(in: .whitespaces)
            for m in matches {
                let min = Double(ns.substring(with: m.range(at: 1))) ?? 0
                let sec = Double(ns.substring(with: m.range(at: 2))) ?? 0
                var frac = 0.0
                if m.range(at: 3).location != NSNotFound {
                    let msStr = ns.substring(with: m.range(at: 3))
                    if let ms = Double(msStr) { frac = ms / pow(10, Double(msStr.count)) }
                }
                result.append((min * 60 + sec + frac, content))
            }
        }
        return result.sorted { $0.0 < $1.0 }
    }

'''

YRC = r'''    static func parseYRC(_ yrc: String) -> [LyricLine] {
        let lineTag = try! NSRegularExpression(pattern: "^\\[(\\d+),(\\d+)\\]")
        let wordTag = try! NSRegularExpression(pattern: "\\((\\d+),(\\d+),\\d+\\)([^(]*)")
        var lines: [LyricLine] = []
        for raw in yrc.components(separatedBy: .newlines) {
            let line = raw.trimmingCharacters(in: .whitespaces)
            let ns = line as NSString
            let full = NSRange(location: 0, length: ns.length)
            guard let head = lineTag.firstMatch(in: line, range: full) else { continue }
            let lineStart = (Double(ns.substring(with: head.range(at: 1))) ?? 0) / 1000
            let lineDuration = (Double(ns.substring(with: head.range(at: 2))) ?? 0) / 1000
            var words: [LyricWord] = []
            for w in wordTag.matches(in: line, range: full) {
                let piece = ns.substring(with: w.range(at: 3))
                if piece.allSatisfy(\.isWhitespace) {
                    if let last = words.indices.last {
                        words[last] = words[last].replacingText(words[last].text + piece)
                    }
                    continue
                }
                let start = (Double(ns.substring(with: w.range(at: 1))) ?? 0) / 1000
                let duration = (Double(ns.substring(with: w.range(at: 2))) ?? 0) / 1000
                words.append(LyricWord(text: piece, start: start, duration: duration))
            }
            if let first = words.indices.first {
                words[first] = words[first].replacingText(String(words[first].text.drop(while: \.isWhitespace)))
            }
            if let last = words.indices.last {
                words[last] = words[last].replacingText(trimmingTrailingWhitespace(words[last].text))
            }
            words.removeAll { $0.text.isEmpty }
            let text = words.map(\.text).joined()
            guard !text.isEmpty else { continue }
            let end = lineDuration > 0 ? lineStart + lineDuration : (words.last?.end ?? lineStart)
            lines.append(LyricLine(id: lines.count, time: lineStart, end: end, text: text, words: words))
        }
        return lines
    }

'''

p = 'Sources/Kumone/Core/Models/LyricsParser.swift'
t = rd(p)
s = t.index('    static func parseLRC(')
y = t.index('    static func parseYRC(')
e = t.index('    static func parse(_ response: LyricResponse)')
doc = t[t.index('    /// Parses the service'):y]
wr(p, t[:s] + LRC + doc + YRC + t[e:])
print('OK lyricsparser regex -> NSRegularExpression')
