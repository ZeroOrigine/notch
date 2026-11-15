import SwiftUI
import AppIntents

@main
struct NotchApp: App {
    @Environment(\.scenePhase) var phase
    var body: some Scene {
        WindowGroup {
            HomeScreen()
                .preferredColorScheme(.dark)
                .onOpenURL { url in
                    if url.host == "listen" { Nova.shared.listen() }
                }
                .onChange(of: phase) { _, p in if p == .active { Nova.shared.startIsland() } }
                .onAppear { Nova.shared.startIsland() }
        }
    }
}

struct Stars: View {
    var body: some View {
        TimelineView(.animation(minimumInterval: 1 / 30)) { tl in
            Canvas { ctx, size in
                let t = tl.date.timeIntervalSinceReferenceDate
                for i in 0..<120 {
                    let fx = Double((i * 7919) % 1000) / 1000, fy = Double((i * 104729) % 1000) / 1000
                    let tw = 0.3 + 0.7 * (0.5 + 0.5 * sin(t * (0.7 + Double(i % 7) * 0.3) + Double(i)))
                    let r = 0.6 + Double(i % 3) * 0.5
                    ctx.fill(Path(ellipseIn: CGRect(x: fx * size.width - r, y: fy * size.height - r, width: r * 2, height: r * 2)),
                             with: .color(novaCream.opacity(tw * 0.6)))
                }
                let period = 6.0
                let ph = t.truncatingRemainder(dividingBy: period) / period
                if ph < 0.2 {
                    let q = ph / 0.2, seed = floor(t / period)
                    let sx = abs(sin(seed * 12.9898)) * size.width * 0.7, sy = abs(sin(seed * 78.233)) * size.height * 0.4
                    let head = CGPoint(x: sx + q * 260, y: sy + q * 120), tail = CGPoint(x: head.x - 90, y: head.y - 42)
                    var p = Path(); p.move(to: tail); p.addLine(to: head)
                    ctx.stroke(p, with: .linearGradient(Gradient(colors: [.clear, novaPeach.opacity(1 - q)]), startPoint: tail, endPoint: head), lineWidth: 2)
                }
            }
        }
        .ignoresSafeArea()
    }
}

struct HomeScreen: View {
    @ObservedObject var g = Nova.shared
    @FocusState var focused: Bool

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            RadialGradient(colors: [novaOrange.opacity(0.25), .clear], center: .top, startRadius: 0, endRadius: 500).ignoresSafeArea()
            Stars()
            VStack(spacing: 14) {
                header
                chat
                chips
                inputBar
            }
            .padding(.horizontal, 16)
            .frame(maxWidth: 720)
        }
    }

    var header: some View {
        VStack(spacing: 4) {
            Orb(size: 150, fast: g.mode == "thinking" || g.mode == "speaking")
            Text(title).font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundStyle(LinearGradient(colors: [novaOrange, novaCream], startPoint: .leading, endPoint: .trailing))
            if let end = g.timerEnd {
                Text(timerInterval: Date()...end, countsDown: true).font(.system(size: 30, weight: .bold).monospacedDigit()).foregroundStyle(novaOrange)
            }
        }
        .padding(.top, 8)
    }
    var title: String {
        switch g.mode {
        case "listening": return "Listening…"
        case "thinking": return "Thinking…"
        case "speaking": return "Nova"
        default: return "Hi, I'm Nova"
        }
    }

    var chat: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 8) {
                    if g.turns.isEmpty {
                        Text("Ask me anything. Try “torch on” or “set a 5 minute timer”.")
                            .font(.system(size: 16)).foregroundStyle(.white.opacity(0.6)).multilineTextAlignment(.center).padding(.top, 30)
                    }
                    ForEach(Array(g.turns.enumerated()), id: \.offset) { pair in
                        let me = pair.element.first == "you"
                        HStack {
                            if me { Spacer(minLength: 50) }
                            Text(pair.element.last ?? "").font(.system(size: 17)).textSelection(.enabled)
                                .padding(.horizontal, 14).padding(.vertical, 10)
                                .background(RoundedRectangle(cornerRadius: 18, style: .continuous).fill(me ? novaOrange.opacity(0.3) : .white.opacity(0.09)))
                            if !me { Spacer(minLength: 50) }
                        }.id(pair.offset)
                    }
                }
            }
            .scrollIndicators(.hidden)
            .onAppear { proxy.scrollTo(g.turns.count - 1, anchor: .bottom) }
            .onChange(of: g.turns.count) { _, n in withAnimation { proxy.scrollTo(n - 1, anchor: .bottom) } }
        }
    }

    var chips: some View {
        ScrollView(.horizontal) {
            HStack(spacing: 8) {
                chip(g.torch ? "flashlight.on.fill" : "flashlight.off.fill", g.torch ? "Torch off" : "Torch") { g.setTorch(!g.torch) }
                chip("timer", "5 min") { g.startTimer(minutes: 5) }
                chip(g.voiceOn ? "speaker.wave.2.fill" : "speaker.slash.fill", g.voiceOn ? "Voice on" : "Voice off") { g.voiceOn.toggle() }
                chip("sparkles", "Island") { g.startIsland() }
                chip("plus.bubble", "New chat") { g.newChat() }
            }
        }.scrollIndicators(.hidden)
    }
    func chip(_ icon: String, _ t: String, _ a: @escaping () -> Void) -> some View {
        Button(action: a) {
            Label(t, systemImage: icon).font(.system(size: 15, weight: .semibold))
                .padding(.horizontal, 14).padding(.vertical, 9)
                .background(Capsule().fill(.white.opacity(0.1))).foregroundStyle(.white)
        }
    }

    var inputBar: some View {
        HStack(spacing: 10) {
            TextField(g.mode == "listening" ? "Listening…" : "Ask Nova", text: $g.input)
                .font(.system(size: 18)).focused($focused).submitLabel(.send).onSubmit { g.send() }
            if g.mode != "idle" {
                Button { g.stop() } label: {
                    Image(systemName: "stop.fill").frame(width: 42, height: 42).background(Circle().fill(.red)).foregroundStyle(.white)
                }
            }
            Button { g.listen() } label: {
                Image(systemName: g.mode == "listening" ? "waveform" : "mic.fill").font(.system(size: 18, weight: .bold))
                    .frame(width: 46, height: 46).background(Circle().fill(novaOrange)).foregroundStyle(.black)
            }
        }
        .padding(.leading, 18).padding(.trailing, 6).frame(height: 58)
        .background(Capsule().fill(.white.opacity(0.08)))
        .overlay(Capsule().stroke(LinearGradient(colors: [novaOrange, novaCream], startPoint: .leading, endPoint: .trailing), lineWidth: 1.5))
        .padding(.bottom, 8)
    }
}

// MARK: - Siri

struct AskNovaIntent: AppIntent {
    static var title: LocalizedStringResource = "Ask Nova"
    static var openAppWhenRun = true
    @Parameter(title: "Question") var question: String
    @MainActor func perform() async throws -> some IntentResult {
        Nova.shared.startIsland(); Nova.shared.send(question); return .result()
    }
}
struct TalkToNovaIntent: AppIntent {
    static var title: LocalizedStringResource = "Talk to Nova"
    static var openAppWhenRun = true
    @MainActor func perform() async throws -> some IntentResult {
        Nova.shared.startIsland(); Nova.shared.listen(); return .result()
    }
}
struct StartIslandIntent: AppIntent {
    static var title: LocalizedStringResource = "Start Nova Island"
    static var openAppWhenRun = true
    @MainActor func perform() async throws -> some IntentResult { Nova.shared.startIsland(); return .result() }
}
struct NovaShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(intent: TalkToNovaIntent(), phrases: ["Talk to \(.applicationName)", "Hey \(.applicationName)"], shortTitle: "Talk to Nova", systemImageName: "mic.fill")
        AppShortcut(intent: StartIslandIntent(), phrases: ["Start \(.applicationName)", "Start \(.applicationName) island"], shortTitle: "Start island", systemImageName: "sparkles")
        AppShortcut(intent: AskNovaIntent(), phrases: ["Ask \(.applicationName)"], shortTitle: "Ask Nova", systemImageName: "sparkle")
    }
}
