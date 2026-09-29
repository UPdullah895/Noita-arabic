"""Turn logical-order Arabic into the visual-order, pre-shaped text Noita needs.

Noita's renderer has no shaping and no bidi: it draws codepoints left to right,
one atlas cell each. So we do both jobs ahead of time -- map letters to their
Arabic presentation forms, then emit the glyphs in visual order.
"""
import re
import arabic_reshaper

_reshaper = arabic_reshaper.ArabicReshaper(configuration={
    "delete_harakat": True,          # the atlas cannot position combining marks
    "support_ligatures": False,
})

TOKEN = re.compile(r"\$\d+|\[[\x20-\x5A\x5E-\x7E]*\]")   # $0, [ENTER]; not translated [..] prose
RTL = re.compile("[\u0600-\u065F\u066A-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
LTR = re.compile("[%A-Za-z0-9\u00C0-\u024F\u0660-\u0669]")   # Arabic-Indic digits run LTR
SIGNED = re.compile("[0-9\x00]")
MIRROR = str.maketrans("()[]{}<>«»", ")(][}{><»«")


def _runs(s):
    """Split into (kind, text) runs.

    Whitespace forms its own run: if it were absorbed into a neighbour it would
    be flipped to that run's far side, and the gap around an embedded Latin or
    numeric run would end up on the wrong edge. Other neutrals (punctuation)
    follow the Unicode bidi rule: they take the direction of the strong text on
    both sides when it agrees, and the paragraph direction (RTL) otherwise, so
    a closing bracket or full stop after a number still lands on its RTL side.
    Protected tokens (\x00: $0, [ENTER]) are numbers or key names: LTR.
    """
    kinds = []
    for ch in s:
        if ch.isspace():
            kinds.append("sp")
        elif RTL.match(ch):
            kinds.append("rtl")
        elif ch == "\x00" or LTR.match(ch):
            kinds.append("ltr")
        elif ch in "+-" and SIGNED.match(s, len(kinds) + 1):   # keep "+5" signed
            kinds.append("ltr")
        else:
            kinds.append(None)
    strong = [k if k in ("rtl", "ltr") else None for k in kinds]
    for i, k in enumerate(kinds):
        if k is None:
            prev = next((x for x in reversed(strong[:i]) if x), "rtl")
            nxt = next((x for x in strong[i + 1:] if x), "rtl")
            kinds[i] = prev if prev == nxt else "rtl"
    out = []
    for ch, kind in zip(s, kinds):
        if out and out[-1][0] == kind:
            out[-1][1].append(ch)
        else:
            out.append((kind, [ch]))
    return [(k, "".join(v)) for k, v in out]


def _visual(line):
    parts, holes = [], []
    last = 0
    for m in TOKEN.finditer(line):                  # protect $0 / [ENTER]
        parts.append(line[last:m.start()])
        holes.append(m.group(0))
        last = m.end()
    parts.append(line[last:])

    shaped = [_reshaper.reshape(p) for p in parts]
    text = "\x00".join(shaped)

    pieces = []
    for kind, run in _runs(text):
        pieces.append(run[::-1].translate(MIRROR) if kind == "rtl" else run)
    visual = "".join(reversed(pieces))

    # holes were numbered left-to-right in logical order; after reversing the
    # run order they come back out right-to-left, so refill from the end.
    it = iter(reversed(holes))
    return re.sub("\x00", lambda _: next(it), visual)


def arabize(text):
    if not text or not RTL.search(text):
        return text
    # keep literal "\n" separators (two chars in the CSV) intact
    return "\\n".join(_visual(l) for l in text.split("\\n"))


if __name__ == "__main__":
    for s in ["ابدأ لعبة جديدة", "الخيارات", "لديك $0 ذهب", "اضغط [ENTER] للمتابعة",
              "الإصدار 1.0 من اللعبة"]:
        print(f"{s!r}\n  -> {arabize(s)!r}\n")
