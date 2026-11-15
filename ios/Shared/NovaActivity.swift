import ActivityKit
import SwiftUI

struct NovaAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var mode: String          // idle, listening, thinking, speaking, timer
        var text: String
        var timerEnd: Date?
    }
    var name: String
}

let novaOrange = Color(red: 1.0, green: 0.541, blue: 0.239)
let novaPeach = Color(red: 1.0, green: 0.761, blue: 0.561)
let novaCream = Color(red: 1.0, green: 0.851, blue: 0.722)

/// Still Nova star (two tetrahedra) drawn with plain paths, so it also works inside the island.
struct NovaStar: View {
    var angle: Double = 0.7
    var body: some View {
        GeometryReader { geo in
            let W = min(geo.size.width, geo.size.height)
            let V: [[Double]] = [[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1],[-1,-1,-1],[-1,1,1],[1,-1,1],[1,1,-1]]
            let E = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3),(4,5),(4,6),(4,7),(5,6),(5,7),(6,7)]
            let P: [CGPoint] = V.map { v in
                let ay = angle, ax = 0.5
                let X = v[0]*cos(ay) - v[2]*sin(ay)
                var Z = v[0]*sin(ay) + v[2]*cos(ay)
                let Y = v[1]*cos(ax) - Z*sin(ax)
                Z = v[1]*sin(ax) + Z*cos(ax)
                let f = 3.2/(3.2+Z), s = W*0.3
                return CGPoint(x: W/2 + X*s*f, y: W/2 + Y*s*f)
            }
            ZStack {
                Circle().fill(RadialGradient(colors: [novaOrange.opacity(0.35), .clear], center: .center, startRadius: 0, endRadius: W/2))
                Path { p in for e in E { p.move(to: P[e.0]); p.addLine(to: P[e.1]) } }
                    .stroke(LinearGradient(colors: [novaOrange, novaCream], startPoint: .topLeading, endPoint: .bottomTrailing),
                            style: StrokeStyle(lineWidth: max(1, W*0.05), lineCap: .round))
                Circle().fill(Color.white).frame(width: W*0.14, height: W*0.14).shadow(color: novaOrange, radius: W*0.12)
            }
            .frame(width: W, height: W)
        }
        .aspectRatio(1, contentMode: .fit)
    }
}
