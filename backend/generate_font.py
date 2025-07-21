import os
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.ttGlyphPen import TTGlyphPen
from xml.dom import minidom

letter_map = {
    "alef": 0x05D0, "bet": 0x05D1, "gimel": 0x05D2, "dalet": 0x05D3,
    "he": 0x05D4, "vav": 0x05D5, "zayin": 0x05D6, "het": 0x05D7,
    "tet": 0x05D8, "lamed": 0x05DC, "yod": 0x05D9, "kaf": 0x05DB,
    "mem": 0x05DE, "nun": 0x05E0, "samekh": 0x05E1, "ayin": 0x05E2,
    "pe": 0x05E4, "tsadi": 0x05E6, "qof": 0x05E7, "resh": 0x05E8,
    "shin": 0x05E9, "tav": 0x05EA,
    "final_kaf": 0x05DA, "final_mem": 0x05DD, "final_nun": 0x05DF,
    "final_pe": 0x05E3, "final_tsadi": 0x05E5
}

def generate_ttf(svg_folder, output_ttf):
    print("🚀 יצירת פונט עם FontTools")
    font = Font()
    font.info.familyName = "Hebrew Font"
    font.info.styleName = "Regular"
    font.info.fullname = "Hebrew Font"
    font.info.unitsPerEm = 1000
    font.info.ascender = 800
    font.info.descender = -200

    glyph_count = 0

    for filename in os.listdir(svg_folder):
        if not filename.endswith(".svg"):
            continue

        parts = filename.split("_", 1)
        if len(parts) != 2:
            continue

        name = parts[1].replace(".svg", "")
        if name not in letter_map:
            continue

        code = int(letter_map[name])
        svg_path = os.path.join(svg_folder, filename)

        try:
            doc = minidom.parse(svg_path)
            paths = doc.getElementsByTagName('path')
            if not paths:
                doc.unlink()
                continue

            d = paths[0].getAttribute('d')
            if not d:
                doc.unlink()
                continue

            glyph = font.newGlyph(name)
            glyph.unicode = code
            pen = TTGlyphPen(None)
            parse_path(d, pen)
            tt_glyph = pen.glyph()

            # בדיקה אם הגליף ריק
            if not tt_glyph or not hasattr(tt_glyph, 'getBoundingBox'):
                print(f"⚠️ גליף ריק או לא תקין: {filename}")
                doc.unlink()
                continue

            glyph.contours = tt_glyph

            # חישוב גבולות הגליף
            bounds = tt_glyph.getBoundingBox()
            if bounds:
                xmin, ymin, xmax, ymax = bounds
                outline_width = int(xmax - xmin)
                glyph.width = outline_width + 80
                glyph.left_side_bearing = 27
                glyph.right_side_bearing = 27
            else:
                print(f"⚠️ לא ניתן לחשב גבולות עבור {filename}")
                doc.unlink()
                continue

            glyph_count += 1
            print(f"✅ {filename} → {name} ✓")
            doc.unlink()

        except Exception as e:
            print(f"⚠️ שגיאה בקובץ {filename}: {e}")
            if 'doc' in locals():
                doc.unlink()

    if glyph_count == 0:
        print("❌ אין גליפים תקינים")
        return False

    try:
        os.makedirs(os.path.dirname(output_ttf), exist_ok=True)
        ttf = compileTTF(font)
        ttf.save(output_ttf)
        print(f"✅ הפונט נוצר: {output_ttf}")
        return True
    except Exception as e:
        print(f"❌ שגיאה בשמירת הפונט: {e}")
        return False
