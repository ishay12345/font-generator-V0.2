import os
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.ttGlyphPen import TTGlyphPen
from xml.dom import minidom

# מיפוי שמות האותיות לעברית
letter_map = {
    "alef": 0x05D0, "bet": 0x05D1, "gimel": 0x05D2, "dalet": 0x05D3,
    "he": 0x05D4, "vav": 0x05D5, "zayin": 0x05D6, "het": 0x05D7,
    "tet": 0x05D8, "yod": 0x05D9, "kaf": 0x05DB, "lamed": 0x05DC,
    "mem": 0x05DE, "nun": 0x05E0, "samekh": 0x05E1, "ayin": 0x05E2,
    "pe": 0x05E4, "tsadi": 0x05E6, "qof": 0x05E7, "resh": 0x05E8,
    "shin": 0x05E9, "tav": 0x05EA,
    "final_kaf": 0x05DA, "final_mem": 0x05DD, "final_nun": 0x05DF,
    "final_pe": 0x05E3, "final_tsadi": 0x05E5
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_FOLDER = os.path.join(BASE_DIR, 'svg_letters')
EXPORT_PATH = os.path.join(BASE_DIR, '..', 'exports', 'hebrew_font.ttf')

def generate_ttf(svg_folder, output_path):
    print("🚀 Generating font with defcon + ufo2ft")
    print("📁 SVG folder:", svg_folder)
    print("📄 Output path:", output_path)

    font = Font()
    font.info.familyName = "HebrewFont"
    font.info.styleName = "Regular"
    font.info.unitsPerEm = 1000
    font.info.ascender = 800
    font.info.descender = -200

    found_glyphs = 0

    for filename in os.listdir(svg_folder):
        if not filename.endswith(".svg"):
            continue

        parts = filename.split("_")
        if len(parts) != 2:
            print(f"⚠️ שם קובץ לא תקני: {filename}")
            continue

        name = parts[1].replace(".svg", "")
        if name not in letter_map:
            print(f"⚠️ אות לא במיפוי: {name}")
            continue

        unicode_val = letter_map[name]
        glyph = font.newGlyph(name)
        glyph.unicode = unicode_val
        glyph.width = 600

        svg_path = os.path.join(svg_folder, filename)
        try:
            doc = minidom.parse(svg_path)
            paths = doc.getElementsByTagName('path')
            if not paths:
                print(f"⚠️ קובץ {filename} לא מכיל path")
                continue

            d = paths[0].getAttribute('d')
            if not d:
                print(f"⚠️ path חסר ב־{filename}")
                continue

            doc.unlink()

            pen = TTGlyphPen(None)
            try:
                parse_path(d, pen)
            except Exception as e:
                print(f"❌ שגיאה בפענוח path ב־{filename}: {e}")
                continue

            glyph._glyph = pen.glyph()
            found_glyphs += 1
            print(f"✅ נוספה אות: {name}")

        except Exception as e:
            print(f"❌ שגיאה ב־{filename}: {e}")

    if found_glyphs == 0:
        print("❌ לא נמצאו גליפים חוקיים - הפונט לא יישמר.")
        return

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        ttf = compileTTF(font)
        ttf.save(output_path)
        print(f"✅ הפונט נשמר בהצלחה: {output_path}")
    except Exception as e:
        print(f"❌ שגיאה בשמירת פונט: {e}")

if __name__ == "__main__":
    generate_ttf(SVG_FOLDER, EXPORT_PATH)
