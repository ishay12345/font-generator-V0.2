from flask import Flask, request, send_file
from split_letters import split_letters_from_file
import os
import shutil
import zipfile

app = Flask(__name__)
UPLOAD_FOLDER = 'backend/uploads'
OUTPUT_FOLDER = 'backend/split_letters_output'
ZIP_PATH = 'backend/split_letters_output.zip'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # נקה את הפלט הקודם
    shutil.rmtree(OUTPUT_FOLDER)
    os.makedirs(OUTPUT_FOLDER)

    # חתוך את האותיות
    split_letters_from_file(file_path, OUTPUT_FOLDER)

    # צור ZIP
    with zipfile.ZipFile(ZIP_PATH, 'w') as zipf:
        for root, _, files in os.walk(OUTPUT_FOLDER):
            for filename in files:
                filepath = os.path.join(root, filename)
                arcname = os.path.relpath(filepath, OUTPUT_FOLDER)
                zipf.write(filepath, arcname)

    return send_file(ZIP_PATH, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

