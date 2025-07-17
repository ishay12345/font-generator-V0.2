# backend/server.py
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

# ייבוא הפונקציה ישירות
from generate_font import generate_ttf

# בסיס ותיקיות
BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD = os.path.join(BASE, 'uploads')
SPLIT = os.path.join(BASE, 'split_letters_output')
BW    = os.path.join(BASE, 'bw_letters')
SVG   = os.path.join(BASE, 'svg_letters')
EXPORT= os.path.join(BASE, '..', 'exports')

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
    if 'file' not in request.files:
        return jsonify({'error': 'אין קובץ בבקשה'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'לא נבחר קובץ'}), 400

    # שמירת התמונה
    filename = secure_filename('all_letters.jpg')
    img_path = os.path.join(UPLOAD, filename)
    file.save(img_path)

    # הפעלת השלבים בסקריפטים של הפייתון
    try:
        import split_letters
        split_letters.split_letters(img_path, SPLIT)

        import bw_converter
        bw_converter.convert_to_bw(SPLIT, BW)

        import svg_converter
        svg_converter.convert_to_svg(BW, SVG)

        # כאן במקום subprocess – קריאה ישירה
        font_file = os.path.join(EXPORT, 'hebrew_font.ttf')
        ok = generate_ttf(SVG, font_file)
        if not ok:
            return jsonify({'error': 'כשל ביצירת הפונט'}), 500

    except Exception as e:
        print("Error pipeline:", e)
        return jsonify({'error': f'⚠ שגיאה: {e}'}), 500

    return jsonify({'message': 'הפונט נוצר בהצלחה!'}), 200

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

