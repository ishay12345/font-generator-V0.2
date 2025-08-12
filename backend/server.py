import os
import base64
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from process_image import convert_to_black_white, normalize_and_center_glyph

# בסיס פרויקט
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# נתיבי תבניות וסטטיים
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# תיקיות עבודה
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
PROCESSED_DIR = os.path.join(STATIC_DIR, 'processed')
GLYPHS_DIR = os.path.join(STATIC_DIR, 'glyphs')

for d in (UPLOADS_DIR, PROCESSED_DIR, GLYPHS_DIR):
    os.makedirs(d, exist_ok=True)

# Flask
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# סדר האותיות
LETTERS_ORDER = [
    "alef","bet","gimel","dalet","he","vav","zayin","het","tet",
    "yod","kaf","lamed","mem","nun","samekh","ayin","pe","tsadi",
    "qof","resh","shin","tav","final_kaf","final_mem","final_nun",
    "final_pe","final_tsadi"
]

# תזוזות אנכיות
VERTICAL_OFFSETS = {
    "yod": -60,
    "qof": 50,
    "final_kaf": 50,
    "final_nun": 50,
    "final_pe": 50,
    "final_tsadi": 50
}

@app.route('/')
def index():
    return render_template('index.html')

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

    # המרה לשחור-לבן
    processed_name = f"proc_{filename}"
    processed_path = os.path.join(PROCESSED_DIR, processed_name)
    convert_to_black_white(input_path, processed_path)

    return redirect(url_for('crop', filename=processed_name))

@app.route('/crop')
def crop():
    filename = request.args.get('filename')
    if not filename:
        return redirect(url_for('index'))

    image_url = url_for('static', filename=f'processed/{filename}')
    return render_template('crop.html', image_url=image_url, letters=LETTERS_ORDER)

@app.route('/backend/save_crop', methods=['POST'])
def save_crop():
    data = request.get_json()
    if not data:
        return jsonify({"error": "no json"}), 400

    name = data.get('name')
    index = data.get('index')
    imageData = data.get('data')

    if not name or imageData is None:
        return jsonify({"error": "missing fields"}), 400

    try:
        _, b64 = imageData.split(',', 1)
        binary = base64.b64decode(b64)
    except Exception:
        return jsonify({"error": "invalid base64"}), 400

    tmp_name = f"tmp_{index}_{name}.png"
    tmp_path = os.path.join(PROCESSED_DIR, tmp_name)
    with open(tmp_path, 'wb') as fh:
        fh.write(binary)

    vertical = VERTICAL_OFFSETS.get(name, 0)
    out_name = f"{index:02d}_{name}.png"
    out_path = os.path.join(GLYPHS_DIR, out_name)
    try:
        normalize_and_center_glyph(tmp_path, out_path, target_size=600, margin=50, vertical_offset=vertical)
    except Exception:
        with open(out_path, 'wb') as fh:
            fh.write(binary)

    files = sorted([f for f in os.listdir(GLYPHS_DIR) if f.lower().endswith('.png')])
    return jsonify({"saved": out_name, "files": files})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
