import os
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.ttGlyphPen import TTGlyphPen
from xml.dom import minidom

# מיפוי אותיות לעברית
letter_map = {
    "alef": 0x05D0, "bet": 0x05D1, "gimel": 0x05D2, "dalet": 0x05D3,
    "he": 0x05D4, "vav": 0x05D5, "zayin": 0x05D6, "het": 0x05D7,
    "tet": 0x05D8, "yod": 0x05D9, "kaf": 0x05DB, "final_kaf": 0x05DA,
    "lamed": 0x05DC, "mem": 0x05DE, "final_mem": 0x05DD,
    "nun": 0x05E0, "final_nun": 0x05DF, "samekh": 0x05E1, "ayin": 0x05E2,
    "pe": 0x05E4, "final_pe": 0x05E3, "tsadi": 0x05E6, "final_tsadi": 0x05E5,
    "qof": 0x05E7, "resh": 0x05E8, "shin": 0x05E9, "tav": 0x05EA
}

def generate_ttf(svg_folder, output_ttf):
    print("🚀 התחלת יצירת פונט...")
    font = Font()
    font.info.familyName = "Hebrew Handwriting"
    font.info.styleName = "Regular"
    font.info.fullName = "bHebrew Handwriting"
    font.info.unitsPerEm = 1000
    font.info.ascender = 800
    font.info.descender = -200

    count = 0
    for filename in sorted(os.listdir(svg_folder)):
        if not filename.endswith(".svg"):
            continue

        try:
            if "_" in filename:
                name = filename.split("_", 1)[1].replace(".svg", "")
            else:
                name = filename.replace(".svg", "")

            if name not in letter_map:
                print(f"🔸 אות לא נמצאה במפה: {name}")
                continue

            unicode_val = letter_map[name]
            svg_path = os.path.join(svg_folder, filename)

            doc = minidom.parse(svg_path)
            paths = doc.getElementsByTagName('path')
            if not paths:
                doc.unlink()
                continue

            d = paths[0].getAttribute('d')
            doc.unlink()
            if not d:
                continue

            # צור גליף חדש לפונט
            glyph = font.newGlyph(name)
            glyph.unicode = unicode_val
            glyph.width = 700

            # השתמש ב־TTGlyphPen לציור הגליף
            pen = glyph.getPen()
            try:
                parse_path(d, pen)
            except Exception as e:
                print(f"⚠️ שגיאה בפירוק path ב-{filename}: {e}")
                continue

            print(f"✅ {filename} הומר בהצלחה")
            count += 1

        except Exception as e:
            print(f"❌ שגיאה בעיבוד {filename}: {e}")

    if count == 0:
        print("❌ לא נוצרו גליפים")
        return False

    try:
        os.makedirs(os.path.dirname(output_ttf), exist_ok=True)
        ttf = compileTTF(font)
        ttf.save(output_ttf)
        print(f"\n🎉 הפונט נוצר בהצלחה בנתיב: {output_ttf}")
        return True
    except Exception as e:
        print(f"❌ שגיאה בשמירת הפונט: {e}")
        return False
