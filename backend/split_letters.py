import cv2
import os
import numpy as np

# שמות האותיות לפי הסדר בעברית
HEBREW_LETTERS = [
    'alef','bet','gimel','dalet','he','vav','zayin','het','tet',
    'yod','kaf','lamed','mem','nun','samekh','ayin','pe','tsadi',
    'qof','resh','shin','tav','final_kaf','final_mem','final_nun','final_pe','final_tsadi'
]

# אותיות שמותר להן להיות "כפולות" בגלל הצרות שלהן
THIN_LETTERS = {'vav', 'yod'}

def split_letters_from_image(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"⚠️ לא נמצאה תמונה בנתיב: {image_path}")

    # עיבוד בסיסי: בינארי וניקוי רעשים
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    cleaned = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=1)

    # מציאת קונטורים
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]

    # סינון לפי שטח ורווחים פנימיים
    filtered = []
    for x, y, w, h in boxes:
        if w * h < 60:
            continue
        inside = False
        for ox, oy, ow, oh in boxes:
            if (x, y, w, h) != (ox, oy, ow, oh) and x >= ox and y >= oy and x + w <= ox + ow and y + h <= oy + oh:
                inside = True
                break
        if not inside:
            filtered.append([x, y, w, h])

    # מיון לפי שורות ועמודות - מימין לשמאל ומלמעלה למטה
    filtered.sort(key=lambda b: b[1])  # לפי y
    rows = []
    for b in filtered:
        x, y, w, h = b
        placed = False
        for row in rows:
            if abs(row[0][1] - y) < h:
                row.append(b)
                placed = True
                break
        if not placed:
            rows.append([b])

    # מיון סופי מימין לשמאל בתוך כל שורה
    rows.sort(key=lambda r: r[0][1])  # לפי y שוב
    ordered = []
    for row in rows:
        row.sort(key=lambda b: -b[0])  # מימין לשמאל (x יורד)
        ordered.extend(row)

    used_hashes = set()
    saved_count = 0
    padding = 10

    for i, (x, y, w, h) in enumerate(ordered):
        if i >= len(HEBREW_LETTERS):
            name = f"letter_{i}"
        else:
            name = HEBREW_LETTERS[i]

        x1, y1 = max(x - padding, 0), max(y - padding, 0)
        x2, y2 = min(x + w + padding, img.shape[1]), min(y + h + padding, img.shape[0])
        crop = img[y1:y2, x1:x2]

        # מניעת כפילויות – רק לאותיות שאינן צרות
        hash_val = hash(crop.tobytes())
        if name not in THIN_LETTERS and hash_val in used_hashes:
            print(f"🚫 אות כפולה (תוכן זהה): {name}, לא נוסף")
            continue

        used_hashes.add(hash_val)
        filename = os.path.join(output_dir, f"{i:02d}_{name}.png")
        cv2.imwrite(filename, crop)
        print(f"✅ {filename}")
        saved_count += 1

    print(f"\n✅ נשמרו {saved_count} אותיות לתיקייה: {output_dir}")

# הפעלה לדוגמה:
# split_letters_from_image("input.png", "output_letters")

