import os
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Identity
from xml.dom import minidom

# מיפוי אותיות לעברית
letter_map = {
    "alef": 0x05D0, "bet": 0x05D1, "gimel": 0x05D2, "dalet": 0x05D3,
    "he": 0x05D4, "vav": 0x05D5, "zayin": 0x05D6, "het": 0x05D7,
    "tet": 0x05D8, "kaf": 0x05DB, "lamed": 0x05DC, "yod": 0x05D9,
    "mem": 0x05DE, "nun": 0x05E0, "samekh": 0x05E1, "ayin": 0x05E2,
    "pe": 0x05E4, "tsadi": 0x05E6, "qof": 0x05E7, "resh": 0x05E8,
    "shin": 0x05E9, "tav": 0x05EA,
    "final_kaf": 0x05DA, "final_mem": 0x05DD, "final_nun": 0x05DF,
    "final_pe": 0x05E3, "final_tsadi": 0x05E5
}

# אותיות שצריך להקטין ולהוריד
letters_to_scale = {
    "tsadi": 120,
    "qof": 120,
    "final_kaf": 120,
    "final_nun": 120,
    "final_pe": 120,
    "final_tsadi": 120
}

def generate_ttf(svg_folder, output_ttf):
    print("🚀 התחלת יצירת פונט...")
    font = Font()
    font.info.familyName = "gHebrew Handwriting"
    font.info.styleName = "Regular"
    font.info.fullName = "gHebrew Handwriting"
    font.info.unitsPerEm = 1000
    font.info.ascender = 800
    font.info.descender = -200

    used_letters = set()
    count = 0

    for filename in sorted(os.listdir(svg_folder)):
        if not filename.lower().endswith(".svg"):
            continue

        try:
            if "_" in filename:
                name = filename.split("_", 1)[1].replace(".svg", "")
            else:
                name = filename.replace(".svg", "")

            if name not in letter_map:
                print(f"🔸 אות לא במפה: {name}")
                continue

            unicode_val = letter_map[name]
            svg_path = os.path.join(svg_folder, filename)

            doc = minidom.parse(svg_path)
            paths = doc.getElementsByTagName('path')
            if not paths:
                doc.unlink()
                print(f"⚠️ אין path בקובץ: {filename}")
                continue

            glyph = font.newGlyph(name)
            glyph.unicode = unicode_val
            glyph.width = 350

            # ✨ הרחבת מרווחים בין אותיות
            glyph.leftMargin = 40
            glyph.rightMargin = 40

            successful = False
            for path_element in paths:
                d = path_element.getAttribute('d')
                if not d.strip():
                    continue
                try:
                    # טיפול באותיות שדורשות הקטנה והורדה משמעותית
                    if name in letters_to_scale:
                        scale_factor = 0.85  # הקטנה קלה
                        translate_down = -letters_to_scale[name]  # הורדה חזקה
                        transform = Identity.scale(scale_factor, scale_factor).translate(0, translate_down)
                        pen = TransformPen(glyph.getPen(), transform)
                    elif name == "yod":
                        transform = Identity.translate(0, 120)  # הזזה למעלה ל-י'
                        pen = TransformPen(glyph.getPen(), transform)
                    else:
                        # הורדה כללית לכל האותיות כדי שלא יהיו חתוכות למעלה
                        transform = Identity.translate(0, -60)
                        pen = TransformPen(glyph.getPen(), transform)

                    parse_path(d, pen)
                    successful = True
                except Exception as e:
                    print(f"⚠️ שגיאה בנתיב ב-{filename}: {e}")

            doc.unlink()

            if not successful:
                print(f"❌ לא ניתן לנתח path עבור {filename}")
                continue

            print(f"✅ {name} נוסף בהצלחה")
            used_letters.add(name)
            count += 1

        except Exception as e:
            print(f"❌ שגיאה בעיבוד {filename}: {e}")

    # דיווח על אותיות חסרות
    missing_letters = sorted(set(letter_map.keys()) - used_letters)
    if missing_letters:
        print("\n🔻 אותיות שלא נכנסו:")
        for letter in missing_letters:
            print(f" - {letter}")

    if count == 0:
        print("❌ לא נוצרו גליפים כלל.")
        return False

    # שמירת הפונט
    try:
        os.makedirs(os.path.dirname(output_ttf), exist_ok=True)
        ttf = compileTTF(font)
        ttf.save(output_ttf)
        print(f"\n🎉 הפונט נוצר בהצלחה בנתיב: {output_ttf}")
        return True
    except Exception as e:
        print(f"❌ שגיאה בשמירת הפונט: {e}")
        return False
