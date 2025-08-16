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
    "finalkaf": 0x05DA,   # ך
    "finalmem": 0x05DD,   # ם
    "finalnun": 0x05DF,   # ן
    "finalpe": 0x05E3,    # ף
    "finaltsadi": 0x05E5  # ץ
}

# ===== הזזות אנכיות מותאמות =====
vertical_offsets = {
    "yod": 500,
    "qof": -250,
}

# ===== הזזה גלובלית ל־Y =====
GLOBAL_Y_SHIFT = -400  # ניתן לשנות
PADDING_GENERAL = 35    # פדינג כללי
PADDING_LARGE = 150    # פדינג לאותיות סופיות

# ===== מיפוי רווח אופקי מותאם עבור אותיות צמודות =====
HORIZONTAL_ADJUST = {
    ("yod", "kaf"): 80,
    ("shin", "tav"): 60,
    ("kaf", "lamed"): 30
}

# ===== טרנספורמציות מיוחדות לאותיות =====
special_transforms = {
    "finalpe": Identity.scale(0.70, 0.70).translate(50, 250),     # ף מוקטן + מורם
    "finaltsadi": Identity.scale(0.68, 0.70).translate(50, 250),  # ץ מוקטן + מורם
}

# ===== סקייל כללי לכל האותיות =====
GLOBAL_SCALE = 0.7


def generate_ttf(svg_folder, output_ttf):
    print("🚀 התחלת יצירת פונט...")
    font = Font()
    font.info.familyName = "uiHebrew Handwriting"
    font.info.styleName = "Regular"
    font.info.fullName = "uiHebrew Handwriting"
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
