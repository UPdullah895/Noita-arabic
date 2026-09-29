"""Convert a 'suffix | Arabic' worklist into src/ar/<group>.json.

Usage: pipe2json.py <prefix> <in.txt> <out.json>
Each line is '<key-without-prefix> | <text>'; '\\n' in the text is a line break.
"""
import json, sys

prefix, src, out = sys.argv[1:4]
d = {}
for line in open(src, encoding="utf-8"):
    if " | " not in line:
        continue
    k, v = line.rstrip("\n").split(" | ", 1)
    d[prefix + k.strip()] = v.replace("\\n", "\n")
json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(d), "->", out)
