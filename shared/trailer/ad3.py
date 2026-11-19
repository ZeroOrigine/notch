# NoTcH OS trailer v3: the full advertisement. 128 beats at 100 bpm = 76.8 s, 1920x1080, 30 fps.
# Adds to v2: floating light, light sweeps over the lettering, lens streaks on the hits, the rainbow screen edge,
# a twelve-cut montage of the smaller features, the three places it runs, and a strobe build before the title.
import sys, math, os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R1
from render import load_orbs, ORB_N, homography, text_sprite, ease, out, pulse, FONT_BLACK, FONT_BOLD, blit
from ad import studio, over, shadow, orb, finish, macbook, card, dashboard, to_f, FEATS, F, W, H, FPS, BEAT, OUT

rng = np.random.default_rng(11)

# ---------- floating soft lights (depth, not stars) ----------
def disc(r):
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32); d = np.hypot(x, y) / r
    return (np.clip(1 - d, 0, 1) ** 0.6 * (d < 1))[:, :, None]
DISCS = [cv2.GaussianBlur(disc(r), (0, 0), r * 0.18)[:, :, None] if False else disc(r) for r in (26, 44, 70, 110)]
BK = [(rng.uniform(0, W), rng.uniform(0, H), rng.integers(0, 4), rng.uniform(0.3, 1.0), rng.uniform(0, 6.28), rng.uniform(0.5, 1.0, 3)) for _ in range(34)]
def bokeh(c, t, gain=1.0, tint=(1, 1, 1)):
    for x, y, k, sp, ph, col in BK:
        px = (x + t * 26 * sp * (1 + k)) % (W + 300) - 150; py = y + 40 * math.sin(t * 0.5 * sp + ph)
        a = 0.035 * gain * (0.6 + 0.4 * math.sin(t * 0.9 + ph)) * (1.4 - k * 0.25)
        blit(c, DISCS[k] * (np.array(col, np.float32) * np.array(tint, np.float32)), px, py, a)

def text(c, spr, cx, cy, alpha=1.0, color=(1, 1, 1), scale=1.0, yaw=0.0, pitch=0.0, sweep=None):
    """Lettering. sweep (0..1) passes a band of light across it."""
    if alpha <= 0.003: return
    h, w = spr.shape
    m = cv2.warpPerspective(spr, homography(w, h, cx, cy, scale, yaw, pitch), (W, H), flags=cv2.INTER_LINEAR)
    a = m[:, :, None] * alpha
    c *= (1 - a); c += a * np.array(color, np.float32)
    if sweep is not None and 0 < sweep < 1:
        pos = cx - w * scale * 0.7 + sweep * w * scale * 1.4
        band = np.exp(-(((R1.xx - pos) + (R1.yy - cy) * 0.5) / 70.0) ** 2)
        c += (m * band * 0.9 * alpha)[:, :, None]

def text_left(c, spr, x, cy, alpha=1.0, color=(1, 1, 1), fit=820, sweep=None):
    sc = min(1.0, fit / (spr.shape[1] - 80))
    text(c, spr, x + (spr.shape[1] / 2 - 40) * sc, cy, alpha, color, sc, sweep=sweep)

def floor(c, cx, y, w, gain=0.35):
    """A soft pool of light under the product, so it sits on something."""
    g = np.exp(-(((R1.xx - cx) / w) ** 2 + ((R1.yy - y) / 46.0) ** 2)); c += g[:, :, None] * gain

# rainbow screen edge, like the app's "glowing screen edge"
def edge_glow(scr, strength):
    if strength <= 0.02: return
    h, w = scr.shape[:2]
    m = np.zeros((h, w), np.float32); cv2.rectangle(m, (6, 38), (w - 7, h - 7), 1.0, 14); m = cv2.GaussianBlur(m, (0, 0), 16)
    ang = np.arctan2(np.linspace(-1, 1, h, dtype=np.float32)[:, None], np.linspace(-1, 1, w, dtype=np.float32)[None, :])
    rain = np.stack([0.5 + 0.5 * np.cos(ang * 2 + p) for p in (0.0, 2.1, 4.2)], 2)
    m = m * (scr.max(2) > 0.03)          # never paint over the black island itself
    scr += rain * m[:, :, None] * 1.6 * strength

# ---------- device pictures for "where it runs" ----------
def browser(orbs, t):
    BW, BH = 900, 580
    im = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, BW - 1, BH - 1], radius=22, fill=(245, 246, 250, 255), outline=(150, 154, 165, 255), width=2)
    d.rounded_rectangle([0, 0, BW - 1, 70], radius=22, fill=(222, 225, 232, 255)); d.rectangle([0, 40, BW - 1, 70], fill=(222, 225, 232, 255))
    for i, col in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]): d.ellipse([20 + i * 26, 16, 36 + i * 26, 32], fill=col)
    d.rounded_rectangle([130, 34, 770, 62], radius=14, fill=(255, 255, 255, 255)); d.text((150, 38), "any website", font=F(18), fill=(120, 124, 135))
    for i in range(5): d.rounded_rectangle([70, 230 + i * 56, 830 - (i % 3) * 150, 262 + i * 56], radius=10, fill=(214, 218, 226, 255))
    d.rounded_rectangle([BW / 2 - 190, 70, BW / 2 + 190, 200], radius=44, fill=(0, 0, 0, 255)); d.rectangle([BW / 2 - 190, 70, BW / 2 + 190, 110], fill=(0, 0, 0, 255))
    d.text((BW / 2 - 20, 118), "Ask Nova…", font=F(26), fill=(255, 255, 255))
    rgb, al = to_f(im); s = 96; spr = cv2.resize(orbs[int(t * 14) % ORB_N], (s, s), interpolation=cv2.INTER_AREA)
    x0 = BW // 2 - 150; rgb[86:86 + s, x0:x0 + s] = np.maximum(rgb[86:86 + s, x0:x0 + s], spr)
    return rgb, al

def phone(orbs, t):
    PW, PH = 380, 780
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], radius=64, fill=(12, 12, 16, 255), outline=(150, 154, 165, 255), width=5)
    d.rounded_rectangle([14, 14, PW - 15, PH - 15], radius=52, fill=(22, 24, 44, 255))
    d.rounded_rectangle([PW / 2 - 130, 34, PW / 2 + 130, 190], radius=50, fill=(0, 0, 0, 255))
    d.text((PW / 2 - 62, 150), "Listening…", font=F(24), fill=(255, 255, 255))
    for i, s in enumerate(["Set a 5 minute timer", "Done. Timer is running."]):
        y = 300 + i * 120; mine = i == 0
        d.rounded_rectangle([40 if not mine else 70, y, PW - 40 if mine else PW - 70, y + 84], radius=30, fill=(40, 110, 255, 255) if mine else (48, 50, 66, 255))
        d.text((62 if not mine else 92, y + 28), s, font=F(21), fill=(255, 255, 255))
    d.rounded_rectangle([PW / 2 - 60, PH - 34, PW / 2 + 60, PH - 28], radius=3, fill=(230, 230, 235, 255))
    rgb, al = to_f(im); s = 100; spr = cv2.resize(orbs[int(t * 14) % ORB_N], (s, s), interpolation=cv2.INTER_AREA)
    x0 = PW // 2 - s // 2; rgb[42:42 + s, x0:x0 + s] = np.maximum(rgb[42:42 + s, x0:x0 + s], spr)
    return rgb, al

MONTAGE = [("“Hey Nova.”", (0.30, 0.45, 1.0), (0.6, 0.3, 0.9)), ("Fix my text.", (1.0, 0.5, 0.3), (0.9, 0.3, 0.5)),
           ("Translate.", (0.2, 0.75, 0.6), (0.2, 0.5, 0.95)), ("Music in the notch.", (0.95, 0.35, 0.6), (0.5, 0.3, 0.95)),
           ("Drop a file on it.", (1.0, 0.7, 0.2), (0.95, 0.4, 0.3)), ("Clipboard history.", (0.3, 0.6, 1.0), (0.2, 0.8, 0.8)),
           ("25 minute focus.", (0.6, 0.4, 1.0), (0.9, 0.35, 0.6)), ("It remembers you.", (0.2, 0.8, 0.55), (0.9, 0.7, 0.2)),
           ("Touch ID before it sends.", (1.0, 0.4, 0.35), (0.5, 0.35, 0.95)), ("English. Hindi. Hinglish.", (1.0, 0.6, 0.2), (0.2, 0.7, 0.5)),
           ("Hidden from screen share.", (0.4, 0.45, 1.0), (0.2, 0.75, 0.7)), ("Wakes when you look.", (0.95, 0.45, 0.25), (0.3, 0.45, 1.0))]

def sprites():
    T = {"open": text_sprite("Every Mac has a notch.", 104, FONT_BOLD), "sits": text_sprite("It just sits there.", 104, FONT_BOLD),
         "meet": text_sprite("Meet Nova.", 160, FONT_BLACK), "lives": text_sprite("It lives in your notch.", 96, FONT_BOLD),
         "talk": text_sprite("Just talk.", 160, FONT_BLACK), "more": text_sprite("And so much more.", 120, FONT_BLACK),
         "where": text_sprite("On your Mac. In Chrome. On your phone.", 78, FONT_BOLD),
         "whole": text_sprite("Your whole Mac. One island.", 92, FONT_BOLD),
         "title": text_sprite("NoTcH OS", 300, FONT_BLACK, 6), "tag": text_sprite("Nova lives in your notch.", 64, FONT_BOLD),
         "free": text_sprite("Free for Mac", 140, FONT_BLACK), "url": text_sprite("notch.zeroorigine.com", 84, FONT_BOLD),
         "apple": text_sprite("Signed and checked by Apple", 40, FONT_BOLD), "by": text_sprite("A ZeroOrigine product", 34, FONT_BOLD)}
    for k, h, s, _, _ in FEATS: T[k + "_h"] = text_sprite(h, 100, FONT_BLACK); T[k + "_s"] = text_sprite(s, 46, FONT_BOLD)
    for i, (w, _, _) in enumerate(MONTAGE): T["m%d" % i] = text_sprite(w, 150, FONT_BLACK)
    return T

def mac_on(c, orbs, t, drop, cx, cy, sc, yaw, pitch, ui=None, glow=0.0):
    rgb, al = macbook(orbs, t, drop, ui)
    if glow > 0: scr = rgb[22:22 + 875, 22:22 + 1400]; edge_glow(scr, glow)
    M = homography(rgb.shape[1], rgb.shape[0], cx, cy, sc, yaw, pitch)
    shadow(c, al, M); over(c, np.clip(rgb, 0, 1.6), al, M)

def scene(n, orbs, T):
    if n == 1:      # 0-8: two calm lines
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; c = studio(t, (0.25, 0.3, 0.6), (0.5, 0.25, 0.5)); bokeh(c, t, 0.8)
            text(c, T["open"], W / 2, H / 2, ease(f / 12) * (1 - ease((f - 4 * BEAT + 10) / 9)), scale=1 + f * 0.0005, sweep=(f - 14) / 40)
            g = f - 4 * BEAT
            text(c, T["sits"], W / 2, H / 2, ease(g / 10) * (1 - ease((g - 4 * BEAT + 10) / 9)), (0.8, 0.84, 0.95), 1 + max(0, g) * 0.0005)
            yield finish(c, fade=ease(f / 10))
    if n == 2:      # 8-16: Meet Nova
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.9, 0.4, 0.25), (0.2, 0.4, 1.0)); bokeh(c, t, 1.2, (1.0, 0.8, 0.7))
            R1.flare(c, W / 2, 420, 0.5 * pulse(f, 0, 16) + 0.10, (1.0, 0.8, 0.6))
            orb(c, orbs, t, W / 2, 420 - 10 * u, 300 + 250 * out(u * 1.6) + 20 * u, 1.0, 0.8)
            text(c, T["meet"], W / 2, 870, ease((f - BEAT) / 10) * (1 - ease((f - N + 8) / 8)), scale=1 + 0.03 * u, sweep=(f - 30) / 45)
            yield finish(c, flash=0.9 * pulse(f, 0, 4))
    if n == 3:      # 16-24: the Mac turns toward us
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.3, 0.4, 0.9), (0.7, 0.3, 0.6), 0.02); bokeh(c, t, 0.9)
            floor(c, W / 2, 800, 620, 0.22)
            mac_on(c, orbs, t, 0.0, W / 2, 470, 0.76 + 0.05 * u, 0.75 * (1 - out(u * 1.5)) - 0.08, 0.20 * (1 - out(u * 1.5)) + 0.03)
            text(c, T["lives"], W / 2, 965, ease((f - 2 * BEAT) / 10), sweep=(f - 50) / 45)
            yield finish(c, flash=0.7 * pulse(f, 0, 4))
    if n == 4:      # 24-32: the notch drops, the screen edge lights up
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.3, 0.4, 0.9), (0.7, 0.3, 0.6), 0.02); bokeh(c, t, 0.7)
            sc = 0.81 + 1.05 * out(u * 1.4); d = ease((f - 16) / 20)
            mac_on(c, orbs, t, d, W / 2, 470 + (sc - 0.81) * 395, sc, -0.08 * (1 - u), 0.03, glow=d * (0.75 + 0.25 * math.sin(t * 6)))
            text(c, T["talk"], W / 2, 900, ease((f - 3 * BEAT) / 10), sweep=(f - 70) / 40)
            yield finish(c, flash=0.6 * pulse(f, 0, 4))
    if n == 5:      # 32-68: six features
        for i, (k, _, _, a, b) in enumerate(FEATS):
            N = 6 * BEAT; side = 1 if i % 2 == 0 else -1
            for f in range(N):
                t = f / FPS; u = f / N; c = studio(t + i * 3, a, b, 0.015); bokeh(c, t + i * 5, 0.9, a)
                rgb, al = card(k, orbs, t, u)
                cx = W / 2 + side * 500; e = out(u * 2.5)
                M = homography(860, 600, cx + side * 220 * (1 - e), H / 2 + 10 + 8 * math.sin(t * 1.5), 0.88 + 0.05 * u, -side * (0.42 - 0.20 * e) + 0.03 * math.sin(t * 1.1), 0.05)
                shadow(c, al * e, M); over(c, rgb, al * e, M)
                orb(c, orbs, t, cx - side * 330 * e, H / 2 - 290, 120, e, 0.7)
                tx = 90 if side == 1 else W / 2 + 60
                a1 = ease((f - 4) / 9); a2 = ease((f - 14) / 9)
                text_left(c, T[k + "_h"], tx - 40 * (1 - a1), H / 2 - 60, a1, sweep=(f - 22) / 40)
                text_left(c, T[k + "_s"], tx, H / 2 + 60, a2, (0.86, 0.9, 1.0))
                R1.flare(c, cx, H / 2, 0.35 * pulse(f, 0, 7), a)
                yield finish(c, flash=0.9 * pulse(f, 0, 3.5))
    if n == 6:      # 68-72: "And so much more."
        N = 4 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.9, 0.45, 0.3), (0.3, 0.4, 1.0)); bokeh(c, t, 1.2)
            text(c, T["more"], W / 2, H / 2, ease(f / 8), scale=0.96 + 0.08 * u, sweep=(f - 16) / 36)
            yield finish(c, flash=0.8 * pulse(f, 0, 4))
    if n == 7:      # 72-84: twelve flash cuts, one per beat
        for i, (w, a, b) in enumerate(MONTAGE):
            spr = T["m%d" % i]; fit = min(1.0, 1640 / (spr.shape[1] - 80)); side = 1 if i % 2 == 0 else -1
            for f in range(BEAT):
                t = f / FPS; u = f / BEAT; c = studio(i * 2.3 + t, a, b, 0.02); bokeh(c, i * 4 + t * 3, 1.3, a)
                orb(c, orbs, t + i, W / 2 + side * 690, 210, 170, 1.0, 0.8)
                text(c, spr, W / 2, H / 2 + 30, 1.0, (1, 1, 1), fit * (1.16 - 0.16 * out(u * 3) + 0.03 * u), side * 0.30 * (1 - out(u * 3)), -0.04, sweep=u * 1.3)
                R1.flare(c, W / 2, H / 2 + 30, 0.5 * pulse(f, 0, 5), a)
                yield finish(c, flash=1.1 * pulse(f, 0, 2.5))
    if n == 8:      # 84-92: where it runs
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.25, 0.5, 0.95), (0.6, 0.3, 0.85), 0.02); bokeh(c, t, 0.9)
            floor(c, W / 2, 800, 900, 0.20)
            e1, e2, e3 = out(u * 3), out(u * 3 - 0.35), out(u * 3 - 0.7)
            rgb, al = browser(orbs, t); M = homography(900, 580, 1420 + 200 * (1 - e2), 470, 0.74, -0.38 + 0.05 * u, 0.04); shadow(c, al * e2, M); over(c, rgb, al * e2, M)
            mac_on(c, orbs, t, 1.0, 620 - 200 * (1 - e1), 450, 0.60, 0.30 - 0.05 * u, 0.04, glow=0.6)
            rgb, al = phone(orbs, t); M = homography(380, 780, 1030, 520 + 120 * (1 - e3), 0.78, -0.10 + 0.20 * u, 0.02); shadow(c, al * e3, M); over(c, rgb, al * e3, M)
            text(c, T["where"], W / 2, 975, ease((f - 2 * BEAT) / 10), sweep=(f - 60) / 45)
            yield finish(c, flash=0.8 * pulse(f, 0, 4))
    if n == 9:      # 92-100: the whole app
        N = 8 * BEAT; ui = dashboard()
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.9, 0.5, 0.25), (0.3, 0.35, 0.9), 0.02); bokeh(c, t, 0.9)
            floor(c, W / 2, 790, 640, 0.22)
            mac_on(c, orbs, t, 0.0, W / 2, 450, 0.78 + 0.10 * u, 0.30 - 0.5 * ease(u), 0.06, ui)
            text(c, T["whole"], W / 2, 975, ease((f - BEAT) / 10), sweep=(f - 50) / 45)
            yield finish(c, flash=0.7 * pulse(f, 0, 4))
    if n == 10:     # 100-104: the build, the sphere strobes and swells, then black
        N = 4 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t * 3, (0.9 * u, 0.4 * u, 0.3 * u), (0.2 * u, 0.4 * u, 1.0 * u))
            orb(c, orbs, t * (1 + 3 * u), W / 2, H / 2, 120 + 520 * u * u, 1.0, 0.5 + u)
            R1.flare(c, W / 2, H / 2, 0.6 * u * u)
            per = max(2, int(9 - 7 * u)); st = 0.45 * u if f % per == 0 else 0.0
            yield finish(c, flash=st, fade=1.0 if f < N - 4 else 0.0)
    if n == 11:     # 104-116: the title
        N = 12 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.95, 0.45, 0.25), (0.2, 0.4, 1.0), 0.01); bokeh(c, t, 1.3, (1.0, 0.85, 0.75))
            R1.flare(c, W / 2, 300, 0.9 * pulse(f, 0, 16) + 0.12, (1.0, 0.85, 0.7))
            orb(c, orbs, t, W / 2, 300 - 8 * u, 340 + 20 * u, 1.0, 0.85)
            yaw = 0.20 * math.sin(t * 0.6); sc = 0.9 + 0.12 * out(f / 22) + 0.03 * u
            for i in range(14, 0, -2):
                text(c, T["title"], W / 2 - i * 2.5 * math.sin(yaw) * 5, 670 + i * 1.6, 1.0, (0.10 + 0.01 * (14 - i), 0.12, 0.25), sc * (1 - i * 0.003), yaw, -0.05)
            text(c, T["title"], W / 2, 670, 1.0, (1, 1, 1), sc, yaw, -0.05, sweep=((f - 30) % 150) / 55)
            text(c, T["tag"], W / 2, 900, ease((f - 4 * BEAT) / 10), (0.9, 0.93, 1.0))
            yield finish(c, flash=1.3 * pulse(f, 0, 5))
    if n == 12:     # 116-128: where to get it
        N = 12 * BEAT
        for f in range(N):
            t = f / FPS; c = studio(t, (0.3, 0.4, 0.95), (0.9, 0.45, 0.3), 0.01); bokeh(c, t, 1.0)
            orb(c, orbs, t, W / 2, 210, 200, 1.0, 0.8)
            text(c, T["free"], W / 2, 470, ease(f / 10), sweep=(f - 20) / 45)
            text(c, T["url"], W / 2, 650, ease((f - 2 * BEAT) / 10), (1.0, 0.82, 0.55))
            text(c, T["apple"], W / 2, 800, ease((f - 4 * BEAT) / 10) * 0.95, (0.88, 0.9, 0.96))
            text(c, T["by"], W / 2, 960, ease((f - 6 * BEAT) / 10) * 0.75, (0.8, 0.83, 0.92))
            yield finish(c, flash=0.5 * pulse(f, 0, 5), fade=1 - ease((f - N + 34) / 32))

PICKS = {1: [30, 110], 2: [100], 3: [130], 4: [130], 5: [60, 384], 6: [50], 7: [10, 64, 154], 8: [130], 9: [120], 10: [50], 11: [120], 12: [170]}
def render(n):
    orbs = load_orbs(); T = sprites(); tmp = f"{OUT}/c{n}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    k = 0
    for fr in scene(n, orbs, T): p.stdin.write(fr.tobytes()); k += 1
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, f"{OUT}/c{n}.mp4"); print("scene", n, k)

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        orbs = load_orbs(); T = sprites()
        for n in ([int(x) for x in sys.argv[2:]] or PICKS):
            for i, fr in enumerate(scene(n, orbs, T)):
                if i in PICKS[n]: Image.fromarray(fr).save(f"{OUT}/v3_{n:02d}_{i:03d}.jpg", quality=88)
                if i >= max(PICKS[n]): break
    else:
        for n in sys.argv[1:]: render(int(n))
