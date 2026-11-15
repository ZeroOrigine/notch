// Unit tests for Core.swift (pure logic). Built and run by build.sh before the app is built.
import Foundation

var passed = 0, failed = 0
func check(_ ok: Bool, _ name: String, file: String = #file, line: Int = #line) {
    if ok { passed += 1 } else { failed += 1; print("FAIL line \(line): \(name)") }
}

@main struct CoreTests {
    static func main() {
        // Safety.webURL: only http/https
        check(Safety.webURL("youtube.com")?.absoluteString == "https://youtube.com", "bare domain gets https")
        check(Safety.webURL("http://example.com/a?b=1") != nil, "http allowed")
        check(Safety.webURL("file:///etc/passwd") == nil, "file: refused")
        check(Safety.webURL("javascript:alert(1)") == nil, "javascript: refused")
        check(Safety.webURL("shortcuts://run-shortcut?name=x") == nil, "custom scheme refused")
        check(Safety.webURL("x-apple.systempreferences:com.apple") == nil, "system prefs scheme refused")
        check(Safety.webURL("") == nil, "empty refused")
        check(Safety.webURL("two words") == nil, "spaces refused")

        // Safety.isOpenableDocument: documents yes, programs no
        check(Safety.isOpenableDocument(path: "/Users/a/report.pdf", isExecutable: false, isDirectory: false), "pdf ok")
        check(Safety.isOpenableDocument(path: "/Users/a/Book.xlsx", isExecutable: false, isDirectory: false), "xlsx ok")
        check(Safety.isOpenableDocument(path: "/Users/a/Projects", isExecutable: false, isDirectory: true), "folder ok")
        check(!Safety.isOpenableDocument(path: "/Applications/Terminal.app", isExecutable: false, isDirectory: true), "app refused")
        check(!Safety.isOpenableDocument(path: "/Users/a/build.command", isExecutable: true, isDirectory: false), "command refused")
        check(!Safety.isOpenableDocument(path: "/Users/a/run.sh", isExecutable: false, isDirectory: false), "sh refused")
        check(!Safety.isOpenableDocument(path: "/Users/a/setup.pkg", isExecutable: false, isDirectory: false), "pkg refused")
        check(!Safety.isOpenableDocument(path: "/Users/a/tool", isExecutable: true, isDirectory: false), "bare executable refused")
        check(!Safety.isOpenableDocument(path: "/Users/a/x.SCPT", isExecutable: false, isDirectory: false), "uppercase ext refused")

        // Safety.isSendingKey
        check(Safety.isSendingKey("cmd+return", frontApp: "com.apple.TextEdit"), "cmd+return anywhere")
        check(Safety.isSendingKey("return", frontApp: "com.apple.MobileSMS"), "return in Messages")
        check(Safety.isSendingKey("enter", frontApp: "com.tinyspeck.slackmacgap"), "enter in Slack")
        check(Safety.isSendingKey("cmd+shift+d", frontApp: "com.apple.mail"), "send in Mail")
        check(!Safety.isSendingKey("return", frontApp: "com.apple.TextEdit"), "return in TextEdit is fine")
        check(!Safety.isSendingKey("tab", frontApp: "com.apple.MobileSMS"), "tab is fine")
        check(!Safety.isSendingKey("cmd+s", frontApp: "com.apple.mail"), "save is fine")

        // NovaText
        check(NovaText.noDashes("Hi — there") == "Hi, there", "em dash removed")
        check(NovaText.noDashes("a–b") == "a, b", "en dash removed")
        check(NovaText.trimmed("abcdef", max: 3) == "abc", "trim")

        // ToolSpec schema + title
        let t = ToolSpec(name: "open_app", description: "Open an app", params: [ToolParam(name: "name", type: "string")], required: ["name"],
                         label: { "Opening \($0["name"] as? String ?? "")" })
        let schema = t.schema
        check(schema["name"] as? String == "open_app", "schema name")
        check(((schema["input_schema"] as? [String: Any])?["required"] as? [String]) == ["name"], "schema required")
        check(t.title(["name": "Excel"]) == "Opening Excel", "custom title")
        check(ToolSpec(name: "get_status", description: "").title([:]) == "Get Status", "default title")

        // NotchWire
        check(NotchWire.validDevice(UUID().uuidString), "uuid is a valid device id")
        check(!NotchWire.validDevice("short"), "short id invalid")
        check(!NotchWire.validDevice("bad id with spaces 123456"), "spaces invalid")
        let msgs = (0..<20).map { NotchWire.Message(role: $0 % 2 == 0 ? "user" : "assistant", content: String(repeating: "x", count: 5000)) }
        let body = NotchWire.body(client: "mac", messages: msgs, memory: Array(repeating: "m", count: 40), tools: ["open_app"], now: "now")
        let bm = body["messages"] as? [[String: String]] ?? []
        check(bm.count == 14, "keeps last 14 messages")
        check(bm.allSatisfy { ($0["content"] ?? "").count == 4000 }, "trims each to 4000")
        check((body["memory"] as? [String])?.count == 30, "keeps 30 memories")
        let ok = NotchWire.parse(status: 200, data: #"{"reply":"Opening it — now","actions":[{"tool":"open_url","args":{"url":"https://a.com"}},{"args":{}}]}"#.data(using: .utf8)!)
        if case .answer(let r, let a) = ok { check(r == "Opening it, now" && a.count == 1 && a[0].tool == "open_url", "parse answer") } else { check(false, "parse answer") }
        let lim = NotchWire.parse(status: 429, data: #"{"error":"limit: 30 questions an hour"}"#.data(using: .utf8)!)
        if case .refused(let m) = lim { check(m.contains("30 questions"), "parse limit") } else { check(false, "parse limit") }
        let bad = NotchWire.parse(status: 500, data: Data("not json".utf8))
        if case .refused(let m) = bad { check(m.contains("500"), "parse garbage") } else { check(false, "parse garbage") }

        print("TESTS: \(passed) passed, \(failed) failed")
        exit(failed == 0 ? 0 : 1)
    }
}
