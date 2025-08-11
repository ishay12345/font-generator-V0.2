import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from process_image import convert_to_black_white

# הגדרות Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file uploaded", 400
    
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    
    # שמירת קובץ
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_path)
    
    # המרה לשחור־לבן
    bw_path = os.path.join(app.config['UPLOAD_FOLDER'], "bw_" + file.filename)
    convert_to_black_white(input_path, bw_path)
    
    # מעבר לעמוד החיתוך
    return redirect(url_for("crop_page", filename="bw_" + file.filename))

@app.route("/crop/<filename>")
def crop_page(filename):
    return render_template("crop.html", image_url=url_for('static', filename=f'processed/{filename}'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
