import time


def find_empty_cell(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                return row, col

    return None


def can_place(board, row, col, value):
    for index in range(9):
        if board[row][index] == value:
            return False

        if board[index][col] == value:
            return False

    box_row = (row // 3) * 3
    box_col = (col // 3) * 3

    for current_row in range(box_row, box_row + 3):
        for current_col in range(box_col, box_col + 3):
            if board[current_row][current_col] == value:
                return False

    return True


operations = 0


def solve_sudoku(board):
    global operations

    empty_cell = find_empty_cell(board)

    if empty_cell is None:
        return True

    row, col = empty_cell

    for value in range(1, 10):
        if can_place(board, row, col, value):
            board[row][col] = value
            operations += 1

            if solve_sudoku(board):
                return True

            board[row][col] = 0

    return False


def print_sudoku(board):
    for row in range(9):
        if row in [0, 3, 6]:
            print("-------------------------")

        for col in range(9):
            if col in [0, 3, 6]:
                print("| ", end="")

            value = board[row][col]
            print(". " if value == 0 else f"{value} ", end="")

        print("|")

    print("-------------------------")


if __name__ == "__main__":
    sudoku = [
        [0, 0, 0, 3, 8, 0, 0, 0, 0],
        [7, 0, 0, 0, 0, 6, 0, 0, 0],
        [0, 1, 0, 4, 7, 0, 0, 9, 0],
        [0, 6, 0, 7, 3, 0, 0, 0, 5],
        [3, 0, 4, 0, 0, 1, 0, 2, 0],
        [0, 0, 0, 0, 4, 0, 7, 0, 0],
        [0, 0, 1, 0, 9, 4, 0, 0, 2],
        [8, 0, 0, 0, 0, 3, 5, 0, 0],
        [6, 0, 9, 0, 0, 0, 0, 3, 0],
    ]

    start = time.time()

    if solve_sudoku(sudoku):
        elapsed_ms = int((time.time() - start) * 1000)
        print_sudoku(sudoku)
        print(f"Operations={operations}")
        print(f"Elapsed(ms)={elapsed_ms}")
        print(f"Elapsed(s)={elapsed_ms / 1000}")
    else:
        elapsed_ms = int((time.time() - start) * 1000)
        print("Brak rozwiazania.")
        print(f"Operations={operations}")
        print(f"Elapsed(ms)={elapsed_ms}")
