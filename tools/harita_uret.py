#!/usr/bin/env python3
"""Natural Earth (world-atlas npm paketi, kamu malı) verisinden uygulamanın kullandığı iki dosyayı üretir:

  harita.js       Avrupa ülke sınırları (sadeleştirilmiş), duvardaki başvuru haritası için
  dunya-kara.png  Dünya kara maskesi (eşdikdörtgen), yörünge manzarasındaki Dünya için

Kullanım:
    npm pack world-atlas@2.0.2 && tar xzf world-atlas-2.0.2.tgz
    pip install pillow
    python3 tools/harita_uret.py package/
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent


def decode(topo, obj_name):
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(a if not out else a[1:])
        return out

    feats = []
    for g in topo["objects"][obj_name]["geometries"]:
        polys = []
        if g["type"] == "Polygon":
            polys.append([ring(r) for r in g["arcs"]])
        elif g["type"] == "MultiPolygon":
            for p in g["arcs"]:
                polys.append([ring(r) for r in p])
        feats.append(((g.get("properties") or {}).get("name", ""), polys))
    return feats


def simplify_ring(pts, tol):
    # Kapalı halkayı en uzak noktadan ikiye bölüp iki açık yol olarak sadeleştir
    if len(pts) < 5:
        return pts
    far = max(range(len(pts)), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    return simplify(pts[: far + 1], tol)[:-1] + simplify(pts[far:], tol)


def simplify(pts, tol):
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        L = (dx * dx + dy * dy) ** 0.5 or 1e-12
        best, bi = 0, -1
        for i in range(a + 1, b):
            x, y = pts[i]
            d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L
            if d > best:
                best, bi = d, i
        if best > tol and bi > 0:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def europe(pkg):
    topo = json.load(open(pkg / "countries-50m.json"))
    out = []
    for name, polys in decode(topo, "countries"):
        rings = []
        for poly in polys:
            for r in poly[:1]:  # yalnızca dış halka (Avrupa ölçeğinde göl delikleri gereksiz)
                xs = [p[0] for p in r]
                ys = [p[1] for p in r]
                if max(xs) < -32 or min(xs) > 60 or max(ys) < 28 or min(ys) > 75:
                    continue
                r = [(min(75, max(-40, x)), min(82, max(25, y))) for x, y in r]
                r = simplify_ring(r, 0.025)
                if len(r) < 4:
                    continue
                flat = []
                for x, y in r:
                    flat += [round(x, 2), round(y, 2)]
                rings.append(flat)
        if rings:
            out.append({"n": name, "r": rings})
    js = "// Natural Earth 1:50m (kamu malı) verisinden tools/harita_uret.py ile üretildi.\nwindow.EUROPE_GEO = " + json.dumps(out, separators=(",", ":")) + ";\n"
    (ROOT / "harita.js").write_text(js, encoding="utf-8")
    print("harita.js", len(js) // 1024, "KB,", len(out), "ülke")


def land_mask(pkg):
    topo = json.load(open(pkg / "land-50m.json"))
    W, H = 4096, 2048
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for _, polys in decode(topo, "land"):
        for poly in polys:
            for k, r in enumerate(poly):
                # 180. boylamı geçen halkaları süreklileştir, sonra iki kopya çiz
                un, off, px = [], 0.0, None
                for x, y in r:
                    if px is not None and x + off - px > 180:
                        off -= 360
                    elif px is not None and x + off - px < -180:
                        off += 360
                    px = x + off
                    un.append((px, y))
                for shift in (0, 360, -360):
                    pts = [((x + shift + 180) / 360 * W, (90 - y) / 180 * H) for x, y in un]
                    if len(pts) > 2:
                        d.polygon(pts, fill=255 if k == 0 else 0)
    land = img.filter(ImageFilter.GaussianBlur(1.2))
    coast = img.filter(ImageFilter.GaussianBlur(14))
    rgb = Image.merge("RGB", (land, coast, Image.new("L", (W, H), 0))).resize((2048, 1024), Image.LANCZOS)
    rgb.save(ROOT / "dunya-kara.png", optimize=True)
    print("dunya-kara.png", (ROOT / "dunya-kara.png").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    pkg = Path(sys.argv[1] if len(sys.argv) > 1 else "package")
    europe(pkg)
    land_mask(pkg)
