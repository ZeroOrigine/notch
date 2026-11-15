import SwiftUI

struct Orb: View {
    var size: CGFloat = 64
    var fast = false
    // "Nova orange" palette from the Nova site
    static let a = Color(red: 1.0, green: 0.541, blue: 0.239)      // #FF8A3D
    static let b = Color(red: 1.0, green: 0.761, blue: 0.561)      // #FFC28F
    static let c = Color(red: 1.0, green: 0.851, blue: 0.722)      // #FFD9B8
    static let dim = Color(red: 0.604, green: 0.416, blue: 0.290)  // #9A6A4A
    static let core = Color(red: 1.0, green: 0.957, blue: 0.910)   // #FFF4E8
    static let V: [[Double]] = [[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1], [-1, 1, 1], [1, -1, 1], [1, 1, -1]]
    static let E: [(Int, Int)] = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3), (4, 5), (4, 6), (4, 7), (5, 6), (5, 7), (6, 7)]

    var body: some View {
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate.truncatingRemainder(dividingBy: 100000)
            let think: Double = fast ? 1 : 0
            Canvas { ctx, sz in
                let W = Double(sz.width)
                let cx = W / 2
                let center = CGPoint(x: cx, y: cx)
                let sc = W * 0.22
                let ay = t * 0.5 * (fast ? 4 : 1)
                let ax = 0.5 + sin(t * 0.4) * 0.2
                var P: [(x: Double, y: Double, z: Double)] = []
                for v in Orb.V {
                    let X = v[0] * cos(ay) - v[2] * sin(ay)
                    var Z = v[0] * sin(ay) + v[2] * cos(ay)
                    let Y = v[1] * cos(ax) - Z * sin(ax)
                    Z = v[1] * sin(ax) + Z * cos(ax)
                    let f = 3.2 / (3.2 + Z)
                    P.append((cx + X * sc * f, cx + Y * sc * f, Z))
                }
                // glow
                ctx.fill(Path(CGRect(origin: .zero, size: sz)),
                         with: .radialGradient(Gradient(colors: [Orb.a.opacity(0.16 + think * 0.14), Orb.a.opacity(0)]), center: center, startRadius: 0, endRadius: W * 0.5))
                // orbit ring and three moons
                let rx = W * 0.46, ry = W * 0.16, rot = -0.35
                var moons: [(p: CGPoint, front: Bool, r: Double)] = []
                if W >= 34 {
                    let tr = CGAffineTransform(translationX: cx, y: cx).rotated(by: rot)
                    let ring = Path(ellipseIn: CGRect(x: -rx, y: -ry, width: rx * 2, height: ry * 2)).applying(tr)
                    ctx.stroke(ring, with: .color(Orb.a.opacity(0.22)), lineWidth: max(0.7, W / 280))
                    let radii = [2.6, 1.8, 2.2]
                    for m in 0..<3 {
                        let th = t * (0.55 + Double(m) * 0.18) * (1 + think * 1.5) + Double(m) * 2.1
                        let ex = rx * cos(th), ey = ry * sin(th)
                        let p = CGPoint(x: cx + ex * cos(rot) - ey * sin(rot), y: cx + ex * sin(rot) + ey * cos(rot))
                        moons.append((p, sin(th) > 0, max(0.9, radii[m] * W / 280)))
                    }
                }
                for mo in moons where !mo.front {
                    var g2 = ctx
                    g2.opacity = 0.35
                    g2.fill(Path(ellipseIn: CGRect(x: mo.p.x - mo.r, y: mo.p.y - mo.r, width: mo.r * 2, height: mo.r * 2)), with: .color(Orb.c))
                }
                // edges, far ones first
                let lwFront = min(3.0, max(1.3, W * 0.0064))
                var edges: [(i: Int, j: Int, z: Double)] = []
                for e in Orb.E { edges.append((e.0, e.1, (P[e.0].z + P[e.1].z) / 2)) }
                edges.sort { $0.z > $1.z }
                for (k, e) in edges.enumerated() {
                    let p0 = CGPoint(x: P[e.i].x, y: P[e.i].y)
                    let p1 = CGPoint(x: P[e.j].x, y: P[e.j].y)
                    let front = e.z < 0
                    var line = Path()
                    line.move(to: p0)
                    line.addLine(to: p1)
                    var g2 = ctx
                    g2.opacity = front ? 0.95 : 0.28
                    let grad = Gradient(colors: [e.i < 4 ? Orb.a : Orb.b, e.j < 4 ? Orb.a : Orb.c])
                    g2.stroke(line, with: .linearGradient(grad, startPoint: p0, endPoint: p1),
                              style: StrokeStyle(lineWidth: front ? lwFront : lwFront * 0.56, lineCap: .round))
                    if fast {
                        let u = (t * 1.6 + Double(k) * 0.37).truncatingRemainder(dividingBy: 1)
                        let q = CGPoint(x: p0.x + (p1.x - p0.x) * u, y: p0.y + (p1.y - p0.y) * u)
                        let pr = max(0.8, 1.8 * W / 280)
                        ctx.fill(Path(ellipseIn: CGRect(x: q.x - pr, y: q.y - pr, width: pr * 2, height: pr * 2)), with: .color(Orb.core))
                    }
                }
                // points
                let dot = min(4.0, max(1.5, W * 0.0107))
                var gd = ctx
                gd.addFilter(.shadow(color: Orb.a, radius: min(10, max(3, W * 0.036))))
                for p in P {
                    let r = dot * (p.z < 0 ? 1 : 0.6)
                    gd.fill(Path(ellipseIn: CGRect(x: p.x - r, y: p.y - r, width: r * 2, height: r * 2)), with: .color(p.z < 0 ? Orb.c : Orb.dim))
                }
                // core
                let cr = min(5.0, max(2.0, W * 0.0143)) * (1 + 0.25 * sin(t * 3) + think * 0.6)
                var g3 = ctx
                g3.addFilter(.shadow(color: Orb.a, radius: min(24, max(6, W * 0.086))))
                g3.fill(Path(ellipseIn: CGRect(x: cx - cr, y: cx - cr, width: cr * 2, height: cr * 2)), with: .color(Orb.core))
                // moons in front
                var gm = ctx
                gm.addFilter(.shadow(color: Orb.a, radius: max(2, 8 * W / 280)))
                for mo in moons where mo.front {
                    gm.fill(Path(ellipseIn: CGRect(x: mo.p.x - mo.r, y: mo.p.y - mo.r, width: mo.r * 2, height: mo.r * 2)), with: .color(Orb.c))
                }
            }
            .frame(width: size, height: size)
        }
    }
}
