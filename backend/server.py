from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import subprocess

# בסיס – תיקיית הקובץ הנוכחי (backend/)
BASE = os.path.dirname(os.path.abspath(__file__))

# תיקיות עבודה
UPLOAD_FOLDER       = os.path.join(BASE, 'uploads')
SPLIT_OUTPUT_FOLDER = os.path.join(BASE, 'split_letters_output')
BW_FOLDER           = os.path.join(BASE, 'bw_letters')
SVG_FOLDER          = os.path.join(BASE, 'svg_letters')
EXPORT_FONT_FOLDER  = os.path.join(BASE, '..', 'exports')

# ודא שכל התיקיות קיימות
for folder in [UPLOAD_FOLDER, SPLIT_OUTPUT_FOLDER, BW_FOLDER, SVG_FOLDER, EXPORT_FONT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# אתחול Flask עם תבניות וסטטיים מה-frontend
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

    filename = secure_filename('all_letters.jpg')
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # ודא שהתיקייה קיימת לפני שמירה (למקרה ונדפקה)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': f'שגיאה בשמירת קובץ: {str(e)}'}), 500

    # הרץ סקריפטים בשלבים
    try:
        subprocess.run(['python3', 'split_letters.py'], check=True, cwd=BASE)
        subprocess.run(['python3', 'bw_converter.py'], check=True, cwd=BASE)
        subprocess.run(['python3', 'svg_converter.py'], check=True, cwd=BASE)
        subprocess.run(['python3', 'generate_font.py'], check=True, cwd=BASE)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'שגיאה בהרצת שלב: {e.cmd}'}), 500

    return jsonify({'message': 'הפונט נוצר בהצלחה!'})

@app.route('/download_font')
def download_font():
    font_path = os.path.join('exports', 'hebrew_font.ttf')
    if os.path.exists(font_path):
        return send_file(font_path, as_attachment=True)
    else:
        return jsonify({"error": "קובץ הפונט לא נמצא"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
