import os
import cv2
import numpy as np

def convert_to_black_white(input_path, output_path, filename=None):
    os.makedirs(output_path, exist_ok=True)

    # קביעת קבצים לטיפול
    if filename:
        files = [filename]
    else:
        files = [f for f in os.listdir(input_path) if f.lower().endswith(".png")]

    for fname in files:
        img_path = os.path.join(input_path, fname)
        gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            print(f"⚠️ לא ניתן לקרוא את הקובץ {fname}")
            continue

        # שיפור ניגודיות
        gray_eq = cv2.equalizeHist(gray)

        # טשטוש עדין להסרת רעשים קטנים
        blur = cv2.GaussianBlur(gray_eq, (3, 3), 0)

        # הפיכה לשחור-לבן חדה עם Otsu
        _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # לוודא שהאות שחורה והרקע לבן
        white_bg = np.sum(bw == 255)
        black_fg = np.sum(bw == 0)
        if black_fg > white_bg:
            bw = cv2.bitwise_not(bw)

        # ניקוי נקודות קטנות (רעשים)
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel_small, iterations=1)

        # סגירה קלה לאיחוד חלקי אותיות
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel_close, iterations=1)

        # ניקוי כתמים גדולים מדי
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cv2.bitwise_not(bw), connectivity=8)
        cleaned = np.full_like(bw, 255)
        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]
            if 10 < area < 5000:  # לשנות אם האותיות גדולות יותר
                cleaned[labels == i] = 0

        # שמירה
        out_path = os.path.join(output_path, fname)
        cv2.imwrite(out_path, cleaned)
        print(f"✅ {fname} → {out_path}")
