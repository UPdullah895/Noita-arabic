# Internals

## Working on it

```
python -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/python tools/extract.py        # refresh work/en/<group>.json: what is still untranslated
./venv/bin/python tools/check.py          # validate src/ar/*.json
./venv/bin/python tools/build_mod.py      # build fonts + mod, install into the game, write build/translation_ar.zip
tools/release.sh                          # dist/NoitaArabic-<VERSION>.zip: mod + both installers + licences
```

`NOITA` at the top of `tools/build_mod.py` (and `build_font.py`, `extract.py`) points at the
game install. The build reads the stock CSV and fonts from there. It never writes anywhere
except `mods/translation_ar`.

To translate a batch, write `suffix | text` lines to `work/<group>_ar.txt` and convert them:

```
./venv/bin/python tools/pipe2json.py <key-prefix> work/<group>_ar.txt src/ar/<group>.json
```

`\n` in a line is a literal line break. Terminology lives in [glossary.md](glossary.md).

## Where the text lives

- `data/translations/common.csv` in the game holds all 3,706 keys. Columns are
  `key,en,ru,pt-br,…`.
- `src/ar/*.json` maps key to logical-order Arabic. The file split mirrors the key prefixes in
  `tools/extract.py` `GROUPS`: ui, action, actiondesc, perk, perkdesc, item, mat, animal, biome,
  status, log, book, misc, streaming and menu.
- A few keys contain a trailing space (`actiondesc_cloud_acid `, `bookdesc07_forged `). They
  are real keys and live in `misc.json`.
- Untranslated keys fall back to English. About 30 remain: debug strings and pure format
  strings such as `$0:$1`, `[$0]` and `$0K`.

## How it works

Noita has a first-class translation mod type (`mod.xml` with `is_translation="1"`). A language
is a CSV plus an XML of font slots. The engine has **no shaping, no bidi and no wrapping**, so
the build does all three:

1. **Shaping and bidi** (`tools/arabize.py`). arabic_reshaper produces presentation forms,
   with harakat deleted and ligatures off. A small bidi pass then reverses the RTL runs.
   - Whitespace is its own run.
   - `$N` and ASCII `[KEY]` tokens are protected and count as LTR.
   - `%` and a sign directly before a number stay with the number.
   - Other neutrals take the direction of their neighbours when those agree, and the
     paragraph's RTL direction otherwise, so a period after `50%` lands on the left.
   - Brackets and « » are mirrored.
2. **Wrapping** (`tools/wrap.py`). Wrapping applies only to strings whose English has
   authored `\n` breaks. Arabic lines are limited to the widest English line × 1.15, with a
   floor of 120px.
3. **Fonts** (`tools/build_font.py`). Each font is the stock pixel atlas plus Arabic glyphs
   from Pixel AE (a 10px design grid, rendered 1-bit at 10px). They are written as `ar_pixel`,
   `ar_pixel_big` and `ar_pixel_huge` (the huge one at 2×).

### Font geometry: the two limits that matter

- **Menus size each row as 2 × the tallest `rect_h`.** Arabic therefore has to live inside the
  stock 11px cell. Changing `LineHeight` does nothing to menus.
- **Wand and spell tooltips stack stat rows at a fixed 8px pitch**, matching their 8px icons.
  Neither `LineHeight` nor `rect_h` changes this. The stock Latin sits in rows 2–9 of the cell,
  with the baseline at 8. So the small fonts keep Arabic inside those same 8 rows: **6 up and
  2 down**. Neighbouring rows then never share ink; only the 1px shadow touches, exactly as it
  does for Latin. The 2× title font keeps the full 8/3 budget.

`tools/fit_glyph.py` squeezes each glyph into its budget:

1. It deletes rows that exactly duplicate their neighbour, which shortens straight stems and
   tails.
2. If that isn't enough, it ORs together the most alike adjacent pair of **inked** rows.
3. It merges a blank row only as a last resort. A blank row is the gap that keeps a dot off its
   letter, so merging it fuses them.

Two earlier versions failed. Clipping the outermost row deleted exactly the dots (ي→ى, ج→ح).
Letting blank rows merge on ties fused dots into bodies.

The shapes the squeezer still can't shrink are hand-drawn in `COMPACT` in
`tools/glyph_overrides.py`, used only by budgeted fonts:
- ي isolated and final: the bowl is lifted so the dots get their own row.
- ج: the dot goes inside the bowl.
- ع and غ: two-row tails.
- initial and medial ئ: a two-row hamza.

`OVERRIDES` holds the full-height drawings, used by the title font. It includes the Arabic
semicolon, which is drawn from scratch since Pixel AE lacks it, and borrows the comma's advance.
Check the whole set with a labelled sheet before shipping. `PITCH=8 tools/preview.py …` shows
the tooltip stacking.

### Things that were tried and rejected

- **`.bin` generated fonts** (the CJK path). They are bilinear-filtered and capped at scale 1,
  so they render tiny and blurry.
- **`fonts_pixel_font="0"` with the XML font.** Text renders at 1×, unreadably small.
- **Raising the cell height or `LineHeight`.** This either inflates menus off-screen or does
  nothing.

## Layout

```
src/ar/*.json          translations (the only hand-edited content besides docs)
docs/glossary.md       terminology
tools/                 arabize, wrap, fit_glyph, glyph_overrides, build_font, build_mod,
                       extract, check, pipe2json, preview
work/*_ar.txt          pipe-format sources the JSON was generated from
work/en/               untranslated worklists (Nolla's text; not for committing)
fonts/                 PixelAE-Regular.ttf (CC0)
mod/                   build output (gitignored)
dist/                  release archives from tools/release.sh (gitignored)
spacing_mod/           experimental: LuaJIT FFI mod raising the tooltip row pitch 8 -> 11
install.sh, install-windows.{bat,ps1}, packaging/README.txt   shipped in the release zip
```

## Checking

- `tools/check.py` reports errors for:
  - unknown keys
  - `$N` or `[KEY]` mismatches against the English
  - characters with no glyph
  - duplicate keys

  It also warns about Latin words that don't appear in the English.
- `tools/preview.py <font.xml> <out.png> <zoom> <text>...` renders through the built atlas.
  Use `PITCH=8` to stack the lines the way the wand tooltip does.
- In-game automation under Proton/XWayland:
  - `xdotool key --window` and `xdotool mousemove --window` work; clicks don't register.
  - Focus the game (`hyprctl dispatch focuswindow class:steam_app_881100`) before `grim`.
  - Stop the game with `kill $(pgrep -x noita.exe)`, never `pkill -f`.

## State

- 3,578 of 3,610 translatable keys are translated. `check.py` reports 0 errors.
- Verified in-game at 1080p:
  - main menu, Options, the New Game panel and the crash-recovery dialog
  - inventory headers
  - wand tooltip (all 8 stats), spell tooltips (projectile and bomb); the 6/2 font
    is previewed only, not yet checked in-game
  - flask tooltip
- Known and unfixable from a translation mod: the game concatenates some pieces left to right
  (a flask's name plus its fullness, "label - value" pairs). Each piece reads correctly, but
  the order between pieces is LTR.
- Not yet seen in-game:
  - the biome-entry title in the 2× font (checked in preview only)
  - perk pickup text
  - the end-of-run screen
