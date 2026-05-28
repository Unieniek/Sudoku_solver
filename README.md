# Sudoku Solver with Image Recognition

This project is a Python program that solves Sudoku puzzles automatically.  
The program can read a Sudoku board from an image, recognize the digits on the board, convert them into a format usable by the solver, and then solve the puzzle using a backtracking algorithm.

## Features

- Reads a Sudoku board from an image file
- Detects digits in each Sudoku cell
- Converts the board into a 9x9 array
- Uses `0` for empty cells
- Solves the Sudoku puzzle automatically
- Prints the recognized board before solving
- Prints the solved Sudoku board
- Measures and displays the solving time

## How to turn it on

- download dependencies by using this chain of commands in bash
- python -m venv .venv
- source .venv/Scripts/activate
- pip install -r requirements.txt
- python sudokusolver.py

## How It Works

The program has two main parts:

1. **Image processing and digit recognition**
2. **Sudoku solving algorithm**

First, the image of the Sudoku board is loaded using OpenCV.  
The board is resized to `450x450` pixels, so each cell has a size of `50x50` pixels.

Each cell is processed separately. The program removes the cell borders, converts the cell to a black-and-white image, removes noise, and extracts the digit if one exists.

The extracted digit is normalized to a `40x40` image. This makes it easier to compare it with generated digit templates.

The program creates digit templates for numbers from `1` to `9` using system fonts. Each detected digit is compared with those templates. If the similarity score is high enough, the digit is accepted. Otherwise, the cell is treated as empty and saved as `0`.

After the board is recognized, the program passes the data to the Sudoku solver.

## Digit Recognition Process

The digit recognition process contains several steps:

```text
cell image
→ convert to grayscale
→ remove cell borders
→ blur image
→ convert to binary image
→ remove noise
→ extract digit
→ resize and center digit
→ compare with templates
→ return recognized digit
```

## Solving Algorithm
Solver uses a simple backtracking algorithm that tries every possible combination until it finds the correct one 

Example input:
430500006008020019017000450860200070074800260109007830200178043001940007000650000

Output:
Data for solver
430500006008020019017000450860200070074800260109007830200178043001940007000650000

Recognised field
-------------------------
| 4 3 . | 5 . . | . . 6 |
| . . 8 | . 2 . | . 1 9 |
| . 1 7 | . . . | 4 5 . |
-------------------------
| 8 6 . | 2 . . | . 7 . |
| . 7 4 | 8 . . | 2 6 . |
| 1 . 9 | . . 7 | 8 3 . |
-------------------------
| 2 . . | 1 7 8 | . 4 3 |
| . . 1 | 9 4 . | . . 7 |
| . . . | 6 5 . | . . . |
-------------------------
Solved Sudoku:
-------------------------------
| 3, 1, 6 | 5, 4, 9 | 8, 2, 7 |
| 4, 8, 9 | 6, 7, 2 | 5, 3, 1 |
| 7, 5, 2 | 8, 3, 1 | 6, 4, 9 |
-------------------------------
| 6, 9, 1 | 2, 8, 4 | 7, 5, 3 |
| 5, 4, 7 | 3, 9, 6 | 2, 1, 8 |
| 2, 3, 8 | 1, 5, 7 | 4, 9, 6 |
-------------------------------
| 8, 7, 3 | 4, 1, 5 | 9, 6, 2 |
| 9, 2, 4 | 7, 6, 3 | 1, 8, 5 |
| 1, 6, 5 | 9, 2, 8 | 3, 7, 4 |
-------------------------------
Elapsed(ms)=3
Elapsed(s)=0.003
Elapsed(min)=5e-05
