def split_letters_from_image(image_path, output_dir):
    import cv2, os
    import numpy as np
    from pathlib import Path

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    img_gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_gray is None:
        raise ValueError(f"Cannot load image: {image_path}")

    # --- שלב 1: הכנה לשחור-לבן חד ---
    _, bw = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # ניקוי רעשים קטנים וחיבור רכיבים קרובים
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel, iterations=2)
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel, iterations=1)

    # --- שלב 2: איתור קונטורים ---
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h > 50:  # סינון רעשים קטנים
            boxes.append((x, y, w, h))

    # --- שלב 3: סידור תיבות בשורות, מימין לשמאל ---
    boxes = sorted(boxes, key=lambda b: (b[1], -b[0]))  # קודם לפי Y, אחר כך X הפוך

    # טיפול באותיות צרות (ו, י, ן) – הגדלת padding
    def expand_box(box, pad_ratio_x=0.2, pad_ratio_y=0.2):
        x, y, w, h = box
        pad_x = int(w * pad_ratio_x)
        pad_y = int(h * pad_ratio_y)
        return (max(x - pad_x, 0),
                max(y - pad_y, 0),
                min(w + 2 * pad_x, img_gray.shape[1]),
                min(h + 2 * pad_y, img_gray.shape[0]))

    expanded_boxes = []
    for (x, y, w, h) in boxes:
        if w < h * 0.5:  # אות צרה
            expanded_boxes.append(expand_box((x, y, w, h), pad_ratio_x=0.6, pad_ratio_y=0.25))
        else:
            expanded_boxes.append(expand_box((x, y, w, h), pad_ratio_x=0.25, pad_ratio_y=0.25))

    # --- שלב 4: מיזוג אם יש יותר מדי ---
    # מיזוג תיבות קרובות מדי או חופפות כדי להתקרב ל-27
    def merge_close_boxes(boxes, min_dist=5):
        merged = []
        used = [False] * len(boxes)
        for i in range(len(boxes)):
            if used[i]: continue
            x1, y1, w1, h1 = boxes[i]
            X1A, Y1A, X1B, Y1B = x1, y1, x1 + w1, y1 + h1
            for j in range(i + 1, len(boxes)):
                if used[j]: continue
                x2, y2, w2, h2 = boxes[j]
                X2A, Y2A, X2B, Y2B = x2, y2, x2 + w2, y2 + h2
                if not (X2A > X1B + min_dist or X2B < X1A - min_dist or Y2A > Y1B + min_dist or Y2B < Y1A - min_dist):
                    X1A = min(X1A, X2A)
                    Y1A = min(Y1A, Y2A)
                    X1B = max(X1B, X2B)
                    Y1B = max(Y1B, Y2B)
                    used[j] = True
            merged.append((X1A, Y1A, X1B - X1A, Y1B - Y1A))
            used[i] = True
        return merged

    while len(expanded_boxes) > 27:
        expanded_boxes = merge_close_boxes(expanded_boxes, min_dist=10)

    # --- שלב 5: אם פחות מדי – להרחיב ---
    if len(expanded_boxes) < 27:
        avg_w = int(np.mean([b[2] for b in expanded_boxes]))
        avg_h = int(np.mean([b[3] for b in expanded_boxes]))
        while len(expanded_boxes) < 27:
            expanded_boxes.append((0, 0, avg_w, avg_h))  # דמה (לבדוק אחר כך)

    # --- שלב 6: סידור סופי לשמירה ---
    expanded_boxes = sorted(expanded_boxes, key=lambda b: (b[1], -b[0]))

    hebrew_letters = [
        'alef', 'bet', 'gimel', 'dalet', 'he', 'vav', 'zayin', 'het', 'tet',
        'yod', 'kaf', 'lamed', 'mem', 'nun', 'samekh', 'ayin', 'pe', 'tsadi',
        'qof', 'resh', 'shin', 'tav', 'final_kaf', 'final_mem', 'final_nun',
        'final_pe', 'final_tsadi'
    ]

    for i, (x, y, w, h) in enumerate(expanded_boxes[:27]):
        crop = img_gray[y:y+h, x:x+w]
        name = hebrew_letters[i]
        out_path = os.path.join(output_dir, f"{i:02d}_{name}.png")
        cv2.imwrite(out_path, crop)
        print(f"נשמרה אות {i}: {name}")

    print(f"\n✅ נחתכו ונשמרו {min(len(expanded_boxes),27)} אותיות בתיקייה:\n{output_dir}")
