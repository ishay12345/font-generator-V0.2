# backend/split_letters.py
import cv2
import os
import numpy as np
from collections import defaultdict

def split_all_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)  # תמונה צבעונית
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.boundingRect(c)[2] * cv2.boundingRect(c)[3] > 100]

    # קיבוץ לשורות עם סובלנות לגובה
    line_dict = defaultdict(list)
    line_tolerance = 50
    boxes.sort(key=lambda b: b[1])  # לפי Y

    line_index = 0
    current_line_y = None
    for box in boxes:
        x, y, w, h = box
        y_center = y + h // 2
        if current_line_y is None or abs(y_center - current_line_y) > line_tolerance:
            line_index += 1
            current_line_y = y_center
        line_dict[line_index].append(box)

    # מיון בתוך כל שורה מימין לשמאל
    sorted_lines = []
    for key in sorted(line_dict.keys()):
        line = line_dict[key]
        line.sort(key=lambda b: -b[0])  # עברית: מימין לשמאל
        sorted_lines.append(line)

    padding = 15
    counter = 0
    for row in sorted_lines:
        for x, y, w, h in row:
            x1 = max(x - padding, 0)
            y1 = max(y - padding, 0)
            x2 = min(x + w + padding, img.shape[1])
            y2 = min(y + h + padding, img.shape[0])
            crop = img[y1:y2, x1:x2]

            filename = os.path.join(output_dir, f"{counter:02d}.png")
            cv2.imwrite(filename, crop)
            print(f"שמר אות #{counter} ב־ {filename}")
            counter += 1

    print(f"\n✅ נשמרו {counter} תווים בתיקייה:\n{output_dir}")
