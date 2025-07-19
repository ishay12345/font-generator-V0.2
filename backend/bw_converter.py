import os
import cv2
import numpy as np

def convert_to_bw(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".png"):
            continue

        img_path = os.path.join(input_dir, fname)
        gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            continue

        # הפיכה לשחור-לבן בצורה חדה
        _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # לוודא שהאות שחורה והרקע לבן
        white_bg = np.sum(bw == 255)
        black_fg = np.sum(bw == 0)
        if black_fg > white_bg:
            bw = cv2.bitwise_not(bw)

        out_path = os.path.join(output_dir, fname)
        cv2.imwrite(out_path, bw)
        print(f"✅ {fname} → {out_path}")
