import cv2
import numpy as np
import os
from pathlib import Path

def split_letters_from_image(image_path, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # קריאת תמונה בגווני אפור
    img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_gray is None:
        raise ValueError(f"Cannot load image: {image_path}")

    # שיפור קונטרסט
    img_gray = cv2.equalizeHist(img_gray)

    # חיזוק קצוות ושחור-לבן
    blur = cv2.GaussianBlur(img_gray, (3, 3), 0)
    thresh_adapt = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        25, 15
    )

    # מיזוג עם OTSU לשיפור קצה
    _, thresh_otsu = cv2.threshold(
        blur, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    bw = cv2.bitwise_or(thresh_adapt, thresh_otsu)

    # ניקוי רעשים
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)

    # מציאת רכיבים מחוברים
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bw, connectivity=8)

    min_area = 30  # הורדתי כדי שגם אותיות קטנות ייכנסו
    letter_boxes = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        if area >= min_area:
            letter_boxes.append((x, y, w, h))

    # פונקציית מיון עברית
    def sort_boxes_hebrew(boxes, line_tol=15):
        boxes = sorted(boxes, key=lambda b: b[1])
        lines = []
        current_line = []
        current_y = -1000
        for box in boxes:
            x, y, w, h = box
            if abs(y - current_y) > line_tol:
                if current_line:
                    lines.append(current_line)
                current_line = [box]
                current_y = y
            else:
                current_line.append(box)
        if current_line:
            lines.append(current_line)
        sorted_boxes = []
        for line in lines:
            line_sorted = sorted(line, key=lambda b: -b[0])
            sorted_boxes.extend(line_sorted)
        return sorted_boxes

    # אותיות עם הורדת y מיוחדת
    letters_shift_down = {
        'tsadi': 15, 'qof': 15, 'final_kaf': 15,
        'final_nun': 15, 'final_pe': 15, 'final_tsadi': 15,
    }

    hebrew_letters = [
        'alef', 'bet', 'gimel', 'dalet', 'he', 'vav', 'zayin', 'het', 'tet',
        'yod', 'kaf', 'lamed', 'mem', 'nun', 'samekh', 'ayin', 'pe', 'tsadi',
        'qof', 'resh', 'shin', 'tav', 'final_kaf', 'final_mem', 'final_nun',
        'final_pe', 'final_tsadi'
    ]

    # גם אם אין בדיוק 27 — נמשיך
    expanded_boxes = letter_boxes

    # הרחבת קופסאות
    def expand_box(box, pad_x=15, pad_y_top=20, pad_y_bottom=10):
        x, y, w, h = box
        nx = max(x - pad_x, 0)
        ny = max(y - pad_y_top, 0)
        nw = min(w + 2*pad_x, img_gray.shape[1] - nx)
        nh = min(h + pad_y_top + pad_y_bottom, img_gray.shape[0] - ny)
        return (nx, ny, nw, nh)

    expanded_boxes = [expand_box(b) for b in expanded_boxes]
    expanded_boxes = sort_boxes_hebrew(expanded_boxes)

    # חיתוך ושמירה
    for i, (x, y, w, h) in enumerate(expanded_boxes):
        letter_name = hebrew_letters[i] if i < len(hebrew_letters) else f"unknown_{i}"
        shift_down = letters_shift_down.get(letter_name, 0)

        ny = y + shift_down
        ny = max(0, ny)
        if ny + h > img_gray.shape[0]:
            ny = img_gray.shape[0] - h

        crop = img_gray[ny:ny+h, x:x+w]
        out_path = os.path.join(output_dir, f"{i:02d}_{letter_name}.png")
        cv2.imwrite(out_path, crop)
        print(f"✅ נשמרה אות {i}: {letter_name} (shift {shift_down}px)")

    print(f"\n✅ נשמרו {len(expanded_boxes)} אותיות בתיקייה:\n{output_dir}")
