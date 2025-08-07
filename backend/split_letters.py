# backend/split_letters.py
import cv2
import os
from collections import defaultdict

def split_letters_manual(image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)

    # רשימת תיבות קבועות לפי המיקום הידני מהפלט הקודם
    boxes = [
        (50, 51, 68, 83), (149, 51, 68, 83), (248, 51, 68, 83), (348, 51, 68, 83),
        (50, 150, 68, 83), (149, 150, 68, 83), (248, 150, 68, 83), (348, 150, 68, 83),
        (50, 249, 68, 83), (149, 249, 68, 83), (248, 249, 68, 83), (348, 249, 68, 83),
        (50, 348, 68, 83), (149, 348, 68, 83), (248, 348, 68, 83), (348, 348, 68, 83),
        (50, 447, 68, 83), (149, 447, 68, 83), (248, 447, 68, 83), (348, 447, 68, 83),
        (50, 546, 68, 83), (149, 546, 68, 83), (248, 546, 68, 83), (348, 546, 68, 83),
        (50, 645, 68, 83), (149, 645, 68, 83), (248, 645, 68, 83)
    ]

    hebrew_letters = [
        'alef','bet','gimel','dalet','he','vav','zayin','het','tet',
        'yod','kaf','lamed','mem','nun','samekh','ayin','pe','tsadi',
        'qof','resh','shin','tav','final_kaf','final_mem','final_nun','final_pe','final_tsadi'
    ]

    padding = 15
    used_positions = []
    taken_letters = []

    def is_duplicate(x, y, w, h, positions, min_dist=25):
        cx, cy = x + w//2, y + h//2
        for px, py in positions:
            if abs(cx - px) < min_dist and abs(cy - py) < min_dist:
                return True
        return False

    for i, (x, y, w, h) in enumerate(boxes):
        if i >= len(hebrew_letters):
            break
        if is_duplicate(x, y, w, h, used_positions):
            continue
        used_positions.append((x + w//2, y + h//2))
        taken_letters.append(((x, y, w, h), i))  # שומר תיבה + אינדקס אות

    # הוספת האות "he" אחרי "dalet"
    dalet_index = [i for i, (_, idx) in enumerate(taken_letters) if hebrew_letters[idx] == "dalet"]
    if dalet_index:
        dalet_box, _ = taken_letters[dalet_index[0]]
        he_candidates = [b for b in boxes if b[0] > dalet_box[0] - 50 and b[1] > dalet_box[1] + 20]
        if he_candidates:
            he_box = sorted(he_candidates, key=lambda b: (b[1], -b[0]))[0]
            taken_letters.insert(dalet_index[0] + 1, (he_box, hebrew_letters.index("he")))

    # הוספת "final_nun" אחרי "final_mem"
    mem_index = [i for i, (_, idx) in enumerate(taken_letters) if hebrew_letters[idx] == "final_mem"]
    if mem_index:
        mem_box, _ = taken_letters[mem_index[0]]
        nun_candidates = [b for b in boxes if b[0] > mem_box[0] - 50 and b[1] > mem_box[1] + 20]
        if nun_candidates:
            nun_box = sorted(nun_candidates, key=lambda b: (b[1], -b[0]))[0]
            taken_letters.insert(mem_index[0] + 1, (nun_box, hebrew_letters.index("final_nun")))

    # שמירה
    saved_names = set()
    for box, idx in taken_letters:
        letter_name = hebrew_letters[idx]
        if letter_name in saved_names:
            continue
        saved_names.add(letter_name)

        x, y, w, h = box
        x1 = max(x - padding, 0)
        y1 = max(y - padding, 0)
        x2 = min(x + w + padding, img.shape[1])
        y2 = min(y + h + padding, img.shape[0])
        crop = img[y1:y2, x1:x2]

        out_path = os.path.join(output_dir, f"{idx:02d}_{letter_name}.png")
        cv2.imwrite(out_path, crop)
        print(f"שמורה אות {idx}: {letter_name}")

    print(f"\n✅ נשמרו {len(saved_names)} אותיות בתיקייה:\n{output_dir}")

# דוגמה להרצה
split_letters_manual("input.png", "split_letters_output")
