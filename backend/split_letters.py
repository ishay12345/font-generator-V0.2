import cv2
import numpy as np
import os
from pathlib import Path

def split_letters_from_image(image_path, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_gray is None:
        raise ValueError(f"Cannot load image: {image_path}")

    _, bw = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bw, connectivity=8)

    min_area = 50
    letter_boxes = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        if area >= min_area:
            letter_boxes.append((x, y, w, h))

    def sort_boxes_hebrew(boxes, line_tol=15):
        boxes = sorted(boxes, key=lambda b: b[1])
        lines = []
        current_line = []
        current_y = -1000
        for box in boxes:
            x, y, w, h = box
            if abs(y - current_y) > line_tol:
                if current_line:
                    lines.append(current_line)
                current_line = [box]
                current_y = y
            else:
                current_line.append(box)
        if current_line:
            lines.append(current_line)
        sorted_boxes = []
        for line in lines:
            line_sorted = sorted(line, key=lambda b: -b[0])
            sorted_boxes.extend(line_sorted)
        return sorted_boxes

    letters_expand_top = ['tsadi', 'qof', 'final_kaf', 'final_nun', 'final_pe', 'final_tsadi']

    # מפת הורדת פיקסלים מדויקת לכל אות בנפרד
    letters_shift_down = {
        'tsadi': 12,
        'qof': 15,
        'final_kaf': 10,
        'final_nun': 13,
        'final_pe': 12,
        'final_tsadi': 15,
    }

    def expand_box(box, pad_x=10, pad_y_top=15, pad_y_bottom=5, letter_name=None):
        if letter_name in letters_expand_top:
            pad_y_top = 35
        x, y, w, h = box
        nx = max(x - pad_x, 0)
        ny = max(y - pad_y_top, 0)
        nw = min(w + 2*pad_x, img_gray.shape[1] - nx)
        nh = min(h + pad_y_top + pad_y_bottom, img_gray.shape[0] - ny)
        return (nx, ny, nw, nh)

    hebrew_letters = [
        'alef', 'bet', 'gimel', 'dalet', 'he', 'vav', 'zayin', 'het', 'tet',
        'yod', 'kaf', 'lamed', 'mem', 'nun', 'samekh', 'ayin', 'pe', 'tsadi',
        'qof', 'resh', 'shin', 'tav', 'final_kaf', 'final_mem', 'final_nun',
        'final_pe', 'final_tsadi'
    ]

    # הסרת התיבה הראשונה אם היא לא alef (כדי למנוע אות "ו/ן" מוזרה)
    if len(letter_boxes) > 0:
        letter_boxes = letter_boxes[1:]
        hebrew_letters = hebrew_letters[1:]
        print("⚠️ התיבה הראשונה הוסרה כדי למנוע אות לא רצויה.")

    expanded_boxes = []
    for i, box in enumerate(letter_boxes):
        letter_name = hebrew_letters[i] if i < len(hebrew_letters) else None
        expanded_boxes.append(expand_box(box, letter_name=letter_name))

    def merge_close_boxes(boxes, max_dist=15):
        merged = []
        used = [False]*len(boxes)
        for i, b1 in enumerate(boxes):
            if used[i]:
                continue
            x1, y1, w1, h1 = b1
            x1b, y1b = x1 + w1, y1 + h1
            merged_box = b1
            for j in range(i+1, len(boxes)):
                if used[j]:
                    continue
                x2, y2, w2, h2 = boxes[j]
                x2b, y2b = x2 + w2, y2 + h2
                horizontal_gap = max(x2 - x1b, x1 - x2b)
                vertical_overlap = min(y1b, y2b) - max(y1, y2)
                if horizontal_gap < max_dist and vertical_overlap > 0:
                    nx = min(x1, x2)
                    ny = min(y1, y2)
                    nb = max(x1b, x2b)
                    nh = max(y1b, y2b)
                    merged_box = (nx, ny, nb - nx, nh - ny)
                    used[j] = True
            used[i] = True
            merged.append(merged_box)
        return merged

    while len(expanded_boxes) > 27:
        prev_len = len(expanded_boxes)
        expanded_boxes = merge_close_boxes(expanded_boxes)
        if len(expanded_boxes) == prev_len:
            break

    if len(expanded_boxes) < 27:
        avg_w = int(np.mean([b[2] for b in expanded_boxes])) if expanded_boxes else 50
        avg_h = int(np.mean([b[3] for b in expanded_boxes])) if expanded_boxes else 50
        while len(expanded_boxes) < 27:
            expanded_boxes.append((0, 0, avg_w, avg_h))

    expanded_boxes = sort_boxes_hebrew(expanded_boxes)

    for i, (x, y, w, h) in enumerate(expanded_boxes[:27]):
        name = hebrew_letters[i]
        shift_down = letters_shift_down.get(name, 0)

        ny = y + shift_down
        ny = max(0, ny)
        if ny + h > img_gray.shape[0]:
            ny = img_gray.shape[0] - h

        crop = img_gray[ny:ny+h, x:x+w]
        out_path = os.path.join(output_dir, f"{i:02d}_{name}.png")
        cv2.imwrite(out_path, crop)
        print(f"✅ נשמרה אות {i}: {name} (shift down {shift_down}px)")

    print(f"\n✅ נחתכו ונשמרו {min(len(expanded_boxes),27)} אותיות בתיקייה:\n{output_dir}")
