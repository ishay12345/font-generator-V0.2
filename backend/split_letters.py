import cv2
import os
import numpy as np


def split_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    clean = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]

    filtered = []
    for x, y, w, h in boxes:
        if w * h < 60:
            continue
        filtered.append([x, y, w, h])

    filtered.sort(key=lambda b: b[1])
    rows = []
    row_threshold = 50

    for b in filtered:
        x, y, w, h = b
        placed = False
        for row in rows:
            if abs(row[0][1] - y) < row_threshold:
                row.append(b)
                placed = True
                break
        if not placed:
            rows.append([b])

    rows.sort(key=lambda r: r[0][1])
    ordered = []

    for row in rows:
        row.sort(key=lambda b: -b[0])
        ordered.extend(row)

    hebrew_letters = [
        'alef', 'bet', 'gimel', 'dalet', 'he', 'vav', 'zayin', 'het', 'tet',
        'yod', 'kaf', 'lamed', 'mem', 'nun', 'samekh', 'ayin', 'pe', 'tsadi',
        'qof', 'resh', 'shin', 'tav', 'final_kaf', 'final_mem', 'final_nun', 'final_pe', 'final_tsadi'
    ]

    padding_x = 50  # ריווח גדול בין אותיות בציר האופקי
    padding_y = 20  # ריווח בציר האנכי
    saved = 0
    inserted_vav = False

    for i, (x, y, w, h) in enumerate(ordered):
        x1 = max(x - padding_x, 0)
        y1 = max(y - padding_y, 0)
        x2 = min(x + w + padding_x, img.shape[1])
        y2 = min(y + h + padding_y, img.shape[0])
        crop = img[y1:y2, x1:x2]

        is_narrow = w < 20 and h > 30

        if saved < len(hebrew_letters):
            name = hebrew_letters[saved]
        else:
            name = f"letter_{saved}"

        # הכנס את האות ו אחרי ה
        if name == 'zayin' and not inserted_vav:
            vav_candidates = [b for b in ordered if b[2] < 20 and b[3] > 30 and b != (x, y, w, h)]
            if vav_candidates:
                vx, vy, vw, vh = sorted(vav_candidates, key=lambda b: b[0])[-1]
                vx1 = max(vx - padding_x, 0)
                vy1 = max(vy - padding_y, 0)
                vx2 = min(vx + vw + padding_x, img.shape[1])
                vy2 = min(vy + vh + padding_y, img.shape[0])
                vav_crop = img[vy1:vy2, vx1:vx2]
                vav_path = os.path.join(output_dir, f"{saved:02d}_vav.png")
                cv2.imwrite(vav_path, vav_crop)
                print(f"✅ הוזנה ידנית אות: vav")
                saved += 1
                inserted_vav = True

        if is_narrow and name not in ['vav', 'yod', 'final_nun']:
            continue

        out_path = os.path.join(output_dir, f"{saved:02d}_{name}.png")
        cv2.imwrite(out_path, crop)
        print(f"✅ נשמרה אות {saved}: {name}")
        saved += 1

    print(f"\n✅ נחתכו ונשמרו {saved} אותיות בתיקייה:\n{output_dir}")
