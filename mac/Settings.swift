// Notch — preferences, action log, bug reports and the Settings window.
import Cocoa
import SwiftUI

func onMain(_ f: @escaping @MainActor () -> Void) { Task { @MainActor in f() } }
func later(_ seconds: Double, _ f: @escaping @MainActor () -> Void) {
    Task { @MainActor in
        try? await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
        f()
    }
}

// MARK: - Preferences (every feature can be switched off)

final class Prefs: ObservableObject {
    static let shared = Prefs()
    private static func b(_ k: String, _ d: Bool) -> Bool { UserDefaults.standard.object(forKey: k) as? Bool ?? d }
    private func save(_ k: String, _ v: Any) { UserDefaults.standard.set(v, forKey: k); changed?() }
    var changed: (() -> Void)?

    @Published var hoverOpen = Prefs.b("hoverOpen", true) { didSet { save("hoverOpen", hoverOpen) } }
    @Published var liveMusic = Prefs.b("liveMusic", true) { didSet { save("liveMusic", liveMusic) } }
    @Published var fileDrop = Prefs.b("fileDrop", true) { didSet { save("fileDrop", fileDrop) } }
    @Published var haptics = Prefs.b("haptics", true) { didSet { save("haptics", haptics) } }
    @Published var sounds = Prefs.b("sounds", true) { didSet { save("sounds", sounds) } }
    @Published var voiceReply = Prefs.b("voiceReply", true) { didSet { save("voiceReply", voiceReply) } }
    @Published var screenVision = Prefs.b("screenVision", true) { didSet { save("screenVision", screenVision) } }
    @Published var wakeWord = Prefs.b("wakeWord", true) { didSet { save("wakeWord", wakeWord) } }
    @Published var faceWake = Prefs.b("faceWake", false) { didSet { save("faceWake", faceWake) } }
    @Published var shoulderGuard = Prefs.b("shoulderGuard", false) { didSet { save("shoulderGuard", shoulderGuard) } }
    @Published var autoLock = Prefs.b("autoLock", false) { didSet { save("autoLock", autoLock) } }
    @Published var stealth = Prefs.b("stealth", false) { didSet { save("stealth", stealth) } }
    @Published var screenGlow = Prefs.b("screenGlow", true) { didSet { save("screenGlow", screenGlow) } }
    @Published var liquidIsland = Prefs.b("liquidIsland", true) { didSet { save("liquidIsland", liquidIsland) } }
    @Published var weather = Prefs.b("weather", true) { didSet { save("weather", weather) } }
    @Published var clipboard = Prefs.b("clipboard", true) { didSet { save("clipboard", clipboard) } }
    @Published var openAtLogin = Prefs.b("openAtLogin", false) { didSet { save("openAtLogin", openAtLogin) } }
    @Published var chatMode = Prefs.b("chatMode", true) { didSet { save("chatMode", chatMode) } }
    @Published var useApps = Prefs.b("useApps", true) { didSet { save("useApps", useApps) } }
    @Published var stars = Prefs.b("stars", true) { didSet { save("stars", stars) } }
    @Published var updateAlerts = Prefs.b("updateAlerts", true) { didSet { save("updateAlerts", updateAlerts) } }
    @Published var scale = (UserDefaults.standard.object(forKey: "scale") as? Double) ?? 0.8 { didSet { save("scale", scale) } }
    @Published var fixStyle = UserDefaults.standard.string(forKey: "fixStyle") ?? "fix spelling and grammar and make it clear" { didSet { save("fixStyle", fixStyle) } }
    @Published var translateFrom = UserDefaults.standard.string(forKey: "translateFrom") ?? "es-ES" { didSet { save("translateFrom", translateFrom) } }

    var summary: String {
        "hoverOpen=\(hoverOpen) liveMusic=\(liveMusic) fileDrop=\(fileDrop) haptics=\(haptics) sounds=\(sounds) voiceReply=\(voiceReply) screenVision=\(screenVision) wakeWord=\(wakeWord) faceWake=\(faceWake) shoulderGuard=\(shoulderGuard) autoLock=\(autoLock) stealth=\(stealth) screenGlow=\(screenGlow) weather=\(weather) translateFrom=\(translateFrom)"
    }
}

// MARK: - Action log + bug reports

enum Log {
    static let dir: URL = {
        let u = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("Notch")
        try? FileManager.default.createDirectory(at: u.appendingPathComponent("BugReports"), withIntermediateDirectories: true)
        return u
    }()
    static let file = dir.appendingPathComponent("notch.log")
    static let stamp: DateFormatter = { let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd HH:mm:ss"; return f }()

    static func add(_ s: String) {
        let line = "\(stamp.string(from: Date()))  \(s)\n"
        guard let d = line.data(using: .utf8) else { return }
        if let h = try? FileHandle(forWritingTo: file) {
            h.seekToEndOfFile(); h.write(d); try? h.close()
        } else {
            try? d.write(to: file)
        }
    }
    static func tail(_ n: Int) -> String {
        let all = (try? String(contentsOf: file, encoding: .utf8)) ?? ""
        return all.split(separator: "\n").suffix(n).joined(separator: "\n")
    }
}

/// What Nova remembers about you. A plain text file, one fact per line.
enum ChatLog {
    static let file = Log.dir.appendingPathComponent("chat.json")
    static func load() -> [[String]] {
        guard let d = try? Data(contentsOf: file), let a = try? JSONSerialization.jsonObject(with: d) as? [[String]] else { return [] }
        return a
    }
    static func save(_ turns: [[String]]) {
        if let d = try? JSONSerialization.data(withJSONObject: Array(turns.suffix(200))) { try? d.write(to: file) }
    }
}

enum Memory {
    static let file = Log.dir.appendingPathComponent("memory.txt")
    static func all() -> String { ((try? String(contentsOf: file, encoding: .utf8)) ?? "").trimmingCharacters(in: .whitespacesAndNewlines) }
    static func set(_ s: String) { try? s.trimmingCharacters(in: .whitespacesAndNewlines).write(to: file, atomically: true, encoding: .utf8) }
    static func add(_ fact: String) {
        let f = fact.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !f.isEmpty else { return }
        let cur = all()
        if cur.lowercased().contains(f.lowercased()) { return }
        set(cur.isEmpty ? "- \(f)" : cur + "\n- \(f)")
        Log.add("Memory +1")
    }
    @discardableResult
    static func forget(_ q: String) -> Int {
        let k = q.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        guard !k.isEmpty else { return 0 }
        let lines = all().components(separatedBy: "\n")
        let keep = lines.filter { !$0.lowercased().contains(k) }
        set(keep.joined(separator: "\n"))
        return lines.count - keep.count
    }
}

enum NotesApp {
    static func add(_ text: String) -> Bool {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return false }
        let html = Mail.esc(t).replacingOccurrences(of: "\n", with: "<br>")
        let r = run("/usr/bin/osascript", ["-e", "tell application \"Notes\" to make new note with properties {body:\"\(html)\"}"])
        Log.add("Quick note saved: \(r.code == 0)")
        return r.code == 0
    }
}

enum BugReport {
    static func build(_ text: String) -> String {
        let v = ProcessInfo.processInfo.operatingSystemVersion
        let app = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "?"
        return """
        NOTCH BUG REPORT
        When: \(Log.stamp.string(from: Date()))
        NoTcH OS version: \(app)
        macOS: \(v.majorVersion).\(v.minorVersion).\(v.patchVersion)
        Features: \(Prefs.shared.summary)

        WHAT HAPPENED
        \(text)

        LAST 80 ACTIONS
        \(Log.tail(80))
        """
    }
    static func save(_ text: String) -> URL? {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd_HH-mm-ss"
        let url = Log.dir.appendingPathComponent("BugReports/bug_\(f.string(from: Date())).txt")
        do { try build(text).write(to: url, atomically: true, encoding: .utf8); return url } catch { return nil }
    }
}

// MARK: - Settings window

final class UIState: ObservableObject {
    static let shared = UIState()
    @Published var key = ""
    @Published var askKey = ""
    @Published var keySaved = Keychain.get() != nil
    @Published var bug = ""
    @Published var bugStatus = ""
    @Published var memory = Memory.all()
}

@MainActor
struct SettingsView: View {
    @ObservedObject var p = Prefs.shared
    @ObservedObject var ui = UIState.shared
    @ObservedObject var up = Updater.shared

    let languages = [("Spanish", "es-ES"), ("Hindi", "hi-IN"), ("French", "fr-FR"), ("German", "de-DE"),
                     ("Punjabi", "pa-IN"), ("Marathi", "mr-IN"), ("Chinese", "zh-CN"), ("Arabic", "ar-SA")]

    var mode: AppSection? = nil
    @ViewBuilder var body: some View {
        if let m = mode {
            Group {
                switch m {
                case .ai: ai
                case .bug: report
                case .guide: guide
                default: features
                }
            }
        } else { tabs }
    }
    var tabs: some View {
        TabView {
            features.tabItem { Label("Features", systemImage: "switch.2") }
            ai.tabItem { Label("Nova AI", systemImage: "sparkles") }
            report.tabItem { Label("Report a bug", systemImage: "ladybug") }
            guide.tabItem { Label("Guide", systemImage: "book") }
        }
        .frame(width: 520, height: 560)
        .padding(14)
    }

    func row(_ title: String, _ note: String, _ v: Binding<Bool>) -> some View {
        Toggle(isOn: v) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 14, weight: .semibold))
                Text(note).font(.system(size: 12)).foregroundStyle(.secondary)
            }
        }.toggleStyle(.switch)
    }

    var features: some View {
        Form {
            Section("Software update") {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("NoTcH OS \(up.version)").font(.system(size: 14, weight: .semibold))
                        Text(up.status.isEmpty ? "Updates install here. No new download needed." : up.status)
                            .font(.system(size: 12)).foregroundStyle(.secondary)
                    }
                    Spacer()
                    if let v = up.available {
                        Button("Install \(v.version)") { Task { await up.install() } }.disabled(up.busy).buttonStyle(.borderedProminent)
                    } else {
                        Button("Check now") { Task { await up.check(quiet: false) } }.disabled(up.busy)
                    }
                }
                if let n = up.available?.notes, !n.isEmpty { Text(n).font(.system(size: 12)).foregroundStyle(.secondary) }
                row("Tell me when an update is ready", "NoTcH OS checks once a day and lets you know.", $p.updateAlerts)
            }
            Section("Screen privacy") {
                row("Screen guard", "Blurs your whole screen when a second face looks over your shoulder. Uses this Mac's camera, nothing leaves the Mac. Also in the menu bar, the Controls tab, or say “screen guard on”.", $p.shoulderGuard)
                row("Hide NoTcH OS from screen sharing", "Screenshots and shared screens (Zoom, Teams, Meet) skip NoTcH OS and your chats with Nova. A few newer capture apps may still see it.", $p.stealth)
            }
            Section("The island") {
                Picker("Island size", selection: $p.scale) {
                    Text("Small").tag(0.7)
                    Text("Medium").tag(0.8)
                    Text("Large").tag(1.0)
                }.pickerStyle(.segmented)
                row("Liquid glass island", "While Nova thinks or speaks, the notch drops into a glass island like the new iPhone.", $p.liquidIsland)
                row("Open when the mouse touches the notch", "Off: use the hotkey ⌥⌘G or the menu bar icon.", $p.hoverOpen)
                row("Show music in the notch", "Album art and controls for Spotify and Music.", $p.liveMusic)
                row("Catch dropped files", "Drag a file onto the notch to summarise or email it.", $p.fileDrop)
                row("Weather on the Home tab", "Uses your rough location from your internet address.", $p.weather)
                row("Clipboard history", "Keeps your last 20 copies in the Clips tab. Not saved to disk.", $p.clipboard)
                row("Haptic click", "A small trackpad tap when the notch opens.", $p.haptics)
                row("Sounds", "A short tone when a task finishes.", $p.sounds)
            }
            Section("Camera features (camera light stays on)") {
                row("Wake on look", "Greets you when you sit down.", $p.faceWake)
                row("Auto-lock", "Locks the Mac 30 seconds after you walk away.", $p.autoLock)
            }
            Section("Microphone features") {
                row("“Hey Nova” wake word", "Listens all the time, on this Mac only.", $p.wakeWord)
                row("Nova speaks answers aloud", "", $p.voiceReply)
                row("Chat mode", "After Nova talks, it listens again. Say “stop” or “thanks” to end.", $p.chatMode)
            }
            Section("Nova powers") {
                row("Open NoTcH OS when the Mac starts", "", $p.openAtLogin)
                row("Let Nova use apps for you", "Clicks and types inside apps. Needs a Claude key, Accessibility and Screen Recording. Asks Touch ID before send, delete, buy or pay.", $p.useApps)
                row("Starfield and shooting stars", "", $p.stars)
                row("Glowing screen edge", "A rainbow light around the screen while Nova listens or talks, like the new Siri.", $p.screenGlow)
            }
        }.formStyle(.grouped).scrollContentBackground(.hidden)
    }

    var ai: some View {
        Form {
            Section("Your own Claude key (optional)") {
                Text(ui.keySaved ? "Your key is saved in the Keychain. Nova can see your screen and use apps." : "Optional. Without a key Nova uses ZeroOrigine’s brain (free, with daily limits). Add your own key to let Nova see the screen and use apps.")
                    .font(.system(size: 13)).foregroundStyle(ui.keySaved ? Color.green : Color.orange)
                SecureField("Paste a new key", text: $ui.key)
                Button("Save key") {
                    let k = ui.key.trimmingCharacters(in: .whitespacesAndNewlines)
                    guard !k.isEmpty else { return }
                    Keychain.set(k); ui.key = ""; ui.keySaved = true; Nova.shared.hasKey = true
                }
            }
            Section("What Nova remembers about you") {
                TextEditor(text: $ui.memory).font(.system(size: 13)).frame(height: 84)
                HStack {
                    Button("Save changes") { Memory.set(ui.memory) }
                    Button("Reload") { ui.memory = Memory.all() }
                    Button("Forget everything") { Memory.set(""); ui.memory = "" }
                }
                Text("Tell Nova “remember that…” and it lands here. Stored only on this Mac.")
                    .font(.system(size: 12)).foregroundStyle(.secondary)
            }
            Section("Abilities") {
                row("Nova can look at your screen", "Only when you ask. Needs Screen Recording permission.", $p.screenVision)
                Picker("Text fixer (⌥⌘X) should", selection: $p.fixStyle) {
                    Text("Fix mistakes").tag("fix spelling and grammar and make it clear")
                    Text("Make it shorter").tag("make it shorter and clearer")
                    Text("Make it more polite").tag("make it more polite and friendly")
                    Text("Make it professional").tag("make it professional and concise")
                }
                Picker("Live translate from", selection: $p.translateFrom) {
                    ForEach(languages, id: \.1) { Text($0.0).tag($0.1) }
                }
                Text("Sending email always asks for Touch ID. This cannot be switched off.")
                    .font(.system(size: 12)).foregroundStyle(.secondary)
            }
        }.formStyle(.grouped).scrollContentBackground(.hidden)
    }

    func tip(_ icon: String, _ title: String, _ how: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon).font(.system(size: 18)).frame(width: 28).foregroundStyle(Color.accentColor)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 14, weight: .semibold))
                Text(how).font(.system(size: 12)).foregroundStyle(.secondary)
            }
        }
    }
    var guide: some View {
        Form {
            Section("Open it") {
                tip("cursorarrow.rays", "Hover the notch", "Move the mouse to the top centre of the screen.")
                tip("keyboard", "Hotkey ⌥⌘G", "Opens Nova from any app.")
                tip("waveform", "Say “Hey Nova”", "Turn it on in Features first.")
            }
            Section("Ask Nova") {
                tip("app.badge", "Open things", "“Open Excel”, “open zoho.com”, “find my close file and open it”.")
                tip("envelope", "Email", "“Email Sam the summary.” Sending always asks for Touch ID.")
                tip("eye", "Screen", "“What’s on my screen?” Nova takes one screenshot and explains it.")
                tip("globe", "Translate live", "Tap Translate live, then speak. Pick the language in Nova AI.")
                tip("sun.max", "Morning briefing", "Say “Good morning”. Nova tells you the time, weather, battery and today’s events.")
                tip("wand.and.stars", "Text fixer", "Select text in any app and press ⌥⌘X. Nova rewrites it in place. Needs Accessibility permission.")
                tip("doc.on.clipboard", "Clipboard history", "The Clips tab keeps your last 20 copies. Click one to copy it again.")
                tip("note.text", "Quick note", "Type “note: buy milk” and it saves to Apple Notes.")
                tip("brain.head.profile", "Memory", "“Remember that my manager is Sam.” Nova uses it next time.")
                tip("doc", "Files", "Drag a PDF, Word file or image onto the notch, then tap Summarise.")
            }
            Section("Controls") {
                tip("sun.max", "Brightness and volume", "Sliders in the Controls tab.")
                tip("timer", "Timers", "“Timer 25” or the buttons in Controls. Shows live in the notch.")
                tip("person.2", "Shoulder guard", "Hides the screen if a second face appears. Off by default.")
            }
            Section("Something wrong?") {
                tip("ladybug", "Report a bug", "Use the Report a bug tab. Copy the report and paste it to Claude.")
                tip("switch.2", "Switch a feature off", "Every feature has a switch in the Features tab.")
            }
        }.formStyle(.grouped).scrollContentBackground(.hidden)
    }

    var report: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("What went wrong?").font(.system(size: 15, weight: .semibold))
            Text("Write what you did and what you expected. NoTcH OS adds your settings and its last 80 actions. No passwords or keys are included.")
                .font(.system(size: 12)).foregroundStyle(.secondary)
            TextEditor(text: $ui.bug)
                .font(.system(size: 13))
                .frame(height: 200)
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(.gray.opacity(0.3)))
            HStack {
                Button("Save report") {
                    if let u = BugReport.save(ui.bug) {
                        ui.bugStatus = "Saved: \(u.lastPathComponent)"
                        NSWorkspace.shared.activateFileViewerSelecting([u])
                        ui.bug = ""
                    } else { ui.bugStatus = "Could not save the report." }
                }.disabled(ui.bug.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                Button("Copy report") {
                    NSPasteboard.general.clearContents()
                    NSPasteboard.general.setString(BugReport.build(ui.bug), forType: .string)
                    ui.bugStatus = "Copied. Paste it to Claude to get a fix."
                }.disabled(ui.bug.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                Button("Open reports folder") { NSWorkspace.shared.open(Log.dir.appendingPathComponent("BugReports")) }
            }
            Text(ui.bugStatus).font(.system(size: 12)).foregroundStyle(.secondary)
            Spacer()
        }.padding(10)
    }
}
