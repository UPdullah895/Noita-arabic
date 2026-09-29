"""Hand-drawn replacements for Pixel AE glyphs whose tails can't fit Noita's cell.

Noita's 11px cell leaves 3 rows below the baseline, but Pixel AE draws these
tails 4-5 rows deep with no repeated rows to drop, so automatic fitting could
only clip them (losing the hamza of إ, the bowl of ج/ع). These are redrawn
into 3 rows in Pixel AE's own style; connection pixels are kept where they were.

Format: rows above the baseline, a "--" line, then rows below it.
'#' is ink. Horizontal placement and advance come from the original glyph.
"""

_ART = {
    0x0625: """
        .#..
        .#..
        .#..
        .#..
        .#..
        .#..
        .#..
        .#..
        --
        ....
        .##.
        ##..
    """,  # ALEF WITH HAMZA BELOW (isolated forms fall back to this)
    0xFE88: """
        .#..
        .#..
        .#..
        .#..
        .#..
        .#..
        .#..
        ..##
        --
        ....
        .##.
        ##..
    """,  # ALEF WITH HAMZA BELOW FINAL
    0x062C: """
        ######
        ..#...
        .#....
        #.....
        --
        #..#..
        .#...#
        ..###.
    """,  # JEEM
    0xFE9E: """
        ######.
        ..#...#
        .#....#
        #......
        --
        #..#...
        .#...#.
        ..###..
    """,  # JEEM FINAL
    0x0639: """
        ..###.
        .#...#
        .#....
        ..#...
        .####.
        --
        #.....
        #....#
        .####.
    """,  # AIN
    0xFECA: """
        ..###..
        .#...#.
        .#.....
        ..#....
        .######
        --
        #......
        #....#.
        .####..
    """,  # AIN FINAL
    0x063A: """
        ...#..
        ......
        ......
        ..###.
        .#...#
        .#....
        ..#...
        .####.
        --
        #.....
        #....#
        .####.
    """,  # GHAIN
    0xFECE: """
        ...#...
        .......
        .......
        ..###..
        .#...#.
        .#.....
        ..#....
        .######
        --
        #......
        #....#.
        .####..
    """,  # GHAIN FINAL
    0x064A: """
        .....##.
        .#..#..#
        #...#..#
        #....#..
        --
        .####...
        ........
        ..#.#...
    """,  # YEH
    0xFEF2: """
        .....##..
        .#..#..#.
        #...#..#.
        #....#..#
        --
        .####....
        .........
        ..#.#....
    """,  # YEH FINAL
    0x061B: """
        .#
        ..
        .#
        #.
        ##
        --
    """,  # ARABIC SEMICOLON -- absent from Pixel AE: a dot over its own comma
}

# Codepoints Pixel AE lacks entirely: drawn above, spaced like this donor glyph.
DONORS = {0x061B: 0x060C}   # semicolon takes the Arabic comma's advance


def _parse(art):
    lines = [l.strip() for l in art.strip().splitlines()]
    cut = lines.index("--")
    rows = [tuple(1 if c == "#" else 0 for c in l) for l in lines if l != "--"]
    return rows, cut


OVERRIDES = {cp: _parse(a) for cp, a in _ART.items()}


# Compact (6-up/2-down) drawings, used by fonts built with a budget. The wand
# and spell tooltips stack rows every 8px, so glyphs must stay inside the
# same 8 rows as the stock Latin; these are the shapes the squeezer could not
# shrink without pushing a dot into its letter.
_ART_COMPACT = {
    0x064A: """
    .....##.
    .#..#..#
    #...#..#
    #....#..
    .####...
    --
    ........
    ..#.#...
    """,  # YEH isolated: bowl lifted a row so the dots keep a gap
    0xFEF2: """
    .....##..
    .#..#..#.
    #...#...#
    .####...#
    --
    .........
    ..#.#....
    """,  # YEH final
    0x062C: """
    ######
    ..#...
    .#....
    #..#..
    --
    #....#
    .####.
    """,  # JEEM isolated: dot moves inside the bowl
    0xFE9E: """
    ######.
    ..#...#
    .#....#
    #..#...
    --
    #....#.
    .####..
    """,  # JEEM final
    0x0639: """
    ..###.
    .#...#
    .#....
    ..#...
    .####.
    --
    #.....
    .#####
    """,  # AIN isolated: open two-row tail
    0xFECA: """
    ..###..
    .#...#.
    .#.....
    ..#....
    .######
    --
    #......
    .#####.
    """,  # AIN final
    0x063A: """
    ...#..
    ......
    ..###.
    .#...#
    ..#...
    .####.
    --
    #.....
    .#####
    """,  # GHAIN isolated
    0xFECE: """
    ...#...
    .......
    ..###..
    .#...#.
    ..#....
    .######
    --
    #......
    .#####.
    """,  # GHAIN final
    0xFE8B: """
    ..##
    ###.
    ....
    ..#.
    ..#.
    ##..
    --
    """,  # YEH WITH HAMZA initial: two-row hamza keeps the tooth readable
    0xFE8C: """
    ..##
    ###.
    ....
    ..#.
    ..#.
    ##.#
    --
    """,  # YEH WITH HAMZA medial
}

COMPACT = {cp: _parse(a) for cp, a in _ART_COMPACT.items()}
