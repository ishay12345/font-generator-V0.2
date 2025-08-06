# backend/split_letters.py
# backend/split_letters.py
import cv2
import os
import numpy as np
from collections import defaultdict

def split_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.boundingRect(c)[2] * cv2.boundingRect(c)[3] > 100]

    # קיבוץ לשורות לפי גובה עם סובלנות
    line_dict = defaultdict(list)
    line_tolerance = 50
    boxes.sort(key=lambda b: b[1])  # מיון לפי Y

    line_index = 0
    current_line_y = None
    for box in boxes:
        x, y, w, h = box
        y_center = y + h // 2
        if current_line_y is None or abs(y_center - current_line_y) > line_tolerance:
            line_index += 1
            current_line_y = y_center
        line_dict[line_index].append(box)

    # מיון בכל שורה מימין לשמאל
    sorted_lines = []
    for key in sorted(line_dict.keys()):
        line = line_dict[key]
        line.sort(key=lambda b: -b[0])  # ימין לשמאל
        sorted_lines.append(line)

    # רשימת האותיות לפי הסדר הנכון
    hebrew_letters = [
        'alef','bet','gimel','dalet',
        'he','vav','zayin','het',
        'tet','yod','kaf','lamed',
        'mem','nun','samekh','ayin',
        'pe','tsadi','qof','resh',
        'shin','tav','final_kaf','final_mem',
        'final_nun','final_pe','final_tsadi'
    ]

    used_positions = []
    saved = 0
    padding = 15

    def is_duplicate(x, y, w, h, positions, min_dist=25):
        cx, cy = x + w // 2, y + h // 2
        for px, py in positions:
            if abs(cx - px) < min_dist and abs(cy - py) < min_dist:
                return True
        return False

    for row_index, row in enumerate(sorted_lines):
        for col_index, (x, y, w, h) in enumerate(row):
            if saved >= len(hebrew_letters):
                break

            letter_name = hebrew_letters[saved]

            # תנאים מיוחדים:
            if letter_name == 'alef' and not (row_index == 0 and col_index == 0):
                continue
            if letter_name == 'vav' and not (row_index == 1 and col_index == 1):
                continue
            if letter_name == 'yod' and not (row_index == 2 and col_index == 1):
                continue
            if letter_name == 'final_nun' and not (row_index == 6 and col_index == 0):
                continue

            if is_duplicate(x, y, w, h, used_positions):
                continue

            used_positions.append((x + w // 2, y + h // 2))

            x1 = max(x - padding, 0)
            y1 = max(y - padding, 0)
            x2 = min(x + w + padding, img.shape[1])
            y2 = min(y + h + padding, img.shape[0])
            crop = img[y1:y2, x1:x2]

            out_path = os.path.join(output_dir, f"{saved:02d}_{letter_name}.png")
            cv2.imwrite(out_path, crop)
            print(f"שמורה אות {saved}: {letter_name}")
            saved += 1

    print(f"\n✅ נשמרו {saved} אותיות בתיקייה:\n{output_dir}")
