import cv2
import os
import numpy as np

def split_letters_pixel_scan(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError(f"תמונה לא נטענה כראוי: {image_path}")

    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    height, width = binary.shape
    min_letter_width = 5  # מניעת אותיות כפולות
    min_letter_height = 10
    letter_images = []
    padding = 8

    y = 0
    while y < height:
        row_has_content = np.any(binary[y] > 0)
        if not row_has_content:
            y += 1
            continue

        # חפש שורת אות (כלומר טווח שורות עם תוכן)
        y_start = y
        while y < height and np.any(binary[y] > 0):
            y += 1
        y_end = y

        line = binary[y_start:y_end, :]
        x = width - 1
        while x >= 0:
            if np.any(line[:, x] > 0):
                # התחלת אות
                x_end = x
                while x >= 0 and np.any(line[:, x] > 0):
                    x -= 1
                x_start = x + 1

                letter_width = x_end - x_start
                letter_height = y_end - y_start

                if letter_width >= min_letter_width and letter_height >= min_letter_height:
                    x1 = max(x_start - padding, 0)
                    x2 = min(x_end + padding, width)
                    y1 = max(y_start - padding, 0)
                    y2 = min(y_end + padding, height)
                    letter_img = img[y1:y2, x1:x2]
                    letter_images.append(letter_img)
            else:
                x -= 1

    # שמירה
    for i, letter_img in enumerate(letter_images):
        path = os.path.join(output_dir, f"{i:02d}.png")
        cv2.imwrite(path, letter_img)

    print(f"✅ נחתכו {len(letter_images)} אותיות ונשמרו בתיקייה:\n{output_dir}")
