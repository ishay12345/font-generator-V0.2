import os
import hashlib
import numpy as np
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Identity
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from xml.dom import minidom
import cv2

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

def get_combined_bbox(paths):
    pen = RecordingPen()
    for d in paths:
        parse_path(d, pen)
    bounds_pen = BoundsPen(None)
    pen.replay(bounds_pen)
    return bounds_pen.bounds, pen

def hash_d_list(d_list):
    all_d = "".join(sorted(d_list))
    return hashlib.sha256(all_d.encode('utf-8')).hexdigest()

def render_path_to_image(d_list, size=128):
    img = np.ones((size, size), dtype=np.uint8) * 255
    pen = RecordingPen()
    for d in d_list:
        parse_path(d, pen)
    bounds_pen = BoundsPen(None)
    pen.replay(bounds_pen)
    bounds = bounds_pen.bounds
    if not bounds:
        return None
    xMin, yMin, xMax, yMax = bounds
    width = xMax - xMin
    height = yMax - yMin
    scale = 0.8 * size / max(width, height)
    tx = -xMin * scale + (size - width * scale) / 2
    ty = -yMin * scale + (size - height * scale) / 2

    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.basePen import decomposeQuadraticSegment
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.boundsPen import ControlBoundsPen

    path = np.zeros((size, size), dtype=np.uint8)
    canvas = np.ones((size, size), dtype=np.uint8) * 255
    for d in d_list:
        pts = cv2.approxPolyDP(np.array(cv2.convexHull(np.array([[float(x), float(y)] for x, y in parse_path(d).toAbsolute().asPoints()])), dtype=np.int32), 3, True)
        if pts.shape[0] >= 3:
            cv2.fillPoly(canvas, [pts], 0)

    return canvas

def compute_hu_moments(d_list):
    img = render_path_to_image(d_list)
    if img is None:
        return None
    moments = cv2.moments(img)
    hu = cv2.HuMoments(moments).flatten()
    return hu

def is_similar_hu(hu1, hu2, threshold=0.005):
    if hu1 is None or hu2 is None:
        return False
    return np.linalg.norm(np.log1p(hu1) - np.log1p(hu2)) < threshold

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
    seen_hashes = set()
    seen_hu = []
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
            d_list = [el.getAttribute('d') for el in paths if el.getAttribute('d').strip()]
            doc.unlink()

            if not d_list:
                print(f"⚠️ אין נתיבים בקובץ: {filename}")
                continue

            d_hash = hash_d_list(d_list)
            if d_hash in seen_hashes:
                print(f"🚫 אות {name} דלגה כי זהה ב־hash לאחרת")
                continue

            hu = compute_hu_moments(d_list)
            if any(is_similar_hu(hu, prev_hu) for prev_hu in seen_hu):
                print(f"🚫 אות {name} דלגה כי דומה חזותית לאחרת")
                continue

            seen_hashes.add(d_hash)
            seen_hu.append(hu)

            glyph = font.newGlyph(name)
            glyph.unicode = unicode_val

            if name == "space":
                glyph.width = 300
                print("␣ רווח הוסף")
                used_letters.add(name)
                count += 1
                continue

            bounds, combined_pen = get_combined_bbox(d_list)
            if not bounds:
                print(f"❌ לא נמצאו גבולות ל-{filename}")
                continue

            xMin, yMin, xMax, yMax = bounds
            width = xMax - xMin
            height = yMax - yMin

            transform = Identity
            max_dim = max(width, height)
            if max_dim > 800:
                scale = 800 / max_dim
                transform = transform.scale(scale)
                print(f"📏 {name} הוקטנה בקנה מידה {round(scale,2)}")

            if name == "yod":
                transform = transform.translate(0, -80)
            elif name == "lamed":
                transform = transform.translate(0, 120)
            elif name == "qof":
                transform = transform.translate(0, -120)
            elif name == "kaf":
                transform = transform.translate(0, 190)

            pen = TransformPen(glyph.getPen(), transform)
            combined_pen.replay(pen)

            glyph.leftMargin = 50
            glyph.rightMargin = 50
            glyph.width = int(width * (scale if max_dim > 800 else 1) + glyph.leftMargin + glyph.rightMargin + 80)

            print(f"✅ {name} נוסף, רוחב כולל: {glyph.width}")
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
