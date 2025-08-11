from PIL import Image

def convert_to_black_white(input_path, output_path):
    # פתיחת התמונה
    img = Image.open(input_path).convert("L")  # גרסקייל
    # הפיכת כל מה שמעל 200 ללבן, ומתחת לשחור
    threshold = 200
    img = img.point(lambda p: 0 if p < threshold else 255)
    img = img.convert("RGB")  # חזרה ל-RGB לשמירה
    img.save(output_path)
