# backend/split_letters.py
import cv2
import os
import numpy as np

def split_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    img = cv2.imread(image_path)
    h, w, _ = img.shape

    # חלוקה לפי רשת של 7 שורות (6 עם 4 תאים, אחרונה עם 3)
    row_configs = [4, 4, 4, 4, 4, 4, 3]
    hebrew_letters = [
        'alef','bet','gimel','dalet',
        'he','vav','zayin','het',
        'tet','yod','kaf','lamed',
        'mem','nun','samekh','ayin',
        'pe','tsadi','qof','resh',
        'shin','tav','final_kaf','final_mem',
        'final_nun','final_pe','final_tsadi'
    ]

    if sum(row_configs) != len(hebrew_letters):
        raise ValueError("מספר האותיות לא תואם לרשת השורות")

    row_height = h / len(row_configs)
    col_width = w / 4  # כל שורה גם אם היא עם 3 תאים, עדיין 4 משבצות ברוחב

    index = 0
    padding = 10

    for row_idx, num_cols in enumerate(row_configs):
        for col_idx in range(num_cols):
            if index >= len(hebrew_letters):
                break

            x1 = int(col_idx * col_width) - padding
            x2 = int((col_idx + 1) * col_width) + padding
            y1 = int(row_idx * row_height) - padding
            y2 = int((row_idx + 1) * row_height) + padding

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

            crop = img[y1:y2, x1:x2]
            name = hebrew_letters[index]
            out_path = os.path.join(output_dir, f"{index:02d}_{name}.png")
            cv2.imwrite(out_path, crop)

            print(f"שמורה אות {index}: {name}")
            index += 1

    print(f"\n✅ נשמרו {index} אותיות בתיקייה:\n{output_dir}")
