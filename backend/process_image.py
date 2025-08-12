import cv2
import numpy as np
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def convert_to_black_white(input_path, output_path, filename=None):
    """
    הופך תמונה לשחור־לבן עם אותיות שחורות ורקע לבן,
    מנקה לכלוך גדול ומונע כתמים כהים.
    """
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image: {input_path}")

    # הסרת רעשים והחלקה
    blur = cv2.GaussianBlur(img, (5, 5), 0)

    # Adaptive Threshold - מתאים לכל אזור בנפרד
    bw = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=35,  # גודל האזור לחישוב סף
        C=15           # הורדה קלה כדי לשמור אותיות כהות
    )

    # הבטחה שאותיות שחורות
    white_pixels = np.sum(bw == 255)
    black_pixels = np.sum(bw == 0)
    if black_pixels > white_pixels:
        bw = cv2.bitwise_not(bw)

    # הסרת רכיבים גדולים מדי (כתמים)
    inv = cv2.bitwise_not(bw)
    contours, _ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 20000:  # סף שטח - להתאים לגודל התמונה
            cv2.drawContours(bw, [cnt], -1, 255, -1)

    # שמירה
    cv2.imwrite(output_path, bw)
    print(f"[OK] BW image saved to: {output_path}")

    if filename:
        static_uploads = os.path.join(BASE_DIR, 'static', 'uploads')
        os.makedirs(static_uploads, exist_ok=True)
        shutil.copy(output_path, os.path.join(static_uploads, filename))
        print(f"[OK] Copied to static/uploads/{filename}")

    return output_path
