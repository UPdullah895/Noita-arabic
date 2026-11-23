"""Dump the game's English strings per group into work/en/ (not committed:
it is Nolla's text). Used as the worklist for translation.

Groups are key prefixes; each file is key -> English, only for keys that
still lack an Arabic translation in src/ar/.
"""
import csv, glob, json, os, re

# Set NOITA_DIR to point at your own install.
NOITA = os.environ.get(
    "NOITA_DIR", "/run/media/updullah/SSD 480GB/SteamLibrary/steamapps/common/Noita")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GROUPS = [  # (group name, key regex) -- first match wins
    ("actiondesc", r"^actiondesc_"), ("action", r"^action_"),
    ("perkdesc", r"^perkdesc_"), ("perk", r"^perk_"),
    ("mat", r"^mat_"), ("animal", r"^animal_"),
    ("itemdesc", r"^item(desc|pickupdesc)_"), ("item", r"^item(pickup)?_"),
    ("status", r"^status(desc)?_"),
    ("streaming", r"^streaming"),
    ("book", r"^book(title|desc)"),
    ("log", r"^log(desc)?_"),
    ("biome", r"^biome"),
    ("menu", r"^(menu|option|gamemode|input|controls|inventory|hud|stat|progress|"
             r"credits|achievement|reward|teleport|damage|Month_|boss|current_language)"),
]


def load_ar(per_file=False):
    """All translations. JSON "\\n" is a real newline; Noita's CSV wants the
    two characters backslash-n, so convert here -- the one place files are read."""
    files = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "src", "ar", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        files[os.path.basename(f)] = {k: v.replace("\n", "\\n") for k, v in d.items()}
    if per_file:
        return files
    return {k: v for d in files.values() for k, v in d.items()}


def english():
    rows = list(csv.reader(open(f"{NOITA}/data/translations/common.csv", encoding="utf-8")))
    return {r[0]: r[1] for r in rows[1:] if r and r[0] and len(r) > 1 and r[1].strip()}


def group_of(key):
    for name, rx in GROUPS:
        if re.match(rx, key):
            return name
    return "misc"


if __name__ == "__main__":
    en, ar = english(), load_ar()
    out = {}
    for k, v in en.items():
        if k not in ar:
            out.setdefault(group_of(k), {})[k] = v
    os.makedirs(os.path.join(ROOT, "work", "en"), exist_ok=True)
    for g, d in sorted(out.items()):
        json.dump(d, open(os.path.join(ROOT, "work", "en", g + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"{g:12s}{len(d):5d} todo  {sum(map(len, d.values())):7d} chars")
    print("translated", len(ar), "of", len(en))
