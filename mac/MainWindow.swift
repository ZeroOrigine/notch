// Notch — the main app window: a sidebar with one section per feature.
import Cocoa
import SwiftUI

enum AppSection: String, CaseIterable {
    case dashboard, nova, notes, timer, clips, music, controls, memory, features, ai, bug, guide
    var title: String {
        switch self {
        case .dashboard: return "Dashboard"
        case .nova: return "Nova"
        case .notes: return "Notes"
        case .timer: return "Timer"
        case .clips: return "Clipboard"
        case .music: return "Music"
        case .controls: return "Controls"
        case .memory: return "Memory"
        case .features: return "Features"
        case .ai: return "Nova settings"
        case .bug: return "Report a bug"
        case .guide: return "Guide"
        }
    }
    var icon: String {
        switch self {
        case .dashboard: return "square.grid.2x2.fill"
        case .nova: return "sparkles"
        case .notes: return "note.text"
        case .timer: return "timer"
        case .clips: return "doc.on.clipboard"
        case .music: return "music.note"
        case .controls: return "flashlight.on.fill"
        case .memory: return "brain.head.profile"
        case .features: return "switch.2"
        case .ai: return "gearshape.fill"
        case .bug: return "ladybug"
        case .guide: return "book"
        }
    }
    static let groups: [(String, [AppSection])] = [
        ("", [.dashboard, .nova]),
        ("TOOLS", [.notes, .timer, .clips, .music, .controls]),
        ("SETTINGS", [.memory, .features, .ai, .bug, .guide]),
    ]
}

final class AppState: ObservableObject {
    static let shared = AppState()
    @Published var section: AppSection = .dashboard
}

@MainActor
struct MainView: View {
    @ObservedObject var app = AppState.shared
    @ObservedObject var g = Nova.shared
    let amber = Color(red: 1.0, green: 0.56, blue: 0.24)

    var body: some View {
        HStack(spacing: 0) {
            sidebar
            Rectangle().fill(Color.white.opacity(0.08)).frame(width: 1)
            VStack(alignment: .leading, spacing: 16) {
                Text(app.section.title).font(.system(size: 28, weight: .bold))
                content
                Spacer(minLength: 0)
            }
            .padding(26)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
        .frame(minWidth: 940, maxWidth: .infinity, minHeight: 640, maxHeight: .infinity)
        .foregroundStyle(Color.white)
        .background(
            ZStack {
                Color(red: 0.07, green: 0.065, blue: 0.08)
                Aurora(on: true).opacity(0.5)
            }
        )
        .preferredColorScheme(.dark)
    }

    var sidebar: some View {
        VStack(alignment: .leading, spacing: 3) {
            HStack(spacing: 10) {
                Orb(size: 40)
                VStack(alignment: .leading, spacing: 0) {
                    Text("NoTcH OS").font(.system(size: 20, weight: .bold))
                    HStack(spacing: 4) { Text("with").font(.system(size: 11)).foregroundStyle(Color.white.opacity(0.5)); NovaWord(size: 12) }
                }
            }
            .padding(.bottom, 14).padding(.leading, 6)
            ForEach(AppSection.groups, id: \.0) { group in
                if !group.0.isEmpty {
                    Text(group.0).font(.system(size: 10, weight: .bold)).foregroundStyle(Color.white.opacity(0.4))
                        .padding(.top, 12).padding(.leading, 10).padding(.bottom, 2)
                }
                ForEach(group.1, id: \.self) { s in
                    Button { app.section = s } label: {
                        HStack(spacing: 10) {
                            Image(systemName: s.icon).font(.system(size: 14, weight: .semibold)).frame(width: 20)
                            Text(s.title).font(.system(size: 14, weight: .semibold))
                            Spacer()
                        }
                        .padding(.horizontal, 10).frame(height: 34)
                        .foregroundStyle(app.section == s ? Color.black : Color.white.opacity(0.85))
                        .background(RoundedRectangle(cornerRadius: 9, style: .continuous).fill(app.section == s ? amber : Color.clear))
                        .contentShape(Rectangle())
                    }.buttonStyle(Pop())
                }
            }
            Spacer()
            Text("Version \(Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "")")
                .font(.system(size: 11)).foregroundStyle(Color.white.opacity(0.35)).padding(.leading, 10)
        }
        .padding(14)
        .frame(width: 200)
        .background(Color.black.opacity(0.35))
    }

    @ViewBuilder var content: some View {
        switch app.section {
        case .dashboard: DashboardView()
        case .nova: VStack(spacing: 14) { card { AskView() }; card { TranscriptView() } }
        case .notes: card { NotesView() }
        case .timer: card { TimerView() }
        case .clips: card { ClipsView() }
        case .music: card { MusicView() }
        case .controls: card { ControlsView() }
        case .memory: MemoryView()
        case .features: SettingsView(mode: .features)
        case .ai: SettingsView(mode: .ai)
        case .bug: SettingsView(mode: .bug)
        case .guide: SettingsView(mode: .guide)
        }
    }
    func card<V: View>(@ViewBuilder _ v: () -> V) -> some View {
        v().padding(20)
            .frame(maxWidth: .infinity, alignment: .topLeading)
            .background(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(Color.black.opacity(0.55)))
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).stroke(Color.white.opacity(0.08)))
    }
}

@MainActor
struct DashboardView: View {
    @ObservedObject var g = Nova.shared
    let amber = Color(red: 1.0, green: 0.56, blue: 0.24)
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 14) {
                tile {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(g.greeting()).font(.system(size: 17, weight: .semibold)).foregroundStyle(Color.white.opacity(0.7))
                        TimelineView(.periodic(from: .now, by: 1)) { tl in
                            Text(tl.date, format: .dateTime.hour().minute()).font(.system(size: 54, weight: .bold, design: .rounded))
                        }
                        Text(Date(), format: .dateTime.weekday(.wide).day().month(.wide)).font(.system(size: 15)).foregroundStyle(Color.white.opacity(0.6))
                    }
                }
                tile {
                    VStack(alignment: .leading, spacing: 10) {
                        stat(g.weatherIcon, g.weatherText.isEmpty ? "Weather not loaded" : g.weatherText)
                        stat(g.battery.1 ? "battery.100.bolt" : "battery.75", "Battery \(g.battery.0)%\(g.battery.1 ? " · charging" : "")")
                        stat("music.note", g.track.map { "\($0.title) · \($0.artist)" } ?? "Nothing playing")
                        stat("timer", g.timerEnd == nil ? "No timer running" : "Timer running")
                    }
                }
            }
            Text("Quick actions").font(.system(size: 15, weight: .bold)).foregroundStyle(Color.white.opacity(0.6))
            HStack(spacing: 12) {
                action("sun.max.fill", "Morning briefing") { g.reply = g.briefing(); g.speak(g.reply) }
                action("mic.fill", "Talk to Nova") { AppDelegate.shared?.open(tab: .ask); g.toggleMic() }
                action("wand.and.stars", "Fix text  ⌥⌘X") { g.fixSelection() }
                action("camera.viewfinder", "Screenshot") { DispatchQueue.global().async { Sys.screenshot() } }
            }
            HStack(spacing: 12) {
                action("timer", "25 min focus") { g.startTimer(25); g.notify("Timer set for 25 minutes.") }
                action(g.awake ? "cup.and.saucer.fill" : "cup.and.saucer", g.awake ? "Awake: on" : "Keep awake") { g.setAwake(!g.awake) }
                action("moon.fill", g.dark ? "Light mode" : "Dark mode") { let v = !g.dark; g.dark = v; DispatchQueue.global().async { Sys.setDark(v) } }
                action("lock.fill", "Lock Mac") { Sys.lock() }
            }
            if !g.reply.isEmpty {
                HStack(alignment: .top, spacing: 12) {
                    Orb(size: 36)
                    Text(g.reply).font(.system(size: 15)).lineLimit(4).frame(maxWidth: .infinity, alignment: .leading)
                }
                .padding(14)
                .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(Color.black.opacity(0.5)))
            }
        }
    }
    func tile<V: View>(@ViewBuilder _ v: () -> V) -> some View {
        v().padding(18).frame(maxWidth: .infinity, minHeight: 150, alignment: .topLeading)
            .background(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(Color.black.opacity(0.55)))
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).stroke(Color.white.opacity(0.08)))
    }
    func stat(_ icon: String, _ text: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: icon).symbolRenderingMode(.multicolor).font(.system(size: 16)).frame(width: 24)
            Text(text).font(.system(size: 15, weight: .medium)).lineLimit(1)
        }
    }
    func action(_ icon: String, _ title: String, _ a: @escaping () -> Void) -> some View {
        Button(action: a) {
            VStack(spacing: 8) {
                Image(systemName: icon).font(.system(size: 22, weight: .semibold)).foregroundStyle(amber)
                Text(title).font(.system(size: 13, weight: .semibold)).lineLimit(1).minimumScaleFactor(0.8)
            }
            .frame(maxWidth: .infinity).frame(height: 78)
            .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(Color.white.opacity(0.07)))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Color.white.opacity(0.08)))
        }.buttonStyle(Pop())
    }
}

@MainActor
struct MemoryView: View {
    @ObservedObject var ui = UIState.shared
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("This is what Nova remembers about you. One fact per line. It stays on this Mac.")
                .font(.system(size: 14)).foregroundStyle(Color.white.opacity(0.6))
            TextEditor(text: $ui.memory)
                .font(.system(size: 15))
                .scrollContentBackground(.hidden)
                .padding(12)
                .frame(height: 320)
                .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(Color.black.opacity(0.55)))
            HStack(spacing: 10) {
                Button("Save changes") { Memory.set(ui.memory) }
                Button("Reload") { ui.memory = Memory.all() }
                Button("Forget everything") { Memory.set(""); ui.memory = "" }
            }
            Text("Tip: say “Hey Nova, remember that my manager is Sam.”").font(.system(size: 13)).foregroundStyle(Color.white.opacity(0.5))
        }
        .onAppear { ui.memory = Memory.all() }
    }
}
