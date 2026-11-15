import SwiftUI
import ActivityKit
import AVFoundation
import Speech
import UIKit

@MainActor
final class Nova: NSObject, ObservableObject, AVSpeechSynthesizerDelegate {
    static let shared = Nova()

    @Published var turns: [[String]] = Nova.loadChat()
    @Published var input = ""
    @Published var mode = "idle"          // idle, listening, thinking, speaking
    @Published var status = ""
    @Published var torch = false
    @Published var timerEnd: Date?
    @Published var chatting = false
    @Published var voiceOn = UserDefaults.standard.object(forKey: "voiceOn") as? Bool ?? true { didSet { UserDefaults.standard.set(voiceOn, forKey: "voiceOn") } }

    let synth = AVSpeechSynthesizer()
    private var activity: Activity<NovaAttributes>?
    private var job: Task<Void, Never>?
    private let engine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?
    private var silence: Task<Void, Never>?

    override init() { super.init(); synth.delegate = self }

    // MARK: saved chat
    static var chatURL: URL { FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent("chat.json") }
    static func loadChat() -> [[String]] {
        guard let d = try? Data(contentsOf: chatURL), let a = try? JSONSerialization.jsonObject(with: d) as? [[String]] else { return [] }
        return a
    }
    func add(_ who: String, _ text: String) {
        turns.append([who, text])
        if turns.count > 200 { turns.removeFirst(turns.count - 200) }
        if let d = try? JSONSerialization.data(withJSONObject: turns) { try? d.write(to: Nova.chatURL) }
    }
    func newChat() { turns = []; try? FileManager.default.removeItem(at: Nova.chatURL) }

    static var memory: [String] {
        get { UserDefaults.standard.stringArray(forKey: "memory") ?? [] }
        set { UserDefaults.standard.set(Array(newValue.suffix(60)), forKey: "memory") }
    }

    // MARK: Dynamic Island
    func startIsland() {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }
        for a in Activity<NovaAttributes>.activities where a.id != activity?.id { Task { await a.end(nil, dismissalPolicy: .immediate) } }
        if let a = activity, a.activityState == .active { return }
        let st = NovaAttributes.ContentState(mode: "idle", text: "Tap to talk to Nova", timerEnd: nil)
        activity = try? Activity.request(attributes: NovaAttributes(name: "Nova"), content: .init(state: st, staleDate: nil), pushType: nil)
    }
    func island(_ m: String, _ text: String) {
        if activity == nil || activity?.activityState != .active { startIsland() }
        let st = NovaAttributes.ContentState(mode: timerEnd != nil && m == "idle" ? "timer" : m, text: String(text.prefix(120)), timerEnd: timerEnd)
        let a = activity
        Task { await a?.update(.init(state: st, staleDate: nil)) }
    }

    // MARK: talking to Nova
    func send(_ raw: String? = nil) {
        let text = (raw ?? input).trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, mode != "thinking" else { return }
        input = ""
        let low = text.lowercased()
        if chatting && ["stop", "bye", "thanks", "thank you", "that's all"].contains(where: { low == $0 || low.hasSuffix(" " + $0) }) {
            chatting = false; reply("Okay. I'm here when you need me."); return
        }
        add("you", text)
        if let r = local(low) { add("nova", r); reply(r); return }
        mode = "thinking"; status = "Thinking"
        island("thinking", "Thinking…")
        job = Task { @MainActor in
            let r = await self.ask()
            if Task.isCancelled { return }
            self.add("nova", r)
            self.reply(r)
        }
    }

    func reply(_ r: String) {
        status = ""
        if voiceOn && !r.hasPrefix("⚠︎") {
            mode = "speaking"; island("speaking", r)
            synth.stopSpeaking(at: .immediate)
            try? AVAudioSession.sharedInstance().setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .duckOthers])
            let u = AVSpeechUtterance(string: r)
            u.voice = AVSpeechSynthesisVoice(language: "en-GB"); u.rate = 0.5
            synth.speak(u)
        } else {
            mode = "idle"; island("idle", r)
        }
    }

    nonisolated func speechSynthesizer(_ s: AVSpeechSynthesizer, didFinish u: AVSpeechUtterance) {
        Task { @MainActor in
            self.mode = "idle"
            self.island("idle", self.turns.last?.last ?? "")
            if self.chatting { try? await Task.sleep(nanoseconds: 350_000_000); self.listen() }
        }
    }

    func stop() {
        job?.cancel(); synth.stopSpeaking(at: .immediate); stopListening()
        chatting = false; mode = "idle"; status = ""
        island("idle", "Stopped")
    }

    /// Small commands answered on the phone, no internet.
    func local(_ t: String) -> String? {
        if t.contains("torch on") || t.contains("flashlight on") || t == "torch" { setTorch(true); return "Torch on." }
        if t.contains("torch off") || t.contains("flashlight off") { setTorch(false); return "Torch off." }
        if t.contains("timer"), let n = t.split(whereSeparator: { !$0.isNumber }).first.flatMap({ Int($0) }) {
            startTimer(minutes: n); return "Timer set for \(n) minute\(n == 1 ? "" : "s")."
        }
        let sites = ["youtube": "youtube.com", "google": "google.com", "gmail": "mail.google.com", "maps": "maps.google.com",
                     "instagram": "instagram.com", "netflix": "netflix.com", "amazon": "amazon.ca", "nova": "nova.zeroorigine.com", "chatgpt": "chatgpt.com"]
        for p in ["open ", "go to "] where t.hasPrefix(p) {
            let w = t.dropFirst(p.count).replacingOccurrences(of: " please", with: "").trimmingCharacters(in: .punctuationCharacters.union(.whitespaces))
            let dom = w.contains(".") ? w : (sites[w] ?? (w.contains(" ") ? "" : w + ".com"))
            if !dom.isEmpty, let u = Safety.webURL(dom) { UIApplication.shared.open(u); return "Opening \(w)." }
        }
        for p in ["search for ", "google ", "search "] where t.hasPrefix(p) {
            let q = String(t.dropFirst(p.count))
            if let u = URL(string: "https://www.google.com/search?q=" + (q.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")) { UIApplication.shared.open(u); return "Searching for \(q)." }
        }
        if t.hasPrefix("remember ") { Nova.memory.append(String(t.dropFirst(9))); return "Got it. I'll remember." }
        return nil
    }

    func setTorch(_ on: Bool) {
        guard let d = AVCaptureDevice.default(for: .video), d.hasTorch else { return }
        try? d.lockForConfiguration(); try? d.setTorchModeOn(level: 1.0); if !on { d.torchMode = .off }; d.unlockForConfiguration()
        torch = on
    }
    func startTimer(minutes: Int) {
        timerEnd = Date().addingTimeInterval(Double(minutes) * 60)
        island("timer", "Timer")
        let end = timerEnd
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: UInt64(minutes) * 60_000_000_000)
            if self.timerEnd == end { self.timerEnd = nil; self.reply("Your timer is done.") }
        }
    }

    // MARK: Nova brain (ZeroOrigine notch-api: brakes, budget and limits live on the server)
    static let tools = ["open_url", "search_web", "youtube", "timer", "remember", "forget", "torch"]
    static var device: String {
        if let d = UserDefaults.standard.string(forKey: "notchDevice"), NotchWire.validDevice(d) { return d }
        let d = UUID().uuidString; UserDefaults.standard.set(d, forKey: "notchDevice"); return d
    }

    func ask() async -> String {
        var msgs: [NotchWire.Message] = []
        for t in turns.suffix(14) where t.count == 2 {
            let role = t[0] == "you" ? "user" : "assistant"
            if msgs.isEmpty && role != "user" { continue }
            msgs.append(.init(role: role, content: t[1]))
        }
        var req = URLRequest(url: URL(string: NotchWire.base + "/ask")!)
        req.httpMethod = "POST"; req.timeoutInterval = 45
        req.setValue("application/json", forHTTPHeaderField: "content-type")
        req.setValue(Nova.device, forHTTPHeaderField: "x-notch-device")
        req.httpBody = try? JSONSerialization.data(withJSONObject: NotchWire.body(client: "ios", messages: msgs, memory: Nova.memory, tools: Nova.tools, now: Date().description))
        guard let got = try? await URLSession.shared.data(for: req) else { return "⚠︎ No internet. Try again." }
        switch NotchWire.parse(status: (got.1 as? HTTPURLResponse)?.statusCode ?? 0, data: got.0) {
        case .refused(let m): return m
        case .answer(let reply, let actions):
            for a in actions { act(a.tool, a.args) }
            return reply.isEmpty ? "Done." : reply
        }
    }

    func act(_ name: String, _ a: [String: Any]) {
        switch name {
        case "open_url": if let u = Safety.webURL(a["url"] as? String ?? "") { UIApplication.shared.open(u) }
        case "search_web", "youtube":
            var c = URLComponents(string: name == "youtube" ? "https://www.youtube.com/results" : "https://www.google.com/search")!
            c.queryItems = [URLQueryItem(name: name == "youtube" ? "search_query" : "q", value: a["query"] as? String ?? "")]
            if let u = c.url { UIApplication.shared.open(u) }
        case "torch": setTorch((a["on"] as? Bool) ?? true)
        case "timer": startTimer(minutes: max(1, Int((a["minutes"] as? Double) ?? Double(a["minutes"] as? Int ?? 1))))
        case "remember": if let f = a["fact"] as? String { Nova.memory.append(String(f.prefix(200))) }
        case "forget": if let t = (a["text"] as? String)?.lowercased() { Nova.memory.removeAll { $0.lowercased().contains(t) } }
        default: break
        }
    }

    // MARK: voice in
    func listen() {
        if mode == "listening" { stopListening(); return }
        synth.stopSpeaking(at: .immediate)
        chatting = true
        Nova.askVoicePermission()
    }
    nonisolated static func askVoicePermission() {
        SFSpeechRecognizer.requestAuthorization { st in
            guard st == .authorized else { Task { @MainActor in Nova.shared.reply("Please allow Speech Recognition in Settings.") }; return }
            AVAudioApplication.requestRecordPermission { ok in
                Task { @MainActor in ok ? Nova.shared.beginListening() : Nova.shared.reply("Please allow the microphone in Settings.") }
            }
        }
    }
    func beginListening() {
        guard let rec = SFSpeechRecognizer(locale: Locale(identifier: "en-IN")), rec.isAvailable else { reply("Voice is not available right now."); return }
        let s = AVAudioSession.sharedInstance()
        try? s.setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker, .duckOthers])
        try? s.setActive(true, options: .notifyOthersOnDeactivation)
        let r = SFSpeechAudioBufferRecognitionRequest(); r.shouldReportPartialResults = true
        request = r
        let node = engine.inputNode
        node.removeTap(onBus: 0)
        node.installTap(onBus: 0, bufferSize: 1024, format: node.outputFormat(forBus: 0), block: Nova.tap(r))
        engine.prepare(); try? engine.start()
        mode = "listening"; input = ""
        island("listening", "Listening…")
        task = rec.recognitionTask(with: r, resultHandler: Nova.onResult)
        armSilence(first: true)
    }
    /// Audio and speech callbacks run off the main thread, so they are built outside the main actor.
    nonisolated static func tap(_ r: SFSpeechAudioBufferRecognitionRequest) -> AVAudioNodeTapBlock {
        { buf, _ in r.append(buf) }
    }
    nonisolated static func onResult(_ res: SFSpeechRecognitionResult?, _ err: Error?) {
        let text = res?.bestTranscription.formattedString
        let done = err != nil || res?.isFinal == true
        Task { @MainActor in
            let n = Nova.shared
            if let text { n.input = text; n.armSilence() }
            if done { n.finishListening() }
        }
    }
    func armSilence(first: Bool = false) {
        silence?.cancel()
        silence = Task { @MainActor in
            try? await Task.sleep(nanoseconds: first ? 6_000_000_000 : 1_400_000_000)
            if !Task.isCancelled && self.mode == "listening" { self.finishListening() }
        }
    }
    func finishListening() {
        guard mode == "listening" else { return }
        stopListening()
        if input.isEmpty { chatting = false; mode = "idle"; island("idle", "Tap to talk to Nova") } else { send() }
    }
    func stopListening() {
        silence?.cancel()
        engine.stop(); engine.inputNode.removeTap(onBus: 0)
        request?.endAudio(); task?.cancel(); request = nil; task = nil
        if mode == "listening" { mode = "idle" }
    }
}
