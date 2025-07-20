from flask import Flask, request, send_from_directory, render_template, jsonify
import os
import uuid
from split_letters import split_letters_from_image  # ודא שהקובץ קיים

app = Flask(__name__, template_folder='../frontend/templates')

app.config['UPLOAD_FOLDER'] = 'backend/uploads'
app.config['SPLIT_FOLDER'] = 'backend/split_letters_output'

# יצירת התיקיות אם לא קיימות
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SPLIT_FOLDER'], exist_ok=True)

# עמוד הבית (טופס העלאת תמונה)
@app.route('/')
def index():
    return render_template('index.html')

# עיבוד תמונה אחרי שליחה מהטופס
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return "לא נבחר קובץ", 400

    file = request.files['image']
    if file.filename == '':
        return "הקובץ ריק", 400

    # שמירה עם שם ייחודי
    filename = f"{uuid.uuid4().hex}.png"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # ניקוי הפלט הקודם
    for f in os.listdir(app.config['SPLIT_FOLDER']):
        os.remove(os.path.join(app.config['SPLIT_FOLDER'], f))

    # חיתוך האותיות
    split_letters_from_image(file_path, output_dir=app.config['SPLIT_FOLDER'])

    return jsonify({"success": True})

# שליחה של קובץ אות בודדת
@app.route('/letters/<filename>')
def letter_file(filename):
    return send_from_directory(app.config['SPLIT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))



