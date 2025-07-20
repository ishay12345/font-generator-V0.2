from flask import Flask, request, render_template
import os
from split_letters import split_letters_from_image
from bw_converter import convert_to_bw
from svg_converter import convert_to_svg


UPLOAD_FOLDER = 'backend/uploads'
SPLIT_FOLDER = 'backend/split_letters_output'
BW_FOLDER = 'backend/bw_letters'
SVG_FOLDER = 'backend/svg_letters'

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
        return 'No file part'
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        # שלב 1 – חיתוך
        split_letters_from_image(filepath, output_dir=SPLIT_FOLDER)

        # שלב 2 – המרה לשחור־לבן
        convert_to_bw(input_dir=SPLIT_FOLDER, output_dir=BW_FOLDER)
    
        convert_to_svg(input_dir=BW_FOLDER,output_dir=SVG_FOLDER)

        print("✅  ולהפוך לSVGהצליח לחתוך ולהמיר לשחור לבן")  # יופיע בלוג של Render
        # שלב 3 – מצא את הקבצים המומרים
        bw_images = sorted(os.listdir(BW_FOLDER))
svg_images = sorted(os.listdir(SVG_FOLDER))

# תוצאה של כל שלב
cutting_done = len(os.listdir(SPLIT_FOLDER)) > 0
bw_done = len(bw_images) > 0
svg_done = len(svg_images) > 0

# הדפסות ללוג של Render (לא חובה ל-HTML, רק לדיבאג)
print(f"✂️ חיתוך אותיות: {'הושלם' if cutting_done else 'נכשל'}")
print(f"🖤 המרה לשחור-לבן: {'הושלם' if bw_done else 'נכשל'}")
print(f"🟢 המרה ל-SVG: {'הושלם' if svg_done else 'נכשל'}")

# שלח תשובה ל-HTML
return render_template(
    'result.html',
    cutting_done=cutting_done,
    bw_done=bw_done,
    svg_done=svg_done
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))



