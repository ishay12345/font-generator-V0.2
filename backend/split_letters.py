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

    # קיבוץ לשורות עם סובלנות לגובה
    line_dict = defaultdict(list)
    line_tolerance = 50
    boxes.sort(key=lambda b: b[1])

    line_index = 0
    current_line_y = None
    for box in boxes:
        x, y, w, h = box
        y_center = y + h // 2
        if current_line_y is None or abs(y_center - current_line_y) > line_tolerance:
            line_index += 1
            current_line_y = y_center
        line_dict[line_index].append(box)

    # מיון בתוך שורה: מימין לשמאל
    sorted_lines = []
    for key in sorted(line_dict.keys()):
        line = line_dict[key]
        line.sort(key=lambda b: -b[0])  # עברית
        sorted_lines.append(line)

    # flatten לפי סדר שורות ואז ימין לשמאל
    all_boxes = []
    for line in sorted_lines:
        all_boxes.extend(line)

    hebrew_letters = [
        'alef','bet','gimel','dalet','he','vav','zayin','het','tet',
        'yod','kaf','lamed','mem','nun','samekh','ayin','pe','tsadi',
        'qof','resh','shin','tav','final_kaf','final_mem','final_nun','final_pe','final_tsadi'
    ]

    # הכנסת תוספות לפי מיקום אותיות ספציפיות
    def insert_after_letter(boxes, letter_index, insert_box):
        if letter_index + 1 >= len(boxes):
            boxes.append(insert_box)
        else:
            boxes.insert(letter_index + 1, insert_box)
        return boxes

    def find_nearest_box(boxes, condition_fn):
        for i, box in enumerate(boxes):
            if condition_fn(i, box):
                return i, box
        return None, None

    # הכנה לשמירה
    used_positions = []
    padding = 15
    saved = 0

    def is_duplicate(x, y, w, h, positions, min_dist=25):
        cx, cy = x + w//2, y + h//2
        for px, py in positions:
            if abs(cx - px) < min_dist and abs(cy - py) < min_dist:
                return True
        return False

    final_boxes = []
    taken_letters = []

    for i, box in enumerate(all_boxes):
        if saved >= len(hebrew_letters):
            break
        x, y, w, h = box

        if is_duplicate(x, y, w, h, used_positions):
            continue

        used_positions.append((x + w//2, y + h//2))
        taken_letters.append((box, saved))
        saved += 1

    # הוספת האות "he" אחרי "dalet"
    dalet_index = [i for i, (_, idx) in enumerate(taken_letters) if hebrew_letters[idx] == "dalet"]
    if dalet_index:
        dalet_box, dalet_pos = taken_letters[dalet_index[0]]
        # מצא תיבה שנמצאת מתחת ומימין לדalet
        he_candidates = [b for b in all_boxes if b[0] > dalet_box[0] - 50 and b[1] > dalet_box[1] + 20]
        if he_candidates:
            he_box = sorted(he_candidates, key=lambda b: (b[1], -b[0]))[0]
            taken_letters.insert(dalet_index[0] + 1, (he_box, hebrew_letters.index("he")))

    # הוספת "final_nun" אחרי "final_mem"
    mem_index = [i for i, (_, idx) in enumerate(taken_letters) if hebrew_letters[idx] == "final_mem"]
    if mem_index:
        mem_box, mem_pos = taken_letters[mem_index[0]]
        nun_candidates = [b for b in all_boxes if b[0] > mem_box[0] - 50 and b[1] > mem_box[1] + 20]
        if nun_candidates:
            nun_box = sorted(nun_candidates, key=lambda b: (b[1], -b[0]))[0]
            taken_letters.insert(mem_index[0] + 1, (nun_box, hebrew_letters.index("final_nun")))

    # שמירה בפועל
    saved_names = set()
    for i, (box, letter_index) in enumerate(taken_letters):
        if letter_index >= len(hebrew_letters):
            continue
        letter_name = hebrew_letters[letter_index]
        if letter_name in saved_names:
            continue  # לא לשמור כפול
        saved_names.add(letter_name)

        x, y, w, h = box
        x1 = max(x - padding, 0)
        y1 = max(y - padding, 0)
        x2 = min(x + w + padding, img.shape[1])
        y2 = min(y + h + padding, img.shape[0])
        crop = img[y1:y2, x1:x2]

        out_path = os.path.join(output_dir, f"{letter_index:02d}_{letter_name}.png")
        cv2.imwrite(out_path, crop)
        print(f"שמורה אות {letter_index}: {letter_name}")

    print(f"\n✅ נשמרו {len(saved_names)} אותיות בתיקייה:\n{output_dir}")
