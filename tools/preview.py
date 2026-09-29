"""Render strings through a built Noita font exactly as the game composes them.

Usage: preview.py <font.xml> <out.png> <zoom> <text>...
PITCH=<px> stacks lines at that pitch (the wand tooltip uses 8) to show collisions.
Arabic arguments are shaped with arabize() first.
"""
import re, sys, os
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from arabize import arabize

xml_path, out, zoom = sys.argv[1], sys.argv[2], int(sys.argv[3])
xml = open(xml_path).read()
png = os.path.join(os.path.dirname(xml_path), re.search(r"<Texture>\s*(\S+)", xml).group(1).split("/")[-1])
at = Image.open(png).convert("RGBA")
Q = {int(a): (int(ox), int(w), int(x), int(wd)) for a, ox, w, x, wd in re.findall(
    r'id="(\d+)" offset_x="(-?\d+)" offset_y="-?\d+" rect_h="\d+" rect_w="(\d+)" '
    r'rect_x="(\d+)" rect_y="\d+" width="(\d+)"', xml)}
ws = int(re.search(r"<WordSpace>\s*(\d+)", xml).group(1))
H = at.height
rows = []
for t in sys.argv[4:]:
    t = arabize(t)
    im = Image.new("RGBA", (600, H + 2))
    x = 2
    for ch in t:
        if ch == " ":
            x += ws
            continue
        ox, w, rx, wd = Q.get(ord(ch), (0, 0, 0, 4))
        if w:
            im.alpha_composite(at.crop((rx, 0, rx + w, H)), (x + ox, 1))
        x += wd
    rows.append(im.crop((0, 0, min(600, x + 4), H + 2)))
W = max(r.width for r in rows)
pitch = int(os.environ.get("PITCH", H + 2))
sheet = Image.new("RGBA", (W, pitch * (len(rows) - 1) + H + 2), (40, 32, 50, 255))
for i, r in enumerate(rows):
    sheet.alpha_composite(r, (0, i * pitch))
sheet.resize((W * zoom, sheet.height * zoom), Image.NEAREST).save(out)
