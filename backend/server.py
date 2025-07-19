from flask import Flask, request, send_from_directory, render_templates, redirect, url_for
import os
import uuid
from split_letters import split_letters_from_image  # ודא שקיים הקובץ עם הפונקציה

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'backend/uploads'
app.config['SPLIT_FOLDER'] = 'backend/split_letters_output'

# יצירת התיקיות אם לא קיימות
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SPLIT_FOLDER'], exist_ok=True)

# עמוד הבית (טופס העלאת תמונה)
@app.route('/')
def index():
    return render_templates('index.html')

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
    split_letters_from_image(file_path, app.config['SPLIT_FOLDER'])

    return redirect(url_for('view_letters'))

# צפייה באותיות שנחתכו
@app.route('/view_letters')
def view_letters():
    files = os.listdir(app.config['SPLIT_FOLDER'])
    files = [f for f in files if f.endswith('.png')]
    return render_templates('view_letters.html', files=files)

# שליחה של קובץ בודד
@app.route('/letters/<filename>')
def letter_file(filename):
    return send_from_directory(app.config['SPLIT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

