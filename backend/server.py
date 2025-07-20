from flask import Flask, request, render_template
import os
from split_letters import split_image_to_letters
from bw_converter import convert_to_bw

UPLOAD_FOLDER = 'backend/uploads'
SPLIT_FOLDER = 'backend/split_letters_output'
BW_FOLDER = 'backend/bw_letters'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        split_image_to_letters(filepath, output_dir=SPLIT_FOLDER)

        # שלב 2 – המרה לשחור־לבן
        convert_to_bw(input_dir=SPLIT_FOLDER, output_dir=BW_FOLDER)

        print("✅ הצליח לחתוך ולהמיר לשחור לבן")  # יופיע בלוג של Render
        # שלב 3 – מצא את הקבצים המומרים
        bw_images = sorted(os.listdir(BW_FOLDER))
        bw_image_paths = [f'bw_letters/{filename}' for filename in bw_images]

        return render_template('index.html', bw_images=bw_image_paths)

    except Exception as e:
        print("❌ שגיאה בתהליך:", e)
        return f'Error during processing: {str(e)}'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))



