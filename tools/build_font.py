"""Extend Noita's bitmap pixel fonts with Pixel AE Arabic glyphs.

Noita fonts are a single-row PNG atlas plus a <FontData> XML of <QuadChar>
entries keyed by Unicode codepoint. Rules learned the hard way in-game:

* Every UI row is 2 x the tallest rect_h in it, so Arabic must live in the
  stock cell height (11px for font_pixel) or every menu grows. Pixel AE is
  taller than that, so glyphs are fitted by dropping redundant stem rows
  (see fit_glyph.py) instead of being clipped.
* Pixels must be 1-bit; anti-aliased edges read as blur.
* font_pixel bakes a 1px black shadow under each glyph, so Arabic gets one too.
* Each glyph sits in its own atlas box with a 1px gutter. Arabic ink often
  overhangs its advance (hamza marks, joins); that overhang goes into
  offset_x instead of spilling into the neighbouring glyph's box.

The generated .bin font path (used by CJK) was also tried and rejected: it is
bilinear-filtered, never upscaled, and still sizes rows from glyph extents.
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from arabic_reshaper.letters import LETTERS_ARABIC as LETTERS

sys.path.insert(0, os.path.dirname(__file__))
from fit_glyph import fit
from glyph_overrides import OVERRIDES, DONORS, COMPACT

NOITA = "/run/media/updullah/SSD 480GB/SteamLibrary/steamapps/common/Noita"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIXEL_AE = os.path.join(ROOT, "fonts", "PixelAE-Regular.ttf")
QUAD = re.compile(r'<QuadChar id="(\d+)".*?rect_w="(\d+)" rect_x="(\d+)"')


def target_codepoints():
    cps = set()
    for base, forms in LETTERS.items():
        cps.add(ord(base))
        cps.update(ord(c) for f in forms if f for c in f)
    cps.update(range(0xFEF5, 0xFEFD))          # lam-alef ligatures
    cps.update([0x060C, 0x061B, 0x061F, 0x0640, 0x066A, 0x066B, 0x066C])
    cps.update(range(0x0660, 0x066A))          # Arabic-Indic digits
    cps.update(range(0x0621, 0x0653))
    return sorted(cps)


def isolated_fallbacks():
    """Pixel AE lacks the isolated presentation forms; they equal the base letter."""
    import unicodedata as u
    out = {}
    for cp in range(0xFE70, 0xFEFD):
        name = u.name(chr(cp), "")
        if name.endswith(" ISOLATED FORM"):
            try:
                out[cp] = ord(u.lookup(name[:-len(" ISOLATED FORM")]))
            except KeyError:
                pass
    return out


def latin_baseline(atlas, quads):
    w, x = quads[ord("H")]
    rows = [y for y in range(atlas.height)
            if any(atlas.getpixel((x + i, y)) == (255, 255, 255, 255) for i in range(w))]
    return rows[-1] + 1


def glyph(ch, font, scale, cell_h, baseline, shadow, override=None, budget=None):
    """Render, fit and place one glyph. Returns (image, offset_x, advance, clipped)."""
    O = 20
    mask = Image.new("L", (60, 60), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    d.text((O, 40), ch, font=font, fill=255, anchor="ls")
    adv = round(font.getlength(ch)) * scale
    bb = mask.getbbox()
    if not bb:
        return None, 0, adv, 0
    col = mask.crop((bb[0], 0, bb[2], mask.height))
    max_up = baseline // scale
    # descenders may use the full cell; their shadow is simply cut at the cell
    # edge, which costs one barely-visible row instead of a row of the tail
    max_down = (cell_h - baseline) // scale
    if budget:
        max_up, max_down = min(max_up, budget[0]), min(max_down, budget[1])
    if override:
        rows, base = override
        col = Image.new("L", (len(rows[0]), len(rows)))
        col.putdata([v * 255 for r in rows for v in r])
        rows, base, clipped = fit(col, base, max_up, max_down)
    else:
        rows, base, clipped = fit(col, 40, max_up, max_down)
    m = Image.new("L", (col.width, len(rows)))
    m.putdata([v * 255 for r in rows for v in r])
    if scale != 1:
        m = m.resize((m.width * scale, m.height * scale), Image.NEAREST)
    img = Image.new("RGBA", (m.width, cell_h))
    top = baseline - base * scale
    if shadow:
        img.paste((0, 0, 0, 255), (0, top + 1), m)
    img.paste((255, 255, 255, 255), (0, top), m)
    return img, (bb[0] - O) * scale, adv, clipped


def build(src, out_name, outdir, scale=1, budget=None):
    xml = open(f"{NOITA}/data/fonts/{src}.xml", encoding="utf-8").read()
    src_png = re.search(r"<Texture>\s*(\S+)\s*</Texture>", xml).group(1)
    stock = Image.open(os.path.join(NOITA, src_png)).convert("RGBA")
    quads = {int(a): (int(w), int(x)) for a, w, x in QUAD.findall(xml)}
    shadow = any(p[3] and p[:3] == (0, 0, 0) for p in stock.get_flattened_data())
    cell_h, baseline = stock.height, latin_baseline(stock, quads)

    # A scaled-up Arabic (title font) needs scale x the 8-up/3-down budget.
    # Grow the cell to fit and move the stock Latin down onto the new baseline.
    new_base = max(baseline, 8 * scale)
    new_h = new_base + max(cell_h - baseline, 3 * scale)
    shift = new_base - baseline
    if (new_h, shift) != (cell_h, 0):
        grown = Image.new("RGBA", (stock.width, new_h))
        grown.alpha_composite(stock, (0, shift))
        stock, cell_h, baseline = grown, new_h, new_base
        xml = re.sub(r'rect_h="\d+"', f'rect_h="{cell_h}"', xml)

    font = ImageFont.truetype(PIXEL_AE, 10)    # 10px em == Pixel AE's design grid
    cmap = TTFont(PIXEL_AE).getBestCmap()
    fb = isolated_fallbacks()

    cells, missing, clipped = [], [], []
    for cp in target_codepoints():
        if cp in quads:
            continue
        src_cp = cp if cp in cmap else fb.get(cp, DONORS.get(cp))
        if src_cp not in cmap:
            missing.append(cp)
            continue
        drawn = (COMPACT if budget else {}).get(cp, COMPACT.get(src_cp) if budget else None)
        img, ox, adv, clip = glyph(chr(src_cp), font, scale, cell_h, baseline, shadow,
                                   drawn or OVERRIDES.get(cp, OVERRIDES.get(src_cp)), budget)
        if clip:
            clipped.append(cp)
        cells.append((cp, img, ox, adv))

    width = stock.width + sum((c[1].width if c[1] else 0) + 1 for c in cells) + 1
    out = Image.new("RGBA", (width, cell_h))
    out.alpha_composite(stock, (0, 0))
    lines, x = [], stock.width + 1
    for cp, img, ox, adv in cells:
        w = img.width if img else 0
        if img:
            out.alpha_composite(img, (x, 0))
        lines.append(f'  <QuadChar id="{cp}" offset_x="{ox}" offset_y="0" '
                     f'rect_h="{cell_h}" rect_w="{w}" rect_x="{x}" rect_y="0" '
                     f'width="{adv}" >\n  </QuadChar>')
        x += w + 1

    xml = xml.replace(src_png, f"mods/translation_ar/fonts/{out_name}.png")
    xml = xml.replace("</FontData>", "\n".join(lines) + "\n</FontData>")
    os.makedirs(outdir, exist_ok=True)
    out.save(os.path.join(outdir, out_name + ".png"))
    open(os.path.join(outdir, out_name + ".xml"), "w", encoding="utf-8").write(xml)
    print(f"{out_name}: +{len(cells)} arabic (x{scale}) in stock {cell_h}px cell, "
          f"baseline {baseline}, shadow={shadow}, clipped {len(clipped)}, "
          f"missing {len(missing)}")


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "build/fonts"
    # Wand/spell tooltips stack rows every 8px regardless of the font, so the
    # small fonts keep Arabic inside the stock Latin's 8 rows (6 up, 2 down):
    # neighbouring rows then never share ink. Titles are single lines and
    # keep the full cell.
    build("font_pixel", "ar_pixel", outdir, budget=(6, 2))
    build("font_pixel_big", "ar_pixel_big", outdir, budget=(6, 2))
    build("font_pixel_huge", "ar_pixel_huge", outdir, scale=2)
