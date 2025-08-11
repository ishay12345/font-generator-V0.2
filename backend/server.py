# server.py
from flask import Flask, request, render_template, jsonify, send_file, url_for
from pathlib import Path
import os, io, base64
import cv2
import numpy as np
from PIL import Image

# אם יש לך generate_font.py עם generate_ttf(svg_folder, output_ttf)
try:
    from generate_font import generate_ttf
    HAVE_GENERATE_FONT = True
except Exception:
    HAVE_GENERATE_FONT = False

BASE = Path(__file__).parent
UPLOADS = BASE / "uploads"
GLYPHS  = BASE / "glyphs"
OUTPUT  = BASE / "output"

for p in (UPLOADS, GLYPHS, OUTPUT):
    p.mkdir(exist_ok=True)

app = Flask(__name__, template_folder=str(BASE / "templates"), static_folder=str(BASE / "static"))


def process_image_to_bw_bytes(image_bytes):
    """קבל תמונה (bytes) -> החזר bytes של PNG BW מעובדת"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image data")

    # --- שיפורי BW חזקים (כמו שביקשת) ---
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

    # encode to PNG bytes
    _, png = cv2.imencode('.png', bw_final)
    return png.tobytes()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """
    מקבל קובץ תמונה, מחזיר JSON:
      { processed_b64: "data:image/png;base64,..." , filename: "<saved name>" }
    """
    f = request.files.get('file')
    if not f:
        return jsonify({"error": "no file uploaded"}), 400

    raw = f.read()
    # שמירה של המקור
    fname = f.filename
    save_path = UPLOADS / fname
    with open(save_path, 'wb') as fh:
        fh.write(raw)

    try:
        bw_bytes = process_image_to_bw_bytes(raw)
    except Exception as e:
        return jsonify({"error": f"processing error: {e}"}), 500

    # שמירת processed
    proc_name = f"proc_{fname}"
    proc_path = UPLOADS / proc_name
    with open(proc_path, 'wb') as fh:
        fh.write(bw_bytes)

    b64 = base64.b64encode(bw_bytes).decode('ascii')
    return jsonify({
        "processed_b64": f"data:image/png;base64,{b64}",
        "uploaded_filename": fname,
        "processed_filename": proc_name
    })

@app.route('/api/save_crop', methods=['POST'])
def api_save_crop():
    """
    מקבל חיתוך כ־base64 + שם האות + אינדקס:
    JSON body: { name: "alef", index: 0, data: "data:image/png;base64,..." }
    ושומר PNG ב-glyphs/<index>_<name>.png
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "no data"}), 400
    name = data.get('name')
    index = data.get('index')
    imageData = data.get('data')
    if not name or imageData is None:
        return jsonify({"error":"missing fields"}), 400

    header, b64 = imageData.split(',',1) if ',' in imageData else (None, imageData)
    try:
        binary = base64.b64decode(b64)
    except Exception:
        return jsonify({"error":"invalid base64"}), 400

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
    """הרצת המרה->svg->פונט אם יש לך פונקציות מתאימות. כאן רק קורא generate_ttf אם זמין."""
    data = request.get_json() or {}
    outname = data.get('output_ttf', 'my_handwriting.ttf')
    outpath = OUTPUT / outname

    if not HAVE_GENERATE_FONT:
        return jsonify({"error":"generate_ttf not available on server"}), 500

    # כאן מניחים שיש SVGים מוכנים בתוך תקיית glyphs (או generate_ttf יודע להמיר PNG->SVG בעצמו).
    try:
        ok = generate_ttf(str(GLYPHS), str(outpath))
        if ok:
            return jsonify({"ttf": outname})
        else:
            return jsonify({"error":"generate_ttf returned False"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    path = OUTPUT / filename
    if path.exists():
        return send_file(str(path), as_attachment=True, download_name=filename)
    return jsonify({"error":"file not found"}), 404

if __name__ == '__main__':
    # debug עבור פיתוח; ב־render תשתמש ב־production mode
    app.run(host='0.0.0.0', port=5000, debug=True)
