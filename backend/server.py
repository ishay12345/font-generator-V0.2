# server.py
import os
import base64
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from process_image import convert_to_black_white, normalize_and_center_glyph

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
PROCESSED_DIR = os.path.join(STATIC_DIR, 'processed')
GLYPHS_DIR = os.path.join(STATIC_DIR, 'glyphs')

for d in (UPLOADS_DIR, PROCESSED_DIR, GLYPHS_DIR):
    os.makedirs(d, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# (אפשר להתאים רשימת אותיות כאן לפי הסדר שלך)
LETTERS_ORDER = [
    "alef","bet","gimel","dalet","he","vav","zayin","het","tet",
    "yod","kaf","lamed","mem","nun","samekh","ayin","pe","tsadi",
    "qof","resh","shin","tav","final_kaf","final_mem","final_nun",
    "final_pe","final_tsadi"
]

# ברירות מחדל להזזות אנכיות (פיקסלים) לאותיות מסוימות
VERTICAL_OFFSETS = {
    "yod": -60,           # תזוזה למעלה
    "qof": 50,            # תזוזה למטה
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
    # מקבל קובץ אחד בשם 'image'
    if 'image' not in request.files:
        return "no file", 400
    f = request.files['image']
    if f.filename == '':
        return "empty filename", 400

    filename = secure_filename(f.filename)
    input_path = os.path.join(UPLOADS_DIR, filename)
    f.save(input_path)

    # עיבוד לשחור-לבן
    processed_name = f"proc_{filename}"
    processed_path = os.path.join(PROCESSED_DIR, processed_name)
    convert_to_black_white(input_path, processed_path)

    # Redirect לדף החיתוך עם שם הקובץ המעובד
    return redirect(url_for('crop', filename=processed_name))

@app.route('/crop')
def crop():
    # מצפה ל־?filename=proc_xxx.png
    filename = request.args.get('filename')
    if not filename:
        return "missing filename", 400
    image_url = url_for('static', filename=f'processed/{filename}')
    # העבר את רשימת האותיות (ניתן לשנות בסקריפט JS גם)
    return render_template('crop.html', image_url=image_url, letters=LETTERS_ORDER)

@app.route('/backend/save_crop', methods=['POST'])
def save_crop():
    """
    מקבל JSON:
    { name: "alef", index: 0, data: "data:image/png;base64,..." }
    שומר normalized glyph ל־static/glyphs/
    """
    data = request.get_json()
    if not data:
        return jsonify({"error":"no json"}), 400

    name = data.get('name')
    index = data.get('index')
    imageData = data.get('data')
    if not name or imageData is None:
        return jsonify({"error":"missing fields"}), 400

    try:
        header, b64 = imageData.split(',',1) if ',' in imageData else (None, imageData)
        binary = base64.b64decode(b64)
    except Exception as e:
        return jsonify({"error":"invalid base64"}), 400

    # שמור טמפ ראשון
    tmp_name = f"tmp_{index}_{name}.png"
    tmp_path = os.path.join(PROCESSED_DIR, tmp_name)
    with open(tmp_path, 'wb') as fh:
        fh.write(binary)

    # נרמול וגודל אחיד (center + offset לפי מפת האותיות)
    vertical = VERTICAL_OFFSETS.get(name, 0)
    out_name = f"{index:02d}_{name}.png"
    out_path = os.path.join(GLYPHS_DIR, out_name)
    try:
        normalize_and_center_glyph(tmp_path, out_path, target_size=600, margin=50, vertical_offset=vertical)
    except Exception as e:
        # אם משהו נכשל בנרמול - נשמור את הגרסה המקורית
        with open(out_path, 'wb') as fh:
            fh.write(binary)

    # מחזירים רשימת קבצים עדכנית
    files = sorted([f for f in os.listdir(GLYPHS_DIR) if f.lower().endswith('.png')])
    return jsonify({"saved": out_name, "files": files})

@app.route('/api/list_glyphs')
def list_glyphs():
    files = sorted([f for f in os.listdir(GLYPHS_DIR) if f.lower().endswith('.png')])
    return jsonify({"files": files})

@app.route('/api/finalize', methods=['POST'])
def finalize():
    """
    כאן ניתן לקרוא ל־generate_ttf (אם קיים). כרגע מחזירים הצלחה מדומה.
    """
    # אם יש לך generate_font.py שכולל generate_ttf(svg_folder, output_ttf),
    # ניתן לקרוא לזה כאן לאחר שהומרו PNG->SVG (או אם generate_ttf יודע לטפל ב-PNG).
    # לדוגמה:
    # try:
    #     from generate_font import generate_ttf
    #     ok = generate_ttf(str(GLYPHS_DIR), output_ttf_path)
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500

    return jsonify({"ttf":"my_handwriting.ttf"})

# Serve static files (Flask כבר עושה את זה דרך static_folder)
# הורדה של הפונט / קבצים תעשה דרך /download/<filename> אם תרצה.

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
