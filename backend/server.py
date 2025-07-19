from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
import os
from werkzeug.utils import secure_filename
from split_letters import split_letters  # ודא שקובץ זה עובד ומחזיר קבצים

UPLOAD_FOLDER = 'backend/uploads'
OUTPUT_FOLDER = 'backend/split_letters_output'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# דף הבית - טופס העלאה
@app.route('/')
def index():
    return '''
    <h1>העלה תמונת כתב יד</h1>
    <form method="post" enctype="multipart/form-data" action="/upload">
        <input type="file" name="file">
        <input type="submit" value="העלה">
    </form>
    '''

# טיפול בהעלאה
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'לא נשלח קובץ', 400

    file = request.files['file']
    if file.filename == '':
        return 'אין שם לקובץ', 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # נקה את תיקיית הפלט לפני עיבוד חדש
    for f in os.listdir(app.config['OUTPUT_FOLDER']):
        os.remove(os.path.join(app.config['OUTPUT_FOLDER'], f))

    # פילוח האותיות
    split_letters(file_path, app.config['OUTPUT_FOLDER'])

    # הפניה לתצוגה
    return redirect(url_for('view_letters'))

# הצגת כל האותיות שנחתכו
@app.route('/view_letters')
def view_letters():
    images = os.listdir(app.config['OUTPUT_FOLDER'])
    images.sort()
    html = "<h1>תצוגת האותיות</h1>"
    for img in images:
        url = url_for('get_letter', filename=img)
        html += f'<div><img src="{url}" style="height:100px;"><br>{img}</div><hr>'
    return render_template_string(html)

# שליפת תמונה אחת
@app.route('/letters/<filename>')
def get_letter(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

