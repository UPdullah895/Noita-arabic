#!/usr/bin/env bash
# Build the archive that gets attached to a GitHub release: the translation mod, both
# installers and the licences, laid out so a player can unzip it and double-click.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$HERE/VERSION")"
NAME="NoitaArabic-$VERSION"
OUT="$HERE/dist/$NAME"

# builds mod/ (and installs it into the local game, as usual)
"$HERE/venv/bin/python" "$HERE/tools/build_mod.py"

rm -rf "$OUT"
mkdir -p "$OUT"
cp -R "$HERE/mod" "$OUT/translation_ar"
cp "$HERE/install.sh" "$HERE/install-windows.bat" "$HERE/install-windows.ps1" "$OUT/"
cp "$HERE/packaging/README.txt" "$OUT/README.txt"
cp "$HERE/LICENSE" "$OUT/LICENSE.txt"
mkdir -p "$OUT/licences"
cp "$HERE"/fonts/LICENCES/*.txt "$OUT/licences/"
chmod +x "$OUT/install.sh"

python3 - "$OUT" "$HERE/dist/$NAME.zip" <<'PY'
import sys, zipfile
from pathlib import Path

root, archive = Path(sys.argv[1]), Path(sys.argv[2])
# Store everything under one folder so unzipping never sprays files into Downloads.
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            info = zipfile.ZipInfo.from_file(path, Path(root.name) / path.relative_to(root))
            if path.name == "install.sh":
                info.external_attr = 0o755 << 16      # stays executable after unzip
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes())
print(f"{archive} ({archive.stat().st_size // 1024} KiB)")
PY
