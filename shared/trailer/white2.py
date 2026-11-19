# NoTcH OS white ad, version 2. 114 beats at 72 bpm = 95 s.
# New in this version: opens on the notch itself, pastel light that drifts behind every scene, gradient headlines
# that wipe in, cards that slide through with a coloured aura, voice bars in the island, a numbers scene,
# a download button on the end card.
import sys, math, os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import load_orbs, ORB_N, homography, text_sprite, ease, out, FONT_BLACK
import white as Wm
from white import (W, H, FPS, BEAT, OUT, SEMI, F, INK, GREY, BLUE, xx, yy, BG, text, rise, over, orb, to_f,
                   macbook, card, browser, phone, pill, CW, CH, PILLS)

PINK, PURPLE, PEACH, MINT, SKY = (0.98, 0.30, 0.55), (0.52, 0.32, 0.92), (1.0, 0.55, 0.25), (0.10, 0.72, 0.55), (0.0, 0.48, 0.95)
gy, gx = np.mgrid[0:135, 0:240].astype(np.float32); gx /= 240; gy /= 135
def paper(t, a=SKY, b=PINK, k=0.16):
    """White studio with two soft pastel lights drifting slowly."""
    x1 = 0.24 + 0.08 * math.sin(t * 0.30); y1 = 0.30 + 0.08 * math.cos(t * 0.24)
    x2 = 0.78 + 0.07 * math.cos(t * 0.27); y2 = 0.72 + 0.08 * math.sin(t * 0.33)
    l1 = np.exp(-(((gx - x1) / 0.34) ** 2 + ((gy - y1) / 0.46) ** 2))[:, :, None]
    l2 = np.exp(-(((gx - x2) / 0.36) ** 2 + ((gy - y2) / 0.46) ** 2))[:, :, None]
    img = 0.988 - l1 * (1 - np.array(a, np.float32)) * k - l2 * (1 - np.array(b, np.float32)) * k
    return cv2.resize(img.astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)

def head(c, spr, cx, cy, f, start, cols=None, scale=1.0, dur=24):
    """Headline that wipes in from the left. cols = (left colour, right colour) for a gradient, None for ink."""
    p = (f - start) / dur
    if p <= 0: return
    h, w = spr.shape; ws = w * scale
    m = cv2.warpPerspective(spr, homography(w, h, cx, cy + 18 * (1 - out(p)), scale, 0, 0), (W, H), flags=cv2.INTER_LINEAR)
    x0 = cx - ws / 2
    reveal = np.clip((out(p) * (ws + 260) - (xx - x0)) / 220.0, 0, 1)
    a = (m * reveal)[:, :, None]
    if cols is None: col = np.array(INK, np.float32)
    else:
        u = np.clip((xx - x0 - 40) / max(1, ws - 80), 0, 1)[:, :, None]
        col = np.array(cols[0], np.float32) * (1 - u) + np.array(cols[1], np.float32) * u
    c *= (1 - a); c += a * col

def aura(c, cx, cy, rx, ry, col, k=0.30):
    g = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))[:, :, None]
    c -= g * (1 - np.array(col, np.float32)) * k

def finish(c, f, N, fin=10, fout=10):
    k = ease(f / fin) * (1 - ease((f - (N - fout)) / fout))
    return (np.clip(c * k + BG * (1 - k), 0, 1) * 255).astype(np.uint8)

def mac_voice(orbs, t, drop, talk=0.0):
    """The Mac, with voice bars beside the sphere while it listens."""
    rgb, al = macbook(orbs, t, drop)
    if drop > 0.8 and talk > 0:
        ox, B, SW = 60, 20, 1400; cxs = ox + B + SW // 2
        for side in (-1, 1):
            for i in range(7):
                hgt = int((10 + 44 * abs(math.sin(t * 7 + i * 0.9 + side))) * talk * (1 - i * 0.09))
                x = cxs + side * (86 + i * 17); cv2.rectangle(rgb, (x - 4, B + 98 - hgt), (x + 4, B + 98 + hgt), (0.35, 0.75, 1.0) if side < 0 else (1.0, 0.55, 0.45), -1)
    return rgb, al

FEATS = [("ask", "Ask it anything.", "Nova answers out loud, in a second.", SKY, PURPLE), ("apps", "It opens your apps.", "Say it. Nova does it.", PEACH, PINK),
         ("day", "It knows your day.", "It reads your calendar and briefs you.", MINT, SKY), ("weather", "Weather, hour by hour.", "Today, tomorrow, or any day gone by.", PEACH, SKY),
         ("guard", "It guards your screen.", "It blurs when someone looks over your shoulder.", PURPLE, MINT), ("fix", "It fixes your writing.", "Select any text. Press one shortcut.", SKY, PINK),
         ("music", "Your music, in the notch.", "Album art and controls, always there.", PINK, PURPLE), ("update", "It updates itself.", "One click. Nothing to download.", SKY, MINT)]

def button(s):
    f = F(46); w = int(f.getlength(s)) + 120
    im = Image.new("RGBA", (w, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 109], radius=55, fill=(0, 113, 227, 255)); d.text((60, 28), s, font=f, fill=(255, 255, 255))
    return to_f(im)

def sprites():
    T = {"l1": text_sprite("Every Mac has a notch.", 96, SEMI), "l2": text_sprite("We gave it a mind.", 110, FONT_BLACK),
         "nova": text_sprite("Nova.", 230, FONT_BLACK), "novas": text_sprite("The AI that lives in your notch.", 54, SEMI),
         "talk": text_sprite("Just talk.", 160, FONT_BLACK), "talks": text_sprite("No app to open. No window to find.", 50, SEMI),
         "more": text_sprite("And there is more.", 116, FONT_BLACK), "where": text_sprite("Mac. Chrome. Phone.", 116, FONT_BLACK),
         "wheres": text_sprite("Nova goes where you go.", 50, SEMI),
         "n1": text_sprite("20+", 240, FONT_BLACK), "n2": text_sprite("3", 240, FONT_BLACK), "n3": text_sprite("1", 240, FONT_BLACK),
         "c1": text_sprite("things it can do", 46, SEMI), "c2": text_sprite("places it runs", 46, SEMI), "c3": text_sprite("notch", 46, SEMI),
         "title": text_sprite("NoTcH OS", 290, FONT_BLACK, 6), "tag": text_sprite("Nova lives in your notch.", 60, SEMI),
         "free": text_sprite("Free for Mac.", 150, FONT_BLACK), "url": text_sprite("notch.zeroorigine.com", 64, SEMI),
         "apple": text_sprite("Signed and checked by Apple.   A ZeroOrigine product.", 34, SEMI)}
    for k, h, s, _, _ in FEATS: T[k + "_h"] = text_sprite(h, 108, FONT_BLACK); T[k + "_s"] = text_sprite(s, 46, SEMI)
    return T

def scene(n, orbs, T):
    if n == 1:      # 0-8: the notch itself, close up; then it wakes
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper(t, SKY, PURPLE, 0.10)
            wake = ease((f - 4 * BEAT) / 26)
            rgb, al = macbook(orbs, t, wake * 0.55)
            sc = 1.55 + 0.10 * u
            M = homography(rgb.shape[1], rgb.shape[0], W / 2, 60 + rgb.shape[0] * sc / 2, sc, 0.0, 0.02)
            if wake > 0: aura(c, W / 2, 150, 520, 300, PINK, 0.25 * wake)
            over(c, rgb, al, M, 1.0, 0.22, 50, 44)
            c[640:] = c[640:] * 0 + paper(t, SKY, PURPLE, 0.10)[640:] * 1.0 if False else c[640:]
            band = np.clip((yy - 560) / 160, 0, 1)[:, :, None]; c[:] = c * (1 - band) + paper(t, SKY, PURPLE, 0.10) * band     # the screen fades into white below
            a1 = 1 - ease((f - 4 * BEAT + 14) / 12)
            if a1 > 0: head_a = T["l1"]; text(c, head_a, W / 2, 870, ease((f - 10) / 16) * a1, INK)
            head(c, T["l2"], W / 2, 870, f, 4 * BEAT + 4, (SKY, PINK))
            yield finish(c, f, N, 14, 10)
    if n == 2:      # 8-18: Nova
        N = 10 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper(t, PEACH, SKY, 0.18)
            aura(c, W / 2, 390, 420, 330, PURPLE, 0.16 * ease(f / 30))
            orb(c, orbs, t, W / 2, 380 + 40 * (1 - out(u * 2.2)), 340 + 34 * u, ease(f / 20))
            head(c, T["nova"], W / 2, 770, f, 26, (PEACH, PURPLE), 1 + 0.02 * u); rise(c, T["novas"], W / 2, 940, f, 62, GREY)
            yield finish(c, f, N)
    if n == 3:      # 18-30: the Mac; the notch drops and listens
        N = 12 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper(t, SKY, PINK, 0.14)
            d = ease((f - 3 * BEAT) / 30); rgb, al = mac_voice(orbs, t, d, ease((f - 5 * BEAT) / 20))
            sc = 0.70 + 0.05 * u + 0.60 * ease((f - 2 * BEAT) / 80)
            M = homography(rgb.shape[1], rgb.shape[0], W / 2, 430 + (sc - 0.70) * 400, sc, 0.45 * (1 - out(u * 2.4)), 0.10 * (1 - out(u * 2.4)) + 0.03)
            over(c, rgb, al, M, 1.0, 0.26, 56, 46)
            head(c, T["talk"], W / 2, 835, f, 6 * BEAT, (INK, INK)); rise(c, T["talks"], W / 2, 965, f, 7 * BEAT + 8, GREY)
            yield finish(c, f, N)
    if n == 4:      # 30-78: eight features; each card slides in from the right and leaves to the left
        for i, (k, _, _, a, b) in enumerate(FEATS):
            N = 6 * BEAT
            for f in range(N):
                t = f / FPS; u = f / N; c = paper(t + i * 4, a, b, 0.17)
                sc = min(1.0, 1560 / (T[k + "_h"].shape[1] - 80))
                leave = ease((f - (N - 14)) / 14)
                head(c, T[k + "_h"], W / 2 - 60 * leave, 150, f, 5, (a, b), sc); rise(c, T[k + "_s"], W / 2, 262, f, 22, GREY)
                e = out((f - 10) / 36); x = W / 2 + 420 * (1 - e) - 520 * leave
                aura(c, x, 670, 640, 330, a, 0.22 * e * (1 - leave)); aura(c, x + 220, 720, 420, 260, b, 0.16 * e * (1 - leave))
                rgb, al = card(k, orbs, t, u)
                M = homography(CW, CH, x, 660 + 6 * math.sin(t * 1.6), 1.05 + 0.03 * u, -0.34 * (1 - e) + 0.30 * leave, 0.03)
                over(c, rgb, al, M, ease((f - 10) / 16) * (1 - leave), 0.22, 44, 46)
                yield finish(c, f, N, 6, 6)
    if n == 5:      # 78-86: and there is more
        N = 8 * BEAT; P = [pill(s) for s in PILLS]; rows = [P[0:4], P[4:8], P[8:12]]
        for f in range(N):
            t = f / FPS; c = paper(t, MINT, PURPLE, 0.15); head(c, T["more"], W / 2, 200, f, 5, (PURPLE, PINK))
            k = 0
            for r, row in enumerate(rows):
                raw = sum(p[0].shape[1] for p in row) + 28 * (len(row) - 1); z = min(1.25, 1740 / raw); x = W / 2 - raw * z / 2
                for rgb, al in row:
                    w = rgb.shape[1]; st = 22 + k * 9; e = out((f - st) / 14)
                    M = homography(w, 84, x + w * z / 2, 480 + r * 150 + 30 * (1 - e), z * (0.9 + 0.1 * e), 0, 0)
                    over(c, rgb, al, M, ease((f - st) / 10), 0.14, 16, 18); x += (w + 28) * z; k += 1
            yield finish(c, f, N)
    if n == 6:      # 86-94: where it runs
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper(t, SKY, PEACH, 0.15)
            head(c, T["where"], W / 2, 150, f, 5, (SKY, PURPLE)); rise(c, T["wheres"], W / 2, 262, f, 22, GREY)
            e1, e2, e3 = out((f - 12) / 30), out((f - 24) / 30), out((f - 36) / 30)
            rgb, al = browser(orbs, t); M = homography(900, 580, 1440, 690 + 50 * (1 - e2), 0.66, -0.30 + 0.04 * u, 0.03); over(c, rgb, al, M, e2, 0.22)
            rgb, al = macbook(orbs, t, 1.0); M = homography(rgb.shape[1], rgb.shape[0], 600, 680 + 50 * (1 - e1), 0.50, 0.26 - 0.04 * u, 0.03); over(c, rgb, al, M, e1, 0.24)
            rgb, al = phone(orbs, t); M = homography(380, 780, 1030, 720 + 50 * (1 - e3), 0.66, -0.06 + 0.12 * u, 0.02); over(c, rgb, al, M, e3, 0.26)
            yield finish(c, f, N)
    if n == 7:      # 94-100: three numbers
        N = 6 * BEAT
        for f in range(N):
            t = f / FPS; c = paper(t, PINK, SKY, 0.15)
            for j, (num, cap, cols) in enumerate([("n1", "c1", (SKY, PURPLE)), ("n2", "c2", (PURPLE, PINK)), ("n3", "c3", (PINK, PEACH))]):
                x = W / 2 + (j - 1) * 560; st = 6 + j * 16
                head(c, T[num], x, 470, f, st, cols, 0.85 + 0.15 * out((f - st) / 20), 18); rise(c, T[cap], x, 670, f, st + 14, GREY)
            yield finish(c, f, N)
    if n == 8:      # 100-108: the name
        N = 8 * BEAT
        for f in range(N):
            t = f / FPS; u = f / N; c = paper(t, PEACH, SKY, 0.20)
            aura(c, W / 2, 300, 420, 300, PURPLE, 0.18)
            orb(c, orbs, t, W / 2, 290, 310 + 16 * u, ease(f / 18))
            head(c, T["title"], W / 2, 700, f, 14, (INK, INK), 0.96 + 0.04 * u, 30)
            shine = (f - 70) / 50                                  # one pass of colour across the letters
            if 0 < shine < 1:
                spr = T["title"]; h, w = spr.shape; sc = 0.96 + 0.04 * u
                m = cv2.warpPerspective(spr, homography(w, h, W / 2, 700, sc, 0, 0), (W, H))
                pos = W / 2 - w * sc * 0.6 + shine * w * sc * 1.2
                band = (np.exp(-((xx - pos) / 150.0) ** 2) * m)[:, :, None]
                uu = np.clip((xx - (W / 2 - w * sc / 2)) / (w * sc), 0, 1)[:, :, None]
                col = np.array(SKY, np.float32) * (1 - uu) + np.array(PINK, np.float32) * uu
                c *= (1 - band); c += band * col
            rise(c, T["tag"], W / 2, 915, f, 60, GREY)
            yield finish(c, f, N)
    if n == 9:      # 108-114: get it
        N = 6 * BEAT; brgb, bal = button("Download for Mac")
        for f in range(N):
            t = f / FPS; c = paper(t, SKY, PINK, 0.16)
            orb(c, orbs, t, W / 2, 170, 150, ease(f / 14))
            head(c, T["free"], W / 2, 430, f, 6, (SKY, PURPLE))
            e = out((f - 26) / 18); M = homography(brgb.shape[1], 110, W / 2, 620 + 24 * (1 - e), 0.92 + 0.08 * e, 0, 0); over(c, brgb, bal, M, ease((f - 26) / 12), 0.20, 18, 20)
            rise(c, T["url"], W / 2, 770, f, 42, INK); rise(c, T["apple"], W / 2, 900, f, 58, GREY)
            yield finish(c, f, N, 10, 28)

PICKS = {1: [80, 170], 2: [200], 3: [280], 4: [100, 400, 880], 5: [190], 6: [190], 7: [130], 8: [100, 180], 9: [120]}
def render(n):
    orbs = load_orbs(); T = sprites(); tmp = f"{OUT}/x{n}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    k = 0
    for fr in scene(n, orbs, T): p.stdin.write(fr.tobytes()); k += 1
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, f"{OUT}/x{n}.mp4"); print("scene", n, k)

if __name__ == "__main__":
    if sys.argv[1] == "stills":
        orbs = load_orbs(); T = sprites()
        for n in ([int(x) for x in sys.argv[2:]] or PICKS):
            for i, fr in enumerate(scene(n, orbs, T)):
                if i in PICKS[n]: Image.fromarray(fr).save(f"{OUT}/x_{n:02d}_{i:04d}.jpg", quality=90)
                if i >= max(PICKS[n]): break
    else:
        for n in sys.argv[1:]: render(int(n))
