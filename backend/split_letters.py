# backend/split_letters.py
# backend/split_letters.py
import cv2
import os
import numpy as np
import hashlib

def split_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    height, width = img.shape

    # פריסת שורות: 6 שורות עם 4 אותיות + שורה אחרונה עם 3 אותיות
    row_configs = [
        4, 4, 4, 4, 4, 4, 3
    ]

    # שמות האותיות לפי הסדר שאתה עובד איתו
    hebrew_letters = [
        'alef','bet','gimel','dalet',
        'he','vav','zayin','het',
        'tet','yod','kaf','lamed',
        'mem','nun','samekh','ayin',
        'pe','tsadi','qof','resh',
        'shin','tav','final_kaf','final_mem',
        'final_nun','final_pe','final_tsadi'
    ]

    seen_hashes = set()
    padding = 10
    saved = 0
    row_height = height / len(row_configs)

    for row_index, num_cols in enumerate(row_configs):
        col_width = width / 4  # גם לשורה עם 3 אותיות משתמשים ב־4 חלקים, ולוקחים רק 3 מהם

        for col in range(num_cols):
            if saved >= len(hebrew_letters):
                break

            x_start = int(col * col_width)
            x_end = int((col + 1) * col_width)
            y_start = int(row_index * row_height)
            y_end = int((row_index + 1) * row_height)

            x1 = max(x_start - padding, 0)
            x2 = min(x_end + padding, width)
            y1 = max(y_start - padding, 0)
            y2 = min(y_end + padding, height)

            crop = img[y1:y2, x1:x2]

            # הקטנת אות גדולה מדי
            target_size = 120
            scale = target_size / max(crop.shape)
            if scale < 1.0:
                crop = cv2.resize(
                    crop,
                    (int(crop.shape[1] * scale), int(crop.shape[0] * scale)),
                    interpolation=cv2.INTER_AREA
                )

            # בדיקת כפילות
            hash_val = hashlib.sha256(crop.tobytes()).hexdigest()
            if hash_val in seen_hashes:
                continue
            seen_hashes.add(hash_val)

            name = hebrew_letters[saved]
            out_path = os.path.join(output_dir, f"{saved:02d}_{name}.png")
            cv2.imwrite(out_path, crop)
            saved += 1

    print(f"✅ נשמרו {saved} אותיות בתיקייה:\n{output_dir}")
