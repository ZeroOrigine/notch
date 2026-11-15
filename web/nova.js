// Nova star + starfield, same drawing as nova.zeroorigine.com
const NovaArt = (() => {
  const V = [[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1],[-1,-1,-1],[-1,1,1],[1,-1,1],[1,1,-1]];
  const E = [[0,1],[0,2],[0,3],[1,2],[1,3],[2,3],[4,5],[4,6],[4,7],[5,6],[5,7],[6,7]];
  const A = '#FF8A3D', B = '#FFC28F', C = '#FFD9B8', DIM = '#9A6A4A', CORE = '#FFF4E8';
  function star(cv, t, fast) {
    const g = cv.getContext('2d'), W = cv.width, cx = W / 2, sc = W * 0.22;
    g.clearRect(0, 0, W, W);
    const ay = t * 0.5 * (fast ? 4 : 1), ax = 0.5 + Math.sin(t * 0.4) * 0.2;
    const P = V.map(([x, y, z]) => {
      const X = x * Math.cos(ay) - z * Math.sin(ay); let Z = x * Math.sin(ay) + z * Math.cos(ay);
      const Y = y * Math.cos(ax) - Z * Math.sin(ax); Z = y * Math.sin(ax) + Z * Math.cos(ax);
      const f = 3.2 / (3.2 + Z); return [cx + X * sc * f, cx + Y * sc * f, Z];
    });
    const rg = g.createRadialGradient(cx, cx, 0, cx, cx, W / 2);
    rg.addColorStop(0, `rgba(255,138,61,${fast ? .3 : .16})`); rg.addColorStop(1, 'rgba(255,138,61,0)');
    g.fillStyle = rg; g.fillRect(0, 0, W, W);
    const moons = [];
    if (W >= 68) {
      const rx = W * .46, ry = W * .16, rot = -.35;
      g.save(); g.translate(cx, cx); g.rotate(rot); g.strokeStyle = 'rgba(255,138,61,.22)'; g.lineWidth = Math.max(.7, W / 280);
      g.beginPath(); g.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2); g.stroke(); g.restore();
      [2.6, 1.8, 2.2].forEach((r0, m) => {
        const th = t * (.55 + m * .18) * (fast ? 2.5 : 1) + m * 2.1, ex = rx * Math.cos(th), ey = ry * Math.sin(th);
        moons.push([cx + ex * Math.cos(rot) - ey * Math.sin(rot), cx + ex * Math.sin(rot) + ey * Math.cos(rot), Math.sin(th) > 0, Math.max(.9, r0 * W / 280)]);
      });
    }
    const dot = (x, y, r, c, a = 1, blur = 0) => { g.globalAlpha = a; g.shadowColor = A; g.shadowBlur = blur; g.fillStyle = c; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.shadowBlur = 0; g.globalAlpha = 1; };
    moons.filter(m => !m[2]).forEach(m => dot(m[0], m[1], m[3], C, .35));
    const lw = Math.min(3, Math.max(1.3, W * .0064));
    E.map(([i, j], k) => [i, j, (P[i][2] + P[j][2]) / 2, k]).sort((a, b) => b[2] - a[2]).forEach(([i, j, z, k]) => {
      const front = z < 0, gr = g.createLinearGradient(P[i][0], P[i][1], P[j][0], P[j][1]);
      gr.addColorStop(0, i < 4 ? A : B); gr.addColorStop(1, j < 4 ? A : C);
      g.globalAlpha = front ? .95 : .28; g.strokeStyle = gr; g.lineWidth = front ? lw : lw * .56; g.lineCap = 'round';
      g.beginPath(); g.moveTo(P[i][0], P[i][1]); g.lineTo(P[j][0], P[j][1]); g.stroke(); g.globalAlpha = 1;
      if (fast) { const u = (t * 1.6 + k * .37) % 1; dot(P[i][0] + (P[j][0] - P[i][0]) * u, P[i][1] + (P[j][1] - P[i][1]) * u, Math.max(.8, 1.8 * W / 280), CORE); }
    });
    const d = Math.min(4, Math.max(1.5, W * .0107));
    P.forEach(p => dot(p[0], p[1], d * (p[2] < 0 ? 1 : .6), p[2] < 0 ? C : DIM, 1, Math.min(10, Math.max(3, W * .036))));
    dot(cx, cx, Math.min(5, Math.max(2, W * .0143)) * (1 + .25 * Math.sin(t * 3) + (fast ? .6 : 0)), CORE, 1, Math.min(24, Math.max(6, W * .086)));
    moons.filter(m => m[2]).forEach(m => dot(m[0], m[1], m[3], C, 1, Math.max(2, 8 * W / 280)));
  }

  function stars(sc, t) {
    const W = sc.width = sc.clientWidth * 2, H = sc.height = sc.clientHeight * 2, g = sc.getContext('2d'); const n = Math.min(260, Math.round(W * H / 9000));
    if (!W || !H) return;
    for (let i = 0; i < n; i++) {
      const fx = ((i * 7919) % 1000) / 1000, fy = ((i * 104729) % 1000) / 1000;
      const tw = .3 + .7 * (.5 + .5 * Math.sin(t * (.8 + (i % 7) * .3) + i)), r = (.6 + (i % 3) * .45) * 2;
      g.globalAlpha = tw * .55; g.fillStyle = C; g.beginPath(); g.arc(fx * W, fy * H, r, 0, 7); g.fill();
    }
    for (let k = 0; k < 2; k++) {
      const per = 5 + k * 3, ph = ((t + k * 2.3) % per) / per; if (ph > .22) continue;
      const q = ph / .22, seed = Math.floor((t + k * 2.3) / per);
      const hx = (.15 + .6 * Math.abs(Math.sin(seed * 12.9898))) * W + q * 360, hy = (.05 + .3 * Math.abs(Math.sin(seed * 78.233))) * H + q * 140;
      const gr = g.createLinearGradient(hx - 120, hy - 46, hx, hy); gr.addColorStop(0, 'rgba(255,194,143,0)'); gr.addColorStop(1, `rgba(255,194,143,${1 - q})`);
      g.globalAlpha = 1; g.strokeStyle = gr; g.lineWidth = 3; g.beginPath(); g.moveTo(hx - 120, hy - 46); g.lineTo(hx, hy); g.stroke();
    }
    g.globalAlpha = 1;
  }

  return { star, stars };
})();
