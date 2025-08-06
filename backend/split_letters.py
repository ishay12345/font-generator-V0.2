# backend/split_letters.py
# backend/split_letters.py
import cv2
import os
import numpy as np
import hashlib
from collections import defaultdict

def split_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)  # שים לב - לא בשחור לבן

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]

    # סינון רעשים קטנים
    boxes = [b for b in boxes if b[2] * b[3] > 100]

    # קיבוץ לפי שורות עם סובלנות
    line_dict = defaultdict(list)
    line_tolerance = 40  # סובלנות לגובה

    # מיון כל התיבות לפי ציר Y
    boxes.sort(key=lambda b: b[1])

    line_index = 0
    current_line_y = None
    for box in boxes:
        x, y, w, h = box
        y_center = y + h // 2
        if current_line_y is None:
            current_line_y = y_center
        elif abs(y_center - current_line_y) > line_tolerance:
            line_index += 1
            current_line_y = y_center
        line_dict[line_index].append(box)

    # מיון כל שורה לפי X מימין לשמאל
    sorted_lines = []
    for line_key in sorted(line_dict.keys()):
        line = line_dict[line_key]
        line.sort(key=lambda b: -b[0])  # מימין לשמאל
        sorted_lines.append(line)

    # רשימת האותיות לפי סדר
    hebrew_letters = [
        'alef','bet','gimel','dalet',
        'he','vav','zayin','het',
        'tet','yod','kaf','lamed',
        'mem','nun','samekh','ayin',
        'pe','tsadi','qof','resh',
        'shin','tav','final_kaf','final_mem',
        'final_nun','final_pe','final_tsadi'
    ]

    # חיתוך ושמירה
    seen_hashes = set()
    saved = 0
    padding = 15

    for row in sorted_lines:
        for (x, y, w, h) in row:
            if saved >= len(hebrew_letters):
                break

            x1, y1 = max(x - padding, 0), max(y - padding, 0)
            x2, y2 = min(x + w + padding, img.shape[1]), min(y + h + padding, img.shape[0])
            crop = img[y1:y2, x1:x2]

            # בדיקת כפילות לפי hash
            hash_val = hashlib.sha256(crop.tobytes()).hexdigest()
            if hash_val in seen_hashes:
                continue
            seen_hashes.add(hash_val)

            name = hebrew_letters[saved]
            out_path = os.path.join(output_dir, f"{saved:02d}_{name}.png")
            cv2.imwrite(out_path, crop)
            saved += 1

    print(f"✅ נשמרו {saved} אותיות בתיקייה:\n{output_dir}")
