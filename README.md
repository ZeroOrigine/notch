# Notch

Nova, your AI, in a Dynamic Island. Founder-built, adopted into ZeroOrigine on 2026-11-15.
Live: https://notch.zeroorigine.com

| Folder | What | Status |
|---|---|---|
| `web/` | Website + web app (PWA). Netlify publishes this folder. | Live |
| `chrome/` | Chrome extension: the notch on top of every website. | Developer-mode install (Web Store pending) |
| `mac/` | macOS app (Swift). `./build.sh` runs tests, builds Apple + Intel, makes Notch.app. | Founder's Mac only until signed and notarized |
| `ios/` | iPhone/iPad app with a Live Activity island and Siri. Needs Xcode + XcodeGen. | Code only, not compiled yet |
| `api/notch-api/` | Supabase Edge Function on zo-platform: the one door to the model. | Live |
| `shared/` | `nova-core.js`, shared by `web/` and `chrome/`, with tests. | `node shared/tests/nova-core.test.js` |

## Design (SOLID)
- **One door.** Every client asks Nova through `notch-api`. No client holds a model key. Brakes: `NOTCH_PAUSE`, `NOTCH_DAILY_BUDGET_USD` (fail closed), limits per device / user / network. Costs in `zo_cost_logs`, answers in `notch_answers` (append-only).
- **Tools.** The server only describes tools; each client runs only the tools it declared. Mac: `ToolRegistry` (one entry per tool). Web/Chrome: `NovaCore.urlFor` + a small runner.
- **Brains.** Mac talks to the `NovaBrain` protocol: `NotchAPIBrain` (default) or `ClaudeBrain` (only when the user saves their own key: screen vision + app control).
- **Pure core.** `mac/Core.swift` and `shared/nova-core.js` hold the rules (safe links, safe files, sending keys, wire format) and are unit-tested.

## Safety rules
- Links: http/https only. Files: documents only, never programs, scripts or installers.
- Mac mouse/keyboard: Touch ID once per task, and again for any key that sends in a messaging app or browser.
- Text from pages, files, the clipboard or the screen is data, never instructions.
- Chrome microphone: an extension window listens, so websites never get microphone access.
- Web: strict Content-Security-Policy, no inline scripts, no third-party scripts.
