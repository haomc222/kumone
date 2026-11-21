import pathlib
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

NEW = """    private var customTabInterface: some View {
        ZStack {
            page(.home) { tabStack(.home) { HomeView() } }
            page(.explore) { tabStack(.explore) { ExploreView() } }
            page(.fm) { tabStack(.fm) { FMView() } }
            page(.search) { tabStack(.search) { SearchView(query: "") } }
            page(.library) { tabStack(.library) { IOSLibraryView(showLogin: $showLogin) } }
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            VStack(spacing: 8) {
                if player.hasCurrentTrack {
                    IOSMiniPlayerBar(presentation: .legacyOverlay)
                        .nowPlayingTransitionSource(in: nowPlayingTransition)
                        .padding(.horizontal, 12)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }

                GlassTabBar(items: Self.tabItems, selection: $selectedTab) { tab in
                    popToRoot(tab)
                }
            }
            .padding(.bottom, 6)
            .frame(maxWidth: .infinity)
        }
        .animation(AppAnimation.standard, value: player.hasCurrentTrack)
    }"""

p = 'Sources/Kumone/Features/IOSMainWindow.swift'
t = rd(p)
marker = '    private var customTabInterface: some View {'
i = t.find(marker)
if i < 0:
    print('MISSING customTabInterface')
else:
    j = t.index('{', i)
    depth = 0
    k = j
    while k < len(t):
        if t[k] == '{':
            depth += 1
        elif t[k] == '}':
            depth -= 1
            if depth == 0:
                break
        k += 1
    if 'safeAreaInset(edge: .bottom' in t[i:k + 1]:
        print('SKIP already inset-based')
    else:
        wr(p, t[:i] + NEW + t[k + 1:])
        print('OK customTabInterface -> safeAreaInset')
print('done')
