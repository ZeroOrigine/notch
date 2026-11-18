// Updater.swift — NoTcH OS updates itself, like macOS Software Update.
// Reads a small feed on the website, downloads the new version, checks it is really ours
// (SHA-256 from the feed + Apple's notarization + our Developer ID team), swaps the app and reopens it.
// Nothing installs unless every check passes.
import Foundation
import AppKit
import CryptoKit

struct UpdateInfo: Decodable {
    let version: String
    let build: Int
    let url: String
    let sha256: String
    let notes: String?
}

@MainActor
final class Updater: ObservableObject {
    static let shared = Updater()
    static let feed = URL(string: "https://notch.zeroorigine.com/downloads/mac-update.json")!
    static let team = "CXGQA6L88U"

    @Published var available: UpdateInfo?
    @Published var status = ""
    @Published var busy = false
    private var timer: Timer?

    var version: String { Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "?" }
    var build: Int { Int(Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "0") ?? 0 }

    /// Check now, then once a day.
    func start() {
        Task { await check(quiet: true) }
        timer = Timer.scheduledTimer(withTimeInterval: 24 * 3600, repeats: true) { _ in
            Task { @MainActor in await Updater.shared.check(quiet: true) }
        }
    }

    func check(quiet: Bool) async {
        if busy { return }
        if !quiet { status = "Checking…" }
        var req = URLRequest(url: Updater.feed)
        req.cachePolicy = .reloadIgnoringLocalCacheData
        req.timeoutInterval = 20
        do {
            let (data, resp) = try await URLSession.shared.data(for: req)
            guard (resp as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
            let info = try JSONDecoder().decode(UpdateInfo.self, from: data)
            let wasKnown = available?.build == info.build
            if info.build > build {
                available = info
                status = "Version \(info.version) is ready to install."
                if quiet && !wasKnown && Prefs.shared.updateAlerts {
                    Nova.shared.notify("NoTcH OS \(info.version) is ready. Open the menu bar icon to update.")
                }
            } else {
                available = nil
                status = quiet ? "" : "You have the latest version (\(version))."
            }
        } catch {
            if !quiet { status = "Could not check for updates. Check the internet and try again." }
        }
    }

    func install() async {
        // Read the feed again first: what we saw earlier may be a version that has since been replaced.
        if !busy { await check(quiet: true) }
        guard let info = available, !busy, let url = URL(string: info.url),
              url.scheme == "https", url.host == Updater.feed.host else { return }
        busy = true
        defer { busy = false }
        let fm = FileManager.default
        let work = fm.temporaryDirectory.appendingPathComponent("notchos-update-\(info.build)")
        try? fm.removeItem(at: work)
        do {
            try fm.createDirectory(at: work, withIntermediateDirectories: true)
            status = "Downloading \(info.version)…"
            let (tmp, resp) = try await URLSession.shared.download(from: url)
            guard (resp as? HTTPURLResponse)?.statusCode == 200 else { throw Fail("The download failed.") }
            let zip = work.appendingPathComponent("update.zip")
            try fm.moveItem(at: tmp, to: zip)

            status = "Checking the download…"
            let digest = SHA256.hash(data: try Data(contentsOf: zip)).map { String(format: "%02x", $0) }.joined()
            guard digest == info.sha256.lowercased() else { throw Fail("The download did not match. Nothing was changed.") }

            let out = work.appendingPathComponent("app")
            try fm.createDirectory(at: out, withIntermediateDirectories: true)
            guard await Updater.bg("/usr/bin/ditto", ["-x", "-k", zip.path, out.path]).code == 0,
                  let name = try fm.contentsOfDirectory(atPath: out.path).first(where: { $0.hasSuffix(".app") })
            else { throw Fail("The download could not be opened.") }
            let newApp = out.appendingPathComponent(name)

            // Must be signed by our team and accepted by Apple's notarization check.
            let verify = await Updater.bg("/usr/bin/codesign", ["--verify", "--deep", "--strict", newApp.path])
            let who = await Updater.bg("/usr/bin/codesign", ["-dv", "--verbose=2", newApp.path])
            let apple = await Updater.bg("/usr/sbin/spctl", ["-a", "-t", "exec", newApp.path])
            guard verify.code == 0, who.text.contains("TeamIdentifier=\(Updater.team)"), apple.code == 0
            else { throw Fail("The new version failed Apple's safety check. Nothing was changed.") }

            // Swap the app after we quit, then reopen it. If the copy fails, the old app is put back.
            let dest = Bundle.main.bundlePath
            let script = work.appendingPathComponent("swap.sh")
            try """
            #!/bin/sh
            while kill -0 \(ProcessInfo.processInfo.processIdentifier) 2>/dev/null; do sleep 0.3; done
            DEST="$1"; NEW="$2"
            rm -rf "$DEST.old"
            if mv "$DEST" "$DEST.old" && /usr/bin/ditto "$NEW" "$DEST"; then rm -rf "$DEST.old"
            else rm -rf "$DEST"; mv "$DEST.old" "$DEST"; fi
            /usr/bin/open "$DEST"
            """.write(to: script, atomically: true, encoding: .utf8)
            let p = Process()
            p.executableURL = URL(fileURLWithPath: "/bin/sh")
            p.arguments = [script.path, dest, newApp.path]
            try p.run()
            status = "Installing \(info.version). NoTcH OS will reopen in a moment."
            try? await Task.sleep(nanoseconds: 600_000_000)
            Nova.shared.setAwake(false)
            NSApp.terminate(nil)
        } catch {
            status = (error as? Fail)?.text ?? "The update failed: \(error.localizedDescription)"
            try? fm.removeItem(at: work)
        }
    }

    struct Fail: Error { let text: String; init(_ t: String) { text = t } }

    /// Run a tool off the main thread so the app never freezes.
    nonisolated static func bg(_ exe: String, _ args: [String]) async -> (code: Int32, text: String) {
        await Task.detached { run(exe, args) }.value
    }

    nonisolated static func run(_ exe: String, _ args: [String]) -> (code: Int32, text: String) {
        let p = Process(); let pipe = Pipe()
        p.executableURL = URL(fileURLWithPath: exe); p.arguments = args
        p.standardOutput = pipe; p.standardError = pipe
        do { try p.run() } catch { return (-1, "") }
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        p.waitUntilExit()
        return (p.terminationStatus, String(data: data, encoding: .utf8) ?? "")
    }
}
