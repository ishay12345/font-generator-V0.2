import os
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Identity
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from xml.dom import minidom

# מיפוי אותיות לעברית
letter_map = {
    "alef": 0x05D0, "bet": 0x05D1, "gimel": 0x05D2, "dalet": 0x05D3,
    "he": 0x05D4, "vav": 0x05D5, "zayin": 0x05D6, "het": 0x05D7,
    "tet": 0x05D8, "lamed": 0x05DB, "yod": 0x05DC, "kaf": 0x05D9,
    "mem": 0x05DE, "nun": 0x05E0, "samekh": 0x05E1, "ayin": 0x05E2,
    "pe": 0x05E4, "tsadi": 0x05E6, "qof": 0x05E7, "resh": 0x05E8,
    "shin": 0x05E9, "tav": 0x05EA, "final_kaf": 0x05DA,
    "final_mem": 0x05DD, "final_nun": 0x05DF, "final_pe": 0x05E3,
    "final_tsadi": 0x05E5, "space": 0x0020
}

# חישוב גבולות של path
def get_path_bbox(d):
    pen = RecordingPen()
    parse_path(d, pen)
    bounds_pen = BoundsPen(None)
    pen.replay(bounds_pen)
    return bounds_pen.bounds  # (xMin, yMin, xMax, yMax)

def generate_ttf(svg_folder, output_ttf):
    print("🚀 התחלת יצירת פונט...")
    font = Font()
    font.info.familyName = "LHebrew Handwriting"
    font.info.styleName = "Regular"
    font.info.fullName = "LHebrew Handwriting"
    font.info.unitsPerEm = 1000
    font.info.ascender = 800
    font.info.descender = -200

    used_letters = set()
    count = 0

    for filename in sorted(os.listdir(svg_folder)):
        if not filename.lower().endswith(".svg"):
            continue

        try:
            name = filename.split("_", 1)[1].replace(".svg", "") if "_" in filename else filename.replace(".svg", "")
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

            # קביעת ערכי ברירת מחדל
            glyph.leftMargin = 10
            glyph.rightMargin = 10

            if name == "space":
                glyph.width = 300
                print("␣ רווח הוסף")
                used_letters.add(name)
                count += 1
                continue

            successful = False
            max_width = 0

            for path_element in paths:
                d = path_element.getAttribute('d')
                if not d.strip():
                    continue
                try:
                    # תזוזות מיוחדות
                    if name == "yod":
                        transform = Identity.translate(0, -80)
                        pen = TransformPen(glyph.getPen(), transform)
                    elif name == "lamed":
                        transform = Identity.translate(0, 120)
                        pen = TransformPen(glyph.getPen(), transform)
                    elif name == "qof":
                        transform = Identity.translate(0, -120)
                        pen = TransformPen(glyph.getPen(), transform)
                    elif name == "kaf":
                        transform = Identity.translate(0, 190)
                        pen = TransformPen(glyph.getPen(), transform)
                    else:
                        pen = glyph.getPen()

                    parse_path(d, pen)

                    # מחשבים רוחב לפי bbox
                    bounds = get_path_bbox(d)
                    if bounds:
                        xMin, yMin, xMax, yMax = bounds
                        max_width = max(max_width, xMax - xMin)

                    successful = True
                except Exception as e:
                    print(f"⚠️ שגיאה בנתיב ב-{filename}: {e}")

            doc.unlink()

            if not successful:
                print(f"❌ לא ניתן לנתח path עבור {filename}")
                continue

            # רוחב הגליף בהתאם לגודל (הוספת מרווח בטחון)
            glyph.width = int(max_width + 20) if max_width else 330

            print(f"✅ {name} נוסף בהצלחה, רוחב: {glyph.width}")
            used_letters.add(name)
            count += 1

        except Exception as e:
            print(f"❌ שגיאה בעיבוד {filename}: {e}")

    missing_letters = sorted(set(letter_map.keys()) - used_letters)
    if missing_letters:
        print("\n🔻 אותיות שלא נכנסו:")
        for letter in missing_letters:
            print(f" - {letter}")

    if count == 0:
        print("❌ לא נוצרו גליפים כלל.")
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
