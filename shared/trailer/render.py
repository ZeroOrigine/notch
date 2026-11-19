# NoTcH OS trailer. Draws every frame with numpy + OpenCV and pipes raw video to ffmpeg, one file per scene.
# 1920x1080, 30 fps, 36 s. Tempo 100 bpm: one beat = 18 frames, cuts land on beats.
import sys, math, os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS, BEAT = 1920, 1080, 30, 18
OUT = os.path.dirname(os.path.abspath(__file__))
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
rng = np.random.default_rng(7)

# ---------- assets ----------
def band(x0, x1, mid, half, n=120):
    top, bot = [], []
    for i in range(n + 1):
        u = i / n; x = x0 + (x1 - x0) * u; h = half * (math.sin(math.pi * u) ** 0.8)
        top.append((x, mid(x) - h)); bot.append((x, mid(x) + h))
    return top + bot[::-1]

def orb_frame(t, k, S=520):
    """Nova's sphere, same design as the app (Insight.swift Orb)."""
    cx = cy = S / 2; r = S * 0.46
    Z = lambda: Image.new("RGB", (S, S), (0, 0, 0))
    img = Z()
    ball = Image.new("L", (S, S), 0); ImageDraw.Draw(ball).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    body = Z(); ImageDraw.Draw(body).ellipse([cx - r, cy - r, cx + r, cy + r], fill=(10, 10, 13)); img = ImageChops.add(img, body)
    core = lambda x: cy + math.sin((x - cx) / r * 1.7 + t + 0.5) * 0.10 * r * (1 + 0.5 * k)
    specs = [((255, 70, 40), (-0.45, 0.98), -0.13, 0.13, 0.07, 0.85), ((255, 170, 60), (-0.75, 0.80), -0.06, 0.07, 0.05, 0.85),
             ((40, 90, 255), (-0.98, 0.45), 0.13, 0.14, 0.07, 0.9), ((110, 210, 255), (-0.85, 0.60), 0.06, 0.07, 0.05, 0.85),
             ((255, 255, 255), (-0.97, 0.97), 0.0, 0.024, 0.022, 0.95)]
    for col, (a, b), yo, th, bl, al in specs:
        lay = Z()
        ImageDraw.Draw(lay).polygon(band(cx + a * r, cx + b * r, lambda x, yo=yo: core(x) + yo * r, th * r * (1 + 0.3 * k)), fill=tuple(int(v * al) for v in col))
        img = ImageChops.add(img, Image.composite(lay.filter(ImageFilter.GaussianBlur(r * bl)), Z(), ball))
    rim = Z(); d = ImageDraw.Draw(rim)
    for i in range(180):
        a0 = i * 2; ym = math.sin(math.radians(a0 + 1)); v = int(255 * (0.38 + 0.4 * max(0, ym)))
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + 2.5, fill=(v, v, v), width=max(2, int(r * 0.03)))
    img = ImageChops.add(img, Image.composite(rim.filter(ImageFilter.GaussianBlur(r * 0.05)), Z(), ball))
    img = ImageChops.add(img, rim.filter(ImageFilter.GaussianBlur(r * 0.008)).point(lambda v: int(v * 0.45)))
    hz = Z(); ImageDraw.Draw(hz).ellipse([cx - r * 0.8, cy - r * 0.95, cx + r * 0.8, cy - r * 0.1], fill=(30, 30, 36))
    img = ImageChops.add(img, Image.composite(hz.filter(ImageFilter.GaussianBlur(r * 0.18)), Z(), ball))
    e = Z(); d = ImageDraw.Draw(e); rr = r * 0.97; w = int(r * 0.07)
    d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 182, 205, fill=(255, 150, 50), width=w)
    d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 178, fill=(50, 110, 255), width=w)
    d.arc([cx - rr, cy - rr, cx + rr, cy + rr], -8, 14, fill=(200, 200, 210), width=w)
    img = ImageChops.add(img, Image.composite(e.filter(ImageFilter.GaussianBlur(r * 0.05)), Z(), ball))
    return np.asarray(img, np.float32) / 255.0

ORB_N = 48
def load_orbs():
    p = OUT + "/orbs.npy"
    if os.path.exists(p): return np.load(p)
    a = np.stack([orb_frame(2 * math.pi * i / ORB_N, 0.6) for i in range(ORB_N)])
    np.save(p, a); return a

def text_sprite(s, size, font=FONT_BLACK, tracking=0, pad=40):
    f = ImageFont.truetype(font, size)
    if tracking:
        widths = [f.getlength(c) for c in s]; w = int(sum(widths) + tracking * (len(s) - 1)); h = int(size * 1.25)
        im = Image.new("L", (w + pad * 2, h + pad * 2), 0); d = ImageDraw.Draw(im); x = pad
        for c, cw in zip(s, widths): d.text((x, pad), c, font=f, fill=255); x += cw + tracking
    else:
        l, t, r, b = f.getbbox(s); w, h = r - l, b - t
        im = Image.new("L", (w + pad * 2, h + pad * 2), 0); ImageDraw.Draw(im).text((pad - l, pad - t), s, font=f, fill=255)
    return np.asarray(im, np.float32) / 255.0

# ---------- drawing ----------
def homography(w, h, cx, cy, scale, yaw, pitch, f=1600.0):
    """Place a w x h sprite, rotated in 3D about its centre, at (cx, cy) on screen."""
    src = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]], np.float32) * scale
    cyw, syw, cp, sp = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    R = np.array([[cyw, 0, syw], [0, 1, 0], [-syw, 0, cyw]], np.float32) @ np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], np.float32)
    p = src @ R.T
    z = f + p[:, 2]
    dst = np.stack([cx + p[:, 0] * f / z, cy + p[:, 1] * f / z], 1).astype(np.float32)
    return cv2.getPerspectiveTransform(np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32), dst)

def put(canvas, sprite, M, color=(1, 1, 1), gain=1.0):
    warped = cv2.warpPerspective(sprite, M, (W, H), flags=cv2.INTER_LINEAR)
    if warped.ndim == 2:
        for c in range(3):
            if color[c]: canvas[:, :, c] += warped * (color[c] * gain)
    else: canvas += warped * gain
    return warped

def text3d(canvas, spr, cx, cy, scale, yaw, pitch, gain=1.0, depth=10, color=(1, 1, 1), shade=(0.25, 0.3, 0.45)):
    h, w = spr.shape
    for i in range(depth, 0, -2):   # extrusion, back to front
        M = homography(w, h, cx + i * 2.2 * math.sin(yaw) * -6, cy + i * 1.0, scale * (1 - i * 0.004), yaw, pitch)
        put(canvas, spr, M, shade, gain * 0.22)
    M = homography(w, h, cx, cy, scale, yaw, pitch)
    return put(canvas, spr, M, color, gain)

STARS = rng.uniform([-1, -1, 0.05], [1, 1, 1], (2600, 3)).astype(np.float32)
STAR_C = (0.7 + 0.3 * rng.random((2600, 3))).astype(np.float32)
def stars(canvas, travel, speed, gain=1.0, twist=0.0):
    z = (STARS[:, 2] - travel) % 1.0 + 0.02
    ca, sa = math.cos(twist), math.sin(twist)
    X = STARS[:, 0] * ca - STARS[:, 1] * sa; Y = STARS[:, 0] * sa + STARS[:, 1] * ca
    for s in range(1 + int(min(10, speed * 60))):      # streaks when moving fast
        zz = z + s * speed * 0.012
        x = (W / 2 + X / zz * 520).astype(np.int32); y = (H / 2 + Y / zz * 520).astype(np.int32)
        ok = (x >= 0) & (x < W - 1) & (y >= 0) & (y < H - 1)
        b = (np.clip(1.0 - z, 0, 1) ** 1.5 * 2.2 * gain / (1 + s * 0.35))[ok, None] * STAR_C[ok]
        np.add.at(canvas, (y[ok], x[ok]), b); np.add.at(canvas, (y[ok], x[ok] + 1), b); np.add.at(canvas, (y[ok] + 1, x[ok]), b); np.add.at(canvas, (y[ok] + 1, x[ok] + 1), b)

def orb(canvas, orbs, t, cx, cy, size, gain=1.0, glow=0.5):
    spr = orbs[int(t * 14) % ORB_N]
    s = max(8, int(size))
    r = cv2.resize(spr, (s, s), interpolation=cv2.INTER_AREA if s < 520 else cv2.INTER_LINEAR)
    if glow > 0:   # wide coloured bloom behind the glass
        g = int(s * 2.4) | 1
        small = cv2.resize(spr, (64, 64), interpolation=cv2.INTER_AREA)
        pad = cv2.copyMakeBorder(small, 45, 45, 45, 45, cv2.BORDER_CONSTANT)
        bl = cv2.resize(cv2.GaussianBlur(pad, (0, 0), 12), (g, g), interpolation=cv2.INTER_LINEAR)
        blit(canvas, bl, cx, cy, glow * gain * 1.6)
    blit(canvas, r, cx, cy, gain)

def blit(canvas, img, cx, cy, gain=1.0):
    h, w = img.shape[:2]; x0 = int(cx - w / 2); y0 = int(cy - h / 2)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya: return
    canvas[ya:yb, xa:xb] += img[ya - y0:yb - y0, xa - x0:xb - x0] * gain

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.55 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2, 0, 1))[:, :, None]
GRAIN = [cv2.resize(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H))[:, :, None] for _ in range(6)]

def flare(canvas, cx, cy, gain, color=(0.55, 0.75, 1.0)):
    """Anamorphic streak: a long horizontal blue line of light."""
    if gain <= 0.01: return
    dy = np.abs(yy[:, :1] - cy); dx = np.abs(xx[:1, :] - cx)
    line = np.exp(-dy / 3.0) * np.exp(-dx / 520.0) + 0.5 * np.exp(-dy / 14.0) * np.exp(-dx / 260.0)
    canvas += line[:, :, None] * (np.array(color, np.float32) * gain)

def finish(canvas, f, flash=0.0, bars=0.0, ca=2, fade=1.0, shake=0.0):
    img = canvas
    if shake > 0:
        dx, dy = int(rng.normal(0, shake)), int(rng.normal(0, shake)); img = np.roll(img, (dy, dx), (0, 1))
    if ca:   # colour fringing toward the edges, like a big lens
        img = np.stack([np.roll(img[:, :, 0], ca, 1), img[:, :, 1], np.roll(img[:, :, 2], -ca, 1)], 2)
    img = img * VIG + flash
    img = 1 - np.exp(-img * 1.35)                      # filmic roll-off
    img = img + GRAIN[f % 6] * 0.018
    img *= fade
    if bars > 0:
        b = int(bars * 138); img[:b] = 0; img[H - b:] = 0
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def pulse(f, at, decay=7.0): return math.exp(-(f - at) / decay) if f >= at else 0.0

# ---------- laptop screen (flat picture, later tilted in 3D) ----------
def screen_img(orbs, t, drop):
    SW, SH = 1280, 800
    g = np.zeros((SH, SW, 3), np.float32)
    gy = np.linspace(0, 1, SH, dtype=np.float32)[:, None]; gx = np.linspace(0, 1, SW, dtype=np.float32)[None, :]
    g[:, :, 0] = 0.10 + 0.25 * gx * gy; g[:, :, 1] = 0.07 + 0.10 * gy; g[:, :, 2] = 0.22 + 0.30 * (1 - gx) * gy
    pil = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(pil)
    d.rectangle([0, 0, SW, 30], fill=(14, 14, 18))
    nw = 200 + 120 * drop; nh = 30 + 150 * drop
    d.rounded_rectangle([SW / 2 - nw / 2, -40, SW / 2 + nw / 2, nh], radius=int(14 + 50 * drop), fill=(0, 0, 0))
    if drop > 0.6:
        f = ImageFont.truetype(FONT_BOLD, 22); s = "Listening…"; d.text((SW / 2 - f.getlength(s) / 2, nh - 42), s, font=f, fill=(255, 255, 255))
    a = np.asarray(pil, np.float32) / 255.0
    if drop > 0.3:
        s = int(96 * drop); spr = cv2.resize(orbs[int(t * 14) % ORB_N], (s, s), interpolation=cv2.INTER_AREA)
        y0 = int(34 * drop + 4); x0 = SW // 2 - s // 2
        a[y0:y0 + s, x0:x0 + s] = np.maximum(a[y0:y0 + s, x0:x0 + s], spr)
    cv2.rectangle(a, (0, 0), (SW - 1, SH - 1), (0.35, 0.35, 0.4), 6)
    return a

# ---------- scenes ----------
WORDS = [("TALK TO IT.", (1.0, 0.75, 0.45)), ("IT ANSWERS.", (0.55, 0.8, 1.0)), ("IT OPENS YOUR APPS.", (1.0, 0.5, 0.4)),
         ("IT READS YOUR DAY.", (0.6, 1.0, 0.8)), ("IT GUARDS YOUR SCREEN.", (0.75, 0.6, 1.0)), ("IT UPDATES ITSELF.", (1.0, 1.0, 1.0))]

def scene(n, orbs, T):
    """Yield frames for scene n. T holds text sprites."""
    if n == 1:      # beats 0-8: the problem
        for f in range(8 * BEAT):
            c = np.zeros((H, W, 3), np.float32); t = f / FPS
            stars(c, t * 0.02, 0.01, 0.8, t * 0.03)
            a1 = ease((f - 1.2 * BEAT) / 12) * (1 - ease((f - 4.4 * BEAT) / 10))
            if a1 > 0: text3d(c, T["l1"], W / 2, H / 2, 1.0 + f * 0.0006, 0.0, 0.0, a1, depth=0)
            a2 = ease((f - 5 * BEAT) / 8) * (1 - ease((f - 7.5 * BEAT) / 8))
            if a2 > 0: text3d(c, T["l2"], W / 2, H / 2, 1.0 + (f - 5 * BEAT) * 0.0012, 0.0, 0.0, a2, depth=0, color=(1.0, 0.45, 0.4))
            yield finish(c, f, bars=1.0, fade=ease(f / 14) * (1 - ease((f - 8 * BEAT + 5) / 5)))
    if n == 2:      # beats 8-16: the sphere, and the frame opens up
        N = 8 * BEAT
        for f in range(N):
            c = np.zeros((H, W, 3), np.float32); t = f / FPS; u = f / N
            stars(c, 0.2 + t * 0.10, 0.06, 0.7, 0.3 + t * 0.08)
            size = 150 + 560 * out(u)
            orb(c, orbs, t, W / 2, H / 2 - 10, size, 1.0, 0.55)
            flare(c, W / 2, H / 2 - 10, 0.9 * pulse(f, 0, 14) + 0.25)
            a = ease((f - 4 * BEAT) / 6) * (1 - ease((f - 7.4 * BEAT) / 8))
            if a > 0: text3d(c, T["until"], W / 2, H - 150, 1.0, 0.0, 0.0, a, depth=0)
            yield finish(c, f, flash=1.2 * pulse(f, 0, 4), bars=1 - out(f / (2.5 * BEAT)), shake=6 * pulse(f, 0, 5),
                         fade=1 - ease((f - N + 4) / 4))
    if n == 3:      # beats 16-20: it lives in the notch
        N = 4 * BEAT
        for f in range(N):
            c = np.zeros((H, W, 3), np.float32); t = f / FPS; u = f / N
            stars(c, 0.5 + t * 0.03, 0.01, 0.35)
            scr = screen_img(orbs, t, ease((f - 10) / 16))
            yaw = 0.55 - 0.75 * ease(u); pitch = 0.18 - 0.1 * u
            M = homography(1280, 800, W / 2, H / 2 + 40, 1.02 + 0.12 * u, yaw, pitch)
            w = cv2.warpPerspective(scr, M, (W, H), flags=cv2.INTER_LINEAR)
            m = cv2.warpPerspective(np.ones((800, 1280), np.float32), M, (W, H))[:, :, None]
            c = c * (1 - m) + w * 1.25
            yield finish(c, f, flash=0.9 * pulse(f, 0, 4), shake=4 * pulse(f, 0, 4))
    if n == 4:      # beats 20-32: flash cuts, one feature every two beats
        for i, (word, col) in enumerate(WORDS):
            spr = T["w%d" % i]
            for f in range(2 * BEAT):
                c = np.zeros((H, W, 3), np.float32); t = f / FPS; u = f / (2 * BEAT)
                sp = 0.5 * pulse(f, 0, 6) + 0.05
                stars(c, i * 0.37 + t * 0.5 + 0.3 * out(u), sp, 0.9, i * 1.1)
                side = -1 if i % 2 else 1
                orb(c, orbs, t + i, W / 2 + side * 560, H / 2 - 250 + 40 * u, 230 + 30 * u, 0.9, 0.6)
                yaw = side * (0.55 - 0.42 * out(u * 2.2)); pitch = -0.10 + 0.08 * u
                sc = min(1.0, 1650 / spr.shape[1]) * (0.86 + 0.20 * out(u * 2.5) + 0.05 * u)
                text3d(c, spr, W / 2, H / 2 + 60, sc, yaw, pitch, 1.0, depth=12, color=col, shade=tuple(0.5 * v for v in col))
                flare(c, W / 2, H / 2 + 60, 0.7 * pulse(f, 0, 8), col)
                strobe = 0.5 * pulse(f, BEAT, 2.5) if i >= 3 else 0.0     # extra flash on the off-beat as it builds
                yield finish(c, f, flash=1.5 * pulse(f, 0, 3) + strobe, shake=7 * pulse(f, 0, 4), ca=3)
    if n == 5:      # beats 32-36: the breath before the title
        N = 4 * BEAT
        for f in range(N):
            c = np.zeros((H, W, 3), np.float32); t = f / FPS; u = f / N
            stars(c, 3 + u * u * 1.4, 0.02 + 0.5 * u * u, 0.8, t * 0.5)
            orb(c, orbs, t * (1 + 3 * u), W / 2, H / 2, 60 + 260 * u * u, 1.0, 0.4 + u)
            period = max(2, int(10 - 8 * u)); st = 0.5 * u if (f // period) % 2 == 0 and f % period == 0 else 0
            cut = 1.0 if f < N - 4 else 0.0     # four frames of black before the hit
            yield finish(c, f, flash=st, ca=2 + int(4 * u), fade=cut, shake=3 * u)
    if n == 6:      # beats 36-50: the title
        N = 14 * BEAT
        for f in range(N):
            c = np.zeros((H, W, 3), np.float32); t = f / FPS; u = f / N
            stars(c, 5 + t * 0.06 + 0.25 * out(f / 20), 0.03 + 0.5 * pulse(f, 0, 7), 0.75, 1 + t * 0.04)
            orb(c, orbs, t, W / 2, 300 - 10 * u, 330 + 20 * u, 1.0, 0.55)
            flare(c, W / 2, 300, 1.2 * pulse(f, 0, 16) + 0.22)
            yaw = 0.22 * math.sin(t * 0.55) ; pitch = -0.06
            text3d(c, T["title"], W / 2, 660, 0.9 + 0.12 * out(f / 25) + 0.03 * u, yaw, pitch, 1.0, depth=16)
            a = ease((f - 6 * BEAT) / 10)
            if a > 0: text3d(c, T["tag"], W / 2, 860, 1.0, 0.0, 0.0, a * 0.85, depth=0, color=(0.8, 0.85, 1.0))
            yield finish(c, f, flash=1.6 * pulse(f, 0, 5), shake=9 * pulse(f, 0, 5), fade=1 - ease((f - N + 6) / 6))
    if n == 7:      # beats 50-60: where to get it
        N = 10 * BEAT
        for f in range(N):
            c = np.zeros((H, W, 3), np.float32); t = f / FPS
            stars(c, 7 + t * 0.02, 0.01, 0.5, 2.0)
            orb(c, orbs, t, W / 2, 250, 190, 0.95, 0.5)
            text3d(c, T["free"], W / 2, 520, 1.0, 0.0, 0.0, ease(f / 10), depth=0)
            text3d(c, T["url"], W / 2, 680, 1.0, 0.0, 0.0, ease((f - 2 * BEAT) / 10), depth=0, color=(1.0, 0.72, 0.45))
            text3d(c, T["apple"], W / 2, 830, 1.0, 0.0, 0.0, ease((f - 4 * BEAT) / 10) * 0.7, depth=0, color=(0.75, 0.8, 0.9))
            yield finish(c, f, flash=0.6 * pulse(f, 0, 5), fade=ease(f / 6) * (1 - ease((f - N + 30) / 28)))

def sprites():
    T = {"l1": text_sprite("EVERY MAC HAS A NOTCH.", 84, FONT_BOLD, 10), "l2": text_sprite("IT DOES NOTHING.", 96, FONT_BLACK, 10),
         "until": text_sprite("UNTIL NOW.", 72, FONT_BOLD, 22), "title": text_sprite("NoTcH OS", 300, FONT_BLACK, 6),
         "tag": text_sprite("NOVA LIVES IN YOUR NOTCH.", 50, FONT_BOLD, 16), "free": text_sprite("FREE FOR MAC", 120, FONT_BLACK, 10),
         "url": text_sprite("notch.zeroorigine.com", 76, FONT_BOLD, 3), "apple": text_sprite("SIGNED AND CHECKED BY APPLE", 34, FONT_BOLD, 12)}
    for i, (w, _) in enumerate(WORDS): T["w%d" % i] = text_sprite(w, 190, FONT_BLACK, 4)
    return T

def render(n, limit=None):
    orbs = load_orbs(); T = sprites()
    tmp = f"{OUT}/s{n}.tmp.mp4"; final = f"{OUT}/s{n}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    k = 0
    for fr in scene(n, orbs, T):
        p.stdin.write(fr.tobytes()); k += 1
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, final); print("scene", n, k, "frames")

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        orbs = load_orbs(); T = sprites()
        picks = {1: [40, 110], 2: [3, 100], 3: [60], 4: [2, 20, 110, 200], 5: [60], 6: [3, 150], 7: [120]}
        for n, fs in picks.items():
            for i, fr in enumerate(scene(n, orbs, T)):
                if i in fs: Image.fromarray(fr).save(f"{OUT}/still_{n}_{i}.jpg", quality=88)
                if i >= max(fs): break
    else:
        for n in sys.argv[1:]: render(int(n))
