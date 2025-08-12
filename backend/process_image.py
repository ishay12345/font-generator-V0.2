import os
import cv2
import numpy as np
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def convert_to_black_white(input_path, output_path, filename=None):
    """
    קורא תמונה, משפר ניגודיות והופך לשחור־לבן כך שהאותיות שחורות והרקע לבן על כל התמונה.
    """
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image: {input_path}")

    # שיפור ניגודיות ע"י CLAHE (יעיל יותר מ-Hist Equalization רגיל)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    img_eq = clahe.apply(img)

    # טשטוש קל להקטנת רעשים
    blur = cv2.GaussianBlur(img_eq, (3, 3), 0)

    # Threshold בשיטת Otsu
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # הפיכה במידת הצורך כך שהאותיות יהיו שחורות והרקע לבן
    white_pixels = np.sum(bw == 255)
    black_pixels = np.sum(bw == 0)
    if white_pixels < black_pixels:
        bw = cv2.bitwise_not(bw)

    # ניקוי רעשים קטנים ושיפור קווי האותיות
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel, iterations=1)

    # שמירה
    cv2.imwrite(output_path, bw)
    print(f"[OK] BW image saved to: {output_path}")

    # שמירה ל-static/uploads
    if filename:
        static_uploads = os.path.join(BASE_DIR, 'static', 'uploads')
        os.makedirs(static_uploads, exist_ok=True)
        shutil.copy(output_path, os.path.join(static_uploads, filename))
        print(f"[OK] Copied to static/uploads/{filename}")

    return output_path


def normalize_and_center_glyph(input_path, output_path, filename=None, target_size=600, margin=50, vertical_offset=0):
    """
    מנרמל ומרכז אות בודדת כך שהאותיות יהיו שחורות והרקע לבן.
    """
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image: {input_path}")

    # הפיכה לשחור־לבן
    _, bw = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # הפיכה במידת הצורך
    white_pixels = np.sum(bw == 255)
    black_pixels = np.sum(bw == 0)
    if white_pixels < black_pixels:
        bw = cv2.bitwise_not(bw)

    # מציאת גבולות האות
    coords = cv2.findNonZero(cv2.bitwise_not(bw))
    if coords is None:
        canvas = np.full((target_size, target_size), 255, dtype=np.uint8)
        cv2.imwrite(output_path, canvas)
        print(f"[!] אות ריקה נשמרה ב: {output_path}")
        return output_path

    x, y, w, h = cv2.boundingRect(coords)
    glyph = bw[y:y+h, x:x+w]

    # שינוי גודל
    max_dim = target_size - 2 * margin
    scale = min(max_dim / w, max_dim / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(glyph, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # יצירת קנבס ומרכזת
    canvas = np.full((target_size, target_size), 255, dtype=np.uint8)
    x_off = (target_size - new_w) // 2
    y_off = (target_size - new_h) // 2 + vertical_offset
    canvas[y_off:y_off+new_h, x_off:x_off+new_w] = resized

    cv2.imwrite(output_path, canvas)
    print(f"[OK] Normalized glyph saved to: {output_path}")

    if filename:
        static_uploads = os.path.join(BASE_DIR, 'static', 'uploads')
        os.makedirs(static_uploads, exist_ok=True)
        shutil.copy(output_path, os.path.join(static_uploads, filename))
        print(f"[OK] Copied to static/uploads/{filename}")

    return output_path
