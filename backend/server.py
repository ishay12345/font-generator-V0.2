import os
import base64
import shutil
import subprocess
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from process_image import convert_to_black_white, normalize_and_center_glyph

# בסיס פרויקט (דינמי)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# נתיבי תבניות וסטטיים
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# תיקיות עבודה
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
PROCESSED_DIR = os.path.join(STATIC_DIR, 'processed')
GLYPHS_DIR = os.path.join(STATIC_DIR, 'glyphs')
BW_DIR = os.path.join(STATIC_DIR, 'bw')
SVG_DIR = os.path.join(STATIC_DIR, 'svg')
FONT_OUTPUT = os.path.join(STATIC_DIR, 'fonts', 'generated_font.ttf')

# יצירת כל התיקיות
for d in (UPLOADS_DIR, PROCESSED_DIR, GLYPHS_DIR, BW_DIR, SVG_DIR, os.path.dirname(FONT_OUTPUT)):
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

# ------------------------
# טיפול כללי בשגיאות כדי למנוע HTML לא צפוי
# ------------------------
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "error": str(e),
        "logs": [f"❌ שגיאה כללית: {str(e)}"]
    }), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    logs = []
    try:
        if 'image' not in request.files:
            return jsonify({"error": "לא נשלח קובץ", "logs": logs}), 400

        f = request.files['image']
        if f.filename == '':
            return jsonify({"error": "לא נבחר קובץ", "logs": logs}), 400

        filename = secure_filename(f.filename)
        input_path = os.path.join(UPLOADS_DIR, filename)
        f.save(input_path)
        logs.append(f"📥 הקובץ {filename} נשמר בהצלחה")

        # המרה לשחור-לבן
        processed_name = f"proc_{filename}"
        processed_path = os.path.join(PROCESSED_DIR, processed_name)
        convert_to_black_white(input_path, processed_path)
        logs.append(f"🎨 התמונה הומרה לשחור-לבן: {processed_name}")

        # העתקה להצגה
        shutil.copy(processed_path, os.path.join(UPLOADS_DIR, processed_name))

        return jsonify({
            "processed_file": processed_name,
            "logs": logs
        })
    except Exception as e:
        logs.append(f"❌ שגיאה בהעלאת קובץ: {str(e)}")
        return jsonify({"error": str(e), "logs": logs}), 500

@app.route('/crop')
def crop():
    filename = request.args.get('filename')
    if not filename:
        return redirect(url_for('index'))

    image_url = url_for('static', filename=f'processed/{filename}')
    return render_template('crop.html', image_url=image_url, letters=LETTERS_ORDER)

@app.route('/backend/save_crop', methods=['POST'])
def save_crop():
    logs = []
    try:
        # silent=True מונע קריסה אם מגיע JSON פגום
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "לא התקבל JSON תקין", "logs": logs}), 400

        name = data.get('name')
        index = data.get('index')
        imageData = data.get('data')

        if not name or imageData is None:
            return jsonify({"error": "חסרים שדות בנתונים", "logs": logs}), 400

        try:
            _, b64 = imageData.split(',', 1)
            binary = base64.b64decode(b64)
        except Exception:
            return jsonify({"error": "Base64 לא תקין", "logs": logs}), 400

        tmp_path = os.path.join(PROCESSED_DIR, f"tmp_{index}_{name}.png")
        with open(tmp_path, 'wb') as fh:
            fh.write(binary)

        out_path = os.path.join(GLYPHS_DIR, f"{index:02d}_{name}.png")
        vertical = VERTICAL_OFFSETS.get(name, 0)

        try:
            normalize_and_center_glyph(tmp_path, out_path, target_size=600, margin=50, vertical_offset=vertical)
        except Exception:
            shutil.copy(tmp_path, out_path)

        logs.append(f"✅ האות '{name}' נשמרה בשם {os.path.basename(out_path)}")

        files = sorted([f for f in os.listdir(GLYPHS_DIR) if f.lower().endswith('.png')])

        # בדיקה אם יש את כל האותיות
        if len(files) >= len(LETTERS_ORDER):
            logs.append("📢 כל האותיות קיימות — מתחיל המרה...")

            # המרה BW
            result_bw = subprocess.run(["python", "bw_converter.py", GLYPHS_DIR, BW_DIR], capture_output=True, text=True)
            logs.append(result_bw.stdout)
            if result_bw.stderr.strip():
                logs.append(f"⚠️ שגיאת BW: {result_bw.stderr}")

            # המרה SVG
            result_svg = subprocess.run(["python", "svg_converter.py", BW_DIR, SVG_DIR], capture_output=True, text=True)
            logs.append(result_svg.stdout)
            if result_svg.stderr.strip():
                logs.append(f"⚠️ שגיאת SVG: {result_svg.stderr}")

            # יצירת פונט
            logs.append("📢 מתחיל יצירת פונט...")
            result_font = subprocess.run(["python", "generate_font.py", SVG_DIR, FONT_OUTPUT], capture_output=True, text=True)
            logs.append(result_font.stdout)
            if result_font.stderr.strip():
                logs.append(f"⚠️ שגיאת פונט: {result_font.stderr}")

            logs.append("✅ הפונט נוצר בהצלחה!")

        return jsonify({"saved": os.path.basename(out_path), "files": files, "logs": logs})

    except Exception as e:
        logs.append(f"❌ שגיאה כללית: {e}")
        return jsonify({"error": str(e), "logs": logs}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
