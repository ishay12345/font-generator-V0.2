# server.py
from flask import Flask, request, render_template, jsonify, send_file, url_for
from pathlib import Path
import os, io, base64
import cv2
import numpy as np
from PIL import Image

# בדיקת זמינות פונקציית יצירת הפונט
try:
    from generate_font import generate_ttf
    HAVE_GENERATE_FONT = True
except Exception:
    HAVE_GENERATE_FONT = False

BASE = Path(__file__).parent.resolve()

# נתיבים - תיקיית static כוללת תיקיית uploads
STATIC_DIR = BASE / "static"
UPLOADS = STATIC_DIR / "uploads"  # תיקיית ההעלאה בתוך static
GLYPHS  = BASE / "glyphs"
OUTPUT  = BASE / "output"

# יצירת תיקיות במידת הצורך
for p in (UPLOADS, GLYPHS, OUTPUT):
    p.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(BASE / "templates"),
    static_folder=str(STATIC_DIR)
)


def process_image_to_bw_bytes(image_bytes):
    """קבלת bytes של תמונה -> החזרה bytes של PNG בשחור-לבן משופר"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image data")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_eq = cv2.equalizeHist(gray)
    blur = cv2.GaussianBlur(img_eq, (5,5), 0)

    adapt = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY_INV, 23, 9)
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    bw = cv2.bitwise_or(adapt, otsu)

    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel_small, iterations=1)

    kernel_close1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    kernel_close2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel_close1, iterations=2)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel_close2, iterations=1)

    bw = cv2.dilate(bw, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2,2)), iterations=1)

    # הסרת רכיבים קטנים
    min_fg_area = 40
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    mask = np.zeros_like(bw)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_fg_area:
            mask[labels == i] = 255
    bw = mask

    # מילוי חורים קטנים ברקע
    inv = cv2.bitwise_not(bw)
    num2, lbl2, stats2, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
    hole_thresh = 800
    for i in range(1, num2):
        area = stats2[i, cv2.CC_STAT_AREA]
        if area <= hole_thresh:
            inv[lbl2 == i] = 0
    bw_final = cv2.bitwise_not(inv)
    bw_final = cv2.medianBlur(bw_final, 3)

    # encode ל-PNG bytes
    _, png = cv2.imencode('.png', bw_final)
    return png.tobytes()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """
    מקבל קובץ תמונה, שומר, מחזיר JSON עם תמונה מעובדת ב-base64 להצגה ב-frontend
    """
    f = request.files.get('file')
    if not f:
        return jsonify({"error": "לא נבחר קובץ"}), 400

    raw = f.read()
    fname = f.filename
    safe_name = "".join(c for c in fname if c.isalnum() or c in (' ', '.', '_')).rstrip()  # ניקוי שם קובץ בסיסי
    save_path = UPLOADS / safe_name

    try:
        with open(save_path, 'wb') as fh:
            fh.write(raw)

        bw_bytes = process_image_to_bw_bytes(raw)

        proc_name = f"proc_{safe_name}"
        proc_path = UPLOADS / proc_name
        with open(proc_path, 'wb') as fh:
            fh.write(bw_bytes)

        b64 = base64.b64encode(bw_bytes).decode('ascii')
        return jsonify({
            "processed_b64": f"data:image/png;base64,{b64}",
            "uploaded_filename": safe_name,
            "processed_filename": proc_name
        })

    except Exception as e:
        return jsonify({"error": f"שגיאה בעיבוד התמונה: {e}"}), 500


@app.route('/api/save_crop', methods=['POST'])
def api_save_crop():
    """
    מקבל חיתוך כ-base64, שם אות ואינדקס, שומר PNG בתיקיית glyphs
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "לא התקבל מידע"}), 400
    name = data.get('name')
    index = data.get('index')
    imageData = data.get('data')
    if not name or imageData is None:
        return jsonify({"error":"שדות חסרים"}), 400

    header, b64 = imageData.split(',',1) if ',' in imageData else (None, imageData)
    try:
        binary = base64.b64decode(b64)
    except Exception:
        return jsonify({"error":"base64 לא חוקי"}), 400

    out_name = f"{index:02d}_{name}.png" if index is not None else f"{name}.png"
    out_path = GLYPHS / out_name
    with open(out_path, 'wb') as fh:
        fh.write(binary)

    return jsonify({"saved": out_name})


@app.route('/api/list_glyphs')
def api_list_glyphs():
    files = sorted([p.name for p in GLYPHS.glob("*.png")])
    return jsonify({"files": files})


@app.route('/api/finalize', methods=['POST'])
def api_finalize():
    """
    הרצת המרה ל-SVG ולפונט (generate_ttf) אם זמין
    """
    data = request.get_json() or {}
    outname = data.get('output_ttf', 'my_handwriting.ttf')
    outpath = OUTPUT / outname

    if not HAVE_GENERATE_FONT:
        return jsonify({"error":"generate_ttf לא זמין בשרת"}), 500

    try:
        ok = generate_ttf(str(GLYPHS), str(outpath))
        if ok:
            return jsonify({"ttf": outname})
        else:
            return jsonify({"error":"generate_ttf החזיר False"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    path = OUTPUT / filename
    if path.exists():
        return send_file(str(path), as_attachment=True, download_name=filename)
    return jsonify({"error":"הקובץ לא נמצא"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
