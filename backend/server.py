from flask import Flask, request, render_template, send_file, url_for, redirect
import os
from bw_converter import convert_to_bw
from svg_converter import convert_to_svg
from generate_font import generate_ttf

# ---- תיקיות עבודה ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CUT_FOLDER    = os.path.join(BASE_DIR, 'cut_letters')   # פה נשמור את החיתוכים הידניים
BW_FOLDER     = os.path.join(BASE_DIR, 'bw_letters')
SVG_FOLDER    = os.path.join(BASE_DIR, 'svg_letters')
EXPORT_FOLDER = os.path.join(BASE_DIR, '..', 'exports')
FONT_OUTPUT_PATH = os.path.join(EXPORT_FOLDER, 'my_font.ttf')

# ודא שהתיקיות קיימות
for d in (UPLOAD_FOLDER, CUT_FOLDER, BW_FOLDER, SVG_FOLDER, EXPORT_FOLDER):
    os.makedirs(d, exist_ok=True)

# אתחול Flask עם ה־templates
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, '..', 'frontend', 'static')
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CUT_FOLDER']    = CUT_FOLDER
app.config['BW_FOLDER']     = BW_FOLDER
app.config['SVG_FOLDER']    = SVG_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

# --- שלב 1: העלאת התמונה והצגת ממשק חיתוך ---
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error='לא נשלח קובץ')

    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error='לא נבחר קובץ')

    # שמירת התמונה
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # המרה לשחור־לבן (כדי שיהיה נוח לחתוך)
    bw_path = os.path.join(UPLOAD_FOLDER, 'bw_' + file.filename)
    convert_to_bw(input_dir=UPLOAD_FOLDER, output_dir=UPLOAD_FOLDER)

    # הצגת דף החיתוך האינטראקטיבי עם התמונה בשחור־לבן
    return render_template('cutting.html', image_url=url_for('static', filename='uploads/' + 'bw_' + file.filename))

# --- שלב 2: קבלת החיתוכים שנשמרים בצד לקוח ---
@app.route('/save_cut', methods=['POST'])
def save_cut():
    # כאן תקבל מה-JS את קובץ האות החתוכה ותשמור אותו בתיקייה CUT_FOLDER
    letter_name = request.form.get('letter_name')
    file = request.files['file']
    save_path = os.path.join(CUT_FOLDER, f"{letter_name}.png")
    file.save(save_path)
    return "OK"

# --- שלב 3: יצירת הפונט מהחיתוכים ---
@app.route('/generate_font', methods=['POST'])
def generate_font_route():
    try:
        # המרה לשחור־לבן (ליתר ביטחון)
        convert_to_bw(input_dir=CUT_FOLDER, output_dir=BW_FOLDER)

        # המרה ל־SVG
        convert_to_svg(input_dir=BW_FOLDER, output_dir=SVG_FOLDER)

        # יצירת פונט TTF
        font_created = generate_ttf(svg_folder=SVG_FOLDER, output_ttf=FONT_OUTPUT_PATH)

        return render_template(
            'index.html',
            font_created=font_created
        )
    except Exception as e:
        return render_template('index.html', error=f"שגיאה: {str(e)}")

# --- הורדת הפונט ---
@app.route('/download')
def download_font():
    if os.path.exists(FONT_OUTPUT_PATH):
        return send_file(
            FONT_OUTPUT_PATH,
            as_attachment=True,
            download_name='my_font.ttf',
            mimetype='font/ttf'
        )
    return render_template('index.html', error='הפונט לא קיים להורדה'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
