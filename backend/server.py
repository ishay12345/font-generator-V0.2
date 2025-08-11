import os
from flask import Flask, render_template, request, jsonify, send_from_directory

# הגדרת נתיבים
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'templates')  # תיקיית templates מחוץ ל-backend
STATIC_DIR = os.path.join(BASE_DIR, '..', 'static')    # תיקיית static מחוץ ל-backend

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crop')
def crop():
    return render_template('crop.html')

# דוגמה לנתיב לקבלת קבצי סטטיים אם צריך
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)

# לדוגמא - נקודת API לקבלת תמונה ולהחזיר תוצאה מומרת לשחור-לבן
@app.route('/api/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'לא נשלח קובץ'})

    # כאן היית מיישם המרה לשחור לבן או כל עיבוד אחר
    # לדוגמא שמירה זמנית או עיבוד ב-PIL
    # נחזיר כאן תשובה דמה לצורך הדגמה
    return jsonify({'processed_b64': 'data:image/png;base64,...'})

if __name__ == '__main__':
    app.run(debug=True)
