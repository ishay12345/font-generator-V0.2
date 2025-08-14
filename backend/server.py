import os
import base64
import shutil
import subprocess
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from process_image import convert_to_black_white, normalize_and_center_glyph
from generate_font import generate_ttf  # ייבוא הפונקציה

# בסיס פרויקט
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# נתיבי תבניות וסטטיים
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
FONTS_DIR = os.path.join(STATIC_DIR, 'fonts')
os.makedirs(FONTS_DIR, exist_ok=True)

# תיקיות עבודה
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
PROCESSED_DIR = os.path.join(STATIC_DIR, 'processed')
GLYPHS_DIR = os.path.join(STATIC_DIR, 'glyphs')
BW_DIR = os.path.join(STATIC_DIR, 'bw')
SVG_DIR = os.path.join(STATIC_DIR, 'svg')

for d in (UPLOADS_DIR, PROCESSED_DIR, GLYPHS_DIR, BW_DIR, SVG_DIR):
    os.makedirs(d, exist_ok=True)

# תיקיית יצוא לפונטים
EXPORT_FOLDER = os.path.join(BASE_DIR, '..', 'exports')
os.makedirs(EXPORT_FOLDER, exist_ok=True)
FONT_OUTPUT_PATH = os.path.join(EXPORT_FOLDER, 'my_font.ttf')

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

    # המרה לשחור-לבן
    processed_name = f"proc_{filename}"
    processed_path = os.path.join(PROCESSED_DIR, processed_name)
    convert_to_black_white(input_path, processed_path)

    # העתקה ל-static/uploads להצגה
    static_uploads = os.path.join(BASE_DIR, 'static', 'uploads')
    os.makedirs(static_uploads, exist_ok=True)
    shutil.copy(processed_path, os.path.join(static_uploads, processed_name))

    return render_template('crop.html', filename=processed_name, font_ready=os.path.exists(FONT_OUTPUT_PATH))

@app.route('/crop')
def crop():
    filename = request.args.get('filename')
    if not filename:
        return redirect(url_for('index'))

    image_url = url_for('static', filename=f'processed/{filename}')
    font_ready = os.path.exists(FONT_OUTPUT_PATH)
    return render_template('crop.html', image_url=image_url, letters=LETTERS_ORDER, font_ready=font_ready)

@app.route('/backend/save_crop', methods=['POST'])
def save_crop():
    logs = []
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

        try:
            _, b64 = imageData.split(',', 1)
            binary = base64.b64decode(b64)
        except Exception:
            return jsonify({"error": "invalid base64"}), 400

        tmp_path = os.path.join(PROCESSED_DIR, f"tmp_{eng_name}.png")
        with open(tmp_path, 'wb') as fh:
            fh.write(binary)

        vertical = VERTICAL_OFFSETS.get(eng_name, 0)
        out_path = os.path.join(GLYPHS_DIR, f"{eng_name}.png")
        try:
            normalize_and_center_glyph(tmp_path, out_path, target_size=600, margin=50, vertical_offset=vertical)
            logs.append(f"✅ האות '{eng_name}' נוספה לפונט בהצלחה")
        except Exception as e:
            shutil.copy(tmp_path, out_path)
            logs.append(f"❌ בעיה בעיבוד האות '{eng_name}', נשמרה כ-PNG בלבד: {str(e)}")

        print(logs[-1])

        # המרת BW
        bw_out = os.path.join(BW_DIR, f"{eng_name}.png")
        bw_status = os.system(f"python {os.path.join(BASE_DIR, 'bw_converter.py')} {out_path} {bw_out}")
        if bw_status == 0:
            logs.append(f"✅ המרת BW הצליחה עבור {eng_name}")
        else:
            logs.append(f"❌ שגיאה בהמרת BW עבור {eng_name}")
        print(logs[-1])

        # המרת SVG
        svg_out = os.path.join(SVG_DIR, f"{eng_name}.svg")
        svg_status = os.system(f"python {os.path.join(BASE_DIR, 'svg_converter.py')} {bw_out} {svg_out}")
        if svg_status == 0:
            logs.append(f"✅ המרת SVG הצליחה עבור {eng_name}")
        else:
            logs.append(f"❌ שגיאה בהמרת SVG עבור {eng_name}")
        print(logs[-1])

        # אם זו האות האחרונה, יצירת הפונט
        if eng_name == "final_tsadi":
            logs.append("🎉 כל האותיות הושלמו! מתחילים יצירת הפונט...")
            try:
                font_created = generate_ttf(svg_folder=SVG_DIR, output_ttf=FONT_OUTPUT_PATH)
                if font_created:
                    logs.append(f"🎉 הפונט נוצר בהצלחה: {FONT_OUTPUT_PATH}")
                else:
                    logs.append("❌ הפונט לא נוצר - בעיה בתהליך generate_ttf")
            except Exception as e:
                logs.append(f"❌ שגיאה בהרצת generate_ttf: {str(e)}")
            print(logs[-1])
            return jsonify({"font_ready": os.path.exists(FONT_OUTPUT_PATH), "logs": logs})

        return jsonify({"saved": f"{eng_name}.png", "logs": logs})

    except Exception as e:
        logs.append(f"❌ שגיאה כללית: {str(e)}")
        print(logs[-1])
        return jsonify({"error": str(e), "logs": logs}), 500

# API סטטוס לפונט
@app.route('/api/font_status')
def font_status():
    return jsonify({"font_ready": os.path.exists(FONT_OUTPUT_PATH)})

# יצירת הפונט לפי דרישה מה-Frontend
@app.route('/generate_font', methods=['POST'])
def generate_font():
    try:
        # הפעלת סקריפט יצירת הפונט
        subprocess.run(
            ['python', os.path.join(BASE_DIR, 'generate_font.py')],
            check=True
        )

        # החזרת הנתיב להורדה
        font_path = '/download_font'  # נשתמש בנתיב להורדה דרך ה-Route
        return jsonify({"status": "success", "download_url": font_path})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# הורדת הפונט
@app.route('/download_font')
def download_font():
    if os.path.exists(FONT_OUTPUT_PATH):
        print("Font found at:", FONT_OUTPUT_PATH)
        return send_file(
            FONT_OUTPUT_PATH,
            as_attachment=True,
            download_name="my_font.ttf",
            mimetype="font/ttf"
        )
    print("Font not found!")
    return "הפונט עדיין לא נוצר", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
