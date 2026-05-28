import time


def print_sudoku(array):
    for row in range(9):
        if row in [0, 3, 6]:
            print("-------------------------")

        for col in range(9):
            if col in [0, 3, 6]:
                print("| ", end="")

            value = array[col][row]
            print(". " if value == 0 else f"{value} ", end="")

        print("|")

    print("-------------------------")


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

array = [[0 for _ in range(9)] for _ in range(9)]

for row in range(9):
    for col in range(9):
        array[col][row] = sudoku[row][col]

start = time.time()

line = ["" for _ in range(9)]
column = ["" for _ in range(9)]
square = [["" for _ in range(3)] for _ in range(3)]

# position zapamietuje stan cofania:
# (nastepna_cyfra_do_sprawdzenia * 100) + (row * 10) + col
position = [0 for _ in range(81)]

# Cyfry, ktore sa juz w kazdym wierszu.
for row in range(9):
    for col in range(9):
        if array[col][row] != 0:
            line[row] += str(array[col][row])

# Cyfry, ktore sa juz w kazdej kolumnie.
for col in range(9):
    for row in range(9):
        if array[col][row] != 0:
            column[col] += str(array[col][row])

# Cyfry, ktore sa juz w kazdym kwadracie 3x3.
for row in range(9):
    for col in range(9):
        if array[col][row] != 0:
            square[row // 3][col // 3] += str(array[col][row])

empty_index = 0
row = 0
col = 0
operations = 0
can_try_number = True

while row < 9:
    while col < 9:
        if array[col][row] == 0:
            if position[empty_index] == 0:
                position[empty_index] = 100

            if position[empty_index] // 100 == 10:
                can_try_number = False
                position[empty_index] -= 100

            for value in range(position[empty_index] // 100, 10):
                if position[empty_index] != 0:
                    position[empty_index] = 0

                if (
                    str(value) not in line[row]
                    and str(value) not in column[col]
                    and str(value) not in square[row // 3][col // 3]
                    and can_try_number
                ):
                    position[empty_index] = (value + 1) * 100 + row * 10 + col
                    empty_index += 1
                    array[col][row] = value
                    operations += 1

                    line[row] += str(value)
                    column[col] += str(value)
                    square[row // 3][col // 3] += str(value)
                    break

                can_try_number = True

                if value == 9 and array[col][row] == 0:
                    previous_position = position[empty_index - 1]

                    row = (previous_position % 100 - previous_position % 10) // 10
                    col = (previous_position % 10) - 1

                    removed_col = col + 1
                    removed_value = array[removed_col][row]
                    array[removed_col][row] = 0

                    line[row] = line[row].replace(str(removed_value), "", 1)
                    column[removed_col] = column[removed_col].replace(
                        str(removed_value),
                        "",
                        1
                    )
                    square[row // 3][removed_col // 3] = square[row // 3][removed_col // 3].replace(
                        str(removed_value),
                        "",
                        1
                    )

                    empty_index -= 1
                    break

            can_try_number = True

        col += 1

    col = 0
    row += 1

print_sudoku(array)

elapsed_ms = int((time.time() - start) * 1000)
print(f"Operations={operations}")
print(f"Elapsed(ms)={elapsed_ms}")
