import os
import base64
import shutil
from flask import Flask, render_template, request, jsonify, url_for, send_file
from werkzeug.utils import secure_filename
from process_image import convert_to_black_white, normalize_and_center_glyph
from generate_font import generate_ttf  # הפונקציה שלך ליצירת TTF
from svg_converter import convert_png_to_svg  # המרת PNG ל-SVG

# --- נתיבי בסיס ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

FONTS_DIR = os.path.join(STATIC_DIR, 'fonts')
os.makedirs(FONTS_DIR, exist_ok=True)

# תיקיות עבודה
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
PROCESSED_DIR = os.path.join(STATIC_DIR, 'processed')
GLYPHS_DIR = os.path.join(STATIC_DIR, 'glyphs')
BW_DIR = os.path.join(STATIC_DIR, 'bw')
SVG_DIR = os.path.join(STATIC_DIR, 'svg_letters')

for d in (UPLOADS_DIR, PROCESSED_DIR, GLYPHS_DIR, BW_DIR, SVG_DIR):
    os.makedirs(d, exist_ok=True)

EXPORT_FOLDER = os.path.join(BASE_DIR, '..', 'exports')
os.makedirs(EXPORT_FOLDER, exist_ok=True)
FONT_OUTPUT_PATH = os.path.join(EXPORT_FOLDER, 'my_font.ttf')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# סדר האותיות לפי המיקום הרגיל
LETTERS_ORDER = [
    "alef","bet","gimel","dalet","he","vav","zayin","het","tet",
    "yod","kaf","lamed","mem","nun","samekh","ayin","pe","tsadi",
    "qof","resh","shin","tav","finalkaf","finalmem","finalnun",
    "finalpe","finaltsadi"
]

VERTICAL_OFFSETS = {
    "yod": 0, "qof": 0, "finalkaf": 0, "finalnun": 0,
    "finalpe": 0, "finaltsadi": 0
}

@app.route('/')
def index():
    font_ready = os.path.exists(FONT_OUTPUT_PATH)
    return render_template('index.html', font_ready=font_ready)

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return render_template('index.html', error='לא נשלח קובץ')

    f = request.files['image']
    if f.filename == '':
        return render_template('index.html', error='לא נבחר קובץ')

    filename = secure_filename(f.filename)
    input_path = os.path.join(UPLOADS_DIR, filename)
    f.save(input_path)

    # המרה פשוטה לשחור-לבן (ללא התאמות נוספות)
    processed_name = f"proc_{filename}"
    processed_path = os.path.join(PROCESSED_DIR, processed_name)
    convert_to_black_white(input_path, processed_path)

    # העתקה ל-static/uploads להצגה
    shutil.copy(processed_path, os.path.join(STATIC_DIR, 'uploads', processed_name))

    return render_template('crop.html', filename=processed_name, font_ready=os.path.exists(FONT_OUTPUT_PATH))

@app.route('/backend/save_crop', methods=['POST'])
def save_crop():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "no json"}), 400

        index = data.get('index')
        imageData = data.get('data')

        if index is None or imageData is None:
            return jsonify({"error": "missing fields"}), 400

        try:
            index = int(index)
            eng_name = LETTERS_ORDER[index]
        except (ValueError, IndexError):
            return jsonify({"error": "invalid index"}), 400

        # המרה מבסיס64 ל-PNG
        _, b64 = imageData.split(',', 1)
        binary = base64.b64decode(b64)
        tmp_path = os.path.join(PROCESSED_DIR, f"tmp_{eng_name}.png")
        with open(tmp_path, 'wb') as fh:
            fh.write(binary)

        # שמירה ישירה ל-glyphs בלי התאמות חכמות
        out_path = os.path.join(GLYPHS_DIR, f"{eng_name}.png")
        shutil.copy(tmp_path, out_path)

        # שמירה ל-BW
        bw_out = os.path.join(BW_DIR, f"{eng_name}.png")
        shutil.copy(tmp_path, bw_out)

        # המרת SVG
        svg_out = os.path.join(SVG_DIR, f"{eng_name}.svg")
        convert_png_to_svg(bw_out, svg_out)

        # בדיקה: אם זו האות האחרונה, יצירת הפונט
        font_ready = False
        if eng_name == LETTERS_ORDER[-1]:
            success, _ = generate_ttf(svg_folder=SVG_DIR, output_ttf=FONT_OUTPUT_PATH)
            font_ready = success

        return jsonify({"saved": f"{eng_name}.png", "font_ready": font_ready})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_font', methods=['POST'])
def generate_font():
    try:
        success, _ = generate_ttf(svg_folder=SVG_DIR, output_ttf=FONT_OUTPUT_PATH)
        return jsonify({
            "status": "success" if success else "error",
            "download_url": url_for('download_font')
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_font')
def download_font():
    if os.path.exists(FONT_OUTPUT_PATH):
        return send_file(FONT_OUTPUT_PATH, as_attachment=True, download_name="my_font.ttf", mimetype="font/ttf")
    return "הפונט עדיין לא נוצר", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
