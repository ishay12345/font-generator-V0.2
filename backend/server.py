import os
import base64
import shutil
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from process_image import convert_to_black_white, normalize_and_center_glyph
from generate_font import generate_ttf  # הפונקציה המעודכנת שלך

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
SVG_DIR = os.path.join(STATIC_DIR, 'svg_letters')  # תיקייה אחידה ל-SVG

for d in (UPLOADS_DIR, PROCESSED_DIR, GLYPHS_DIR, BW_DIR, SVG_DIR):
    os.makedirs(d, exist_ok=True)

EXPORT_FOLDER = os.path.join(BASE_DIR, '..', 'exports')
os.makedirs(EXPORT_FOLDER, exist_ok=True)
FONT_OUTPUT_PATH = os.path.join(EXPORT_FOLDER, 'my_font.ttf')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# סדר האותיות
LETTERS_ORDER = [
    "alef","bet","gimel","dalet","he","vav","zayin","het","tet",
    "yod","kaf","lamed","mem","nun","samekh","ayin","pe","tsadi",
    "qof","resh","shin","tav","final_kaf","final_mem","final_nun",
    "final_pe","final_tsadi"
]

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
    shutil.copy(processed_path, os.path.join(STATIC_DIR, 'uploads', processed_name))

    return render_template('crop.html', filename=processed_name, font_ready=os.path.exists(FONT_OUTPUT_PATH))

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

        # המרה מבסיס64
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

        # המרת BW ל-SVG בתיקייה אחידה
        bw_out = os.path.join(BW_DIR, f"{eng_name}.png")
        shutil.copy(out_path, bw_out)
        logs.append(f"✅ שמירה/המרת BW הצליחה עבור {eng_name}")
         print(logs[-1])

        svg_out = os.path.join(SVG_DIR, f"{eng_name}.svg")
        try:
            from svg_converter import convert_png_to_svg  # פונקציה מתוך svg_converter.py
            convert_png_to_svg(bw_out, svg_out)
            logs.append(f"✅ המרת SVG הצליחה עבור {eng_name}")
        except Exception as e:
            logs.append(f"❌ המרת SVG נכשלה עבור {eng_name}: {str(e)}")

        print(logs[-1])

        # אם זו האות האחרונה, יצירת הפונט
        if eng_name == LETTERS_ORDER[-1]:
            logs.append("🎉 כל האותיות הושלמו! מתחילים יצירת הפונט...")
            success, font_logs = generate_ttf(svg_folder=SVG_DIR, output_ttf=FONT_OUTPUT_PATH)
            logs.extend(font_logs)
            print(logs[-1])
            return jsonify({"font_ready": os.path.exists(FONT_OUTPUT_PATH), "logs": logs})

        return jsonify({"saved": f"{eng_name}.png", "logs": logs})

    except Exception as e:
        logs.append(f"❌ שגיאה כללית: {str(e)}")
        print(logs[-1])
        return jsonify({"error": str(e), "logs": logs}), 500

@app.route('/generate_font', methods=['POST'])
def generate_font():
    try:
        # יצירת הפונט מתוך כל קבצי ה-SVG בתיקייה
        success, logs = generate_ttf(svg_folder=SVG_DIR, output_ttf=FONT_OUTPUT_PATH)
        return jsonify({
            "status": "success" if success else "error",
            "download_url": url_for('download_font'),
            "logs": logs
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_font')
def download_font():
    if os.path.exists(FONT_OUTPUT_PATH):
        return send_file(
            FONT_OUTPUT_PATH,
            as_attachment=True,
            download_name="my_font.ttf",
            mimetype="font/ttf"
        )
    return "הפונט עדיין לא נוצר", 404

@app.route('/api/font_status')
def font_status():
    return jsonify({"font_ready": os.path.exists(FONT_OUTPUT_PATH)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
