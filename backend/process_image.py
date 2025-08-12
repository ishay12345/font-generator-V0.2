# process_image.py
import cv2
import numpy as np
import os

def convert_to_black_white(input_path, output_path):
    """
    קורא תמונה, מחזק ניגוד, משלב adaptive + otsu, מנקה רעשים ומחזיר תמונה
    שבה הגליפים (האותיות) יהיו שחורות והרקע לבן.
    """
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("cannot read image at: " + input_path)

    # שיפור ניגוד:
    img_eq = cv2.equalizeHist(img)
    blur = cv2.GaussianBlur(img_eq, (5,5), 0)

    # adaptive threshold + otsu -> מאחדים
    try:
        adapt = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 31, 9
        )
    except Exception:
        adapt = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV, 31, 9
        )

    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    bw = cv2.bitwise_or(adapt, otsu)

    # ניקוי: close ואז open כדי לחבר קווים ולנקות נקודות
    kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    kernel5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel3, iterations=2)
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel3, iterations=1)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel5, iterations=1)

    # דילטיה קלה לחיזוק קווים
    bw = cv2.dilate(bw, kernel3, iterations=1)

    # הסרת רכיבים קטנים (רעשים)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    mask = np.zeros_like(bw)
    min_area = 40
    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
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

    # טיפה בלור כדי להחליק גבולות
    bw_final = cv2.medianBlur(bw_final, 3)

    # שמירה
    cv2.imwrite(output_path, bw_final)
    return output_path


def normalize_and_center_glyph(input_path, output_path, target_size=600, margin=50, vertical_offset=0):
    """
    קורא PNG של חתך אות (שחור על לבן או לבן על שחור),
    מוציא את הגבולות, משנה גודל באופן שמור לשוליים, ומרכז / מזיז אנכית.
    שמירת תמונה של ההגליפ בפורמט PNG (שחור על לבן).
    """
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("cannot read image: " + input_path)

    # נדאג לקבל 0=שחור,255=לבן
    _, bw = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

    # אם הגליף לבן על שחור נהפוך (נעדכן לפי תכולת פיקסלים)
    # נצפה שיש יותר פיקסלים לבנים (רקע). אם לא, נטיל אינברט
    white_count = int((bw == 255).sum())
    black_count = int((bw == 0).sum())
    if black_count > white_count:
        bw = cv2.bitwise_not(bw)  # עכשיו רקע=255, גליף=0

    coords = cv2.findNonZero(cv2.bitwise_not(bw))  # נקודות של הגליף (שחור)
    if coords is None:
        # אין גליף: נשמור קנבס לבן ריק
        canvas = 255 * np.ones((target_size, target_size), dtype=np.uint8)
        cv2.imwrite(output_path, canvas)
        return output_path

    x, y, w, h = cv2.boundingRect(coords)
    glyph = cv2.bitwise_not(bw[y:y+h, x:x+w])  # עכשיו glyph: פיקסלים לבנים על שחור => נפשט כך שיהיה שחור על לבן
    # glyph currently: 0 background? We'll normalize below by thresholding again
    glyph = cv2.threshold(glyph, 127, 255, cv2.THRESH_BINARY)[1]

    max_dim = target_size - 2 * margin
    # הגנה מפני w/h =0
    w = max(1, w); h = max(1, h)
    scale = min(max_dim / w, max_dim / h, 1.0)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    resized = cv2.resize(glyph, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = 255 * np.ones((target_size, target_size), dtype=np.uint8)
    x_off = (target_size - new_w) // 2
    y_off = (target_size - new_h) // 2 + vertical_offset
    y_off = max(0, min(y_off, target_size - new_h))
    # הצב: על הקנבס (לבן) נשים שחור בפיקסלים המתאימים
    # resized: 255=white glyph (we want black), invert:
    resized_inv = cv2.bitwise_not(resized)
    mask = resized_inv > 0
    canvas[y_off:y_off+new_h, x_off:x_off+new_w][mask] = 0

    cv2.imwrite(output_path, canvas)
    return output_path
