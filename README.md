# Reddy's Quest: Against Python

An educational desktop game developed with Python and Pygame to help beginners learn fundamental Python programming concepts through interactive puzzles.

## Overview

**Reddy's Quest: Against Python** is an educational game developed as part of my university thesis at the Department of Digital Systems, University of Thessaly.

The player progresses through a series of programming puzzles by writing and executing Python code directly inside the game. Each puzzle focuses on a specific Python concept and provides immediate feedback through visual and audio elements.

The game is designed mainly for beginners and students aged 12–16.

## Features

* 8 interactive Python programming puzzles
* Integrated multiline code editor
* Line numbering and basic editor controls
* Automatic code and output validation
* AST-based validation of submitted code
* Restricted execution environment for user code
* Output capture using `io.StringIO` and `contextlib.redirect_stdout`
* Execution timeout
* Hints and progressive assistance
* Star-based scoring system
* Visual and audio feedback
* Particle effects and animations
* Interactive game progression and quest map

## Python Concepts Covered

| Level | Concept                                 |
| ----: | --------------------------------------- |
|     1 | `print()`                               |
|     2 | Variables                               |
|     3 | Arithmetic operations                   |
|     4 | `if / else`                             |
|     5 | `if / elif / else`                      |
|     6 | `while` loops                           |
|     7 | `for` loops and `range()`               |
|     8 | `for` loops with conditional statements |

## Code Validation and Execution

Before executing the code submitted by the player, the game parses it using Python's **Abstract Syntax Tree (AST)** module.

The validation system checks for restricted operations and constructs, including:

* `import` statements
* access to restricted built-in functions
* attribute access
* `while True`
* `break` and `continue`

The game also executes submitted code with a limited set of built-in functions and captures `print()` output in memory for comparison with the expected result.

An execution timeout is also used to prevent the game from waiting indefinitely for a submitted program.

> The execution environment is designed as a restriction mechanism for this educational application and is not intended to provide a production-grade security sandbox.

## Technologies

* Python
* Pygame
* Abstract Syntax Tree (AST)
* Threading
* `io.StringIO`
* `contextlib`

## Installation

### Requirements

* Python 3.12 recommended
* Pygame

### Setup

Clone the repository and install Pygame:

```bash
pip install pygame
```

Run the game with:

```bash
python ReddysQuest.py
```

## Controls

* **Space** — Continue dialogue / start puzzle
* **Ctrl + Enter** — Run submitted code
* **Enter** — Move to the next line in the editor
* **Tab** — Insert indentation
* **Arrow keys** — Move the cursor
* **Mouse wheel** — Scroll through code and output

## Project Context

This project was developed as part of my university thesis:

**Development of an Educational Game for Learning Python through Interactive Puzzles**

Department of Digital Systems
University of Thessaly

## Author

**Vasileios Ladopoulos**

GitHub: [@vladopoulos](https://github.com/vladopoulos)
