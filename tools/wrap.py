"""Build-time line wrapping in real atlas pixels.

Noita has no text-wrapping API: its own long strings carry authored "\\n", and
a panel simply grows to fit its widest line (that is what pushed the New Game
panel off-screen). So Arabic lines get broken here, before shaping, and each
line is then shaped and reversed on its own -- which also avoids the inverted
line order you get when an engine wraps pre-reversed RTL text.
"""
import re
from arabize import arabize

QUAD = re.compile(r'<QuadChar id="(\d+)".*?width="(\d+)"')


class Metrics:
    def __init__(self, path):
        if path.endswith(".bin"):                   # generated font: advances
            import struct
            d = open(path, "rb").read()
            o = 8 + struct.unpack(">I", d[4:8])[0]
            count = struct.unpack(">I", d[o + 12:o + 16])[0]
            o += 16
            self.w = {}
            for i in range(count):
                cp, *v = struct.unpack(">I7f", d[o + 32 * i:o + 32 * i + 32])
                self.w[cp] = round(v[6])
            self.space = self.w.get(32, 3)
            return
        xml = open(path, encoding="utf-8").read()
        self.w = {int(a): int(b) for a, b in QUAD.findall(xml)}
        self.space = int(re.search(r"<WordSpace>\s*(\d+)", xml).group(1))

    def width(self, s):
        s = re.sub(r"\$\d+\w?", "0000", s)        # placeholders: assume ~4 digits
        return sum(self.space if c == " " else self.w.get(ord(c), 5) for c in s)


def limit_for(en, stock, slack=1.15, floor=120):
    """Max line width for the Arabic, or None when English is a one-liner."""
    lines = en.split("\\n")
    if len(lines) == 1:
        return None
    return max(floor, int(max(stock.width(l) for l in lines) * slack))


def wrap(ar, limit, metrics):
    """Greedy word wrap of logical Arabic; authored \\n breaks are kept."""
    out = []
    for para in ar.split("\\n"):
        words, line = para.split(" "), []
        for wd in words:
            trial = " ".join(line + [wd])
            if line and metrics.width(arabize(trial)) > limit:
                out.append(" ".join(line))
                line = [wd]
            else:
                line.append(wd)
        out.append(" ".join(line))
    return "\\n".join(out)
