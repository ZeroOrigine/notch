// Lock.swift — NoTcH OS 6.0 "Quiet lock".
// Locked: Nova does not listen, look, speak, pop up or open on hover. Only unlocking works
// (menu bar, ⌥⌘L, or Settings). It can lock itself while another app is on a call and unlock after.
import Foundation
import AppKit
import CoreAudio
import Darwin

/// Is another app using the microphone right now (a call, a meeting, a recording)?
enum CallDetector {
    /// Apps whose mic use always means a call or meeting.
    static let meetingHelpers = ["us.zoom.CptHost", "us.zoom.xos", "com.microsoft.teams2", "com.microsoft.teams",
                                 "com.apple.FaceTime", "com.cisco.webexmeetingsapp", "com.webex.meetingmanager"]

    static func onCall() -> Bool {
        if #available(macOS 14.0, *), let used = othersUsingMic() { return used }
        // Older macOS: only Zoom's meeting window can be seen without the mic list.
        return NSWorkspace.shared.runningApplications.contains { ($0.bundleIdentifier ?? "") == "us.zoom.CptHost" }
    }

    /// nil = the system did not answer (treat as unknown, never as "no call").
    @available(macOS 14.0, *)
    static func othersUsingMic() -> Bool? {
        let sys = AudioObjectID(kAudioObjectSystemObject)
        var addr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyProcessObjectList,
                                              mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var size: UInt32 = 0
        guard AudioObjectGetPropertyDataSize(sys, &addr, 0, nil, &size) == noErr, size > 0 else { return nil }
        var ids = [AudioObjectID](repeating: 0, count: Int(size) / MemoryLayout<AudioObjectID>.size)
        guard AudioObjectGetPropertyData(sys, &addr, 0, nil, &size, &ids) == noErr else { return nil }
        let me = getpid()
        let myPath = Bundle.main.bundlePath
        for id in ids {
            var pa = AudioObjectPropertyAddress(mSelector: kAudioProcessPropertyPID, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            var pid: pid_t = 0; var ps = UInt32(MemoryLayout<pid_t>.size)
            guard AudioObjectGetPropertyData(id, &pa, 0, nil, &ps, &pid) == noErr, pid > 0, pid != me else { continue }
            var ra = AudioObjectPropertyAddress(mSelector: kAudioProcessPropertyIsRunningInput, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            var running: UInt32 = 0; var rs = UInt32(MemoryLayout<UInt32>.size)
            guard AudioObjectGetPropertyData(id, &ra, 0, nil, &rs, &running) == noErr, running != 0 else { continue }
            // Count apps only: skip macOS's own listeners (Siri, dictation) and NoTcH OS itself.
            var buf = [CChar](repeating: 0, count: 4096)
            guard proc_pidpath(pid, &buf, UInt32(buf.count)) > 0 else { continue }
            let path = String(cString: buf)
            if path.hasPrefix("/System/") || path.hasPrefix("/usr/") || path.hasPrefix(myPath) { continue }
            if path.contains(".app/") { return true }
        }
        return false
    }
}

@MainActor
final class CallWatch {
    private var timer: Timer?
    private var onCount = 0, offCount = 0
    var changed: ((Bool) -> Void)?
    func start() {
        guard timer == nil else { return }
        timer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] _ in Task { @MainActor in self?.tick() } }
    }
    func stop() { timer?.invalidate(); timer = nil; onCount = 0; offCount = 0 }
    private func tick() {
        if CallDetector.onCall() { onCount += 1; offCount = 0 } else { offCount += 1; onCount = 0 }
        if onCount == 2 { changed?(true) }        // 4 seconds of a call: lock
        if offCount == 3 { changed?(false) }      // 6 seconds after it ends: unlock
    }
}
