import cv2
import os
from pathlib import Path
import numpy as np

def split_letters_from_image(image_path, output_dir):
    """Split Hebrew letters from image into individual PNG files."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Step 1: Convert to BW
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Failed to load image from {image_path}")

    # Adaptive threshold for better handling of varying lighting
    thresh = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )

    # Morphological operations to clean noise and connect components
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
    bw_img = cv2.dilate(closed, kernel, iterations=1)

    # Step 2: Find contours and bounding boxes
    contours, _ = cv2.findContours(bw_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]

    # Filter small noise
    min_area = 100  # Adjusted minimum area
    filtered_boxes = [box for box in boxes if box[2] * box[3] >= min_area]

    # Merge overlapping boxes
    iou_threshold = 0.1
    merged_boxes = []
    used = [False] * len(filtered_boxes)
    for i in range(len(filtered_boxes)):
        if used[i]:
            continue
        current = list(filtered_boxes[i])
        used[i] = True
        for j in range(i + 1, len(filtered_boxes)):
            if used[j]:
                continue
            other = filtered_boxes[j]
            # Calculate IoU
            xA = max(current[0], other[0])
            yA = max(current[1], other[1])
            xB = min(current[0] + current[2], other[0] + other[2])
            yB = min(current[1] + current[3], other[1] + other[3])
            interArea = max(0, xB - xA) * max(0, yB - yA)
            boxAArea = current[2] * current[3]
            boxBArea = other[2] * other[3]
            iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)

            if iou > iou_threshold:
                current[0] = min(current[0], other[0])
                current[1] = min(current[1], other[1])
                current[2] = max(current[0] + current[2], other[0] + other[2]) - current[0]
                current[3] = max(current[1] + current[3], other[1] + other[3]) - current[1]
                used[j] = True
        merged_boxes.append(tuple(current))

    # Calculate average height for row detection
    avg_height = np.mean([box[3] for box in merged_boxes]) if merged_boxes else 50

    # Step 3: Organize into rows (expect 7 rows)
    merged_boxes.sort(key=lambda b: b[1])  # Sort by Y
    rows = []
    current_row = []
    prev_y = merged_boxes[0][1]
    for box in merged_boxes:
        if abs(box[1] - prev_y) > avg_height * 0.5:  # New row if gap is large
            if current_row:
                rows.append(sorted(current_row, key=lambda b: -b[0]))  # Sort right to left
            current_row = [box]
        else:
            current_row.append(box)
        prev_y = box[1]
    if current_row:
        rows.append(sorted(current_row, key=lambda b: -b[0]))
    if len(rows) != 7:
        raise ValueError(f"Detected {len(rows)} rows instead of 7. Check image layout.")

    # Flatten rows into ordered list (right to left per row)
    ordered_boxes = []
    for row in rows:
        ordered_boxes.extend(row)

    # Ensure exactly 27 letters
    if len(ordered_boxes) != 27:
        raise ValueError(f"Detected {len(ordered_boxes)} letters instead of 27. Adjust detection parameters.")

    # Hebrew letter names
    hebrew_letters = [
        'alef', 'bet', 'gimel', 'dalet', 'he', 'vav', 'zayin', 'het', 'tet',
        'yod', 'kaf', 'lamed', 'mem', 'nun', 'samekh', 'ayin', 'pe', 'tsadi',
        'qof', 'resh', 'shin', 'tav', 'final_kaf', 'final_mem', 'final_nun',
        'final_pe', 'final_tsadi'
    ]

    # Step 4: Crop and save each letter
    padding_ratio = 0.2  # 20% padding around each letter
    for i, (x, y, w, h) in enumerate(ordered_boxes):
        pad_x = int(w * padding_ratio)
        pad_y = int(h * padding_ratio)
        x1 = max(x - pad_x, 0)
        y1 = max(y - pad_y, 0)
        x2 = min(x + w + pad_x, img.shape[1])
        y2 = min(y + h + pad_y, img.shape[0])
        crop = img[y1:y2, x1:x2]

        name = hebrew_letters[i]
        output_path = os.path.join(output_dir, f"{i:02d}_{name}.png")
        cv2.imwrite(output_path, crop)
        print(f"Saved letter {name} to {output_path}")

    return len(hebrew_letters)
