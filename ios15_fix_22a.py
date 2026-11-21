import pathlib
B = pathlib.Path('.')
def rd(p): return (B / p).read_text(encoding='utf-8')
def wr(p, t): (B / p).write_text(t, encoding='utf-8')

# .searchable needs a navigation bar to host the field. Our inline stack rendered
# the root bare on iOS 15, so the search tab had no field at all.
p = 'Sources/Kumone/Features/Shared/iOS15NavCompat.swift'
t = rd(p)
if 'NavigationView { CompatInlineStack' in t:
    print('SKIP already wrapped')
else:
    a = """        } else {
            CompatInlineStack(path: path, root: content)
        }"""
    b = """        } else {
            NavigationView {
                CompatInlineStack(path: path, root: content)
            }
            .navigationViewStyle(.stack)
        }"""
    c = """        } else {
            CompatInlineStack(path: $path, root: content)
        }"""
    d = """        } else {
            NavigationView {
                CompatInlineStack(path: $path, root: content)
            }
            .navigationViewStyle(.stack)
        }"""
    n = t.count(a) + t.count(c)
    t = t.replace(a, b).replace(c, d)
    wr(p, t)
    print('OK navigation view wrapped:', n)
print('done')
