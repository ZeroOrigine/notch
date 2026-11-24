import SwiftUI
import AppKit
let bg = LinearGradient(colors: [Color(red: 0.10, green: 0.12, blue: 0.22), Color(red: 0.28, green: 0.18, blue: 0.30)], startPoint: .topLeading, endPoint: .bottomTrailing)
struct Panel<C: View>: View {
    let n: String, title: String, sub: String
    @ViewBuilder var content: C
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 12) {
                Text(n).font(.system(size: 26, weight: .heavy)).foregroundStyle(.black).frame(width: 44, height: 44).background(Circle().fill(.white))
                VStack(alignment: .leading, spacing: 2) {
                    Text(title).font(.system(size: 28, weight: .bold)).foregroundStyle(.white)
                    Text(sub).font(.system(size: 16)).foregroundStyle(.white.opacity(0.75))
                }
            }
            content
        }
        .padding(32).frame(width: 1100, height: 600, alignment: .topLeading).background(bg)
    }
}
struct Cap: View { let s: String; var hi = false
    var body: some View { Text(s).font(.system(size: 15, weight: hi ? .bold : .regular)).foregroundStyle(hi ? .white : .white.opacity(0.7)).multilineTextAlignment(.center).frame(width: 180) } }
struct Notch: View { var body: some View { UnevenRoundedRectangle(bottomLeadingRadius: 14, bottomTrailingRadius: 14).fill(.black).frame(width: 110, height: 26) } }
struct Screen<C: View>: View { @ViewBuilder var c: C
    var body: some View { ZStack(alignment: .top) { RoundedRectangle(cornerRadius: 10).fill(Color(red: 0.55, green: 0.62, blue: 0.78)); c; Notch() }
        .frame(width: 190, height: 250).clipShape(RoundedRectangle(cornerRadius: 10)) } }

@MainActor func shot(_ v: some View, _ name: String) {
    let r = ImageRenderer(content: v); r.scale = 1.5
    guard let img = r.nsImage, let t = img.tiffRepresentation, let b = NSBitmapImageRep(data: t),
          let d = b.representation(using: .jpeg, properties: [.compressionFactor: 0.88]) else { print("fail \(name)"); return }
    try? d.write(to: URL(fileURLWithPath: name))
}

@MainActor func run() {
    // 1 word sync
    let words = ["Hey", "(pause)", "it's", "sunny", "(pause)"]
    let now: [Double] = [0.8, 0.6, 0.4, 0.9, 0.7], new: [Double] = [0.9, 0.0, 0.6, 1.0, 0.0]
    shot(Panel(n: "1", title: "Pulse on her real words", sub: "Top: today, the ball pulses on a made-up beat, even in pauses. Bottom: 6.1 pulses only when a word is spoken.") {
        ForEach(0..<2) { row in
            HStack(spacing: 0) {
                Text(row == 0 ? "Today" : "6.1").font(.system(size: 18, weight: .bold)).foregroundStyle(row == 0 ? .white.opacity(0.6) : .green).frame(width: 90)
                ForEach(0..<5) { i in
                    let v = row == 0 ? now[i] : new[i]
                    VStack(spacing: 2) { OrbStill(size: 150, t: 2 + Double(i) * 0.6, talk: row == 0 ? 1 : (v > 0 ? 1 : 0.25), voice: v)
                        Cap(s: words[i], hi: row == 1 && v > 0) }.frame(width: 190)
                }
            }
        }
    }, "m1.jpg")
    // 2 entrance and exit
    shot(Panel(n: "2", title: "Entrance and exit", sub: "She drops out of the notch with a splash, talks, then shrinks back into the notch.") {
        HStack(spacing: 18) {
            VStack { Screen { EmptyView() }; Cap(s: "1. You ask") }
            VStack { Screen { OrbStill(size: 60, t: 1).offset(y: 6) }; Cap(s: "2. She peeks out") }
            VStack { Screen { OrbStill(size: 140, t: 1.3, splash: 1).offset(y: 30) }; Cap(s: "3. Drops with a splash", hi: true) }
            VStack { Screen { OrbStill(size: 140, t: 2.1, talk: 1, voice: 0.9).offset(y: 30) }; Cap(s: "4. Talks") }
            VStack { Screen { OrbStill(size: 50, t: 3).offset(y: 2) }; Cap(s: "5. Back into the notch") }
        }.padding(.top, 20)
    }, "m2.jpg")
    // 3 motion level
    shot(Panel(n: "3", title: "Motion level (you choose)", sub: "Same moment, three settings. If your Mac has 'Reduce motion' on, Nova picks Calm by herself.") {
        HStack(spacing: 40) {
            VStack { OrbStill(size: 200, t: 2, talk: 0.0, voice: 0.0, k: 0.2); Cap(s: "Calm\nno rings, light glow", hi: true) }
            VStack { OrbStill(size: 200, t: 2, talk: 0.7, voice: 0.5); Cap(s: "Normal\nsoft rings", hi: true) }
            VStack { OrbStill(size: 200, t: 2, talk: 1, voice: 1); Cap(s: "Lively\nbig pulse, bright rings", hi: true) }
        }.padding(.leading, 120)
        VStack(alignment: .leading, spacing: 10) {
            HStack { Text("Nova's motion").foregroundStyle(.white); Spacer()
                HStack(spacing: 0) { ForEach(["Calm", "Normal", "Lively"], id: \.self) { s in
                    Text(s).font(.system(size: 14, weight: .semibold)).foregroundStyle(s == "Normal" ? .black : .white).frame(width: 80, height: 28)
                        .background(RoundedRectangle(cornerRadius: 7).fill(s == "Normal" ? Color.white : Color.clear)) } }
                .padding(2).background(RoundedRectangle(cornerRadius: 9).fill(.white.opacity(0.15))) }
            HStack { Image(systemName: "checkmark.square.fill").foregroundStyle(.blue); Text("Use Calm when the Mac's 'Reduce motion' is on").foregroundStyle(.white.opacity(0.85)) }
        }.font(.system(size: 16)).padding(18).frame(width: 640).background(RoundedRectangle(cornerRadius: 14).fill(.black.opacity(0.45))).padding(.leading, 200)
    }, "m3.jpg")
    // 4 moods
    shot(Panel(n: "4", title: "Mood colours", sub: "You can tell what Nova is doing without reading anything.") {
        HStack(spacing: 30) {
            VStack { OrbStill(size: 210, t: 1.5, k: 0.4, mood: 1); Cap(s: "Listening\nsoft blue glow", hi: true) }
            VStack { OrbStill(size: 210, t: 2.4, mood: 2); Cap(s: "Thinking\na light circles round", hi: true) }
            VStack { OrbStill(size: 210, t: 2.0, talk: 1, voice: 0.9); Cap(s: "Talking\ncolour rings", hi: true) }
            VStack { OrbStill(size: 210, t: 3, k: 0.2); Cap(s: "Idle\nquiet and clear", hi: true) }
        }.padding(.top, 30).padding(.leading, 20)
    }, "m4.jpg")
    // 5 battery
    let cards: [(String, String, String, Double)] = [("eye.slash", "Nova hidden", "Animation stops.\n0 frames a second.", 0.25),
                                                     ("battery.50", "On battery", "Draws 30 frames\na second.", 0.7),
                                                     ("powerplug", "Plugged in", "Full smooth\n60 frames a second.", 1)]
    shot(Panel(n: "5", title: "Battery saver", sub: "The glow must not drain the battery. These are my targets; I measure real CPU use before launch.") {
        HStack(spacing: 24) { ForEach(0..<3) { i in
            VStack(spacing: 12) {
                Image(systemName: cards[i].0).font(.system(size: 34)).foregroundStyle(.white)
                OrbStill(size: 150, t: 2, talk: i == 0 ? 0 : 1, voice: 0.7).opacity(cards[i].3)
                Text(cards[i].1).font(.system(size: 22, weight: .bold)).foregroundStyle(.white)
                Text(cards[i].2).font(.system(size: 16)).foregroundStyle(.white.opacity(0.8)).multilineTextAlignment(.center)
            }.frame(width: 320, height: 380).background(RoundedRectangle(cornerRadius: 20).fill(.black.opacity(0.35)))
        } }
        Text("Target: under 3% CPU while she talks.").font(.system(size: 17, weight: .semibold)).foregroundStyle(.green)
    }, "m5.jpg")
    // 6 launch clip storyboard
    let shots: [(String, String)] = [("0 to 3 s", "A Mac, just the notch"), ("3 to 6 s", "Nova drops out: \"Hey, I'm Nova.\""),
                                     ("6 to 11 s", "She talks: rings and swirl"), ("11 to 15 s", "NoTcH OS 6.1\nnotch.zeroorigine.com")]
    shot(Panel(n: "6", title: "15-second launch clip", sub: "White, calm, Apple-style. For the website, the App Store and social posts.") {
        HStack(spacing: 16) { ForEach(0..<4) { i in
            VStack(spacing: 10) {
                ZStack(alignment: .top) {
                    RoundedRectangle(cornerRadius: 12).fill(.white)
                    Notch()
                    if i == 1 { OrbStill(size: 130, t: 1.3, splash: 0.8).offset(y: 40) }
                    if i == 2 { OrbStill(size: 150, t: 2, talk: 1, voice: 0.9).offset(y: 35) }
                    if i == 3 { VStack(spacing: 8) { OrbStill(size: 80, t: 3); Text("NoTcH OS 6.1").font(.system(size: 22, weight: .bold)).foregroundStyle(.black)
                        Text("notch.zeroorigine.com").font(.system(size: 13)).foregroundStyle(.gray) }.padding(.top, 50) }
                }.frame(width: 245, height: 260).clipShape(RoundedRectangle(cornerRadius: 12))
                Text(shots[i].0).font(.system(size: 14, weight: .bold)).foregroundStyle(.green)
                Text(shots[i].1).font(.system(size: 15)).foregroundStyle(.white).multilineTextAlignment(.center).frame(width: 240)
            }
        } }.padding(.top, 10)
    }, "m6.jpg")
    print("done")
}
@main struct M { @MainActor static func main() { run() } }
