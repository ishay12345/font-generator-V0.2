from flask import Flask, request, render_template, send_file, url_for
import os
from split_letters import split_letters_from_image
from bw_converter import convert_to_bw
from svg_converter import convert_to_svg
from generate_font import generate_ttf

UPLOAD_FOLDER = 'backend/uploads'
SPLIT_FOLDER = 'backend/split_letters_output'
BW_FOLDER = 'backend/bw_letters'
SVG_FOLDER = 'backend/svg_letters'
FONT_OUTPUT_PATH = 'exports/my_font.ttf'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SPLIT_FOLDER'] = SPLIT_FOLDER
app.config['BW_FOLDER'] = BW_FOLDER
app.config['SVG_FOLDER'] = SVG_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error='לא נשלח קובץ')

    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error='לא נבחר קובץ')

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        # שלב 1 – חיתוך
        split_letters_from_image(filepath, output_dir=SPLIT_FOLDER)

        # שלב 2 – המרה לשחור־לבן
        convert_to_bw(input_dir=SPLIT_FOLDER, output_dir=BW_FOLDER)

        # שלב 3 – המרה ל־SVG
        convert_to_svg(input_dir=BW_FOLDER, output_dir=SVG_FOLDER)

        # שלב 4 – יצירת פונט TTF
        font_created = generate_ttf(svg_folder=SVG_FOLDER, output_ttf=FONT_OUTPUT_PATH)

        # בדיקה אם נוצרו קבצים בתיקיות
        cutting_done = len(os.listdir(SPLIT_FOLDER)) > 0
        bw_done = len(os.listdir(BW_FOLDER)) > 0
        svg_done = len(os.listdir(SVG_FOLDER)) > 0

        print(f"✂️ חיתוך אותיות: {'הושלם' if cutting_done else 'נכשל'}")
        print(f"🖤 המרה לשחור-לבן: {'הושלם' if bw_done else 'נכשל'}")
        print(f"🟢 המרה ל-SVG: {'הושלם' if svg_done else 'נכשל'}")
        print(f"🔠 יצירת פונט: {'הושלם' if font_created else 'נכשל'}")

        return render_template(
            'index.html',
            cutting_done=cutting_done,
            bw_done=bw_done,
            svg_done=svg_done,
            font_created=font_created
        )

    except Exception as e:
        print("❌ שגיאה בתהליך:", str(e))
        return render_template('index.html', error=f"שגיאה: {str(e)}")

@app.route('/download')
def download_font():
    if os.path.exists(FONT_OUTPUT_PATH):
        return send_file(FONT_OUTPUT_PATH, as_attachment=True)
    return "הפונט לא קיים להורדה", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))




