import os
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Identity
from xml.dom import minidom

# ===== מיפוי אותיות =====
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
    "lamed": 0x05DC,
    "mem": 0x05DE,
    "nun": 0x05E0,
    "samekh": 0x05E1,
    "ayin": 0x05E2,
    "pe": 0x05E4,
    "tsadi": 0x05E6,
    "qof": 0x05E7,
    "resh": 0x05E8,
    "shin": 0x05E9,
    "tav": 0x05EA,
    # אותיות סופיות
    "final_kaf": 0x05DA,   # ך
    "final_mem": 0x05DD,   # ם
    "final_nun": 0x05DF,   # ן
    "final_pe": 0x05E3,    # ף
    "final_tsadi": 0x05E5  # ץ
}

# ===== הזזות אנכיות מותאמות =====
vertical_offsets = {
    "yod": 500,
    "qof": -200,
    "final_kaf": -200,
    "final_nun": -200,
    "final_pe": -200,
    "final_tsadi": -200,
}

# ===== הזזה גלובלית ל־Y =====
GLOBAL_Y_SHIFT = -400  # אפשר לשנות כדי "להוריד" או "להעלות" את הפונט כולו

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

    # ===== טעינת כל האותיות הרגילות כולל סופיות אם קיימות ב־svg_folder =====
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

            vertical_shift = vertical_offsets.get(name, 0) + GLOBAL_Y_SHIFT
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

    # ===== טעינת האותיות הסופיות ידנית מהמיקום הקבוע =====
    final_svgs = {
        "final_kaf": "app/backend/static/svg_letters/final_kaf.svg",
        "final_mem": "app/backend/static/svg_letters/final_mem.svg",
        "final_nun": "app/backend/static/svg_letters/final_nun.svg",
        "final_pe": "app/backend/static/svg_letters/final_pe.svg",
        "final_tsadi": "app/backend/static/svg_letters/final_tsadi.svg"
    }

    for name, path in final_svgs.items():
        if not os.path.exists(path):
            msg = f"⚠️ קובץ סופי לא נמצא: {path}"
            print(msg)
            logs.append(msg)
            continue

        try:
            unicode_val = letter_map[name]
            doc = minidom.parse(path)
            paths = doc.getElementsByTagName('path')
            glyph = font.newGlyph(name)
            glyph.unicode = unicode_val
            glyph.width = 600
            glyph.leftMargin = 40
            glyph.rightMargin = 40
            vertical_shift = vertical_offsets.get(name, 0) + GLOBAL_Y_SHIFT
            pen = glyph.getPen()
            transform = Identity.translate(0, vertical_shift)
            tp = TransformPen(pen, transform)

            for path_element in paths:
                d = path_element.getAttribute('d')
                if not d.strip():
                    continue
                parse_path(d, tp)

            doc.unlink()
            msg = f"✅ אות סופית {name} נטענה בהצלחה"
            print(msg)
            logs.append(msg)
            used_letters.add(name)

        except Exception as e:
            msg = f"❌ שגיאה בטעינת האות הסופית {name}: {e}"
            print(msg)
            logs.append(msg)

    # ===== סיום ושמירת הפונט =====
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
