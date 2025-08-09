import cv2
import os
from pathlib import Path
import numpy as np

def split_letters_from_image(image_path, output_dir):
    """Split Hebrew letters from image into individual PNG files.
    הגישה:
    - המרה ל-BW (אות שחורה, רקע לבן)
    - זיהוי קונטורים לאחר חיבור קווים דקים (dilation פרופורציונלי לגובה אות)
    - איחוד תיבות קרובות
    - עבור כל תיבה: הרחבה דינמית עד ש"כל הצדדים לבנים" ואז חיתוך
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # --- קריאה והמרה לשחור-לבן (אות שחורה, רקע לבן) ---
    img_color = cv2.imread(image_path)
    if img_color is None:
        raise ValueError(f"Failed to load image from {image_path}")
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)

    # Adaptive threshold — נקבל תמונה בה האות היא 0 (שחור) והרקע 255 (לבן)
    bw = cv2.adaptiveThreshold(img_gray, 255,
                               cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 15, 8)

    # הפוך (נרצה לעבוד עם חלופות בהן האות לבנה עבור findContours)
    inv_for_contours = 255 - bw  # כאן האות = 255, רקע = 0

    # --- הערכה ראשונית של גובה אות ממוצעת (נשתמש לזה לפרופורציות דינמיות) ---
    prelim_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    prelim_closed = cv2.morphologyEx(inv_for_contours, cv2.MORPH_CLOSE, prelim_kernel, iterations=1)
    prelim_contours, _ = cv2.findContours(prelim_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in prelim_contours] if prelim_contours else [50]
    median_h = int(np.median(heights))
    if median_h <= 0:
        median_h = 50

    # --- חיבור/דילציה חכמה כדי לאחד קווים מקרטעים (חשוב ל־י/ו/ן) ---
    # גודל ליבה פרופורציונלי לגובה אות
    dilate_size = max(1, int(max(1, median_h * 0.06)))  # ~6% מהגובה הממוצע
    if dilate_size % 2 == 0:
        dilate_size += 1
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_size, dilate_size))
    connected = cv2.dilate(inv_for_contours, dilate_kernel, iterations=1)

    # מעט סגירה כדי למלא חורים קטנים (שלא יפצלו אות)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    connected = cv2.morphologyEx(connected, cv2.MORPH_CLOSE, close_kernel, iterations=1)

    # למצוא קונטורים לאחר החיבור
    contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]

    # --- סינון דינמי לפי שטח מינימלי (מבוסס על median_h) ---
    min_area = max(30, (median_h * 0.35) ** 2)  # מגן נגד רעשים קטנים
    boxes = [b for b in boxes if (b[2] * b[3]) >= min_area]

    # --- איחוד תיבות קרובות במיוחד (אופקית/אנכית) ---
    # נשתמש באיחוד איטרטיבי: אם ממוצע המרחק קטן מ-threshold נאחד
    boxes_sorted = sorted(boxes, key=lambda b: (b[1], b[0]))  # לפי Y ואז X
    merged = []
    used = [False] * len(boxes_sorted)
    for i in range(len(boxes_sorted)):
        if used[i]:
            continue
        x, y, w, h = boxes_sorted[i]
        cur = [x, y, w, h]
        used[i] = True
        for j in range(i + 1, len(boxes_sorted)):
            if used[j]:
                continue
            x2, y2, w2, h2 = boxes_sorted[j]
            # תנאי איחוד: חפיפה אנכית/אותה שורה או מאוד קרוב אופקית/אנכית
            vert_overlap = not (y2 > cur[1] + cur[3] or y2 + h2 < cur[1])
            horiz_dist = x2 - (cur[0] + cur[2])
            # סף דינמי לפי median_h
            horiz_thresh = max(3, int(median_h * 0.45))
            vert_thresh = max(3, int(median_h * 0.35))
            if vert_overlap and (horiz_dist <= horiz_thresh and horiz_dist >= -max(cur[2], w2)):
                # ממזגים תיבות שממש סמוכות או חופפות אנכית (שורות צמודות/אותיות צמודות)
                nx1 = min(cur[0], x2)
                ny1 = min(cur[1], y2)
                nx2 = max(cur[0] + cur[2], x2 + w2)
                ny2 = max(cur[1] + cur[3], y2 + h2)
                cur = [nx1, ny1, nx2 - nx1, ny2 - ny1]
                used[j] = True
            else:
                # בדיקה אם שתי תיבות קרובות מאוד (גם אנכית) -> איחוד
                center_dist = np.hypot((cur[0]+cur[2]/2)-(x2+w2/2), (cur[1]+cur[3]/2)-(y2+h2/2))
                if center_dist < max(median_h * 0.6, 20):
                    nx1 = min(cur[0], x2)
                    ny1 = min(cur[1], y2)
                    nx2 = max(cur[0] + cur[2], x2 + w2)
                    ny2 = max(cur[1] + cur[3], y2 + h2)
                    cur = [nx1, ny1, nx2 - nx1, ny2 - ny1]
                    used[j] = True
        merged.append(tuple(cur))

    # אם אין תיבות — נסיים מוקדם
    if not merged:
        print("❌ לא נמצא אף אות. בדוק את התמונה/התאורה.")
        return 0

    # --- כעת עבור כל תיבה: הרחבה דינמית עד שהכל לבן מסביב לתיבה ---
    final_boxes = []
    H, W = bw.shape
    for idx, (x, y, w, h) in enumerate(merged):
        # מתחילים מתיבה בסיסית; נשמור גבולות ראשוניים
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(W, x + w)
        y2 = min(H, y + h)

        # צעד הרחבה פרופורציונלי
        step = max(2, int(max(w, h) * 0.06))  # ~6% מהגודל - דינמי
        max_expand = max(W, H)  # רק כדי למנוע לולאה אינסופית

        # נבדוק עד שנקבל "פס לבן" מסביב או עד שנגיעה לקצה התמונה
        # בדיקה: האם יש פיקסלים שחורים באזור המסגרת החיצונית (רוחב border_check_px)
        border_check_px = max(2, int(min(w, h) * 0.12))  # עובי הסרט שבודקים שהוא לבן
        # הבדיקה תתחשב בגבולות התמונה כ'לבן' מבחינה פרקטית (כי אין נתונים שם)

        safety_counter = 0
        while True:
            safety_counter += 1
            if safety_counter > 200:
                # הגבלה כדי שלא נתקע
                break

            # חשב אזור מורחב שבו נבדוק אם יש שחור בחוץ
            ex1 = max(0, x1 - border_check_px)
            ey1 = max(0, y1 - border_check_px)
            ex2 = min(W, x2 + border_check_px)
            ey2 = min(H, y2 + border_check_px)

            # חלק חיצוני = האזור המורחב פחות האזור הפנימי
            region = bw[ey1:ey2, ex1:ex2]  # בתמונה bw: אות=0, רקע=255
            inner = bw[y1:y2, x1:x2]
            # ניצור מסכה של האזור החיצוני (כל המורחב) ונוציא את האזור הפנימי
            # כדי לבדוק אם יש פיקסלים שחורים מחוץ לאזור החיתוך
            mask_outer = np.ones(region.shape, dtype=np.uint8) * 255  # רקע לבן
            # קבע אינדקסים של האזור הפנימי בתוך region
            in_y1 = y1 - ey1
            in_y2 = in_y1 + (y2 - y1)
            in_x1 = x1 - ex1
            in_x2 = in_x1 + (x2 - x1)
            mask_outer[in_y1:in_y2, in_x1:in_x2] = 0  # אפס = לא חלק חיצוני

            # אז נקבל ערכים בחלק החיצוני (pixels where mask_outer==255)
            outer_pixels = region[mask_outer == 255]
            # הגדרת מצב: האם יש פיקסלים שחורים בחיצון? (אותות הם 0)
            has_black_outside = np.any(outer_pixels == 0)

            # אם אין שחור מחוץ — מצאנו תיבה שטוחה עם לבן מסביב -> עצור
            if not has_black_outside:
                # ניתן גם להוסיף פד לבטחון סביב החיתוך (padding קטן)
                pad_x = max(2, int((x2 - x1) * 0.06))
                pad_y = max(2, int((y2 - y1) * 0.06))
                fx1 = max(0, x1 - pad_x)
                fy1 = max(0, y1 - pad_y)
                fx2 = min(W, x2 + pad_x)
                fy2 = min(H, y2 + pad_y)
                final_boxes.append((fx1, fy1, fx2 - fx1, fy2 - fy1))
                break

            # אחרת — הרחב את התיבה בעד step (בקפיצות) ונספור שוב
            # נא להרחיב בצורה סימטרית מעט (ועד קצה התמונה)
            x1 = max(0, x1 - step)
            y1 = max(0, y1 - step)
            x2 = min(W, x2 + step)
            y2 = min(H, y2 + step)

            # עצור אם רחב מדי
            if (x2 - x1) >= W - 1 or (y2 - y1) >= H - 1:
                # לא הצלחנו לקבל משטח לבן מסביב — קח את מה שיש (אבל עם פד קטן)
                pad_x = max(2, int((x2 - x1) * 0.03))
                pad_y = max(2, int((y2 - y1) * 0.03))
                fx1 = max(0, x1 - pad_x)
                fy1 = max(0, y1 - pad_y)
                fx2 = min(W, x2 + pad_x)
                fy2 = min(H, y2 + pad_y)
                final_boxes.append((fx1, fy1, fx2 - fx1, fy2 - fy1))
                break

    # --- מיון לשורות (מימין לשמאל בכל שורה), לפי Y ואז לפי X הפוכ
    if not final_boxes:
        print("❌ לא נותרו תיבות לאחר ההרחבה הדינמית.")
        return 0

    final_boxes.sort(key=lambda b: b[1])  # לפי Y על מנת לקבץ שורות
    rows = []
    avg_h_final = np.median([b[3] for b in final_boxes])
    current_row = [final_boxes[0]]
    prev_y = final_boxes[0][1]
    for b in final_boxes[1:]:
        if abs(b[1] - prev_y) > max(10, avg_h_final * 0.6):
            # סיום שורה
            rows.append(sorted(current_row, key=lambda r: -r[0]))  # ימינה -> שמאלה
            current_row = [b]
        else:
            current_row.append(b)
        prev_y = b[1]
    if current_row:
        rows.append(sorted(current_row, key=lambda r: -r[0]))

    ordered_boxes = [box for row in rows for box in row]

    # --- חיתוך ושמירה לפי סדר שנמצא ---
    padding_ratio = 0.02  # כבר היינו זהירים; יש padding קטן כי הרחבנו קודם
    saved = 0
    for i, (x, y, w, h) in enumerate(ordered_boxes):
        pad_x = int(w * padding_ratio)
        pad_y = int(h * padding_ratio)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(W, x + w + pad_x)
        y2 = min(H, y + h + pad_y)
        crop = img_gray[y1:y2, x1:x2]
        out_path = os.path.join(output_dir, f"{i:02d}.png")
        cv2.imwrite(out_path, crop)
        print(f"✅ נשמרה אות {saved}: {out_path}")
        saved += 1

    print(f"\n✅ נחתכו ונשמרו {saved} אותיות בתיקייה: {output_dir}")
    return saved
