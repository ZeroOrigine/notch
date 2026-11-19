# NoTcH OS trailer v2: a clean product advertisement. Bright studio light, the Mac, the notch, one feature at a time.
# 1920x1080, 30 fps, 96 beats at 100 bpm = 57.6 s. No stars, no grain: everything stays sharp and readable.
import sys, math, os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import load_orbs, ORB_N, homography, text_sprite, ease, out, pulse, FONT_BLACK, FONT_BOLD, blit

W, H, FPS, BEAT = 1920, 1080, 30, 18
OUT = os.path.dirname(os.path.abspath(__file__))
FONT_MED = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F = lambda size, heavy=False: ImageFont.truetype(FONT_BLACK if heavy else FONT_MED, size)

# ---------- studio background: soft moving light on a deep colour ----------
gy, gx = np.mgrid[0:135, 0:240].astype(np.float32); gx /= 240; gy /= 135
def studio(t, a, b, lift=0.0):
    """a = key colour, b = second colour. Two soft lights drift slowly."""
    x1 = 0.30 + 0.10 * math.sin(t * 0.35); y1 = 0.35 + 0.08 * math.cos(t * 0.28)
    x2 = 0.75 + 0.08 * math.cos(t * 0.31); y2 = 0.70 + 0.08 * math.sin(t * 0.40)
    l1 = np.exp(-(((gx - x1) / 0.42) ** 2 + ((gy - y1) / 0.55) ** 2))
    l2 = np.exp(-(((gx - x2) / 0.45) ** 2 + ((gy - y2) / 0.55) ** 2))
    base = np.array([0.035, 0.04, 0.07], np.float32)
    img = base + l1[:, :, None] * np.array(a, np.float32) * 0.55 + l2[:, :, None] * np.array(b, np.float32) * 0.45 + lift
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)

def over(canvas, rgb, alpha, M=None):
    """Alpha-composite an RGB float picture with an alpha mask, optionally through a 3D transform."""
    if M is not None:
        rgb = cv2.warpPerspective(rgb, M, (W, H), flags=cv2.INTER_LINEAR)
        alpha = cv2.warpPerspective(alpha, M, (W, H), flags=cv2.INTER_LINEAR)
    a = alpha[:, :, None]
    canvas *= (1 - a); canvas += rgb * a

def shadow(canvas, alpha, M, dy=40, blur=45, strength=0.55):
    a = cv2.warpPerspective(alpha, M, (W, H))
    a = cv2.GaussianBlur(np.roll(cv2.resize(a, (W // 4, H // 4)), dy // 4, 0), (0, 0), blur / 4)
    canvas *= (1 - strength * cv2.resize(a, (W, H))[:, :, None])

def text(canvas, spr, cx, cy, alpha=1.0, color=(1, 1, 1), scale=1.0, yaw=0.0, pitch=0.0):
    if alpha <= 0.003: return
    h, w = spr.shape
    m = cv2.warpPerspective(spr, homography(w, h, cx, cy, scale, yaw, pitch), (W, H), flags=cv2.INTER_LINEAR)[:, :, None] * alpha
    canvas *= (1 - m); canvas += m * np.array(color, np.float32)

def text_left(canvas, spr, x, cy, alpha=1.0, color=(1, 1, 1), fit=820):
    """Left-aligned at x, shrunk if needed so it never runs past `fit` pixels."""
    sc = min(1.0, fit / (spr.shape[1] - 80))
    text(canvas, spr, x + (spr.shape[1] / 2 - 40) * sc, cy, alpha, color, sc)

def orb(canvas, orbs, t, cx, cy, size, gain=1.0, glow=0.6):
    spr = orbs[int(t * 14) % ORB_N]; s = max(8, int(size))
    r = cv2.resize(spr, (s, s), interpolation=cv2.INTER_AREA if s < 520 else cv2.INTER_CUBIC)
    if glow > 0:
        g = int(s * 2.6) | 1
        pad = cv2.copyMakeBorder(cv2.resize(spr, (64, 64), interpolation=cv2.INTER_AREA), 50, 50, 50, 50, cv2.BORDER_CONSTANT)
        blit(canvas, cv2.resize(cv2.GaussianBlur(pad, (0, 0), 13), (g, g)), cx, cy, glow * gain * 1.8)
    # the sphere is solid glass: cover what is behind it, then add its light
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32); m = np.clip((s * 0.46 - np.hypot(xx - s / 2, yy - s / 2)) / 1.5, 0, 1)
    x0 = int(cx - s / 2); y0 = int(cy - s / 2)
    if x0 >= 0 and y0 >= 0 and x0 + s <= W and y0 + s <= H:
        canvas[y0:y0 + s, x0:x0 + s] *= (1 - m[:, :, None] * gain)
    blit(canvas, r, cx, cy, gain)

def finish(canvas, flash=0.0, fade=1.0):
    img = canvas + flash
    img = np.where(img > 0.8, 0.8 + (1 - np.exp(-(img - 0.8) * 2.5)) * 0.2, img)   # gentle highlight roll-off, mid-tones untouched
    return (np.clip(img * fade, 0, 1) * 255).astype(np.uint8)

# ---------- flat pictures that get placed in 3D ----------
def to_f(pil):
    a = np.asarray(pil, np.float32) / 255.0
    return a[:, :, :3].copy(), a[:, :, 3].copy()

def macbook(orbs, t, drop, ui=None):
    """A MacBook seen from the front: bezel, screen, notch, hinge lip."""
    SW, SH, B = 1400, 875, 22
    im = Image.new("RGBA", (SW + 2 * B, SH + 2 * B + 34), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, SW + 2 * B, SH + 2 * B], radius=34, fill=(16, 16, 20, 255), outline=(90, 92, 100, 255), width=3)
    d.rounded_rectangle([-40 + 0, SH + 2 * B - 4, SW + 2 * B + 0, SH + 2 * B + 30], radius=14, fill=(176, 180, 190, 255))
    d.rounded_rectangle([SW / 2 + B - 110, SH + 2 * B - 4, SW / 2 + B + 110, SH + 2 * B + 10], radius=7, fill=(120, 124, 134, 255))
    rgb, al = to_f(im)
    scr = np.zeros((SH, SW, 3), np.float32)
    yy = np.linspace(0, 1, SH, dtype=np.float32)[:, None]; xx = np.linspace(0, 1, SW, dtype=np.float32)[None, :]
    scr[:, :, 0] = 0.20 + 0.55 * xx * yy + 0.15 * (1 - yy); scr[:, :, 1] = 0.22 + 0.25 * yy * (1 - xx) + 0.10 * xx; scr[:, :, 2] = 0.55 + 0.35 * (1 - xx) - 0.2 * yy
    if ui is not None:
        uh, uw = ui[0].shape[:2]; x0 = (SW - uw) // 2; y0 = 110
        a = ui[1][:, :, None]; scr[y0:y0 + uh, x0:x0 + uw] = scr[y0:y0 + uh, x0:x0 + uw] * (1 - a) + ui[0] * a
    p = Image.fromarray((np.clip(scr, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(p)
    d.rectangle([0, 0, SW, 32], fill=(20, 20, 26))
    for i, s in enumerate(["NoTcH OS", "File", "Edit", "View"]): d.text((60 + i * 110 if i else 22, 6), s, font=F(17), fill=(235, 235, 240))
    nw = 210 + 250 * drop; nh = 32 + 190 * drop
    d.rounded_rectangle([SW / 2 - nw / 2, -60, SW / 2 + nw / 2, nh], radius=int(12 + 58 * drop), fill=(0, 0, 0))
    if drop > 0.75:
        s = "Listening…"; f = F(26); d.text((SW / 2 - f.getlength(s) / 2, nh - 50), s, font=f, fill=(255, 255, 255))
    scr = np.asarray(p, np.float32) / 255.0
    if drop > 0.35:
        s = int(120 * drop); spr = cv2.resize(orbs[int(t * 14) % ORB_N], (s, s), interpolation=cv2.INTER_AREA)
        y0 = int(38 * drop + 2); x0 = SW // 2 - s // 2
        scr[y0:y0 + s, x0:x0 + s] = np.maximum(scr[y0:y0 + s, x0:x0 + s], spr)
    rgb[B:B + SH, B:B + SW] = scr
    return rgb, al

def card(kind, orbs, t, u):
    """One feature shown as a glass card, 860 x 600."""
    CW, CH = 860, 600
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, CW - 1, CH - 1], radius=46, fill=(18, 19, 26, 240), outline=(255, 255, 255, 70), width=2)
    white, dim = (255, 255, 255, 255), (170, 176, 190, 255)
    if kind == "ask":
        d.rounded_rectangle([330, 60, 800, 150], radius=40, fill=(40, 110, 255, 255)); d.text((372, 82), "What's on today?", font=F(44), fill=white)
        d.rounded_rectangle([60, 210, 800, 520], radius=40, fill=(40, 42, 54, 255))
        n = int(min(1, u * 2.2) * 3 + 0.999)
        for i, s in enumerate(["Two meetings, the first at 10.", "Rain from 3 PM, take a jacket.", "Battery is at 100%."][:n]):
            d.text((210, 250 + i * 80), s, font=F(38), fill=white)
    if kind == "apps":
        cols = [(255, 95, 87), (255, 189, 46), (40, 200, 120), (40, 140, 255), (160, 100, 255), (255, 120, 190), (90, 210, 230), (240, 240, 245)]
        hot = int(u * 9) % 8 if u < 0.6 else 3
        for i, c in enumerate(cols):
            x = 70 + (i % 4) * 190; y = 70 + (i // 4) * 190; g = 16 if i == hot else 0
            d.rounded_rectangle([x - g, y - g, x + 150 + g, y + 150 + g], radius=38, fill=c + (255,), outline=white if i == hot else None, width=6)
        d.text((70, 480), "“Open YouTube.”  Done.", font=F(54), fill=white)
    if kind == "day":
        d.text((60, 50), "TODAY", font=F(34), fill=dim)
        for i, (tm, ev, c) in enumerate([("10:00", "Team meeting", (255, 120, 80)), ("12:30", "Lunch with Sam", (60, 200, 130)), ("3:00", "Project review", (70, 140, 255)), ("6:30", "Gym", (190, 120, 255))]):
            y = 125 + i * 112; a = int(255 * min(1, max(0, u * 5 - i * 0.6)))
            d.rounded_rectangle([60, y, 800, y + 92], radius=24, fill=(40, 42, 54, a)); d.rounded_rectangle([60, y, 76, y + 92], radius=8, fill=c + (a,))
            d.text((110, y + 20), tm, font=F(40, True), fill=(255, 255, 255, a)); d.text((290, y + 22), ev, font=F(38), fill=(255, 255, 255, a))
    if kind == "weather":
        d.text((60, 50), "MISSISSAUGA  ·  BY THE HOUR", font=F(30), fill=dim)
        temps = [9, 10, 12, 13, 12, 10, 8]
        for i, tv in enumerate(temps):
            x = 80 + i * 108; hgt = int((tv - 4) * 30 * min(1, u * 3));
            d.rounded_rectangle([x, 430 - hgt, x + 70, 430], radius=18, fill=(255, 190, 70, 255) if i < 4 else (90, 160, 255, 255))
            d.text((x + 6, 380 - hgt), f"{tv}°", font=F(36, True), fill=white); d.text((x + 2, 450), ["12", "1", "2", "3", "4", "5", "6"][i] + " PM", font=F(22), fill=dim)
        d.text((60, 515), "Rain starts at 3 PM.", font=F(40), fill=white)
    if kind == "guard":
        for i in range(5): d.rounded_rectangle([70, 70 + i * 62, 790 - (i % 3) * 120, 110 + i * 62], radius=14, fill=(120, 126, 140, 255))
        im = im.filter(ImageFilter.GaussianBlur(14 * min(1, u * 2.5))); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, CW - 1, CH - 1], radius=46, outline=(255, 255, 255, 70), width=2)
        d.rounded_rectangle([170, 400, 690, 520], radius=60, fill=(30, 200, 120, 255)); d.text((222, 428), "Screen guard is on", font=F(46, True), fill=white)
    if kind == "update":
        d.text((60, 70), "Software update", font=F(34), fill=dim); d.text((60, 130), "NoTcH OS 5.6", font=F(84, True), fill=white)
        p = min(1, u * 1.6)
        d.rounded_rectangle([60, 300, 800, 336], radius=18, fill=(50, 52, 64, 255)); d.rounded_rectangle([60, 300, 60 + int(740 * p), 336], radius=18, fill=(60, 140, 255, 255))
        s = "Installing…" if p < 1 else "Up to date.  One click."
        d.text((60, 380), s, font=F(48), fill=white)
        d.text((60, 470), "Signed and checked by Apple.", font=F(32), fill=dim)
    rgb, al = to_f(im)
    if kind == "ask":
        s = 110; spr = cv2.resize(orbs[int(t * 14) % ORB_N], (s, s), interpolation=cv2.INTER_AREA); rgb[240:240 + s, 80:80 + s] = np.maximum(rgb[240:240 + s, 80:80 + s], spr)
    return rgb, al

def dashboard():
    """The app's main window, redrawn (clock, weather, quick actions)."""
    DW, DH = 1080, 660
    im = Image.new("RGBA", (DW, DH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, DW - 1, DH - 1], radius=26, fill=(17, 17, 22, 255), outline=(70, 72, 82, 255), width=2)
    d.rectangle([0, 30, 215, DH - 30], fill=(24, 24, 31, 255))
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]): d.ellipse([18 + i * 24, 16, 32 + i * 24, 30], fill=c)
    d.text((70, 52), "NoTcH OS", font=F(24, True), fill=(255, 255, 255))
    for i, s in enumerate(["Dashboard", "Nova", "Notes", "Timer", "Clipboard", "Music", "Controls", "Memory", "Features"]):
        y = 112 + i * 46
        if i == 0: d.rounded_rectangle([14, y - 8, 200, y + 30], radius=12, fill=(240, 150, 80))
        d.text((50, y - 2), s, font=F(20), fill=(20, 20, 24) if i == 0 else (225, 226, 232))
    d.text((250, 50), "Dashboard", font=F(34, True), fill=(255, 255, 255))
    d.rounded_rectangle([250, 110, 630, 280], radius=22, fill=(8, 8, 12)); d.text((274, 126), "Good evening", font=F(20), fill=(200, 200, 210)); d.text((272, 156), "7:21 PM", font=F(74, True), fill=(255, 255, 255))
    d.rounded_rectangle([650, 110, 1050, 280], radius=22, fill=(8, 8, 12))
    for i, s in enumerate(["9°C · Cloudy · Mississauga", "Battery 100%", "Nothing playing", "No timer running"]): d.text((680, 128 + i * 36), s, font=F(20), fill=(235, 235, 240))
    acts = ["Morning briefing", "Talk to Nova", "Fix text", "Screenshot", "25 min focus", "Keep awake", "Dark mode", "Lock Mac"]
    for i, s in enumerate(acts):
        x = 250 + (i % 4) * 202; y = 320 + (i // 4) * 112
        d.rounded_rectangle([x, y, x + 190, y + 98], radius=20, fill=(34, 35, 44)); d.ellipse([x + 80, y + 16, x + 110, y + 46], fill=(245, 160, 80))
        d.text((x + 95 - F(17).getlength(s) / 2, y + 60), s, font=F(17), fill=(240, 240, 245))
    d.rounded_rectangle([250, 560, 1050, 630], radius=20, fill=(8, 8, 12)); d.text((330, 582), "Hi. Ask me anything, or say “open Excel”.", font=F(20), fill=(235, 235, 240))
    return to_f(im)

FEATS = [("ask", "Ask it anything.", "Nova answers out loud, in a second.", (0.30, 0.45, 1.0), (0.55, 0.25, 0.9)),
         ("apps", "It opens your apps.", "Say it. Nova does it.", (1.0, 0.45, 0.30), (0.9, 0.25, 0.55)),
         ("day", "It knows your day.", "Reads your calendar for a briefing.", (0.20, 0.75, 0.55), (0.2, 0.45, 0.95)),
         ("weather", "Weather by the hour.", "Today, tomorrow, or any day back.", (1.0, 0.65, 0.20), (0.25, 0.5, 1.0)),
         ("guard", "It guards your screen.", "Blurs it when someone looks over.", (0.55, 0.40, 1.0), (0.2, 0.75, 0.6)),
         ("update", "It updates itself.", "One click. No downloads.", (0.25, 0.55, 1.0), (0.2, 0.8, 0.9))]

def sprites():
    T = {"open": text_sprite("Every Mac has a notch.", 104, FONT_MED), "meet": text_sprite("Meet Nova.", 150, FONT_BLACK),
         "lives": text_sprite("It lives in your notch.", 96, FONT_MED), "talk": text_sprite("Just talk.", 150, FONT_BLACK),
         "whole": text_sprite("Your whole Mac. One island.", 92, FONT_MED),
         "title": text_sprite("NoTcH OS", 300, FONT_BLACK, 6), "tag": text_sprite("Nova lives in your notch.", 64, FONT_MED),
         "free": text_sprite("Free for Mac", 140, FONT_BLACK), "url": text_sprite("notch.zeroorigine.com", 84, FONT_MED),
         "apple": text_sprite("Signed and checked by Apple", 40, FONT_MED)}
    for k, h, s, _, _ in FEATS: T[k + "_h"] = text_sprite(h, 100, FONT_BLACK); T[k + "_s"] = text_sprite(s, 46, FONT_MED)
    return T

def scene(n, orbs, T):
    if n == 1:      # 0-4: the line
        N = 4 * BEAT
        for f in range(N):
            t = f / FPS; c = studio(t, (0.25, 0.3, 0.6), (0.5, 0.25, 0.5))
            text(c, T["open"], W / 2, H / 2, ease(f / 12) * (1 - ease((f - N + 12) / 10)), scale=1 + f * 0.0006)
            yield finish(c, fade=ease(f / 10))
    if n == 2:      # 4-12: Meet Nova
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.9, 0.4, 0.25), (0.2, 0.4, 1.0))
            orb(c, orbs, t, W / 2, 420 - 10 * u, 300 + 240 * out(u * 1.6) + 20 * u, 1.0, 0.7)
            text(c, T["meet"], W / 2, 860, ease((f - BEAT) / 10) * (1 - ease((f - N + 8) / 8)), scale=1 + 0.03 * u)
            yield finish(c, flash=0.7 * pulse(f, 0, 4))
    if n == 3:      # 12-20: the Mac turns toward us
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.3, 0.4, 0.9), (0.7, 0.3, 0.6), 0.02)
            rgb, al = macbook(orbs, t, 0.0)
            M = homography(rgb.shape[1], rgb.shape[0], W / 2, 470, 0.76 + 0.05 * u, 0.75 * (1 - out(u * 1.5)) - 0.08, 0.20 * (1 - out(u * 1.5)) + 0.03)
            shadow(c, al, M); over(c, rgb, al, M)
            text(c, T["lives"], W / 2, 965, ease((f - 2 * BEAT) / 10))
            yield finish(c, flash=0.6 * pulse(f, 0, 4))
    if n == 4:      # 20-28: close on the notch, it drops into the island
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.3, 0.4, 0.9), (0.7, 0.3, 0.6), 0.02)
            rgb, al = macbook(orbs, t, ease((f - 16) / 20))
            sc = 0.81 + 1.05 * out(u * 1.4)
            M = homography(rgb.shape[1], rgb.shape[0], W / 2, 470 + (sc - 0.81) * 395, sc, -0.08 * (1 - u), 0.03)
            shadow(c, al, M); over(c, rgb, al, M)
            text(c, T["talk"], W / 2, 900, ease((f - 3 * BEAT) / 10))
            yield finish(c, flash=0.5 * pulse(f, 0, 4))
    if n == 5:      # 28-64: six features, six beats each
        for i, (k, _, _, a, b) in enumerate(FEATS):
            N = 6 * BEAT; side = 1 if i % 2 == 0 else -1
            for f in range(N):
                t = f / FPS; u = f / N; c = studio(t + i * 3, a, b, 0.015)
                rgb, al = card(k, orbs, t, u)
                cx = W / 2 + side * 500; e = out(u * 2.5)
                M = homography(860, 600, cx + side * 220 * (1 - e), H / 2 + 10, 0.88 + 0.05 * u, -side * (0.42 - 0.20 * e) , 0.05)
                shadow(c, al * e, M); over(c, rgb, al * e, M)
                tx = 90 if side == 1 else W / 2 + 60
                a1 = ease((f - 4) / 9); a2 = ease((f - 14) / 9)
                text_left(c, T[k + "_h"], tx - 40 * (1 - a1), H / 2 - 60, a1)
                text_left(c, T[k + "_s"], tx, H / 2 + 60, a2, (0.86, 0.9, 1.0))
                yield finish(c, flash=0.85 * pulse(f, 0, 3.5), fade=1 - 0.0 * u)
    if n == 6:      # 64-72: the whole app, slow push
        N = 8 * BEAT; ui = dashboard()
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.9, 0.5, 0.25), (0.3, 0.35, 0.9), 0.02)
            rgb, al = macbook(orbs, t, 0.0, ui)
            M = homography(rgb.shape[1], rgb.shape[0], W / 2, 450, 0.78 + 0.10 * u, 0.30 - 0.5 * ease(u), 0.06)
            shadow(c, al, M); over(c, rgb, al, M)
            text(c, T["whole"], W / 2, 975, ease((f - BEAT) / 10))
            yield finish(c, flash=0.7 * pulse(f, 0, 4), fade=1.0 if f < N - 3 else 0.0)
    if n == 7:      # 72-86: the title
        N = 14 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = studio(t, (0.95, 0.45, 0.25), (0.2, 0.4, 1.0), 0.01)
            orb(c, orbs, t, W / 2, 300 - 8 * u, 340 + 20 * u, 1.0, 0.75)
            yaw = 0.20 * math.sin(t * 0.6); sc = 0.9 + 0.12 * out(f / 22) + 0.03 * u
            for i in range(14, 0, -2):    # solid 3D depth behind the letters
                text(c, T["title"], W / 2 - i * 2.5 * math.sin(yaw) * 5, 670 + i * 1.6, 1.0, (0.10 + 0.01 * (14 - i), 0.12, 0.25), sc * (1 - i * 0.003), yaw, -0.05)
            text(c, T["title"], W / 2, 670, 1.0, (1, 1, 1), sc, yaw, -0.05)
            text(c, T["tag"], W / 2, 900, ease((f - 5 * BEAT) / 10), (0.9, 0.93, 1.0))
            yield finish(c, flash=1.2 * pulse(f, 0, 5))
    if n == 8:      # 86-96: where to get it
        N = 10 * BEAT
        for f in range(N):
            t = f / FPS; c = studio(t, (0.3, 0.4, 0.95), (0.9, 0.45, 0.3), 0.01)
            orb(c, orbs, t, W / 2, 230, 200, 1.0, 0.7)
            text(c, T["free"], W / 2, 500, ease(f / 10)); text(c, T["url"], W / 2, 690, ease((f - 2 * BEAT) / 10), (1.0, 0.82, 0.55))
            text(c, T["apple"], W / 2, 850, ease((f - 4 * BEAT) / 10) * 0.9, (0.88, 0.9, 0.96))
            yield finish(c, flash=0.5 * pulse(f, 0, 5), fade=1 - ease((f - N + 30) / 28))

def render(n):
    orbs = load_orbs(); T = sprites(); tmp = f"{OUT}/a{n}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    k = 0
    for fr in scene(n, orbs, T): p.stdin.write(fr.tobytes()); k += 1
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, f"{OUT}/a{n}.mp4"); print("scene", n, k)

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        orbs = load_orbs(); T = sprites()
        picks = {1: [40], 2: [100], 3: [30, 130], 4: [130], 5: [60, 168, 276, 384, 492, 600], 6: [120], 7: [150], 8: [130]}
        for n, fs in picks.items():
            for i, fr in enumerate(scene(n, orbs, T)):
                if i in fs: Image.fromarray(fr).save(f"{OUT}/v2_{n:02d}_{i:03d}.jpg", quality=88)
                if i >= max(fs): break
    else:
        for n in sys.argv[1:]: render(int(n))
