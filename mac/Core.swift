// Core.swift — pure logic with no UI and no app state, so it can be unit-tested on its own.
// Holds: tool descriptions (ToolSpec), safety rules (Safety), text rules (NovaText),
// and the notch-api wire format (NotchWire).
import Foundation

// MARK: - Tool description (what a tool is, not what it does)

struct ToolParam {
    let name: String
    let type: String   // "string" | "number" | "boolean"
}

/// Describes one tool. The behaviour lives in ToolRegistry (Tools.swift); this part is pure data.
/// Open/closed: adding a tool means adding one ToolSpec and one runner, nothing else changes.
struct ToolSpec {
    let name: String
    let description: String
    var params: [ToolParam] = []
    var required: [String] = []
    /// Only offered when the user has their own Claude key (screen vision and mouse/keyboard control).
    var needsOwnKey = false
    /// The result is information the brain must read before answering (search, status, clipboard...).
    var returnsInfo = false
    var label: ([String: Any]) -> String = { _ in "" }

    var schema: [String: Any] {
        var props: [String: Any] = [:]
        for p in params { props[p.name] = ["type": p.type] }
        return ["name": name, "description": description,
                "input_schema": ["type": "object", "properties": props, "required": required]]
    }
    func title(_ input: [String: Any]) -> String {
        let l = label(input)
        return l.isEmpty ? name.replacingOccurrences(of: "_", with: " ").capitalized : l
    }
}

// MARK: - Safety rules

enum Safety {
    /// Only plain web links may be opened. Anything else (file:, javascript:, custom app schemes) is refused.
    static func webURL(_ raw: String) -> URL? {
        var s = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        if s.isEmpty || s.contains(" ") { return nil }
        // "javascript:..." or "mailto:..." without "//" is a scheme, not a domain. "site.com:8080" is a port and is fine.
        if !s.contains("://"), s.range(of: #"^[A-Za-z][A-Za-z0-9+.-]*:(?![0-9])"#, options: .regularExpression) != nil { return nil }
        if !s.contains("://") { s = "https://" + s }
        guard let u = URL(string: s), let scheme = u.scheme?.lowercased(),
              scheme == "https" || scheme == "http", let host = u.host, !host.isEmpty else { return nil }
        return u
    }

    static let blockedExtensions: Set<String> = [
        "app", "command", "sh", "bash", "zsh", "csh", "tool", "terminal", "scpt", "scptd", "applescript",
        "workflow", "action", "pkg", "mpkg", "dmg", "py", "rb", "pl", "php", "js", "jar", "exe", "bin",
        "dylib", "so", "kext", "plugin", "prefpane", "webloc", "inetloc", "fileloc", "shortcut", "osax", "mobileconfig",
    ]
    /// Nova may open documents, never programs, scripts, installers or links that launch things.
    static func isOpenableDocument(path: String, isExecutable: Bool, isDirectory: Bool) -> Bool {
        let ext = (path as NSString).pathExtension.lowercased()
        if blockedExtensions.contains(ext) { return false }
        if isDirectory { return true }          // a plain folder opens in Finder
        if isExecutable && ext.isEmpty { return false }
        return true
    }

    static let messagingApps: Set<String> = [
        "com.apple.mail", "com.apple.MobileSMS", "com.tinyspeck.slackmacgap", "net.whatsapp.WhatsApp",
        "com.hnc.Discord", "com.microsoft.teams2", "com.microsoft.teams", "ru.keepcoder.Telegram",
        "com.microsoft.Outlook", "com.facebook.archon", "com.readdle.smartemail-Mac", "com.google.Chrome", "com.apple.Safari",
    ]
    /// Keys that usually send, submit or post. They need Touch ID every time in a messaging app or browser.
    static func isSendingKey(_ combo: String, frontApp: String?) -> Bool {
        let c = combo.lowercased().replacingOccurrences(of: " ", with: "")
        let last = c.components(separatedBy: "+").last ?? c
        let enter = last == "return" || last == "enter"
        if enter && (c.contains("cmd") || c.contains("command") || c.contains("ctrl")) { return true }
        if enter, let app = frontApp, messagingApps.contains(app) { return true }
        if c == "cmd+d" || c == "cmd+shift+d" || c == "cmd+backspace" || c == "cmd+delete" { return true } // send in Mail, delete
        return false
    }
}

// MARK: - Text rules

enum NovaText {
    /// The em dash law: Nova never writes one.
    static func noDashes(_ s: String) -> String {
        s.replacingOccurrences(of: #"\s*[—–]\s*"#, with: ", ", options: .regularExpression)
    }
    static func trimmed(_ s: String, max: Int) -> String { s.count > max ? String(s.prefix(max)) : s }
}

// MARK: - notch-api wire format

enum NotchWire {
    static let base = "https://opgitcuqwicuiplaptkm.supabase.co/functions/v1/notch-api"

    struct Message { let role: String; let content: String }
    struct Action { let tool: String; let args: [String: Any] }
    enum Result { case answer(reply: String, actions: [Action]); case refused(String) }

    static func validDevice(_ id: String) -> Bool {
        id.range(of: #"^[A-Za-z0-9-]{16,64}$"#, options: .regularExpression) != nil
    }

    /// Request body. Keeps the last 14 messages, each at most 4000 characters (the server's own limits).
    static func body(client: String, messages: [Message], memory: [String], tools: [String], now: String) -> [String: Any] {
        let msgs = messages.suffix(14).map { ["role": $0.role, "content": NovaText.trimmed($0.content, max: 4000)] }
        return ["client": client, "messages": msgs, "memory": Array(memory.suffix(30)), "tools": tools, "now": now]
    }

    static func parse(status: Int, data: Data) -> Result {
        let j = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
        guard status == 200 else {
            let e = (j["error"] as? String) ?? "Nova is busy right now (\(status)). Try again."
            return .refused("⚠︎ " + e)
        }
        let reply = NovaText.noDashes((j["reply"] as? String ?? "").trimmingCharacters(in: .whitespacesAndNewlines))
        let acts = (j["actions"] as? [[String: Any]] ?? []).compactMap { a -> Action? in
            guard let t = a["tool"] as? String, !t.isEmpty else { return nil }
            return Action(tool: t, args: a["args"] as? [String: Any] ?? [:])
        }
        return .answer(reply: reply, actions: acts)
    }
}

// MARK: - Day and hour reading (for weather and calendar tools)

enum DayParse {
    /// "today", "tomorrow", "yesterday", "in 3 days", "3 days ago", a weekday name (next one) or YYYY-MM-DD. Empty means today.
    static func date(_ raw: String, now: Date, cal: Calendar = .current) -> Date? {
        let s = raw.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        let today = cal.startOfDay(for: now)
        if s.isEmpty || s == "today" || s == "now" || s == "tonight" { return today }
        if s == "tomorrow" { return cal.date(byAdding: .day, value: 1, to: today) }
        if s == "yesterday" { return cal.date(byAdding: .day, value: -1, to: today) }
        let nums = s.components(separatedBy: CharacterSet.decimalDigits.inverted).compactMap { Int($0) }
        if s.hasPrefix("in "), s.contains("day"), let n = nums.first { return cal.date(byAdding: .day, value: n, to: today) }
        if s.hasSuffix("ago"), s.contains("day"), let n = nums.first { return cal.date(byAdding: .day, value: -n, to: today) }
        if s.hasSuffix("ago"), s.contains("week"), let n = nums.first { return cal.date(byAdding: .day, value: -7 * n, to: today) }
        if s.hasSuffix("ago"), s.contains("year"), let n = nums.first { return cal.date(byAdding: .year, value: -n, to: today) }
        let days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        if let i = days.firstIndex(where: { s.contains($0) }) {
            let wd = cal.component(.weekday, from: today) - 1
            var add = (i - wd + 7) % 7
            if add == 0 { add = s.contains("next") ? 7 : 0 }
            return cal.date(byAdding: .day, value: add, to: today)
        }
        let f = DateFormatter()
        f.calendar = cal; f.timeZone = cal.timeZone; f.locale = Locale(identifier: "en_US_POSIX"); f.dateFormat = "yyyy-MM-dd"
        if let d = f.date(from: String(s.prefix(10))) { return cal.startOfDay(for: d) }
        return nil
    }

    /// "15", "3pm", "3 pm", "15:30", "9am", "noon", "midnight", "morning". nil when no hour was given.
    static func hour(_ raw: String) -> Int? {
        let s = raw.lowercased().replacingOccurrences(of: " ", with: "").replacingOccurrences(of: ".", with: "")
        if s.isEmpty { return nil }
        let named = ["midnight": 0, "morning": 8, "noon": 12, "midday": 12, "afternoon": 15, "evening": 18, "night": 21]
        if let h = named[s] { return h }
        let digits = s.prefix { $0.isNumber }
        guard let h = Int(digits), h >= 0, h <= 23 else { return nil }
        if s.hasSuffix("pm") { return h == 12 ? 12 : (h < 12 ? h + 12 : nil) }
        if s.hasSuffix("am") { return h == 12 ? 0 : (h < 12 ? h : nil) }
        return h
    }

    static func iso(_ d: Date, cal: Calendar = .current) -> String {
        let f = DateFormatter()
        f.calendar = cal; f.timeZone = cal.timeZone; f.locale = Locale(identifier: "en_US_POSIX"); f.dateFormat = "yyyy-MM-dd"
        return f.string(from: d)
    }
}

// MARK: - Weather words (WMO weather codes used by Open-Meteo)

enum WeatherWords {
    static func describe(_ code: Int) -> String {
        switch code {
        case 0: return "clear"
        case 1: return "mostly clear"
        case 2: return "partly cloudy"
        case 3: return "cloudy"
        case 45, 48: return "fog"
        case 51, 53, 55: return "drizzle"
        case 56, 57: return "freezing drizzle"
        case 61: return "light rain"
        case 63: return "rain"
        case 65: return "heavy rain"
        case 66, 67: return "freezing rain"
        case 71: return "light snow"
        case 73: return "snow"
        case 75: return "heavy snow"
        case 77: return "snow grains"
        case 80, 81: return "rain showers"
        case 82: return "heavy showers"
        case 85, 86: return "snow showers"
        case 95: return "thunderstorm"
        case 96, 99: return "thunderstorm with hail"
        default: return "unknown"
        }
    }
    static func icon(_ code: Int, night: Bool) -> String {
        switch code {
        case 0, 1: return night ? "moon.stars.fill" : "sun.max.fill"
        case 2: return night ? "cloud.moon.fill" : "cloud.sun.fill"
        case 3: return "cloud.fill"
        case 45, 48: return "cloud.fog.fill"
        case 51...67, 80...82: return "cloud.rain.fill"
        case 71...77, 85, 86: return "snowflake"
        case 95...99: return "cloud.bolt.fill"
        default: return "cloud.fill"
        }
    }
    /// "3 PM" style label for an hour 0-23.
    static func hourLabel(_ h: Int) -> String {
        h == 0 ? "12 AM" : h < 12 ? "\(h) AM" : h == 12 ? "12 PM" : "\(h - 12) PM"
    }
    /// One spoken line for one hour. rainChance is nil for past days (history has no chance, only amount).
    static func line(hour: Int, temp: Double, feels: Double?, code: Int, rainChance: Double?, rainMM: Double?, wind: Double?) -> String {
        var s = "\(hourLabel(hour)) \(Int(temp.rounded()))°C"
        if let f = feels, abs(f - temp) >= 2 { s += " (feels \(Int(f.rounded()))°C)" }
        s += ", \(describe(code))"
        if let c = rainChance, c >= 20 { s += ", \(Int(c))% chance of rain" }
        if let m = rainMM, m >= 0.2 { s += ", \(String(format: "%.1f", m)) mm" }
        if let w = wind, w >= 25 { s += ", wind \(Int(w.rounded())) km/h" }
        return s
    }
}
