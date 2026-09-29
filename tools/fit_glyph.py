"""Fit a 1-bit glyph into a fixed ascent/descent budget without clipping it.

Noita sizes every text row from the tallest/deepest glyph in the font, so one
overlong Arabic stem stretches every menu. Instead of cutting glyphs off, we
drop *redundant* rows: a row whose ink is identical to its neighbour's is a
straight stem or tail segment, and removing one only shortens that stroke.
Dots and bowls never repeat row-for-row, so they survive untouched.
"""


def _rows(mask):
    w, h = mask.size
    px = mask.load()
    return [tuple(1 if px[x, y] else 0 for x in range(w)) for y in range(h)]


def _merge_closest(rows, lo, hi):
    """OR together the most alike adjacent pair within rows[lo:hi].

    Used once no row is an exact duplicate. Merging keeps every inked pixel,
    so dots and hamzas squeeze closer instead of being cut off. A blank row is
    merged away only when no pair of inked rows is left: it is the gap that
    keeps a dot off its letter, and losing it fuses the two.
    """
    def cost(i):
        a, b = rows[i], rows[i + 1]
        return (not (any(a) and any(b)), sum(x != y for x, y in zip(a, b)))
    i = min(range(lo, hi - 1), key=cost)
    rows[i:i + 2] = [tuple(x | y for x, y in zip(rows[i], rows[i + 1]))]


def fit(mask, baseline, max_up, max_down):
    """mask: 1-bit/L glyph image; baseline: row index of the baseline within it.

    Returns (rows, baseline, squeezed) where rows is a list of row tuples.
    Ascent = rows above the baseline, descent = rows at/below it.
    """
    rows = _rows(mask)
    ink = [i for i, r in enumerate(rows) if any(r)]
    if not ink:
        return rows, baseline, 0
    rows = rows[ink[0]:ink[-1] + 1]
    baseline -= ink[0]
    clipped = 0

    # ascent: remove duplicate rows scanning downward from the top
    while baseline > max_up:
        for i in range(0, baseline - 1):
            if rows[i] == rows[i + 1]:
                del rows[i]
                break
        else:                                # nothing redundant: squeeze
            _merge_closest(rows, 0, baseline)
            clipped += 1
        baseline -= 1

    # descent: remove duplicate rows scanning upward from the bottom
    while len(rows) - baseline > max_down:
        for i in range(len(rows) - 1, baseline, -1):
            if rows[i] == rows[i - 1]:
                del rows[i]
                break
        else:
            _merge_closest(rows, baseline, len(rows))
            clipped += 1
    return rows, baseline, clipped
