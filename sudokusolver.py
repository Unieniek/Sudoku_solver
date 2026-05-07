import time

import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont

#size of the final ss of a cell
TEMPLATE_SIZE = 40

#taking the numbers picture and creating a 40x40 template
#raw number -> snipping -> scaling -> centering -> 40x40
def normalize_digit(binary):
    #finding white pixels
    points = cv2.findNonZero(binary)

    if points is None:
        return None

    x, y, w, h = cv2.boundingRect(points)

    if w * h < 20:
        return None
    #taking the sole number of ss
    digit = binary[y:y + h, x:x + w]

    target_size = TEMPLATE_SIZE - 8
    scale = min(target_size / w, target_size / h)

    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    resized = cv2.resize(digit, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((TEMPLATE_SIZE, TEMPLATE_SIZE), dtype=np.uint8)

    offset_x = (TEMPLATE_SIZE - new_w) // 2
    offset_y = (TEMPLATE_SIZE - new_h) // 2

    canvas[offset_y:offset_y + new_h, offset_x:offset_x + new_w] = resized

    return canvas

#finding and taking one cell
#field -> take edges -> binary (black and white) -> delete noise -> take nmumber -> 40x40
def preprocess_cell(cell):
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape

    # Ucinamy brzegi pola, żeby linie siatki nie przeszkadzały
    margin = int(min(h, w) * 0.16)
    crop = gray[margin:h - margin, margin:w - margin]

    blur = cv2.GaussianBlur(crop, (3, 3), 0)

    threshold = cv2.threshold(
        blur,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )[1]

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        np.ones((2, 2), np.uint8)
    )

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        threshold,
        8
    )

    mask = np.zeros_like(threshold)

    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]
        x, y, width, height = stats[label_id, :4]

        if area > 15 and height > 8:
            mask[labels == label_id] = 255

    return normalize_digit(mask)

#finding fonts on windows
def find_font_paths():
    possible_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]

    return [path for path in possible_paths if os.path.exists(path)]

#creating templates for different sizes and fonts
def create_templates():
    font_paths = find_font_paths()

    if not font_paths:
        raise RuntimeError(
            "Nie znaleziono żadnego fontu. Dopisz ręcznie ścieżkę do fontu w find_font_paths()."
        )

    templates = {}

    for digit in "123456789":
        templates[int(digit)] = []

        for font_path in font_paths:
            for font_size in range(34, 48, 2):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except Exception:
                    continue

                temp_img = Image.new("L", (70, 70), 0)
                draw = ImageDraw.Draw(temp_img)

                bbox = draw.textbbox((0, 0), digit, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]

                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        img = Image.new("L", (70, 70), 0)
                        draw = ImageDraw.Draw(img)

                        x = (70 - text_w) // 2 - bbox[0] + dx
                        y = (70 - text_h) // 2 - bbox[1] + dy

                        draw.text((x, y), digit, font=font, fill=255)

                        arr = np.array(img)
                        normalized = normalize_digit(arr)

                        if normalized is not None:
                            templates[int(digit)].append(normalized)

    return templates

#comparing pictures
def similarity(a, b):
    a = a.astype(np.float32) / 255.0
    b = b.astype(np.float32) / 255.0

    denominator = np.linalg.norm(a) * np.linalg.norm(b) + 1e-6

    return float((a * b).sum() / denominator)


def recognize_digit(normalized_digit, templates):
    if normalized_digit is None:
        return 0, 0.0

    if cv2.countNonZero(normalized_digit) < 25:
        return 0, 0.0

    best_digit = 0
    best_score = -1.0

    for digit, digit_templates in templates.items():
        score = max(
            similarity(normalized_digit, template)
            for template in digit_templates
        )

        if score > best_score:
            best_score = score
            best_digit = digit

    return best_digit, best_score


def read_sudoku_from_image(image_path):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Nie udało się wczytać obrazka.")

    #we assume the ss is a sole playing field or close
    board = cv2.resize(image, (450, 450))

    cell_size = 450 // 9

    templates = create_templates()

    array = [[0 for _ in range(9)] for _ in range(9)]
    line = ""

    for row in range(9):
        for col in range(9):
            x1 = col * cell_size
            y1 = row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            cell = board[y1:y2, x1:x2]

            normalized_digit = preprocess_cell(cell)
            digit, score = recognize_digit(normalized_digit, templates)

            #if the propability is to low we treat the cell as empty
            if score < 0.45:
                digit = 0

            array[col][row] = digit
            line += str(digit)

    return array, line


def print_sudoku(array):
    for row in range(9):
        if row in [0, 3, 6]:
            print("-------------------------")

        for col in range(9):
            if col in [0, 3, 6]:
                print("| ", end="")

            value = array[col][row]

            if value == 0:
                print(". ", end="")
            else:
                print(f"{value} ", end="")

        print("|")

    print("-------------------------")


if __name__ == "__main__":
    image_path = "sudoku.png"

    array, line = read_sudoku_from_image(image_path)

    print("Data for solver")
    print(line)

    print("Recognised field")
    print_sudoku(array)


array = [[0 for _ in range(9)] for _ in range(9)]
for i in range(9):
    for j in range(9):
        array[j][i] = int(line[i * 9 + j])

start = time.time()

line = ["" for _ in range(9)]
column = ["" for _ in range(9)]
square = [["" for _ in range(3)] for _ in range(3)]
position = [0 for _ in range(81)]

# get the numbers missing from each line
for j in range(9):
    for i in range(9):
        if array[i][j] != 0:
            line[j] += str(array[i][j])

# get numbers for column
for j in range(9):
    for k in range(9):
        if array[j][k] != 0:
            column[j] += str(array[j][k])

# get numbers for square
for i in range(9):
    for j in range(9):
        if array[j][i] != 0:
            square[i // 3][j // 3] += str(array[j][i])

l = 0
i = 0
j = 0
combinations = 0
flag = True

while i < 9:
    while j < 9:
        if array[j][i] == 0:
            if position[l] == 0:
                position[l] = 100
            if position[l] // 100 == 10:
                flag = False
                position[l] -= 100
            for k in range(position[l] // 100, 10):
                if position[l] != 0:
                    position[l] = 0
                if (str(k) not in line[i] and
                    str(k) not in column[j] and
                    flag and
                    str(k) not in square[i // 3][j // 3]):

                    position[l] = (k + 1) * 100 + i * 10 + j
                    l += 1
                    array[j][i] = k
                    combinations += 1
                    square[i // 3][j // 3] += str(k)
                    line[i] += str(k)
                    column[j] += str(k)
                    break

                flag = True
                if k == 9 and array[j][i] == 0:
                    i = (position[l - 1] % 100 - position[l - 1] % 10) // 10
                    j = (position[l - 1] % 10) - 1
                    array[j + 1][i] = 0
                    square[i // 3][(j + 1) // 3] = square[i // 3][(j + 1) // 3][:-1]
                    line[i] = line[i][:-1]
                    column[j + 1] = column[j + 1][:-1]
                    l -= 1
                    break
            flag = True
        j += 1
    j = 0
    i += 1

for i in range(9):
    if i in [0, 3, 6]:
        print("-------------------------------")
    for j in range(9):
        if j % 3 == 0:
            print("| ", end="")
        if array[j][i] == 0:
            print(" , ", end="")
        else:
            if j not in [8, 5, 2]:
                print(f"{array[j][i]}, ", end="")
            else:
                print(f"{array[j][i]} ", end="")
        if j == 8:
            print("|")
print("-------------------------------")

elapsed_ms = int((time.time() - start) * 1000)
print(f"Elapsed(ms)={elapsed_ms}")
print(f"Elapsed(s)={elapsed_ms / 1000}")
print(f"Elapsed(min)={elapsed_ms / 60000}")
