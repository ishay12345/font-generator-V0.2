import cv2
import os
from pathlib import Path
import numpy as np

def split_letters_from_image(image_path, output_dir):
    """Split Hebrew letters from image into individual PNG files."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # --- שלב 1: המרה לשחור-לבן ---
    img_color = cv2.imread(image_path)
    if img_color is None:
        raise ValueError(f"Failed to load image from {image_path}")
    img = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

    # Adaptive threshold לשיפור זיהוי בכל תאורה
    thresh = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8
    )

    # ניקוי רעשים וחיבור חלקים
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    morph = cv2.morphologyEx(morph, cv2.MORPH_CLOSE, kernel, iterations=1)
    bw_img = cv2.dilate(morph, kernel, iterations=1)

    # --- שלב 2: מציאת קונטורים ---
    contours, _ = cv2.findContours(bw_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]

    # סינון לפי שטח מינימלי (דינמי)
    avg_h = np.median([h for (_, _, _, h) in boxes])
    min_area = (avg_h * 0.4) ** 2
    boxes = [box for box in boxes if box[2] * box[3] >= min_area]

    # --- שלב 3: איחוד תיבות קרובות (בתוך ה־def) ---
    merged = []
    used = [False] * len(boxes)
    for i in range(len(boxes)):
        if used[i]:
            continue
        x, y, w, h = boxes[i]
        cur_box = [x, y, w, h]
        used[i] = True
        for j in range(i + 1, len(boxes)):
            if used[j]:
                continue
            x2, y2, w2, h2 = boxes[j]
            if abs(y - y2) < max(h, h2) * 0.5 and abs((x + w) - x2) < max(w, w2) * 0.3 * 100:
                nx1 = min(cur_box[0], x2)
                ny1 = min(cur_box[1], y2)
                nx2 = max(cur_box[0] + cur_box[2], x2 + w2)
                ny2 = max(cur_box[1] + cur_box[3], y2 + h2)
                cur_box = [nx1, ny1, nx2 - nx1, ny2 - ny1]
                used[j] = True
        merged.append(tuple(cur_box))

    # --- שלב 4: חלוקה לשורות ---
    avg_height = np.mean([box[3] for box in merged]) if merged else 50
    merged.sort(key=lambda b: b[1])
    rows = []
    current_row = []
    prev_y = merged[0][1]
    for box in merged:
        if abs(box[1] - prev_y) > avg_height * 0.5:
            if current_row:
                rows.append(sorted(current_row, key=lambda b: -b[0]))
            current_row = [box]
        else:
            current_row.append(box)
        prev_y = box[1]
    if current_row:
        rows.append(sorted(current_row, key=lambda b: -b[0]))

    # --- שלב 5: הפיכת השורות לרשימה שטוחה ---
    ordered_boxes = [b for row in rows for b in row]

    # --- שלב 6: חיתוך ושמירה ---
    padding_ratio = 0.2
    for i, (x, y, w, h) in enumerate(ordered_boxes):
        pad_x = int(w * padding_ratio)
        pad_y = int(h * padding_ratio)
        x1 = max(x - pad_x, 0)
        y1 = max(y - pad_y, 0)
        x2 = min(x + w + pad_x, img.shape[1])
        y2 = min(y + h + pad_y, img.shape[0])
        crop = img[y1:y2, x1:x2]
        cv2.imwrite(os.path.join(output_dir, f"{i:02d}.png"), crop)

    print(f"\n✅ נחתכו ונשמרו {len(ordered_boxes)} אותיות בתיקייה:\n{output_dir}")
    return len(ordered_boxes)
