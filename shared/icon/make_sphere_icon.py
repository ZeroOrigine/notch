# NoTcH OS app icon = Nova's talking avatar: a dark glass sphere with a flowing
# orange, white and blue light band inside, on a dark macOS squircle. Same design as the in-app Orb.
import struct, io, math, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
S = 1024

def band_poly(x0, x1, mid, half, n=160):
    top, bot = [], []
    for i in range(n + 1):
        u = i / n; x = x0 + (x1 - x0) * u
        h = half * (math.sin(math.pi * u) ** 0.8)
        top.append((x, mid(x) - h)); bot.append((x, mid(x) + h))
    return top + bot[::-1]

def add_light(base, layer):
    # additive ("plus lighter") blend
    r = ImageChops.add(base.convert("RGB"), layer.convert("RGB"))
    out = r.convert("RGBA"); out.putalpha(base.getchannel("A")); return out

def make(t=0.6):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # background squircle tile: near-black with a soft violet glow
    tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle([100, 100, 924, 924], radius=185, fill=255)
    bg = Image.new("RGBA", (S, S), (8, 8, 14, 255))
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([200, 260, 824, 884], fill=(28, 28, 40, 255))
    bg = add_light(bg, glow.filter(ImageFilter.GaussianBlur(150)))
    tile.paste(bg, (0, 0), m)
    img = tile

    W = 824; ox = 100  # draw inside the tile
    cx, cy, r = ox + W / 2, ox + W / 2, W * 0.37

    # sphere body: dark radial glass
    ball = Image.new("L", (S, S), 0)
    ImageDraw.Draw(ball).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    body = Image.new("RGBA", (S, S), (0, 0, 0, 0)); bp = body.load()
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            dd = math.hypot(x - cx, y - cy) / r
            if dd <= 1:
                v = int(23 * (1 - dd) + 2)
                bp[x, y] = (v, v, v + 2, 255)
    img.paste(body, (0, 0), ball)

    # light ribbons inside the sphere, clipped to it
    inner = [((255, 150, 40), 0.13, 0.35, 0.07, -0.14), ((255, 50, 40), 0.13, 0.25, 0.07, -0.08),
             ((50, 100, 255), 0.13, 0.05, 0.09, 0.08), ((90, 190, 255), 0.13, 0.12, 0.05, 0.03),
             ((255, 240, 230), 0.13, 0.18, 0.018, -0.025)]
    waves = Image.new("RGB", (S, S), (0, 0, 0))
    for col, amp, ph, th, yy in inner:
        lay = Image.new("RGB", (S, S), (0, 0, 0))
        poly = band_poly(cx - r, cx + r, lambda x, amp=amp, ph=ph, yy=yy: cy + yy * r + math.sin((x - cx) / r * 2.2 + 0.4 + ph) * amp * r, th * r)
        ImageDraw.Draw(lay).polygon(poly, fill=tuple(int(v * (0.7 if col[2] > 200 and col[0] > 200 else 0.62)) for v in col))
        waves = ImageChops.add(waves, lay.filter(ImageFilter.GaussianBlur(r * 0.07)))
    waves = Image.composite(waves, Image.new("RGB", (S, S)), ball)
    img = add_light(img, waves)

    # glass rim: a soft white mist all round, brighter at the bottom, plus a faint haze inside the top half
    rim = Image.new("RGB", (S, S), (0, 0, 0)); rp = ImageDraw.Draw(rim)
    for i in range(240):
        a0 = 360 * i / 240; a1 = a0 + 1.6
        ym = math.sin(math.radians(a0))
        v = int(255 * (0.55 + 0.35 * max(0, ym)))
        rp.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=(v, v, v), width=int(r * 0.05))
    halo = rim.filter(ImageFilter.GaussianBlur(r * 0.06))
    inside = Image.composite(halo, Image.new("RGB", (S, S)), ball)
    img = add_light(img, inside)
    img = add_light(img, rim.filter(ImageFilter.GaussianBlur(r * 0.012)).point(lambda v: int(v * 0.6)))
    haze = Image.new("RGB", (S, S), (0, 0, 0))
    ImageDraw.Draw(haze).ellipse([cx - r * 0.95, cy - r * 0.98, cx + r * 0.95, cy + r * 0.15], fill=(26, 26, 30))
    img = add_light(img, Image.composite(haze.filter(ImageFilter.GaussianBlur(r * 0.2)), Image.new("RGB", (S, S)), ball))
    # colour bending at the edges: red left, blue right
    edge = Image.new("RGB", (S, S), (0, 0, 0)); ep = ImageDraw.Draw(edge)
    rr = r * 0.97; w = max(4, int(r * 0.06))
    ep.arc([cx - rr, cy - rr, cx + rr, cy + rr], 100, 200, fill=(220, 140, 60), width=w)
    ep.arc([cx - rr, cy - rr, cx + rr, cy + rr], 140, 190, fill=(60, 110, 230), width=w)
    img = add_light(img, edge.filter(ImageFilter.GaussianBlur(r * 0.035)))
    img.putalpha(m)
    return img

def icns(img):
    chunks = b""
    for code, px in [(b"icp4", 16), (b"icp5", 32), (b"icp6", 64), (b"ic07", 128), (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024)]:
        b = io.BytesIO(); img.resize((px, px), Image.LANCZOS).save(b, "PNG"); d = b.getvalue()
        chunks += code + struct.pack(">I", len(d) + 8) + d
    return b"icns" + struct.pack(">I", len(chunks) + 8) + chunks

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    img = make()
    img.save(out + "/AppIcon.png")
    open(out + "/AppIcon.icns", "wb").write(icns(img))
    for px in (16, 32, 48, 128, 192, 512):
        img.resize((px, px), Image.LANCZOS).save(f"{out}/icon-{px}.png")
    # full-bleed version (no transparent corners) for iOS / Android / apple-touch-icon
    full = Image.new("RGBA", (S, S), (8, 8, 14, 255)); crop = img.crop((100, 100, 924, 924)).resize((S, S), Image.LANCZOS)
    full.paste(crop, (0, 0), crop); full.save(out + "/AppIcon-full.png")
    print("ok")
