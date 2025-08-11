from flask import Flask, request, render_template, jsonify, send_file
from pathlib import Path
import os, base64
import cv2
import numpy as np

# אם יש לך generate_font.py עם פונקציה generate_ttf(svg_folder, output_ttf)
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


# הגדרת הזזות אנכיות לכל אות
vertical_offsets = {
    "yod": -60,         # יוד למעלה
    "qof": 50,          # ק למטה
    "final_kaf": 50,    # ך למטה
    "final_nun": 50,    # ן למטה
    "final_pe": 50,     # ף למטה
    "final_tsadi": 50   # ץ למטה
}


def normalize_and_center_glyph(img, target_size=600, margin=50, vertical_offset=0):
    # המרה לשחור-לבן אם יש צורך
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, img_bw = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

    coords = cv2.findNonZero(img_bw)
    if coords is None:
        # תמונה ריקה - מחזיר קנבס לבן
        return 255 * np.ones((target_size, target_size), dtype=np.uint8)

    x, y, w, h = cv2.boundingRect(coords)
    glyph_cropped = img_bw[y:y+h, x:x+w]

    max_dim = target_size - 2 * margin
    scale = min(max_dim / w, max_dim / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(glyph_cropped, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = 255 * np.ones((target_size, target_size), dtype=np.uint8)
    x_offset = (target_size - new_w) // 2
    y_offset = (target_size - new_h) // 2 + vertical_offset

    # שמירה שהקנבס לא יצא מחוץ לתחום
    y_offset = max(0, min(y_offset, target_size - new_h))

    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return 255 - canvas  # להפוך חזרה לשחור על לבן


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def api_upload():
    f = request.files.get('file')
    if not f:
        return jsonify({"error": "no file uploaded"}), 400

    raw = f.read()
    fname = f.filename
    save_path = UPLOADS / fname
    with open(save_path, 'wb') as fh:
        fh.write(raw)

    # כאן אפשר להוסיף המרה לשחור-לבן אם רוצים

    b64 = base64.b64encode(raw).decode('ascii')
    return jsonify({
        "uploaded_filename": fname,
        "uploaded_b64": f"data:image/png;base64,{b64}"
    })


@app.route('/backend/save_crop', methods=['POST'])
def api_save_crop():
    """
    מקבל חיתוך כ־base64 + שם האות + אינדקס:
    JSON body: { name: "alef", index: 0, data: "data:image/png;base64,..." }
    ושומר PNG מנורמל וממויין ב-glyphs/<index>_<name>.png
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
        nparr = np.frombuffer(binary, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    except Exception:
        return jsonify({"error":"invalid base64 or image"}), 400

    vertical_offset = vertical_offsets.get(name, 0)
    normalized_img = normalize_and_center_glyph(img_np, target_size=600, margin=50, vertical_offset=vertical_offset)

    out_name = f"{index:02d}_{name}.png" if index is not None else f"{name}.png"
    out_path = GLYPHS / out_name
    cv2.imwrite(str(out_path), normalized_img)

    return jsonify({"saved": out_name})


@app.route('/api/list_glyphs')
def api_list_glyphs():
    files = sorted([p.name for p in GLYPHS.glob("*.png")])
    return jsonify({"files": files})


@app.route('/api/finalize', methods=['POST'])
def api_finalize():
    """
    קורא ל-generate_ttf (אם קיים) שיוצר פונט מתוך תיקיית glyphs
    """
    data = request.get_json() or {}
    outname = data.get('output_ttf', 'my_handwriting.ttf')
    outpath = OUTPUT / outname

    if not HAVE_GENERATE_FONT:
        return jsonify({"error":"generate_ttf not available on server"}), 500

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
    app.run(host='0.0.0.0', port=5000, debug=True)
