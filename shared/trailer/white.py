# NoTcH OS trailer, fresh start: a calm, white, premium advertisement.
# 1920x1080, 30 fps, 72 bpm (one beat = 25 frames), 108 beats = 90 s.
# White studio, dark lettering, one idea at a time, soft shadows, slow moves. No flashes.
import sys, math, os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import load_orbs, ORB_N, homography, text_sprite, ease, out, FONT_BLACK, FONT_BOLD

W, H, FPS, BEAT = 1920, 1080, 30, 25
OUT = os.path.dirname(os.path.abspath(__file__))
SEMI = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
if not os.path.exists(SEMI): SEMI = FONT_BOLD
F = lambda size, heavy=False: ImageFont.truetype(FONT_BLACK if heavy else SEMI, size)
INK = (0.114, 0.114, 0.122); GREY = (0.43, 0.43, 0.45); BLUE = (0.0, 0.443, 0.89)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BG = (0.985 - 0.045 * np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.8)) ** 2, 0, 1))[:, :, None] * np.array([1.0, 1.0, 1.008], np.float32)
def paper(): return BG.copy()

def text(c, spr, cx, cy, alpha=1.0, color=INK, scale=1.0, yaw=0.0, pitch=0.0):
    if alpha <= 0.003: return
    h, w = spr.shape
    m = cv2.warpPerspective(spr, homography(w, h, cx, cy, scale, yaw, pitch), (W, H), flags=cv2.INTER_LINEAR)[:, :, None] * alpha
    c *= (1 - m); c += m * np.array(color, np.float32)

def rise(c, spr, cx, cy, f, start, color=INK, scale=1.0, dur=16):
    """Lettering that fades in while drifting up a little: the calm Apple move."""
    a = ease((f - start) / dur); text(c, spr, cx, cy + 26 * (1 - out((f - start) / dur)), a, color, scale)

def over(c, rgb, al, M, alpha=1.0, shadow=0.30, drop=46, blur=38):
    a = cv2.warpPerspective(al, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    if shadow > 0:
        s = cv2.GaussianBlur(np.roll(cv2.resize(a, (W // 4, H // 4)), drop // 4, 0), (0, 0), blur / 4)
        c *= (1 - shadow * cv2.resize(s, (W, H))[:, :, None])
    w = cv2.warpPerspective(rgb, M, (W, H), flags=cv2.INTER_LINEAR)
    c *= (1 - a[:, :, None]); c += w * a[:, :, None]

def orb(c, orbs, t, cx, cy, size, alpha=1.0):
    """The glass sphere on white: a soft shadow and a little of its colour on the floor, then the ball itself."""
    s = max(8, int(size)); spr = cv2.resize(orbs[int(t * 12) % ORB_N], (s, s), interpolation=cv2.INTER_AREA if s < 520 else cv2.INTER_CUBIC)
    fy = cy + s * 0.60
    sh = np.exp(-(((xx - cx) / (s * 0.42)) ** 2 + ((yy - fy) / (s * 0.07)) ** 2))[:, :, None]
    c *= (1 - 0.34 * alpha * sh)
    tint = np.exp(-(((xx - cx) / (s * 0.75)) ** 2 + ((yy - fy) / (s * 0.16)) ** 2))
    c[:, :, 0] -= 0.05 * alpha * tint * (xx < cx); c[:, :, 2] -= 0.05 * alpha * tint * (xx >= cx)   # warm left, cool right
    g, h = np.mgrid[0:s, 0:s].astype(np.float32); m = (np.clip((s * 0.46 - np.hypot(h - s / 2, g - s / 2)) / 1.5, 0, 1) * alpha)[:, :, None]
    x0 = int(cx - s / 2); y0 = int(cy - s / 2)
    if x0 < 0 or y0 < 0 or x0 + s > W or y0 + s > H: return
    c[y0:y0 + s, x0:x0 + s] = c[y0:y0 + s, x0:x0 + s] * (1 - m) + np.clip(spr * 1.15, 0, 1) * m

def finish(c, f, N, fin=12, fout=12):
    k = ease(f / fin) * (1 - ease((f - (N - fout)) / fout))          # in from white, out to white
    img = c * k + BG * (1 - k)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)

def to_f(pil):
    a = np.asarray(pil, np.float32) / 255.0
    return a[:, :, :3].copy(), a[:, :, 3].copy()

# ---------- the Mac ----------
def macbook(orbs, t, drop, play=0.0):
    SW, SH, B = 1400, 875, 20
    im = Image.new("RGBA", (SW + 2 * B + 120, SH + 2 * B + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im); ox = 60
    d.rounded_rectangle([ox, 0, ox + SW + 2 * B, SH + 2 * B], radius=34, fill=(14, 14, 16, 255))
    d.rounded_rectangle([0, SH + 2 * B - 2, SW + 2 * B + 120, SH + 2 * B + 30], radius=15, fill=(214, 216, 222, 255), outline=(170, 172, 180, 255), width=2)
    d.rounded_rectangle([ox + B + SW / 2 - 120, SH + 2 * B - 2, ox + B + SW / 2 + 120, SH + 2 * B + 12], radius=7, fill=(176, 178, 186, 255))
    rgb, al = to_f(im)
    gy = np.linspace(0, 1, SH, dtype=np.float32)[:, None]; gx = np.linspace(0, 1, SW, dtype=np.float32)[None, :]
    scr = np.stack([0.80 + 0.18 * gx * gy - 0.25 * (1 - gy) * (1 - gx), 0.78 - 0.20 * gy * gx + 0.05 * gx, 0.95 - 0.30 * gy * (1 - gx) * 0 - 0.12 * gx * gy], 2).astype(np.float32)
    p = Image.fromarray((np.clip(scr, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(p)
    d.rectangle([0, 0, SW, 32], fill=(236, 236, 240))
    for i, s in enumerate(["NoTcH OS", "File", "Edit", "View"]): d.text((60 + i * 110 if i else 22, 6), s, font=F(17), fill=(40, 40, 46))
    nw = 210 + 250 * drop; nh = 32 + 190 * drop
    d.rounded_rectangle([SW / 2 - nw / 2, -60, SW / 2 + nw / 2, nh], radius=int(12 + 58 * drop), fill=(0, 0, 0))
    if drop > 0.75:
        s = "Listening…"; f = F(26); d.text((SW / 2 - f.getlength(s) / 2, nh - 50), s, font=f, fill=(255, 255, 255))
    scr = np.asarray(p, np.float32) / 255.0
    if drop > 0.35:
        s = int(120 * drop); spr = cv2.resize(orbs[int(t * 12) % ORB_N], (s, s), interpolation=cv2.INTER_AREA)
        y0 = int(38 * drop + 2); x0 = SW // 2 - s // 2; scr[y0:y0 + s, x0:x0 + s] = np.maximum(scr[y0:y0 + s, x0:x0 + s], spr)
    rgb[B:B + SH, ox + B:ox + B + SW] = scr
    return rgb, al

# ---------- feature cards, light theme ----------
CW, CH = 900, 520
def card(kind, orbs, t, u):
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, CW - 1, CH - 1], radius=44, fill=(255, 255, 255, 255), outline=(224, 224, 230, 255), width=2)
    ink, grey, soft = (29, 29, 31, 255), (110, 110, 115, 255), (242, 242, 247, 255)
    if kind == "ask":
        d.rounded_rectangle([420, 50, 850, 130], radius=40, fill=(0, 113, 227, 255)); d.text((458, 70), "What's on today?", font=F(40), fill=(255, 255, 255))
        d.rounded_rectangle([50, 180, 850, 470], radius=40, fill=soft)
        n = int(min(1, max(0, u * 2.4 - 0.25)) * 3 + 0.999) if u > 0.11 else 0
        for i, s in enumerate(["Two meetings, the first at 10.", "Rain from 3 PM. Take a jacket.", "Battery is at 100%."][:n]): d.text((200, 215 + i * 78), s, font=F(38), fill=ink)
    if kind == "apps":
        cols = [(255, 95, 87), (255, 189, 46), (52, 199, 89), (0, 122, 255), (175, 82, 222), (255, 45, 85), (90, 200, 250), (142, 142, 147)]
        hot = int(u * 10) % 8 if u < 0.55 else 3
        for i, col in enumerate(cols):
            x = 80 + (i % 4) * 195; y = 50 + (i // 4) * 170; g = 12 if i == hot else 0
            d.rounded_rectangle([x - g, y - g, x + 140 + g, y + 140 + g], radius=34, fill=col + (255,))
        d.text((80, 410), "“Open YouTube.”", font=F(48), fill=ink); d.text((530, 410), "Done.", font=F(48), fill=(0, 113, 227, 255))
    if kind == "day":
        d.text((50, 36), "TODAY", font=F(30), fill=grey)
        for i, (tm, ev, col) in enumerate([("10:00", "Team meeting", (255, 149, 0)), ("12:30", "Lunch with Sam", (52, 199, 89)), ("3:00", "Project review", (0, 122, 255)), ("6:30", "Gym", (175, 82, 222))]):
            y = 92 + i * 102; a = int(255 * min(1, max(0, u * 5 - 0.4 - i * 0.6)))
            d.rounded_rectangle([50, y, 850, y + 84], radius=22, fill=(242, 242, 247, a)); d.rounded_rectangle([50, y, 64, y + 84], radius=7, fill=col + (a,))
            d.text((96, y + 18), tm, font=F(38, True), fill=(29, 29, 31, a)); d.text((280, y + 20), ev, font=F(36), fill=(29, 29, 31, a))
    if kind == "weather":
        d.text((50, 36), "MISSISSAUGA  ·  BY THE HOUR", font=F(28), fill=grey)
        for i, tv in enumerate([9, 10, 12, 13, 12, 10, 8]):
            x = 80 + i * 112; hgt = int((tv - 4) * 26 * ease(u * 3 - i * 0.12))
            d.rounded_rectangle([x, 370 - hgt, x + 72, 370], radius=18, fill=(255, 179, 64, 255) if i < 3 else (90, 160, 250, 255))
            d.text((x + 8, 324 - hgt), f"{tv}°", font=F(34, True), fill=ink); d.text((x + 4, 384), ["12", "1", "2", "3", "4", "5", "6"][i] + " PM", font=F(22), fill=grey)
        d.text((50, 440), "Rain starts at 3 PM.", font=F(38), fill=ink)
    if kind == "guard":
        for i in range(5): d.rounded_rectangle([60, 50 + i * 58, 820 - (i % 3) * 130, 88 + i * 58], radius=12, fill=(190, 190, 198, 255))
        bl = im.filter(ImageFilter.GaussianBlur(13 * ease(u * 2.5 - 0.3)))
        base = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); ImageDraw.Draw(base).rounded_rectangle([0, 0, CW - 1, CH - 1], radius=44, fill=(255, 255, 255, 255))
        inner = Image.new("L", (CW, CH), 0); ImageDraw.Draw(inner).rounded_rectangle([26, 26, CW - 27, CH - 27], radius=30, fill=255)
        base.paste(bl.convert("RGB"), (0, 0), inner); im = base; d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, CW - 1, CH - 1], radius=44, outline=(224, 224, 230, 255), width=2)
        a = int(255 * ease(u * 2.5 - 0.5))
        d.rounded_rectangle([200, 370, 700, 470], radius=50, fill=(52, 199, 89, a)); d.text((250, 394), "Screen guard is on", font=F(42, True), fill=(255, 255, 255, a))
    if kind == "fix":
        k = ease(u * 2.6 - 0.9)
        d.text((60, 50), "BEFORE", font=F(26), fill=grey); d.text((60, 96), "teh meeting is tommorow at 10", font=F(46), fill=(29, 29, 31, int(255 * (1 - 0.55 * k))))
        if k > 0.05:
            for x0, x1 in ((60, 128), (384, 610)): d.line([x0, 152, x0 + (x1 - x0) * k, 152], fill=(255, 59, 48, 255), width=5)
        a = int(255 * ease(u * 2.6 - 1.2))
        d.rounded_rectangle([50, 250, 850, 450], radius=34, fill=(232, 244, 255, a)); d.text((84, 276), "AFTER", font=F(26), fill=(0, 113, 227, a))
        d.text((84, 330), "The meeting is tomorrow at 10.", font=F(48, True), fill=(29, 29, 31, a))
    if kind == "music":
        d.rounded_rectangle([60, 150, 840, 370], radius=110, fill=(0, 0, 0, 255))
        for i in range(140): d.line([110 + i, 190, 110 + i, 330], fill=(255, 100 + i // 2, 150 - i // 2 + 60, 255))
        d.rounded_rectangle([110, 190, 250, 330], radius=30, outline=(0, 0, 0, 255), width=6)
        d.text((290, 205), "Now playing", font=F(28), fill=(160, 160, 170)); d.text((290, 250), "Your favourite song", font=F(36, True), fill=(255, 255, 255))
        for i in range(6):
            hgt = 20 + 60 * abs(math.sin(t * 5 + i * 1.3)); d.rounded_rectangle([700 + i * 18, 300 - hgt, 710 + i * 18, 300], radius=6, fill=(52, 199, 89, 255))
    if kind == "update":
        d.text((60, 50), "Software update", font=F(30), fill=grey); d.text((60, 100), "NoTcH OS 5.6", font=F(84, True), fill=ink)
        p = ease(u * 1.7 - 0.2)
        d.rounded_rectangle([60, 250, 840, 282], radius=16, fill=soft); d.rounded_rectangle([60, 250, 60 + int(780 * p), 282], radius=16, fill=(0, 113, 227, 255))
        d.text((60, 320), "Installing…" if p < 0.99 else "Up to date.", font=F(46), fill=ink); d.text((60, 410), "Signed and checked by Apple.", font=F(30), fill=grey)
    rgb, al = to_f(im)
    if kind == "ask":
        s = 110; spr = cv2.resize(orbs[int(t * 12) % ORB_N], (s, s), interpolation=cv2.INTER_AREA)
        g, h = np.mgrid[0:s, 0:s].astype(np.float32); m = np.clip((s * 0.46 - np.hypot(h - s / 2, g - s / 2)) / 1.5, 0, 1)[:, :, None]
        rgb[205:205 + s, 70:70 + s] = rgb[205:205 + s, 70:70 + s] * (1 - m) + spr * m
    return rgb, al

FEATS = [("ask", "Ask it anything.", "Nova answers out loud, in a second."), ("apps", "It opens your apps.", "Say it. Nova does it."),
         ("day", "It knows your day.", "It reads your calendar and briefs you."), ("weather", "Weather, hour by hour.", "Today, tomorrow, or any day gone by."),
         ("guard", "It guards your screen.", "It blurs when someone looks over your shoulder."), ("fix", "It fixes your writing.", "Select any text. Press one shortcut."),
         ("music", "Your music, in the notch.", "Album art and controls, always there."), ("update", "It updates itself.", "One click. Nothing to download.")]
PILLS = ["“Hey Nova”", "Translate", "Drop a file", "Clipboard history", "Focus timer", "It remembers you", "Touch ID for anything risky",
         "English, Hindi, Hinglish", "Hidden from screen share", "Wakes when you look", "Notes", "Screenshots"]

def browser(orbs, t):
    BW, BH = 900, 580
    im = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, BW - 1, BH - 1], radius=22, fill=(255, 255, 255, 255), outline=(205, 205, 212, 255), width=2)
    d.rounded_rectangle([0, 0, BW - 1, 70], radius=22, fill=(238, 238, 242, 255)); d.rectangle([1, 40, BW - 2, 70], fill=(238, 238, 242, 255))
    for i, col in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]): d.ellipse([20 + i * 26, 16, 36 + i * 26, 32], fill=col)
    d.rounded_rectangle([130, 34, 770, 62], radius=14, fill=(255, 255, 255, 255)); d.text((150, 38), "any website", font=F(18), fill=(120, 124, 135))
    for i in range(5): d.rounded_rectangle([70, 240 + i * 56, 830 - (i % 3) * 150, 272 + i * 56], radius=10, fill=(236, 236, 241, 255))
    d.rounded_rectangle([BW / 2 - 190, 70, BW / 2 + 190, 200], radius=44, fill=(0, 0, 0, 255)); d.rectangle([BW / 2 - 190, 70, BW / 2 + 190, 110], fill=(0, 0, 0, 255))
    d.text((BW / 2 - 20, 118), "Ask Nova…", font=F(26), fill=(255, 255, 255))
    rgb, al = to_f(im); s = 96; spr = cv2.resize(orbs[int(t * 12) % ORB_N], (s, s), interpolation=cv2.INTER_AREA)
    x0 = BW // 2 - 150; rgb[86:86 + s, x0:x0 + s] = np.maximum(rgb[86:86 + s, x0:x0 + s], spr)
    return rgb, al

def phone(orbs, t):
    PW, PH = 380, 780
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], radius=64, fill=(20, 20, 24, 255), outline=(190, 192, 200, 255), width=5)
    d.rounded_rectangle([14, 14, PW - 15, PH - 15], radius=52, fill=(250, 250, 252, 255))
    d.rounded_rectangle([PW / 2 - 130, 34, PW / 2 + 130, 190], radius=50, fill=(0, 0, 0, 255)); d.text((PW / 2 - 62, 150), "Listening…", font=F(24), fill=(255, 255, 255))
    for i, s in enumerate(["Set a 5 minute timer", "Done. Timer is running."]):
        y = 300 + i * 120; mine = i == 0
        d.rounded_rectangle([40 if not mine else 70, y, PW - 40 if mine else PW - 70, y + 84], radius=30, fill=(0, 113, 227, 255) if mine else (236, 236, 241, 255))
        d.text((62 if not mine else 92, y + 28), s, font=F(21), fill=(255, 255, 255) if mine else (29, 29, 31))
    d.rounded_rectangle([PW / 2 - 60, PH - 34, PW / 2 + 60, PH - 28], radius=3, fill=(40, 40, 46, 255))
    rgb, al = to_f(im); s = 100; spr = cv2.resize(orbs[int(t * 12) % ORB_N], (s, s), interpolation=cv2.INTER_AREA)
    x0 = PW // 2 - s // 2; rgb[42:42 + s, x0:x0 + s] = np.maximum(rgb[42:42 + s, x0:x0 + s], spr)
    return rgb, al

def pill(s):
    f = F(40); w = int(f.getlength(s)) + 76
    im = Image.new("RGBA", (w, 84), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 83], radius=42, fill=(255, 255, 255, 255), outline=(214, 214, 222, 255), width=2); d.text((38, 18), s, font=f, fill=(29, 29, 31))
    return to_f(im)

def sprites():
    T = {"l1": text_sprite("Every Mac has a notch.", 100, SEMI), "l2": text_sprite("We gave it a mind.", 100, SEMI),
         "nova": text_sprite("Nova.", 210, FONT_BLACK), "novas": text_sprite("The AI that lives in your notch.", 54, SEMI),
         "talk": text_sprite("Just talk.", 150, FONT_BLACK), "talks": text_sprite("No app to open. No window to find.", 50, SEMI),
         "more": text_sprite("And there is more.", 110, FONT_BLACK), "where": text_sprite("Mac. Chrome. Phone.", 110, FONT_BLACK),
         "wheres": text_sprite("Nova goes where you go.", 50, SEMI),
         "title": text_sprite("NoTcH OS", 280, FONT_BLACK, 6), "tag": text_sprite("Nova lives in your notch.", 60, SEMI),
         "free": text_sprite("Free for Mac.", 150, FONT_BLACK), "url": text_sprite("notch.zeroorigine.com", 80, SEMI),
         "apple": text_sprite("Signed and checked by Apple.   A ZeroOrigine product.", 36, SEMI)}
    for k, h, s in FEATS: T[k + "_h"] = text_sprite(h, 104, FONT_BLACK); T[k + "_s"] = text_sprite(s, 46, SEMI)
    return T

def scene(n, orbs, T):
    if n == 1:      # 0-8: two quiet lines
        N = 8 * BEAT
        for f in range(N):
            c = paper(); h = 4 * BEAT
            a1 = ease((f - 8) / 18) * (1 - ease((f - h + 16) / 14)); text(c, T["l1"], W / 2, H / 2 + 20 * (1 - out((f - 8) / 18)), a1, INK, 1 + f * 0.0003)
            g = f - h; a2 = ease(g / 18) * (1 - ease((g - h + 18) / 14)); text(c, T["l2"], W / 2, H / 2 + 20 * (1 - out(g / 18)), a2, INK, 1 + max(0, g) * 0.0003)
            yield finish(c, f, N, 1, 1)
    if n == 2:      # 8-18: Nova
        N = 10 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper()
            orb(c, orbs, t, W / 2, 380 + 30 * (1 - out(u * 2)), 330 + 30 * u, ease(f / 20))
            rise(c, T["nova"], W / 2, 760, f, 30, INK, 1 + 0.02 * u); rise(c, T["novas"], W / 2, 925, f, 60, GREY)
            yield finish(c, f, N)
    if n == 3:      # 18-30: the Mac, the notch drops
        N = 12 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper()
            d = ease((f - 4 * BEAT) / 30); rgb, al = macbook(orbs, t, d)
            sc = 0.70 + 0.05 * u + 0.55 * ease((f - 3 * BEAT) / 70)
            M = homography(rgb.shape[1], rgb.shape[0], W / 2, 430 + (sc - 0.70) * 400, sc, 0.42 * (1 - out(u * 2.2)), 0.10 * (1 - out(u * 2.2)) + 0.03)
            over(c, rgb, al, M, 1.0, 0.26, 56, 46)
            rise(c, T["talk"], W / 2, 840, f, 6 * BEAT); rise(c, T["talks"], W / 2, 965, f, 7 * BEAT + 10, GREY)
            yield finish(c, f, N)
    if n == 4:      # 30-78: eight features, six beats each
        for i, (k, _, _) in enumerate(FEATS):
            N = 6 * BEAT
            for f in range(N):
                t = f / FPS; u = f / N; c = paper()
                rise(c, T[k + "_h"], W / 2, 150, f, 6, INK, min(1.0, 1500 / (T[k + "_h"].shape[1] - 80))); rise(c, T[k + "_s"], W / 2, 262, f, 20, GREY)
                e = out((f - 14) / 34); rgb, al = card(k, orbs, t, u)
                M = homography(CW, CH, W / 2, 660 + 70 * (1 - e), 1.04 + 0.03 * u, 0.10 * math.sin(i * 1.7) * (1 - e), 0.30 * (1 - e) + 0.03)
                over(c, rgb, al, M, ease((f - 14) / 20), 0.20, 40, 44)
                yield finish(c, f, N, 10, 10)
    if n == 5:      # 78-86: and there is more
        N = 8 * BEAT; P = [pill(s) for s in PILLS]
        rows = [P[0:4], P[4:8], P[8:12]]
        for f in range(N):
            c = paper(); rise(c, T["more"], W / 2, 200, f, 6)
            k = 0
            for r, row in enumerate(rows):
                raw = sum(p[0].shape[1] for p in row) + 28 * (len(row) - 1); z = min(1.25, 1740 / raw); x = W / 2 - raw * z / 2
                for rgb, al in row:
                    w = rgb.shape[1]; st = 22 + k * 9; e = out((f - st) / 16)
                    M = homography(w, 84, x + w * z / 2, 480 + r * 150 + 24 * (1 - e), z, 0, 0)
                    over(c, rgb, al, M, ease((f - st) / 12), 0.12, 16, 18); x += (w + 28) * z; k += 1
            yield finish(c, f, N)
    if n == 6:      # 86-94: where it runs
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper()
            rise(c, T["where"], W / 2, 150, f, 6); rise(c, T["wheres"], W / 2, 262, f, 22, GREY)
            e1, e2, e3 = out((f - 12) / 30), out((f - 24) / 30), out((f - 36) / 30)
            rgb, al = browser(orbs, t); M = homography(900, 580, 1440, 690 + 50 * (1 - e2), 0.66, -0.30 + 0.04 * u, 0.03); over(c, rgb, al, M, e2, 0.22)
            rgb, al = macbook(orbs, t, 1.0); M = homography(rgb.shape[1], rgb.shape[0], 600, 680 + 50 * (1 - e1), 0.50, 0.26 - 0.04 * u, 0.03); over(c, rgb, al, M, e1, 0.24)
            rgb, al = phone(orbs, t); M = homography(380, 780, 1030, 720 + 50 * (1 - e3), 0.66, -0.06 + 0.12 * u, 0.02); over(c, rgb, al, M, e3, 0.26)
            yield finish(c, f, N)
    if n == 7:      # 94-102: the name
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper()
            orb(c, orbs, t, W / 2, 290, 300 + 16 * u, ease(f / 18))
            a = ease((f - 14) / 22)
            text(c, T["title"], W / 2, 690 + 24 * (1 - out((f - 14) / 22)), a, INK, 0.96 + 0.04 * u, 0.10 * math.sin(t * 0.5), -0.03)
            rise(c, T["tag"], W / 2, 905, f, 60, GREY)
            yield finish(c, f, N)
    if n == 8:      # 102-108: where to get it, then white
        N = 6 * BEAT
        for f in range(N):
            t = f / FPS; c = paper()
            orb(c, orbs, t, W / 2, 200, 170, ease(f / 14))
            rise(c, T["free"], W / 2, 480, f, 8); rise(c, T["url"], W / 2, 665, f, 28, BLUE); rise(c, T["apple"], W / 2, 850, f, 48, GREY)
            yield finish(c, f, N, 12, 26)

PICKS = {1: [45, 150], 2: [200], 3: [60, 280], 4: [130, 280, 430, 580, 730, 880, 1030, 1180], 5: [190], 6: [190], 7: [180], 8: [110]}
def render(n):
    orbs = load_orbs(); T = sprites(); tmp = f"{OUT}/w{n}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    k = 0
    for fr in scene(n, orbs, T): p.stdin.write(fr.tobytes()); k += 1
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, f"{OUT}/w{n}.mp4"); print("scene", n, k)

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        orbs = load_orbs(); T = sprites()
        for n in ([int(x) for x in sys.argv[2:]] or PICKS):
            for i, fr in enumerate(scene(n, orbs, T)):
                if i in PICKS[n]: Image.fromarray(fr).save(f"{OUT}/w_{n:02d}_{i:04d}.jpg", quality=90)
                if i >= max(PICKS[n]): break
    else:
        for n in sys.argv[1:]: render(int(n))
