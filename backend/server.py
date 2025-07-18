# backend/server.py
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import traceback  # ✅ להדפסת שגיאות מלאות
from werkzeug.utils import secure_filename

from generate_font import generate_ttf

# תיקיות בסיס
BASE   = os.path.dirname(os.path.abspath(__file__))
UPLOAD = os.path.join(BASE, 'uploads')
SPLIT  = os.path.join(BASE, 'split_letters_output')
BW     = os.path.join(BASE, 'bw_letters')
SVG    = os.path.join(BASE, 'svg_letters')
EXPORT = os.path.join(BASE, '..', 'exports')

# יצירת תיקיות
for d in [UPLOAD, SPLIT, BW, SVG, EXPORT]:
    os.makedirs(d, exist_ok=True)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE, '..', 'frontend', 'templates'),
    static_folder=os.path.join(BASE, '..', 'frontend', 'static'),
)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'אין קובץ בבקשה'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'לא נבחר קובץ'}), 400

        # שמירת הקובץ
        filename = secure_filename('all_letters.jpg')
        img_path = os.path.join(UPLOAD, filename)
        file.save(img_path)
        print(f"📥 קובץ נשמר: {img_path}")

        # שלב 1: חיתוך אותיות
        import split_letters
        print(f"✂ חיתוך לתיקייה: {SPLIT}")
        split_letters.split_letters(img_path, SPLIT)
        print("📂 קבצים לאחר חיתוך:", os.listdir(SPLIT))

        # שלב 2: המרה לשחור־לבן
        import bw_converter
        print(f"🌓 המרה ל־BW לתיקייה: {BW}")
        bw_converter.convert_to_bw(SPLIT, BW)
        print("📂 קבצים לאחר BW:", os.listdir(BW))

        # שלב 3: המרה ל־SVG
        import svg_converter
        print(f"🧬 המרה ל־SVG לתיקייה: {SVG}")
        svg_converter.convert_to_svg(BW, SVG)
        print("📂 קבצים לאחר SVG:", os.listdir(SVG))

        # שלב 4: יצירת הפונט
        font_file = os.path.join(EXPORT, 'hebrew_font.ttf')
        print(f"🔤 יצירת פונט אל: {font_file}")
        ok = generate_ttf(SVG, font_file)

        if not ok:
            print("❌ כשל ביצירת הפונט")
            return jsonify({'error': 'כשל ביצירת הפונט'}), 500

        print(f"✅ הפונט נוצר בהצלחה: {font_file}")
        return jsonify({'message': 'הפונט נוצר בהצלחה!'}), 200

    except Exception as e:
        print("❌ שגיאה בצינור העיבוד:")
        traceback.print_exc()
        return jsonify({'error': f'⚠ שגיאה פנימית: {str(e)}'}), 500

@app.route('/download-font', methods=['GET'])
def download_font():
    font_path = os.path.join(EXPORT, 'hebrew_font.ttf')
    if os.path.exists(font_path):
        return send_file(
            font_path,
            as_attachment=True,
            download_name='hebrew_font.ttf',
            mimetype='font/ttf'
        )
    else:
        return jsonify({'error': 'קובץ הפונט לא נמצא'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

