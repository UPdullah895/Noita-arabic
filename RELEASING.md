# Releasing

The installers are the product, so every release ends with an install test, not a
`git push`.

## Before you build

1. `VERSION` — bump it for any change that ships.
2. `SUPPORTED_GAME` — the exact build of the game you tested against. The README
   row «اللعبة المدعومة» must contain that string; the docs check enforces it.
3. `python3 tools/check_docs.py` must print `docs ok`. CI runs it on every push to
   `main`, so do not tag while it fails.

## Build the archive

```bash
tools/release.sh
```

It builds the payload, stages `dist/NoitaArabic-<VERSION>/`, normalises the
Windows launchers to CRLF inside the archive, keeps `install.sh` at 0755, and
writes `dist/NoitaArabic-<VERSION>.zip.sha256`.

## Test it before anyone downloads it

```bash
mkdir -p /tmp/fake/Noita && touch /tmp/fake/Noita/noita.exe
cd "dist/NoitaArabic-<VERSION>"
./install.sh "/tmp/fake/Noita"
find "/tmp/fake/Noita" -maxdepth 3
./install.sh --uninstall "/tmp/fake/Noita"
```

The mod must land in `mods/translation_ar`, and the game must still list
*Arabic Translation* under Mods afterwards. Noita has no extra dependency, so a
failure here is a packaging failure.

## Publish

- `git tag -a v<VERSION> -m "NoitaArabic <VERSION>" && git push origin v<VERSION>`
- Attach `dist/NoitaArabic-<VERSION>.zip` **and** the `.sha256` file.
- Notes: what changed, install steps for Windows / Linux / Steam Deck, what is
  deliberately left in English, and what to do after a game update.
- `packaging/README.txt` is what players see inside the zip: edit it in the same
  commit as the change, or the archive ships yesterday's instructions.

## After publishing

- `python3 tools/check_docs.py` still prints `docs ok`.
- Open the raw README on `main` and one `screenshots/` URL: both must load.
- If the game version moved, update `SUPPORTED_GAME`, the README row, and the
  release title together.
