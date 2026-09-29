"""Assemble the Noita Arabic translation mod."""
import csv, glob, json, os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(__file__))
from arabize import arabize
from wrap import Metrics, limit_for, wrap
from extract import load_ar

NOITA = "/run/media/updullah/SSD 480GB/SteamLibrary/steamapps/common/Noita"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = os.path.join(ROOT, "mod")

MOD_XML = '''<Mod
\tname="Arabic Translation"
\tdescription="ترجمة عربية / Arabic translation"
\trequest_no_api_restrictions="0"
\tis_translation="1"
\ttranslation_xml_path="mods/translation_ar/translation.xml"
\ttranslation_csv_path="mods/translation_ar/translation.csv"
>
</Mod>
'''

LANG_XML = '''<Language
\tkey="ar-noita"
\tname="{name}"
\tfont_default="mods/translation_ar/fonts/ar_pixel.xml"
\tfont_inventory_title="mods/translation_ar/fonts/ar_pixel_big.xml"
\tfont_important_message_title="mods/translation_ar/fonts/ar_pixel_huge.xml"
\tfont_world_space_message="mods/translation_ar/fonts/ar_pixel.xml"
\tfonts_utf8="1"
\tfonts_pixel_font="1"
\tui_action_info_offset2="10"
\tui_wand_info_offset1="10"
\tui_wand_info_offset2="20"
>
</Language>
'''


def main():
    shutil.rmtree(os.path.join(MOD, "fonts"), ignore_errors=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_font.py"),
                    os.path.join(MOD, "fonts")], check=True)

    ar = load_ar()
    rows = list(csv.reader(open(f"{NOITA}/data/translations/common.csv", encoding="utf-8")))

    stock = Metrics(f"{NOITA}/data/fonts/font_pixel.xml")
    ours = Metrics(os.path.join(MOD, "fonts", "ar_pixel.xml"))
    wrapped = 0

    out = [["", "ar", "en", "", "", "NOTES – use \\n for newline", "max length"]]
    done = 0
    for r in rows[1:]:
        key = r[0]
        en = r[1] if len(r) > 1 else ""
        if key in ar:
            text, limit = ar[key], limit_for(en, stock)
            if limit:
                new = wrap(text, limit, ours)
                wrapped += new != text
                text = new
            val = arabize(text)
            done += 1
        else:
            val = en                      # untranslated -> fall back to English
        out.append([key, val, en, "", "", "", ""])

    os.makedirs(MOD, exist_ok=True)
    with open(os.path.join(MOD, "translation.csv"), "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    open(os.path.join(MOD, "mod.xml"), "w", encoding="utf-8").write(MOD_XML)
    open(os.path.join(MOD, "translation.xml"), "w", encoding="utf-8").write(
        LANG_XML.format(name=arabize("العربية")))

    if subprocess.run([sys.executable, os.path.join(ROOT, "tools", "check.py")]).returncode:
        sys.exit("check.py failed -- not installing")

    dest = f"{NOITA}/mods/translation_ar"
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(MOD, dest)
    # release archive: unpacks to translation_ar/ inside Noita/mods
    zip_base = os.path.join(ROOT, "build", "translation_ar")
    shutil.make_archive(zip_base, "zip", os.path.dirname(dest), "translation_ar")
    print(f"translated {done}/{len(rows)-1} keys ({wrapped} re-wrapped) -> {dest}")
    print(f"release archive -> {zip_base}.zip")


if __name__ == "__main__":
    main()
