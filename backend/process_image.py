import cv2
import numpy as np

def convert_to_black_white(input_path, output_path):
    """
    קורא תמונה, משפר ניגודיות, הופך אותה לשחור־לבן כך שהאותיות שחורות
    והרקע לבן על כל התמונה.
    """
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image: {input_path}")

    # שיפור ניגודיות
    img_eq = cv2.equalizeHist(img)
    blur = cv2.GaussianBlur(img_eq, (5, 5), 0)

    # Threshold (Otsu) כדי להפריד בין אותיות לרקע
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # נוודא שהאותיות הן שחורות והרקע לבן
    white_pixels = np.sum(bw == 255)
    black_pixels = np.sum(bw == 0)
    if black_pixels > white_pixels:
        bw = cv2.bitwise_not(bw)

    # ניקוי רעשים קטנים
    kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel3, iterations=1)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel3, iterations=1)

    # שמירה
    cv2.imwrite(output_path, bw)
    print(f"[OK] BW image saved to: {output_path}")
    return output_path
