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
        bw_image_paths = [f'bw_letters/{filename}' for filename in bw_images]

        return render_template('index.html', bw_images=bw_image_paths)

    except Exception as e:
        print("❌ שגיאה בתהליך:", e)
        return f'Error during processing: {str(e)}'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))



