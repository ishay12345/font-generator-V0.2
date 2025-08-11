import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
GLYPHS_FOLDER = os.path.join(BASE_DIR, 'static', 'glyphs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GLYPHS_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/crop')
def crop():
    return render_template('crop.html')

# העלאת קובץ
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "לא נבחר קובץ"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "שם קובץ ריק"})
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # כאן אפשר להוסיף עיבוד תמונה (לשחור-לבן וכו')
    # כרגע מחזירים את התמונה עצמה
    return jsonify({
        "processed_b64": f"/uploads/{filename}"
    })

# רשימת אותיות שמורות
@app.route('/api/list_glyphs', methods=['GET'])
def list_glyphs():
    try:
        files = [f for f in os.listdir(GLYPHS_FOLDER) if f.lower().endswith('.png')]
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)})

# שמירת חיתוך של אות
@app.route('/backend/save_crop', methods=['POST'])
def save_crop():
    data = request.get_json()
    if not data:
        return jsonify({"error": "אין נתונים"})
    name = data.get('name')
    index = data.get('index')
    img_data = data.get('data')

    if not (name and img_data):
        return jsonify({"error": "נתונים חסרים"})

    try:
        import base64
        from io import BytesIO
        from PIL import Image

        header, encoded = img_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        image = Image.open(BytesIO(img_bytes))

        filename = f"{index}_{name}.png"
        filepath = os.path.join(GLYPHS_FOLDER, filename)
        image.save(filepath)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})

# יצירת פונט (כאן כרגע זה דמה)
@app.route('/api/finalize', methods=['POST'])
def finalize_font():
    return jsonify({"ttf": "my_handwriting.ttf"})

# הורדת קובץ
@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(BASE_DIR, filename, as_attachment=True)

# הצגת קבצים שהועלו (לשימוש ב-/uploads/filename)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
