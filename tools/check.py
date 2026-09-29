"""Validate src/ar/*.json against the game's English and our font.

Fails (exit 1) on anything that would break or garble in-game:
  * key not present in the game's common.csv
  * $N placeholders or [TOKEN]s differ from the English
  * a character the Arabic font cannot draw
Warns on Latin words left in (usually untranslated fragments).
"""
import collections, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
from extract import english, load_ar
from arabize import arabize
from wrap import Metrics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PH = re.compile(r"\$\d+")
TOK = re.compile(r"\[[A-Z]+\]")          # key/button tokens only


def main():
    en = english()
    font = Metrics(os.path.join(ROOT, "mod", "fonts", "ar_pixel.xml"))
    errors, warns, seen = [], [], {}
    for name, data in load_ar(per_file=True).items():
        for k, v in data.items():
            if k in seen:
                errors.append(f"{name}: {k}: duplicate (also in {seen[k]})")
            seen[k] = name
            if k not in en:
                errors.append(f"{name}: {k}: not a game key")
                continue
            e = en[k]
            if collections.Counter(PH.findall(e)) != collections.Counter(PH.findall(v)):
                errors.append(f"{name}: {k}: placeholders {PH.findall(e)} != {PH.findall(v)}")
            if collections.Counter(TOK.findall(e)) != collections.Counter(TOK.findall(v)):
                errors.append(f"{name}: {k}: tokens {TOK.findall(e)} != {TOK.findall(v)}")
            bad = {c for c in arabize(v) if ord(c) not in font.w and c not in " \\n"}
            if bad:
                errors.append(f"{name}: {k}: no glyph for {sorted(bad)}")
            en_words = set(re.findall(r"[A-Za-z]{3,}", e))
            latin = [w for w in re.findall(r"[A-Za-z]{3,}", v) if w not in en_words]
            if latin:
                warns.append(f"{name}: {k}: latin not in English: {latin}")
    for w in warns:
        print("warn:", w)
    for e in errors:
        print("ERROR:", e)
    print(f"{len(seen)} translated / {len(en)} keys, {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
