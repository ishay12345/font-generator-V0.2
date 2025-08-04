import os
from PIL import Image
import subprocess
import hashlib

def hash_svg_d(path_d):
    """יוצר hash ייחודי לפי התוכן של ה־d"""
    return hashlib.sha256(path_d.encode('utf-8')).hexdigest()

def convert_to_svg(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    seen_hashes = set()

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".png"):
            continue

        # שם האות לפי שם הקובץ (למשל: "23_final_mem" → "final_mem")
        letter_name = os.path.splitext(fname)[0].split("_", 1)[-1]

        input_path = os.path.join(input_dir, fname)
        bmp_path   = input_path.replace(".png", ".bmp")
        svg_path   = os.path.join(output_dir, fname.replace(".png", ".svg"))

        # המרה ל־BMP
        img = Image.open(input_path).convert("1")
        img.save(bmp_path)

        # המרה ל־SVG עם potrace
        subprocess.run(["potrace", bmp_path, "-s", "-o", svg_path])

        # קריאת תוכן SVG
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        # זיהוי תג path
        path_start = svg_content.find("<path")
        if path_start == -1:
            print(f"⚠️ קובץ {svg_path} לא מכיל path – ייתכן שהאות לא תקינה")
            continue

        # שליפת d
        d_start = svg_content.find('d="', path_start)
        d_end = svg_content.find('"', d_start + 3)
        d_value = svg_content[d_start + 3:d_end]

        # חישוב hash לזיהוי כפילויות
        glyph_hash = hash_svg_d(d_value)
        if glyph_hash in seen_hashes:
            print(f"🚫 אות כפולה (תוכן זהה): {letter_name}, לא נוסף")
            os.remove(svg_path)
            os.remove(bmp_path)
            continue

        seen_hashes.add(glyph_hash)

        # הוספת id אם אין
        if 'id="' not in svg_content:
            svg_content = svg_content.replace("<path", f'<path id="{letter_name}"', 1)

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        os.remove(bmp_path)
        print(f"✅ SVG נוצר: {fname} → {svg_path}")

