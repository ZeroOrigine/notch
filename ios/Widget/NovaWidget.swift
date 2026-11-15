import ActivityKit
import WidgetKit
import SwiftUI

@main
struct NovaIslandBundle: WidgetBundle {
    var body: some Widget { NovaLiveActivity() }
}

struct NovaLiveActivity: Widget {
    func icon(_ s: NovaAttributes.ContentState) -> String {
        switch s.mode {
        case "listening": return "mic.fill"
        case "thinking": return "sparkles"
        case "speaking": return "waveform"
        case "timer": return "timer"
        default: return "sparkle"
        }
    }
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: NovaAttributes.self) { ctx in
            // Lock Screen banner
            HStack(spacing: 12) {
                NovaStar().frame(width: 44, height: 44)
                VStack(alignment: .leading, spacing: 2) {
                    Text("Nova").font(.headline).foregroundStyle(novaPeach)
                    if let end = ctx.state.timerEnd, ctx.state.mode == "timer" {
                        Text(timerInterval: Date()...end, countsDown: true).font(.title2.monospacedDigit().bold())
                    } else {
                        Text(ctx.state.text).font(.subheadline).lineLimit(2)
                    }
                }
                Spacer()
            }
            .padding(16)
            .foregroundStyle(.white)
            .activityBackgroundTint(.black)
            .widgetURL(URL(string: "notch://ask"))
        } dynamicIsland: { ctx in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    NovaStar().frame(width: 46, height: 46).padding(.leading, 4)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Image(systemName: icon(ctx.state)).font(.title2).foregroundStyle(novaOrange).padding(.trailing, 6)
                }
                DynamicIslandExpandedRegion(.center) {
                    Text("Nova").font(.headline).foregroundStyle(novaPeach)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    if let end = ctx.state.timerEnd, ctx.state.mode == "timer" {
                        Text(timerInterval: Date()...end, countsDown: true).font(.largeTitle.monospacedDigit().bold())
                    } else {
                        HStack {
                            Text(ctx.state.text).font(.subheadline).lineLimit(2)
                            Spacer()
                            Link(destination: URL(string: "notch://listen")!) {
                                Image(systemName: "mic.fill").font(.title3).padding(10).background(Circle().fill(novaOrange)).foregroundStyle(.black)
                            }
                        }
                    }
                }
            } compactLeading: {
                NovaStar().frame(width: 22, height: 22)
            } compactTrailing: {
                if let end = ctx.state.timerEnd, ctx.state.mode == "timer" {
                    Text(timerInterval: Date()...end, countsDown: true).monospacedDigit().frame(width: 44).foregroundStyle(novaOrange)
                } else {
                    Image(systemName: icon(ctx.state)).foregroundStyle(novaOrange)
                }
            } minimal: {
                NovaStar().frame(width: 20, height: 20)
            }
            .widgetURL(URL(string: "notch://ask"))
            .keylineTint(novaOrange)
        }
    }
}
