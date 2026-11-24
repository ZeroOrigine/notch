import SwiftUI
/// A still frame of Nova's sphere with every moving part set by hand (for preview pictures only).
struct OrbStill: View {
    var size: CGFloat = 120
    var t: Double = 1
    var talk: Double = 0      // 0...1 how much the talking move shows
    var voice: Double = 0     // 0...1 loudness this instant
    var k: Double = 1
    var mood: Int = 0         // 0 none, 1 listening, 2 thinking
    var splash: Double = 0    // 0...1 entrance splash ring
    var body: some View {
        Canvas { ctx, sz in
            let W = Double(sz.width)
            let r = W * 0.40 * (1 + 0.07 * voice)
            let cx = W / 2, cy = W / 2, c = CGPoint(x: cx, y: cy)
            let prism = Orb.prism + [Orb.prism[0]]
            if mood == 1 {
                var g = ctx; g.blendMode = .plusLighter; g.addFilter(.blur(radius: W * 0.07))
                g.stroke(Path(ellipseIn: CGRect(x: cx - r, y: cy - r, width: 2 * r, height: 2 * r)),
                         with: .color(Color(red: 0.35, green: 0.65, blue: 1).opacity(0.95)), lineWidth: W * 0.07)
            }
            if mood == 2 {
                var g = ctx; g.blendMode = .plusLighter; g.addFilter(.blur(radius: W * 0.012))
                var p = Path(); p.addArc(center: c, radius: r * 1.1, startAngle: .degrees(-90), endAngle: .degrees(60), clockwise: false)
                g.stroke(p, with: .conicGradient(Gradient(colors: [Color.clear, Color(red: 0.7, green: 0.5, blue: 1), Color.white]), center: c, angle: .degrees(-95)),
                         style: StrokeStyle(lineWidth: W * 0.03, lineCap: .round))
            }
            if talk > 0.01 {
                for i in 0..<3 {
                    let p = (t / 1.5 + Double(i) / 3).truncatingRemainder(dividingBy: 1)
                    let rr = W * 0.40 * (1.02 + 0.20 * p)
                    var ring = ctx; ring.blendMode = .plusLighter; ring.addFilter(.blur(radius: max(0.5, W * 0.012)))
                    ring.opacity = talk * (1 - p) * (1 - p)
                    ring.stroke(Path(ellipseIn: CGRect(x: cx - rr, y: cy - rr, width: rr * 2, height: rr * 2)),
                                with: .conicGradient(Gradient(colors: prism), center: c, angle: .radians(t * 1.4 + Double(i))),
                                lineWidth: max(1.2, W * 0.026 * (1 - 0.5 * p)))
                }
                var halo = ctx; halo.blendMode = .plusLighter; halo.addFilter(.blur(radius: W * 0.06))
                halo.opacity = talk * (0.25 + 0.6 * voice)
                halo.stroke(Path(ellipseIn: CGRect(x: cx - r, y: cy - r, width: r * 2, height: r * 2)),
                            with: .conicGradient(Gradient(colors: prism), center: c, angle: .radians(-t * 0.9)), lineWidth: W * 0.05)
            }
            if splash > 0.01 {
                let rr = r * (1.05 + 0.25 * (1 - splash))
                var s = ctx; s.addFilter(.blur(radius: W * 0.01))
                s.opacity = splash
                s.stroke(Path(ellipseIn: CGRect(x: cx - rr * 1.25, y: cy - rr * 0.35 - r * 0.9, width: rr * 2.5, height: rr * 0.7)),
                         with: .color(.white.opacity(0.9)), lineWidth: W * 0.02)
            }
            let ball = Orb.blob(c, r, t * 0.8, 0.004 + 0.004 * k, 0)
            ctx.fill(ball, with: .radialGradient(Gradient(stops: [
                .init(color: Color.black.opacity(0.62), location: 0), .init(color: Color.black.opacity(0.40), location: 0.65),
                .init(color: Color.white.opacity(0.05), location: 1)]), center: CGPoint(x: cx, y: cy + r * 0.08), startRadius: 0, endRadius: r * 1.05))
            let phase = t * (0.9 + 1.2 * k), swell = 1 + 0.3 * k + 0.9 * voice
            func core(_ x: Double) -> Double { cy + sin((x - cx) / r * 1.7 + phase + 0.5) * 0.10 * r * swell }
            let spin = Angle.radians(0.35 * sin(t * 0.7) * k + 0.5 * talk * sin(t * 1.3))
            for (col, a, b, yo, th, bl, al) in Orb.ribbon {
                var inn = ctx; inn.clip(to: ball)
                inn.translateBy(x: cx, y: cy); inn.rotate(by: spin); inn.translateBy(x: -cx, y: -cy)
                inn.blendMode = .plusLighter; inn.addFilter(.blur(radius: max(0.3, r * bl)))
                inn.opacity = 0.55 + 0.45 * max(talk > 0 ? voice : 1, 0.3)
                inn.fill(Orb.band(cx + a * r, cx + b * r, { x in core(x) + yo * r }, th * r * (1 + 0.3 * k + 0.45 * voice)), with: .color(col.opacity(al)))
            }
            var mist = ctx; mist.clip(to: ball); mist.blendMode = .plusLighter; mist.addFilter(.blur(radius: max(0.6, r * 0.07)))
            mist.stroke(ball, with: .linearGradient(Gradient(colors: [Color.white.opacity(0.55), Color.white.opacity(0.30), Color.white.opacity(0.95)]),
                        startPoint: CGPoint(x: cx, y: cy - r), endPoint: CGPoint(x: cx, y: cy + r)), lineWidth: max(1.5, r * 0.16))
            var top = ctx; top.clip(to: ball); top.addFilter(.blur(radius: max(0.4, r * 0.05)))
            top.fill(Path(ellipseIn: CGRect(x: cx - r * 0.50, y: cy - r * 0.66, width: r * 0.20, height: r * 0.12)), with: .color(Color.white.opacity(0.75)))
            ctx.stroke(ball, with: .color(Color.white.opacity(0.50)), lineWidth: max(0.6, r * 0.016))
        }
        .frame(width: size, height: size)
    }
}
