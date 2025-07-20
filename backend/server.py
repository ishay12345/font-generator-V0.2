from flask import Flask, request, send_from_directory, render_template, jsonify
import os
import uuid
from split_letters import split_letters_from_image  # ודא שהקובץ קיים ומכיל את הפונקציה הזו

# יצירת אפליקציית Flask
app = Flask(__name__, template_folder='../frontend/templates')

# הגדרות נתיבים לקבצים
app.config['UPLOAD_FOLDER'] = 'backend/uploads'
app.config['SPLIT_FOLDER'] = 'backend/split_letters_output'

# יצירת תיקיות אם הן לא קיימות
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SPLIT_FOLDER'], exist_ok=True)

# עמוד הבית - טופס העלאת תמונה
@app.route('/')
def index():
    return render_template('index.html')

# נקודת קבלת קובץ התמונה
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return "לא נבחר קובץ", 400

    file = request.files['image']
    if file.filename == '':
        return "הקובץ ריק", 400

    # שמירת הקובץ בשם ייחודי
    filename = f"{uuid.uuid4().hex}.png"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # ניקוי תיקיית הפלט לפני פיצול חדש
    for f in os.listdir(app.config['SPLIT_FOLDER']):
        file_to_remove = os.path.join(app.config['SPLIT_FOLDER'], f)
        if os.path.isfile(file_to_remove):
            os.remove(file_to_remove)

    # הרצת הפונקציה לפיצול האותיות
    split_letters_from_image(file_path, output_dir=app.config['SPLIT_FOLDER'])

    return jsonify({"success": True})

# נקודת גישה לתמונות של האותיות אחרי פיצול
@app.route('/letters/<filename>')
def letter_file(filename):
    return send_from_directory(app.config['SPLIT_FOLDER'], filename)

# הרצת השרת
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))




