# backend/split_letters.py
import cv2
import os
import numpy as np

def split_letters_from_grid(image_path, output_dir, padding=15, show_debug=False):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)
    h, w, _ = img.shape

    # הגדרת הרשת: 7 שורות (6 של 4 אותיות + אחת עם 3 סופיות)
    row_configs = [4, 4, 4, 4, 4, 4, 3]
    total_letters = sum(row_configs)

    hebrew_letters = [
        'alef','bet','gimel','dalet',
        'he','vav','zayin','het',
        'tet','yod','kaf','lamed',
        'mem','nun','samekh','ayin',
        'pe','tsadi','qof','resh',
        'shin','tav','final_kaf','final_mem',
        'final_nun','final_pe','final_tsadi'
    ]

    if len(hebrew_letters) != total_letters:
        raise ValueError("מספר האותיות לא תואם למבנה הרשת")

    row_height = h / len(row_configs)
    col_width = w / 4  # גם בשורה של 3, נשמר רוחב של 4 עמודות

    saved = 0
    letter_index = 0

    debug_img = img.copy()

    for row_index, num_cols in enumerate(row_configs):
        for col_index in range(num_cols):
            if letter_index >= len(hebrew_letters):
                break

            x1 = int(col_index * col_width) - padding
            x2 = int((col_index + 1) * col_width) + padding
            y1 = int(row_index * row_height) - padding
            y2 = int((row_index + 1) * row_height) + padding

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            crop = img[y1:y2, x1:x2]
            name = hebrew_letters[letter_index]
            out_path = os.path.join(output_dir, f"{letter_index:02d}_{name}.png")
            cv2.imwrite(out_path, crop)

            if show_debug:
                cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(debug_img, name, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            print(f"שמורה אות {letter_index}: {name}")
            letter_index += 1

    if show_debug:
        debug_path = os.path.join(output_dir, "debug_grid.png")
        cv2.imwrite(debug_path, debug_img)
        print(f"\n🖼️ נשמר קובץ debug: {debug_path}")

    print(f"\n✅ נשמרו {letter_index} אותיות בתיקייה:\n{output_dir}")
