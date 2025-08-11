from flask import Flask, request, render_template, jsonify, send_file
from pathlib import Path
import os, base64
import cv2
import numpy as np

# אם יש לך generate_font.py עם הפונקציה generate_ttf(svg_folder, output_ttf)
try:
    from generate_font import generate_ttf
    HAVE_GENERATE_FONT = True
except Exception:
    HAVE_GENERATE_FONT = False

# נתיב בסיס לתיקיית backend
BASE = Path(__file__).parent.resolve()
UPLOADS = BASE / "uploads"
GLYPHS  = BASE / "glyphs"
OUTPUT  = BASE / "output"

# יצירת תיקיות אם לא קיימות
for p in (UPLOADS, GLYPHS, OUTPUT):
    p.mkdir(exist_ok=True)

app = Flask(
    __name__,
    template_folder=str(BASE / "templates"),
    static_folder=str(BASE / "static")
)

# הזזות אנכיות מותאמות לפי אותיות (פיקסלים)
vertical_offsets = {
    "yod": -60,          # יוד - למעלה
    "qof": 50,           # ק - למטה
    "final_kaf": 50,     # ך - למטה
    "final_nun": 50,     # ן - למטה
    "final_pe": 50,      # ף - למטה
    "final_tsadi": 50    # ץ - למטה
}

def normalize_and_center_glyph(img, target_size=600, margin=50, vertical_offset=0):
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, img_bw = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    coords = cv2.findNonZero(img_bw)
    if coords is None:
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
    y_offset = max(0, min(y_offset, target_size - new_h))

    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return 255 - canvas  # להחזיר לשחור על לבן

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

    try:
        bw_bytes = process_image_to_bw_bytes(raw)
    except Exception as e:
        return jsonify({"error": f"processing error: {e}"}), 500

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

def process_image_to_bw_bytes(image_bytes):
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

    min_fg_area = 40
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    mask = np.zeros_like(bw)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_fg_area:
            mask[labels == i] = 255
    bw = mask

    inv = cv2.bitwise_not(bw)
    num2, lbl2, stats2, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
    hole_thresh = 800
    for i in range(1, num2):
        area = stats2[i, cv2.CC_STAT_AREA]
        if area <= hole_thresh:
            inv[lbl2 == i] = 0
    bw_final = cv2.bitwise_not(inv)
    bw_final = cv2.medianBlur(bw_final, 3)

    _, png = cv2.imencode('.png', bw_final)
    return png.tobytes()

@app.route('/api/save_crop', methods=['POST'])
def api_save_crop():
    data = request.get_json()
    if not data:
        return jsonify({"error": "no data"}), 400
    name = data.get('name')
    index = data.get('index')
    imageData = data.get('data')
    if not name or imageData is None:
        return jsonify({"error": "missing fields"}), 400

    try:
        header, b64 = imageData.split(',', 1) if ',' in imageData else (None, imageData)
        binary = base64.b64decode(b64)
        nparr = np.frombuffer(binary, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    except Exception as e:
        return jsonify({"error": f"invalid base64 or image: {e}"}), 400

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
    data = request.get_json() or {}
    outname = data.get('output_ttf', 'my_handwriting.ttf')
    outpath = OUTPUT / outname

    if not HAVE_GENERATE_FONT:
        return jsonify({"error": "generate_ttf not available on server"}), 500

    try:
        ok = generate_ttf(str(GLYPHS), str(outpath))
        if ok:
            return jsonify({"ttf": outname})
        else:
            return jsonify({"error": "generate_ttf returned False"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    path = OUTPUT / filename
    if path.exists():
        return send_file(str(path), as_attachment=True, download_name=filename)
    return jsonify({"error": "file not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
