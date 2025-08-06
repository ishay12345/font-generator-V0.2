# backend/split_letters.py
import cv2
import os
import numpy as np
import hashlib

def split_letters_from_image(image_path, output_dir, show_debug=False):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)
    debug_img = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    height, width = binary.shape

    # מספר אותיות בכל שורה
    row_configs = [4, 4, 4, 4, 4, 4, 3]  # 6 שורות רגילות + שורה אחת של סופיות

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

    used_positions = []

    def is_duplicate(crop):
        h = hashlib.sha256(crop.tobytes()).hexdigest()
        if h in seen_hashes:
            return True
        seen_hashes.add(h)
        return False

    def save_crop(crop, x1, y1, x2, y2, name, index):
        if crop.size == 0:
            return False
        if is_duplicate(crop):
            return False
        out_path = os.path.join(output_dir, f"{index:02d}_{name}.png")
        cv2.imwrite(out_path, crop)
        if show_debug:
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(debug_img, f"{index}:{name}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        print(f"שמורה אות {index}: {name}")
        return True

    for row_index, num_cols in enumerate(row_configs):
        col_width = width / 4  # גם אם יש רק 3 תאים בשורה, נשמור מבנה של 4 משבצות
        for col in range(num_cols):
            if saved >= len(hebrew_letters):
                break

            letter_name = hebrew_letters[saved]

            # חישוב גבולות
            x_start = int(col * col_width)
            x_end = int((col + 1) * col_width)
            y_start = int(row_index * row_height)
            y_end = int((row_index + 1) * row_height)

            # תוספת סובלנות
            x1 = max(x_start - padding, 0)
            x2 = min(x_end + padding, width)
            y1 = max(y_start - padding, 0)
            y2 = min(y_end + padding, height)

            crop = img[y1:y2, x1:x2]
            crop_gray = binary[y1:y2, x1:x2]

            # בדיקה האם יש תוכן אות (פיקסלים שחורים)
            nonzero_ratio = np.count_nonzero(crop_gray) / crop_gray.size
            if nonzero_ratio < 0.01:
                continue  # תא ריק

            success = save_crop(crop, x1, y1, x2, y2, letter_name, saved)
            if success:
                saved += 1

    if show_debug:
        debug_path = os.path.join(output_dir, "debug_boxes.png")
        cv2.imwrite(debug_path, debug_img)
        print(f"\n🖼️ שמורה תמונת DEBUG ב: {debug_path}")

    print(f"\n✅ נשמרו {saved} אותיות בתיקייה:\n{output_dir}")
