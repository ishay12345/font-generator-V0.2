# backend/generate_font.py
import os
from defcon import Font
from ufo2ft import compileTTF
from fontTools.svgLib.path import parse_path
from fontTools.pens.ttGlyphPen import TTGlyphPen
from xml.dom import minidom

# מיפוי שמות האותיות לעברית
letter_map = {
    # ... כפי שהיה ...
}

def generate_ttf(svg_folder, output_path):
    print("🚀 Generating font with defcon + ufo2ft")
    print("📁 SVG folder:", svg_folder)
    print("📄 Output path:", output_path)

    font = Font()
    font.info.familyName = "HebrewFont"
    font.info.styleName = "Regular"
    font.info.unitsPerEm = 1000
    font.info.ascender = 800
    font.info.descender = -200

    found_glyphs = 0

    for filename in os.listdir(svg_folder):
        if not filename.endswith(".svg"):
            continue
        parts = filename.split("_")
        if len(parts) != 2:
            continue
        name = parts[1].replace(".svg", "")
        if name not in letter_map:
            continue

        unicode_val = letter_map[name]
        glyph = font.newGlyph(name)
        glyph.unicode = unicode_val
        glyph.width = 600

        svg_path = os.path.join(svg_folder, filename)
        try:
            doc = minidom.parse(svg_path)
            paths = doc.getElementsByTagName('path')
            if not paths:
                continue
            d = paths[0].getAttribute('d')
            doc.unlink()
            pen = TTGlyphPen(None)
            parse_path(d, pen)
            glyph._glyph = pen.glyph()
            found_glyphs += 1
        except Exception as e:
            print(f"❌ שגיאה ב־{filename}: {e}")

    if found_glyphs == 0:
        print("❌ No glyphs found, aborting font generation.")
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        ttf = compileTTF(font)
        ttf.save(output_path)
        print(f"✅ Font saved at: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving font: {e}")
        return False

