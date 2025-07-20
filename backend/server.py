import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from split_letters import split_letters_from_image  # ודא שהפונקציה קיימת

# ----  הגדרת נתיבים מוחלטים  ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
SPLIT_DIR  = os.path.join(BASE_DIR, 'split_letters_output')

for d in (UPLOAD_DIR, SPLIT_DIR):
    os.makedirs(d, exist_ok=True)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, '..', 'frontend', 'templates'),
    static_folder=os.path.join(BASE_DIR, '..', 'frontend', 'static')
)

# ----  עמוד הבית (טופס העלאה)  ----
@app.route('/')
def index():
    return render_template('index.html')

# ----  העלאת התמונה וחיתוך האותיות  ----
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify(success=False, error='לא נבחר קובץ'), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify(success=False, error='שם קובץ ריק'), 400

    # שמירת הקובץ עם שם ייחודי
    filename = f"{uuid.uuid4().hex}.png"
    img_path = os.path.join(UPLOAD_DIR, filename)
    file.save(img_path)

    # ניקוי תיקיית הפלט
    for f in os.listdir(SPLIT_DIR):
        os.remove(os.path.join(SPLIT_DIR, f))

    # קריאה לפונקציית החיתוך
    try:
        split_letters_from_image(img_path, SPLIT_DIR)
    except Exception as e:
        return jsonify(success=False, error=f'שגיאה בחיתוך: {e}'), 500

    # בניית מערך כתובות התמונות שנוצרו
    letters = sorted([
        f for f in os.listdir(SPLIT_DIR)
        if f.lower().endswith(('.png', '.svg'))
    ])
    urls = [f"/letters/{name}" for name in letters]
    return jsonify(success=True, letters=urls)

# ----  שליחת קובץ אות בודדת  ----
@app.route('/letters/<filename>')
def letters(filename):
    return send_from_directory(SPLIT_DIR, filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))



