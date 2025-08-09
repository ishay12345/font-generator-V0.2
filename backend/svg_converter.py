import os
from PIL import Image
import subprocess

def convert_to_svg(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".png"):
            continue

        letter_name = os.path.splitext(fname)[0].split("_", 1)[-1]

        input_path = os.path.join(input_dir, fname)
        bmp_path = input_path.replace(".png", ".bmp")
        svg_path = os.path.join(output_dir, fname.replace(".png", ".svg"))

        # המרה ל-BMP
        img = Image.open(input_path).convert("1")
        img.save(bmp_path)

        # המרה ל-SVG עם potrace
        subprocess.run(["potrace", bmp_path, "-s", "-o", svg_path])

        # הוספת id אם אין ב-SVG
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        if 'id="' not in svg_content:
            svg_content = svg_content.replace("<path", f'<path id="{letter_name}"', 1)

            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

        os.remove(bmp_path)
        print(f"✅ SVG נוצר: {fname} → {svg_path}")
