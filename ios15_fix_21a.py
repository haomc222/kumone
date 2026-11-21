import pathlib
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# install the tab page wrapper
src = B / 'ios15_tabpage.txt'
dst = B / 'Sources/Kumone/Features/Shared/IOSLegacyTabPage.swift'
if src.exists():
    wr(dst, rd(src))
    print('OK tab page wrapper installed')

NEW = """    private var legacyTabInterface: some View {
        TabView(selection: $selectedTab) {
            IOSLegacyTabPage { tabStack(.home) { HomeView() } }
                .tabItem { Label("推荐", systemImage: "house") }
                .tag(IOSTab.home)

            IOSLegacyTabPage { tabStack(.explore) { ExploreView() } }
                .tabItem { Label("精选", systemImage: "square.grid.2x2") }
                .tag(IOSTab.explore)

            IOSLegacyTabPage { tabStack(.fm) { FMView() } }
                .tabItem { Label("漫游", systemImage: "dot.radiowaves.left.and.right") }
                .tag(IOSTab.fm)

            IOSLegacyTabPage { tabStack(.search) { SearchView(query: "") } }
                .tabItem { Label("搜索", systemImage: "magnifyingglass") }
                .tag(IOSTab.search)

            IOSLegacyTabPage { tabStack(.library) { IOSLibraryView(showLogin: $showLogin) } }
                .tabItem { Label("我的", systemImage: "person.crop.circle") }
                .tag(IOSTab.library)
        }
    }

    private var customTabInterface: some View {
        legacyTabInterface
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
    wr(p, t[:i] + NEW + t[k + 1:])
    print('OK tab interface -> system TabView')
print('done')
