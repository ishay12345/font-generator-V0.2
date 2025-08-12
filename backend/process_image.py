import os
import cv2
import numpy as np
# import shutil  # רק אם תרצה להפעיל את החלק של העתקת קבצים לסטטיק

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

def normalize_and_center_glyph(input_path, output_path, filename=None, target_size=600, margin=50, vertical_offset=0):
    """
    מנרמל ומרכז אות בודדת כך שהאותיות יהיו שחורות והרקע לבן.
    """
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"⚠️ לא ניתן לקרוא את הקובץ: {input_path}")

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
    print(f"[OK] אות מנורמלת נשמרה ב: {output_path}")

    # אם תרצה להעתיק למקום נוסף (למשל תיקיית static) תוכל להפעיל את זה, כרגע לא פעיל
    """
    if filename:
        static_uploads = os.path.join(BASE_DIR, 'static', 'uploads')
        os.makedirs(static_uploads, exist_ok=True)
        shutil.copy(output_path, os.path.join(static_uploads, filename))
        print(f"[OK] הועתק ל: static/uploads/{filename}")
    """

    return output_path
