# backend/split_letters.py
import cv2
import os

# קלט
input_path = "backend/uploads/handwriting.jpg"
output_folder = "backend/split_letters_output"
os.makedirs(output_folder, exist_ok=True)

# טען תמונה בגווני אפור
img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)

# סף בינארי
_, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

# מצא קונטורים
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# סינון תיבות רעש קטנות
boxes = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    if w * h > 100:  # תיבת אות אמיתית, לא לכלוך
        boxes.append((x, y, w, h))

# מיין לפי Y כדי לקבץ לשורות
boxes.sort(key=lambda b: b[1])  # מיין לפי y

# קיבוץ לשורות לפי קרבת גובה (סובלנות)
row_tolerance = 40
rows = []
for box in boxes:
    added = False
    for row in rows:
        if abs(box[1] - row[0][1]) < row_tolerance:
            row.append(box)
            added = True
            break
    if not added:
        rows.append([box])

# מיין כל שורה מימין לשמאל
ordered = []
for row in rows:
    row.sort(key=lambda b: -b[0])  # מימין לשמאל
    ordered.extend(row)

# שמור את התיבות החתוכות לפי הסדר
for i, (x, y, w, h) in enumerate(ordered):
    letter = img[y:y+h, x:x+w]
    save_path = os.path.join(output_folder, f"{i:02}.png")
    cv2.imwrite(save_path, letter)

print(f"נשמרו {len(ordered)} אותיות בתיקייה: {output_folder}")
