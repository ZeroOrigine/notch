// Notch 2 — extra capabilities: brightness, Touch ID, face presence, privacy guard, file reading.
import Cocoa
import AVFoundation
import Vision
import LocalAuthentication
import PDFKit

// MARK: - Screen brightness (Apple Silicon, DisplayServices)

enum Brightness {
    typealias GetFn = @convention(c) (UInt32, UnsafeMutablePointer<Float>) -> Int32
    typealias SetFn = @convention(c) (UInt32, Float) -> Int32
    static let handle = dlopen("/System/Library/PrivateFrameworks/DisplayServices.framework/DisplayServices", RTLD_NOW)
    static func get() -> Float? {
        guard let h = handle, let s = dlsym(h, "DisplayServicesGetBrightness") else { return nil }
        let f = unsafeBitCast(s, to: GetFn.self)
        var v: Float = 0
        return f(CGMainDisplayID(), &v) == 0 ? v : nil
    }
    static func set(_ v: Float) {
        guard let h = handle, let s = dlsym(h, "DisplayServicesSetBrightness") else { return }
        let f = unsafeBitCast(s, to: SetFn.self)
        _ = f(CGMainDisplayID(), max(0, min(1, v)))
    }
}

// MARK: - Bluetooth power

enum Bluetooth {
    typealias GetFn = @convention(c) () -> Int32
    typealias SetFn = @convention(c) (Int32) -> Void
    static let handle = dlopen("/System/Library/Frameworks/IOBluetooth.framework/IOBluetooth", RTLD_NOW)
    static func isOn() -> Bool {
        guard let h = handle, let s = dlsym(h, "IOBluetoothPreferenceGetControllerPowerState") else { return false }
        return unsafeBitCast(s, to: GetFn.self)() == 1
    }
    static func set(_ on: Bool) {
        guard let h = handle, let s = dlsym(h, "IOBluetoothPreferenceSetControllerPowerState") else { return }
        unsafeBitCast(s, to: SetFn.self)(on ? 1 : 0)
    }
}

// MARK: - Touch ID approval

enum Approve {
    static func ask(_ reason: String) async -> Bool {
        await withCheckedContinuation { c in
            let ctx = LAContext()
            var err: NSError?
            guard ctx.canEvaluatePolicy(.deviceOwnerAuthentication, error: &err) else { c.resume(returning: false); return }
            ctx.evaluatePolicy(.deviceOwnerAuthentication, localizedReason: reason) { ok, _ in c.resume(returning: ok) }
        }
    }
}

// MARK: - Face presence (camera + Vision, all on-device)

final class FaceWatch: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    private let session = AVCaptureSession()
    private let q = DispatchQueue(label: "notch.face")
    private var last = Date.distantPast
    private(set) var running = false
    var onCount: ((Int) -> Void)?

    func start() {
        AVCaptureDevice.requestAccess(for: .video) { ok in
            guard ok else { return }
            self.q.async {
                guard !self.running else { return }
                self.session.beginConfiguration()
                self.session.sessionPreset = .low
                guard let dev = AVCaptureDevice.default(for: .video),
                      let inp = try? AVCaptureDeviceInput(device: dev),
                      self.session.canAddInput(inp) else { self.session.commitConfiguration(); return }
                self.session.addInput(inp)
                let out = AVCaptureVideoDataOutput()
                out.alwaysDiscardsLateVideoFrames = true
                out.setSampleBufferDelegate(self, queue: self.q)
                if self.session.canAddOutput(out) { self.session.addOutput(out) }
                self.session.commitConfiguration()
                self.session.startRunning()
                self.running = true
            }
        }
    }
    func stop() {
        q.async {
            guard self.running else { return }
            self.session.stopRunning()
            self.session.inputs.forEach { self.session.removeInput($0) }
            self.session.outputs.forEach { self.session.removeOutput($0) }
            self.running = false
        }
    }
    func captureOutput(_ output: AVCaptureOutput, didOutput sb: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard Date().timeIntervalSince(last) > 0.6, let px = CMSampleBufferGetImageBuffer(sb) else { return }
        last = Date()
        let req = VNDetectFaceRectanglesRequest()
        try? VNImageRequestHandler(cvPixelBuffer: px, options: [:]).perform([req])
        let faces = (req.results ?? []).filter { $0.boundingBox.width > 0.07 }.count
        DispatchQueue.main.async { self.onCount?(faces) }
    }
}

// MARK: - Privacy guard (blurs the whole screen)

@MainActor
final class PrivacyGuard {
    private var win: NSWindow?
    var isShown: Bool { win != nil }
    func show() {
        guard win == nil, let s = NSScreen.main else { return }
        let w = NSWindow(contentRect: s.frame, styleMask: .borderless, backing: .buffered, defer: false)
        w.level = .statusBar
        w.isOpaque = false
        w.backgroundColor = .clear
        w.ignoresMouseEvents = true
        w.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary]
        let v = NSVisualEffectView(frame: NSRect(origin: .zero, size: s.frame.size))
        v.material = .fullScreenUI
        v.blendingMode = .behindWindow
        v.state = .active
        w.contentView = v
        w.alphaValue = 0
        w.orderFrontRegardless()
        NSAnimationContext.runAnimationGroup { $0.duration = 0.3; w.animator().alphaValue = 1 }
        win = w
    }
    func hide() {
        guard let w = win else { return }
        win = nil
        NSAnimationContext.runAnimationGroup({ $0.duration = 0.35; w.animator().alphaValue = 0 }, completionHandler: { w.orderOut(nil) })
    }
}

// MARK: - File reading (for drop-on-notch)

enum FileReader {
    static let imageExt = ["png", "jpg", "jpeg", "gif", "webp", "heic"]
    static func isImage(_ u: URL) -> Bool { imageExt.contains(u.pathExtension.lowercased()) }

    static func text(_ u: URL) -> String {
        let ext = u.pathExtension.lowercased()
        if ext == "pdf", let d = PDFDocument(url: u) { return d.string ?? "" }
        if ["doc", "docx", "rtf", "html", "odt", "pages"].contains(ext) {
            return run("/usr/bin/textutil", ["-convert", "txt", "-stdout", u.path]).out
        }
        if let s = try? String(contentsOf: u, encoding: .utf8) { return s }
        return ""
    }

    /// Returns (mediaType, base64) — HEIC is converted to JPEG first. Large images are shrunk.
    static func imageBase64(_ u: URL) -> (String, String)? {
        let tmp = NSTemporaryDirectory() + "notch_img_\(UUID().uuidString).jpg"
        defer { try? FileManager.default.removeItem(atPath: tmp) }
        run("/usr/bin/sips", ["-s", "format", "jpeg", "-Z", "1600", u.path, "--out", tmp])
        guard let d = FileManager.default.contents(atPath: tmp) else { return nil }
        return ("image/jpeg", d.base64EncodedString())
    }
}

// MARK: - Mail

enum Mail {
    static func esc(_ s: String) -> String {
        s.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "\"", with: "\\\"")
    }
    @discardableResult
    static func compose(to: String, subject: String, body: String, send: Bool) -> String {
        osa("""
        tell application "Mail"
          set m to make new outgoing message with properties {subject:"\(esc(subject))", content:"\(esc(body))", visible:\(send ? "false" : "true")}
          tell m to make new to recipient at end of to recipients with properties {address:"\(esc(to))"}
          \(send ? "send m" : "activate")
        end tell
        """)
    }
}

// MARK: - Open at login

enum LoginItem {
    static let url = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/LaunchAgents/com.notch.app.plist")
    static func set(_ on: Bool) {
        if on {
            var path = Bundle.main.bundlePath
            if path.contains("/AppTranslocation/") || !path.hasPrefix("/") { path = "/Applications/NoTcH OS.app" }
            let plist: [String: Any] = ["Label": "com.notch.app",
                                        "ProgramArguments": ["/usr/bin/open", "-g", path, "--args", "--login"],
                                        "RunAtLoad": true]
            try? FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
            (plist as NSDictionary).write(to: url, atomically: true)
        } else {
            try? FileManager.default.removeItem(at: url)
        }
    }
}

// MARK: - Knows when Nova starts and stops talking

final class SpeechWatcher: NSObject, AVSpeechSynthesizerDelegate {
    var onStart: (() -> Void)?
    var onEnd: (() -> Void)?
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) { DispatchQueue.main.async { self.onStart?() } }
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) { DispatchQueue.main.async { self.onEnd?() } }
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) { DispatchQueue.main.async { self.onEnd?() } }
}

// MARK: - Hands: mouse and keyboard for Nova (needs Accessibility permission)

enum Hands {
    static var scale: Double = 1
    static var trusted: Bool { AXIsProcessTrusted() }
    static func ask() {
        let o = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true] as CFDictionary
        _ = AXIsProcessTrustedWithOptions(o)
    }
    static func click(_ x: Double, _ y: Double, double: Bool) {
        let p = CGPoint(x: x * scale, y: y * scale)
        let src = CGEventSource(stateID: .combinedSessionState)
        CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: p, mouseButton: .left)?.post(tap: .cghidEventTap)
        usleep(70000)
        for n in 1...(double ? 2 : 1) {
            let d = CGEvent(mouseEventSource: src, mouseType: .leftMouseDown, mouseCursorPosition: p, mouseButton: .left)
            let u = CGEvent(mouseEventSource: src, mouseType: .leftMouseUp, mouseCursorPosition: p, mouseButton: .left)
            d?.setIntegerValueField(.mouseEventClickState, value: Int64(n))
            u?.setIntegerValueField(.mouseEventClickState, value: Int64(n))
            d?.post(tap: .cghidEventTap)
            usleep(40000)
            u?.post(tap: .cghidEventTap)
            usleep(70000)
        }
    }
    static func type(_ text: String) {
        let src = CGEventSource(stateID: .combinedSessionState)
        for ch in text {
            let units = Array(String(ch).utf16)
            let d = CGEvent(keyboardEventSource: src, virtualKey: 0, keyDown: true)
            let u = CGEvent(keyboardEventSource: src, virtualKey: 0, keyDown: false)
            d?.keyboardSetUnicodeString(stringLength: units.count, unicodeString: units)
            u?.keyboardSetUnicodeString(stringLength: units.count, unicodeString: units)
            d?.post(tap: .cghidEventTap)
            u?.post(tap: .cghidEventTap)
            usleep(9000)
        }
    }
    static let keys: [String: Int] = ["return": 36, "enter": 36, "tab": 48, "space": 49, "delete": 51, "backspace": 51, "escape": 53, "esc": 53,
        "left": 123, "right": 124, "down": 125, "up": 126,
        "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9, "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17,
        "1": 18, "2": 19, "3": 20, "4": 21, "6": 22, "5": 23, "9": 25, "7": 26, "8": 28, "0": 29, "o": 31, "u": 32, "i": 34, "p": 35, "l": 37, "j": 38,
        "k": 40, "n": 45, "m": 46, ",": 43, ".": 47, "/": 44, "-": 27, "=": 24]
    static func press(_ combo: String) -> Bool {
        let parts = combo.lowercased().replacingOccurrences(of: " ", with: "").components(separatedBy: "+")
        guard let last = parts.last, let code = keys[last] else { return false }
        var flags: CGEventFlags = []
        for m in parts.dropLast() {
            if m == "cmd" || m == "command" { flags.insert(.maskCommand) }
            if m == "shift" { flags.insert(.maskShift) }
            if m == "alt" || m == "option" || m == "opt" { flags.insert(.maskAlternate) }
            if m == "ctrl" || m == "control" { flags.insert(.maskControl) }
        }
        let src = CGEventSource(stateID: .combinedSessionState)
        let d = CGEvent(keyboardEventSource: src, virtualKey: CGKeyCode(code), keyDown: true)
        let u = CGEvent(keyboardEventSource: src, virtualKey: CGKeyCode(code), keyDown: false)
        d?.flags = flags
        u?.flags = flags
        d?.post(tap: .cghidEventTap)
        usleep(30000)
        u?.post(tap: .cghidEventTap)
        return true
    }
}
