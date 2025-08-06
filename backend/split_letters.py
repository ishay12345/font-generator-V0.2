# backend/split_letters.py
# backend/split_letters.py
import cv2
import os
import numpy as np
from collections import defaultdict

def split_letters_from_image(image_path, output_dir, show_debug=False):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)
    debug_img = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.boundingRect(c)[2] * cv2.boundingRect(c)[3] > 100]

    # קיבוץ לפי שורות עם סובלנות
    line_dict = defaultdict(list)
    line_tolerance = 60
    boxes.sort(key=lambda b: b[1])

    line_ys = []
    for box in boxes:
        x, y, w, h = box
        cy = y + h // 2
        matched = False
        for i, avg_y in enumerate(line_ys):
            if abs(cy - avg_y) < line_tolerance:
                line_dict[i].append(box)
                line_ys[i] = (line_ys[i] + cy) // 2
                matched = True
                break
        if not matched:
            index = len(line_ys)
            line_dict[index].append(box)
            line_ys.append(cy)

    # סדר מימין לשמאל בכל שורה
    sorted_lines = []
    for idx in sorted(line_dict.keys()):
        line = line_dict[idx]
        line.sort(key=lambda b: -b[0])
        sorted_lines.append(line)

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
    taken_letters = set()
    saved = 0
    padding = 15

    def is_duplicate(x, y, w, h, positions, min_dist=30):
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

            # תנאים מיוחדים לפי מיקום
            if letter_name == 'alef' and not (row_index == 0 and col_index == 0):
                continue
            if letter_name == 'vav' and not (row_index == 1 and col_index == 1):
                continue
            if letter_name == 'yod' and not (row_index == 2 and col_index == 1):
                continue
            if letter_name == 'final_nun' and not (row_index == 6 and col_index == 0):
                continue
            if letter_name == 'final_pe' and saved > 25:
                # נוודא שהוא אחרי final_mem בלבד
                if not (saved == 25 and hebrew_letters[saved - 1] == 'final_mem'):
                    continue

            if is_duplicate(x, y, w, h, used_positions):
                continue
            if letter_name in taken_letters:
                continue

            used_positions.append((x + w // 2, y + h // 2))
            taken_letters.add(letter_name)

            x1 = max(x - padding, 0)
            y1 = max(y - padding, 0)
            x2 = min(x + w + padding, img.shape[1])
            y2 = min(y + h + padding, img.shape[0])
            crop = img[y1:y2, x1:x2]

            out_path = os.path.join(output_dir, f"{saved:02d}_{letter_name}.png")
            cv2.imwrite(out_path, crop)

            if show_debug:
                cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(debug_img, f"{saved}:{letter_name}", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            print(f"שמורה אות {saved}: {letter_name}")
            saved += 1

    if show_debug:
        debug_path = os.path.join(output_dir, "debug_boxes.png")
        cv2.imwrite(debug_path, debug_img)
        print(f"\n🖼️ נשמר גם קובץ debug עם תיבות ב: {debug_path}")

    print(f"\n✅ נשמרו {saved} אותיות בתיקייה:\n{output_dir}")
