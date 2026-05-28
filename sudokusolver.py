import time
import tkinter as tk

import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# KONFIGURACJA
# ============================================================

#size of the final ss of a cell
TEMPLATE_SIZE = 40
CELL_SIZE = 60
BOARD_SIZE = CELL_SIZE * 9
ANIMATION_DELAY_MS = 40
MIN_ANIMATION_DELAY_MS = 1
MAX_ANIMATION_DELAY_MS = 300


# ============================================================
# WYKRYWANIE OBRAZU I ROZPOZNAWANIE CYFR
# ============================================================

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


# ============================================================
# FUNKCJE POMOCNICZE DO WYPISYWANIA I KOPIOWANIA PLANSZY
# ============================================================

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


def copy_board(board):
    return [column[:] for column in board]


# ============================================================
# ALGORYTM BACKTRACKING
# ============================================================

def find_empty_cell(board):
    for row in range(9):
        for col in range(9):
            if board[col][row] == 0:
                return row, col

    return None


def can_place(board, row, col, value):
    for index in range(9):
        if board[index][row] == value:
            return False

        if board[col][index] == value:
            return False

    box_row = (row // 3) * 3
    box_col = (col // 3) * 3

    for current_row in range(box_row, box_row + 3):
        for current_col in range(box_col, box_col + 3):
            if board[current_col][current_row] == value:
                return False

    return True


def solve_sudoku_steps(board):
    empty_cell = find_empty_cell(board)

    if empty_cell is None:
        return True

    row, col = empty_cell

    for value in range(1, 10):
        if can_place(board, row, col, value):
            board[col][row] = value
            yield "place", row, col, value

            solved = yield from solve_sudoku_steps(board)

            if solved:
                return True

            board[col][row] = 0
            yield "remove", row, col, 0

    return False


def solve_sudoku(board):
    for _ in solve_sudoku_steps(board):
        pass

    return board


def print_solved_sudoku(array):
    print("Solved Sudoku: ")

    for row in range(9):
        if row in [0, 3, 6]:
            print("-------------------------------")

        for col in range(9):
            if col % 3 == 0:
                print("| ", end="")

            if array[col][row] == 0:
                print(" , ", end="")
            elif col not in [8, 5, 2]:
                print(f"{array[col][row]}, ", end="")
            else:
                print(f"{array[col][row]} ", end="")

            if col == 8:
                print("|")

    print("-------------------------------")


# ============================================================
# WYSWIETLANIE OKNA APLIKACJI I ANIMACJA ROZWIAZYWANIA
# ============================================================

class SudokuVisualizer:
    def __init__(self, board):
        self.board = copy_board(board)
        self.original = copy_board(board)
        self.steps = solve_sudoku_steps(self.board)
        self.step_count = 0
        self.start_time = time.time()

        self.root = tk.Tk()
        self.root.title("Sudoku backtracking visualizer")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=BOARD_SIZE,
            height=BOARD_SIZE,
            bg="#f8fafc",
            highlightthickness=0
        )
        self.canvas.pack(padx=16, pady=(16, 8))

        self.status = tk.StringVar(value="Starting backtracking...")
        tk.Label(
            self.root,
            textvariable=self.status,
            font=("Segoe UI", 11),
            anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 16))

        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=16, pady=(0, 16))

        tk.Label(
            controls,
            text="Speed",
            font=("Segoe UI", 10)
        ).pack(side="left")

        self.speed = tk.IntVar(value=80)
        tk.Scale(
            controls,
            from_=1,
            to=100,
            orient="horizontal",
            variable=self.speed,
            showvalue=True,
            length=260
        ).pack(side="left", fill="x", expand=True, padx=(12, 0))

        self.cell_backgrounds = {}
        self.cell_texts = {}
        self.draw_board()
        self.root.after(500, self.animate)

    def draw_board(self):
        for row in range(9):
            for col in range(9):
                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                fill = "#e2e8f0" if self.original[col][row] != 0 else "#ffffff"
                rect = self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline="#cbd5e1"
                )
                self.cell_backgrounds[(row, col)] = rect

                value = self.original[col][row]
                text = self.canvas.create_text(
                    x1 + CELL_SIZE / 2,
                    y1 + CELL_SIZE / 2,
                    text="" if value == 0 else str(value),
                    fill="#0f172a" if value != 0 else "#2563eb",
                    font=("Segoe UI", 22, "bold" if value != 0 else "normal")
                )
                self.cell_texts[(row, col)] = text

        for index in range(10):
            width = 3 if index % 3 == 0 else 1
            color = "#0f172a" if index % 3 == 0 else "#cbd5e1"
            offset = index * CELL_SIZE

            self.canvas.create_line(
                offset,
                0,
                offset,
                BOARD_SIZE,
                fill=color,
                width=width
            )
            self.canvas.create_line(
                0,
                offset,
                BOARD_SIZE,
                offset,
                fill=color,
                width=width
            )

    def set_cell(self, row, col, value, action):
        if self.original[col][row] != 0:
            return

        if action == "place":
            background = "#dcfce7"
            color = "#166534"
            text = str(value)
        else:
            background = "#fee2e2"
            color = "#991b1b"
            text = ""

        self.canvas.itemconfigure(
            self.cell_backgrounds[(row, col)],
            fill=background
        )
        self.canvas.itemconfigure(
            self.cell_texts[(row, col)],
            text=text,
            fill=color
        )

        self.root.after(
            self.get_delay(),
            lambda: self.canvas.itemconfigure(
                self.cell_backgrounds[(row, col)],
                fill="#ffffff"
            )
        )

    def get_delay(self):
        speed = self.speed.get()
        delay_range = MAX_ANIMATION_DELAY_MS - MIN_ANIMATION_DELAY_MS

        return MAX_ANIMATION_DELAY_MS - int((speed - 1) * delay_range / 99)

    def animate(self):
        try:
            action, row, col, value = next(self.steps)
        except StopIteration as stop:
            elapsed_ms = int((time.time() - self.start_time) * 1000)
            result = "Solved" if stop.value else "No solution"
            self.status.set(f"{result}. Steps={self.step_count}, elapsed={elapsed_ms} ms")

            if stop.value:
                print_solved_sudoku(self.board)

            return

        if action == "place":
            self.step_count += 1
        self.set_cell(row, col, value, action)
        self.status.set(
            f"Step {self.step_count}: {action} "
            f"{value if value else ''} at row {row + 1}, column {col + 1}"
        )
        self.root.after(self.get_delay(), self.animate)

    def run(self):
        self.root.mainloop()


# ============================================================
# URUCHOMIENIE PROGRAMU
# ============================================================

def main():
    image_path = "sudoku2.png"

    array, line = read_sudoku_from_image(image_path)

    print("Data for solver")
    print(line)

    print("Recognised field")
    print_sudoku(array)

    visualizer = SudokuVisualizer(array)
    visualizer.run()


if __name__ == "__main__":
    main()
