# backend/split_letters.py
# backend/split_letters.py
import cv2
import os
import numpy as np
from collections import defaultdict

def split_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)  # בצבע
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.boundingRect(c)[2] * cv2.boundingRect(c)[3] > 100]

    # קיבוץ לקבוצות לפי שורות עם סובלנות לגובה
    line_dict = defaultdict(list)
    line_tolerance = 50
    boxes.sort(key=lambda b: b[1])  # מיין לפי Y

    line_index = 0
    current_line_y = None
    for box in boxes:
        x, y, w, h = box
        y_center = y + h // 2
        if current_line_y is None or abs(y_center - current_line_y) > line_tolerance:
            line_index += 1
            current_line_y = y_center
        line_dict[line_index].append(box)

    # מיון בתוך שורה מימין לשמאל
    sorted_lines = []
    for key in sorted(line_dict.keys()):
        line = line_dict[key]
        line.sort(key=lambda b: -b[0])  # מימין לשמאל
        sorted_lines.append(line)

    # סדר האותיות בעברית כולל סופיות
    hebrew_letters = [
        'alef','bet','gimel','dalet',
        'he','vav','zayin','het',
        'tet','yod','kaf','lamed',
        'mem','nun','samekh','ayin',
        'pe','tsadi','qof','resh',
        'shin','tav','final_kaf','final_mem',
        'final_nun','final_pe','final_tsadi'
    ]

    all_boxes = [b for row in sorted_lines for b in row]

    # סידור התיבות לפי שורות וקואורדינטות
    ordered = []
    used = set()
    padding = 15
    saved = 0

    for expected_index in range(len(hebrew_letters)):
        best_box = None
        best_score = float('inf')
        for i, (x, y, w, h) in enumerate(all_boxes):
            if i in used:
                continue
            center_x = x + w / 2
            center_y = y + h / 2
            # ניקוד לפי מיקום — הכי קרוב למיקום הצפוי
            # נניח שהן מסודרות בקירוב של 4 עמודות לשורה
            expected_row = expected_index // 4 if expected_index < 24 else 6
            expected_col = expected_index % 4 if expected_index < 24 else expected_index - 24
            expected_x = (3 - expected_col) * (img.shape[1] // 4)
            expected_y = expected_row * (img.shape[0] // 7)
            dist = (center_x - expected_x)**2 + (center_y - expected_y)**2
            if dist < best_score:
                best_score = dist
                best_box = i

        if best_box is not None:
            x, y, w, h = all_boxes[best_box]
            used.add(best_box)

            x1 = max(x - padding, 0)
            y1 = max(y - padding, 0)
            x2 = min(x + w + padding, img.shape[1])
            y2 = min(y + h + padding, img.shape[0])
            crop = img[y1:y2, x1:x2]

            name = hebrew_letters[saved]
            out_path = os.path.join(output_dir, f"{saved:02d}_{name}.png")
            cv2.imwrite(out_path, crop)
            print(f"שמורה אות {saved}: {name}")
            saved += 1

    print(f"\n✅ נשמרו {saved} אותיות בתיקייה:\n{output_dir}")
