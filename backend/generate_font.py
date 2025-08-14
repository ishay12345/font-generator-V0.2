import os
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Identity
from xml.dom import minidom

# מיפוי אותיות לעברית
# generate_font.py

letter_map = {
    "alef": 0x05D0,
    "bet": 0x05D1,
    "gimel": 0x05D2,
    "dalet": 0x05D3,
    "he": 0x05D4,
    "vav": 0x05D5,
    "zayin": 0x05D6,
    "het": 0x05D7,
    "tet": 0x05D8,
    "yod": 0x05D9,
    "kaf": 0x05DB,
    "final_kaf": 0x05DA,
    "lamed": 0x05DC,
    "mem": 0x05DE,
    "final_mem": 0x05DD,
    "nun": 0x05E0,
    "final_nun": 0x05DF,
    "samekh": 0x05E1,
    "ayin": 0x05E2,
    "pe": 0x05E4,
    "final_pe": 0x05E3,
    "tsadi": 0x05E6,
    "final_tsadi": 0x05E5,
    "qof": 0x05E7,
    "resh": 0x05E8,
    "shin": 0x05E9,
    "tav": 0x05EA
}



# מיפוי הזזות אנכיות מותאמות לפי אות (פיקסלים)
vertical_offsets = {
    "yod": 500,         # הזזה מעלה (יחסית ל־coordinate system ב־SVG)
    "qof": -200,        # הזזה למטה
    "final_kaf": -200,
    "final_nun": -200,
    "final_pe": -200,
    "final_tsadi": -200,
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
    logs = []

    for filename in sorted(os.listdir(svg_folder)):
        if not filename.lower().endswith(".svg"):
            continue

        try:
            if "_" in filename:
                name = filename.split("_", 1)[1].replace(".svg", "")
            else:
                name = filename.replace(".svg", "")

            if name not in letter_map:
                msg = f"🔸 אות לא במפה: {name}"
                print(msg)
                logs.append(msg)
                continue

            unicode_val = letter_map[name]
            svg_path = os.path.join(svg_folder, filename)
            doc = minidom.parse(svg_path)
            paths = doc.getElementsByTagName('path')

            if not paths:
                msg = f"⚠️ אין path בקובץ: {filename}"
                print(msg)
                logs.append(msg)
                doc.unlink()
                continue

            glyph = font.newGlyph(name)
            glyph.unicode = unicode_val
            glyph.width = 600
            glyph.leftMargin = 40
            glyph.rightMargin = 40
            vertical_shift = vertical_offsets.get(name, 0)

            pen = glyph.getPen()
            transform = Identity.translate(0, vertical_shift)
            tp = TransformPen(pen, transform)

            successful_paths = 0
            for path_element in paths:
                d = path_element.getAttribute('d')
                if not d.strip():
                    continue
                try:
                    parse_path(d, tp)
                    successful_paths += 1
                except Exception as e:
                    msg = f"⚠️ שגיאה בנתיב בקובץ {filename}: {e}"
                    print(msg)
                    logs.append(msg)

            doc.unlink()

            if successful_paths == 0:
                msg = f"❌ לא ניתן לנתח אף path עבור {filename}"
                print(msg)
                logs.append(msg)
                continue

            msg = f"✅ {name} נוסף בהצלחה ({successful_paths} path/paths)"
            print(msg)
            logs.append(msg)
            used_letters.add(name)
            count += 1

        except Exception as e:
            msg = f"❌ שגיאה בעיבוד {filename}: {e}"
            print(msg)
            logs.append(msg)

    missing_letters = sorted(set(letter_map.keys()) - used_letters)
    if missing_letters:
        print("\n🔻 אותיות שלא נכנסו:")
        for letter in missing_letters:
            print(f" - {letter}")
            logs.append(f"❌ לא נכנסה לפונט: {letter}")

    if count == 0:
        msg = "❌ לא נוצרו גליפים כלל."
        print(msg)
        logs.append(msg)
        return False, logs

    try:
        os.makedirs(os.path.dirname(output_ttf), exist_ok=True)
        ttf = compileTTF(font)
        ttf.save(output_ttf)
        msg = f"\n🎉 הפונט נוצר בהצלחה בנתיב: {output_ttf}"
        print(msg)
        logs.append(msg)
        return True, logs
    except Exception as e:
        msg = f"❌ שגיאה בשמירת הפונט: {e}"
        print(msg)
        logs.append(msg)
        return False, logs
