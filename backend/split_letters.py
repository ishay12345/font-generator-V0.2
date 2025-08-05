# backend/split_letters.py
# backend/split_letters.py
import cv2
import os
import numpy as np
import hashlib

def split_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # הפוך לבינארי (לבן=רקע, שחור=כתב)
    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    height, width = img.shape

    # פריסת שורות ועמודות
    row_configs = [4, 4, 4, 4, 4, 4, 3]  # שורת סופיות אחרונה עם 3 אותיות

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
    saved = 0
    padding = 15
    row_height = height / len(row_configs)

    for row_index, num_cols in enumerate(row_configs):
        col_width = width / 4  # גם בשורה עם 3, נשאר רוחב של 4 משבצות

        for col in reversed(range(num_cols)):  # חיתוך מימין לשמאל
            if saved >= len(hebrew_letters):
                break

            # גבולות התא המשוער
            x_start = int(col * col_width)
            x_end = int((col + 1) * col_width)
            y_start = int(row_index * row_height)
            y_end = int((row_index + 1) * row_height)

            # הוספת מרחב סובלנות סביב האות
            x1 = max(x_start - padding, 0)
            x2 = min(x_end + padding, width)
            y1 = max(y_start - padding, 0)
            y2 = min(y_end + padding, height)

            letter_crop = binary[y1:y2, x1:x2]

            # בדיקה האם יש שם משהו בכלל (פיקסלים שחורים)
            nonzero_ratio = np.count_nonzero(letter_crop) / letter_crop.size
            if nonzero_ratio < 0.01:
                continue  # ריק לגמרי, דלג

            # הקטנת אות גדולה מדי
            target_size = 120
            scale = target_size / max(letter_crop.shape)
            if scale < 1.0:
                letter_crop = cv2.resize(
                    letter_crop,
                    (int(letter_crop.shape[1] * scale), int(letter_crop.shape[0] * scale)),
                    interpolation=cv2.INTER_AREA
                )

            # בדיקת כפילות לפי hash
            hash_val = hashlib.sha256(letter_crop.tobytes()).hexdigest()
            if hash_val in seen_hashes:
                continue
            seen_hashes.add(hash_val)

            name = hebrew_letters[saved]
            out_path = os.path.join(output_dir, f"{saved:02d}_{name}.png")
            cv2.imwrite(out_path, 255 - letter_crop)  # הפוך חזרה ללבן רקע
            saved += 1

    print(f"✅ נשמרו {saved} אותיות בתיקייה:\n{output_dir}")
