#!/usr/bin/env python3
"""Kumone iOS 15 patch: deployment targets + ShareLink/ImageRenderer shims + CommentShareCard."""
import pathlib
import re
import sys

BASE = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent

def patch(path, old, new):
    p = BASE / path
    if not p.exists():
        print("MISSING ", path)
        return False
    t = p.read_text(encoding="utf-8")
    if old not in t:
        print("SKIP    ", path, "| pattern not found:", old[:60])
        return False
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("OK      ", path, "|", old[:50])
    return True

# 1) deployment targets
patch("Package.swift", '.iOS("16.0")', '.iOS("15.0")')
patch("ios/KumoneIOSPackage/Package.swift", ".iOS(.v16)", ".iOS(.v15)")
patch("ios/Config/Shared.xcconfig", "IPHONEOS_DEPLOYMENT_TARGET = 16.0", "IPHONEOS_DEPLOYMENT_TARGET = 15.0")
patch("ios/project.yml", 'iOS: "16.0"', 'iOS: "15.0"')

# 2) compatibility shim
SHIM = """import SwiftUI

#if canImport(UIKit)
import UIKit
#elseif canImport(AppKit)
import AppKit
#endif

// iOS 15 兼容层。
//
// 重要：本模块内不允许再出现 ShareLink / SharePreview / Transferable / CoreTransferable。
// 它们会在编译期把 CoreTransferable.framework 写进 App 的 LC_LOAD_DYLIB，
// iOS 15 的 dyld 在运行任何 App 代码之前就中止：
//   Library not loaded: /System/Library/Frameworks/CoreTransferable.framework/CoreTransferable
// 用 #available(iOS 16.0, *) 包住也没有用 —— autolink 发生在编译期。

#if os(iOS)
typealias CompatImage = UIImage
#else
typealias CompatImage = NSImage
#endif

// MARK: - 分享

/// 替代 ShareLink：iOS 走 UIActivityViewController，macOS 走 NSSharingServicePicker。
struct CompatShareLink<Label: View>: View {
    let items: [Any]
    @ViewBuilder var label: () -> Label

    @State private var isPresented = false

    var body: some View {
        #if os(iOS)
        shareButton
            .sheet(isPresented: $isPresented) {
                ActivityViewController(items: items)
            }
        #else
        shareButton
            .background(presenter)
        #endif
    }

    private var shareButton: some View {
        Button {
            isPresented = true
        } label: {
            label()
        }
    }

    #if os(macOS)
    @ViewBuilder
    private var presenter: some View {
        if isPresented {
            SharingServicePicker(items: items)
                .frame(width: 0, height: 0)
                .onAppear {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { isPresented = false }
                }
        }
    }
    #endif
}

#if os(iOS)
private struct ActivityViewController: UIViewControllerRepresentable {
    let items: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }

    func updateUIViewController(_ controller: UIActivityViewController, context: Context) {}
}
#elseif os(macOS)
private struct SharingServicePicker: NSViewRepresentable {
    let items: [Any]

    func makeNSView(context: Context) -> NSView {
        NSView(frame: .zero)
    }

    func updateNSView(_ nsView: NSView, context: Context) {
        guard !context.coordinator.didShow else { return }
        context.coordinator.didShow = true
        DispatchQueue.main.async {
            NSSharingServicePicker(items: items)
                .show(relativeTo: nsView.bounds, of: nsView, preferredEdge: .minY)
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator() }

    final class Coordinator {
        var didShow = false
    }
}
#endif

// MARK: - 渲染

/// iOS 16+ / macOS 13+ 用 ImageRenderer（同属 SwiftUI，不引入额外框架），
/// iOS 15 退回 UIHostingController + UIGraphicsImageRenderer。
func renderViewToImage<V: View>(_ view: V, width: CGFloat, scale: CGFloat = 3) -> CompatImage? {
    if #available(iOS 16.0, macOS 13.0, *) {
        let renderer = ImageRenderer(content: view)
        renderer.scale = scale
        renderer.proposedSize = ProposedViewSize(width: width, height: nil)
        #if os(iOS)
        return renderer.uiImage
        #else
        return renderer.nsImage
        #endif
    } else {
        #if os(iOS)
        return legacyHostingImage(view, width: width, scale: scale)
        #else
        return nil
        #endif
    }
}

#if os(iOS)
private func legacyHostingImage<V: View>(_ view: V, width: CGFloat, scale: CGFloat) -> UIImage? {
    let controller = UIHostingController(rootView: view)
    controller.view.backgroundColor = .clear

    let fitting = controller.sizeThatFits(in: CGSize(width: width, height: .greatestFiniteMagnitude))
    let size = CGSize(width: width, height: max(1, fitting.height.rounded(.up)))
    controller.view.bounds = CGRect(origin: .zero, size: size)

    let format = UIGraphicsImageRendererFormat.default()
    format.scale = scale
    format.opaque = false
    return UIGraphicsImageRenderer(size: size, format: format).image { context in
        controller.view.layer.render(in: context.cgContext)
    }
}
#endif
"""
shim_path = BASE / "Sources/Kumone/Features/Shared/iOS15Shims.swift"
shim_path.parent.mkdir(parents=True, exist_ok=True)
shim_path.write_text(SHIM, encoding="utf-8")
print("OK       wrote Sources/Kumone/Features/Shared/iOS15Shims.swift")

# 3) CommentShareCard: ShareLink / ImageRenderer
p = BASE / "Sources/Kumone/Features/Shared/CommentShareCard.swift"
if p.exists():
    src = p.read_text(encoding="utf-8")
    out = src.replace("            let shared = Image(platformImage: image)\n", "")
    out, n1 = re.subn(
        r"ShareLink\([\s\S]*?\)\s*\{",
        "CompatShareLink(items: [image]) {",
        out,
    )
    out, n2 = re.subn(
        r"let renderer = ImageRenderer\(content: card\)[\s\S]*?#endif\n",
        "image = renderViewToImage(card, width: CommentShareCard.width, scale: 3)\n",
        out,
        count=1,
    )
    p.write_text(out, encoding="utf-8")
    print("OK       CommentShareCard | ShareLink->CompatShareLink:", n1, "| ImageRenderer->renderViewToImage:", n2)
else:
    print("MISSING  CommentShareCard.swift")

# 4) residual scan
pat = re.compile(r"(?<!Compat)(ShareLink|SharePreview)|Transferable|ImageRenderer")
hits = []
for base in ("Sources", "ios"):
    d = BASE / base
    if not d.exists():
        continue
    for f in d.rglob("*.swift"):
        if f.name == "iOS15Shims.swift":
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pat.search(line):
                hits.append("%s:%d: %s" % (f.relative_to(BASE), i, line.strip()))
print("--- residual ShareLink/Transferable/ImageRenderer: %d ---" % len(hits))
for h in hits[:80]:
    print(h)
