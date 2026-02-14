# Project Overview

This project provides a comprehensive system for generating optimized timetables, catering to both interactive GUI-based management and high-performance command-line solving for complex scenarios.

It essentially comprises two distinct applications:

1. **GUI Timetable Generator**: A user-friendly desktop application built with PyQt5, allowing users to manage teachers, subjects, sections, and rooms. It uses an **event-based CP-SAT verification model** (not backtracking) for reliable timetable generation and includes features like multi-view timetables and PDF export.

2. **Advanced CLI Timetable Solver**: A powerful, standalone command-line application that leverages Google's OR-Tools CP-SAT solver for highly optimized timetable generation. This solver handles a wide array of hard and soft constraints, supports large datasets, and includes a "problem finder" to detect conflicts before solving. It is designed for more complex, real-world university timetabling problems.

**Key Technologies:**

* **Python**: Primary programming language.
* **PyQt5**: For the graphical user interface.
* **Google OR-Tools CP-SAT**: For advanced constraint programming and optimization in the CLI solver.
* **ReportLab**: For PDF generation in the GUI application.
* **Pandas/NumPy**: For data manipulation (inferred from `requirements.txt`).

# Building and Running

## Prerequisites

* Python 3.7 or higher

## Installation

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

This will install `PyQt5`, `reportlab`, `pandas`, and `numpy`.

## Running the Applications

### 1. GUI Timetable Generator

To run the interactive desktop application:

```bash
python main.py
```

Upon launching, you can interact with the UI to set up data, generate timetables, view results, and export PDFs. For a quick start, use the "SETUP" page to initialize sample data.

### 2. Advanced CLI Timetable Solver

This part of the system is designed for command-line execution and is typically used in two steps:

#### Step 1: Run the Problem Finder (Recommended)

First, run the `large_timetable_generator.py` script to generate a large dataset and detect potential conflicts or issues before solving.

```bash
python large_timetable_generator.py
```

This script will output detected problems (e.g., shared teacher conflicts, hour limit violations) and generate `large_dataset.json`. Review its output to understand any constraints or resource limitations.

#### Step 2: Solve the Timetable

After (optionally) running the problem finder, execute the main solver script:

```bash
python timetable_solver.py
```

This script will load data (by default, `example_dataset.json` or a generated `large_dataset.json` if `large_timetable_generator.py` was run), build the CP-SAT model, apply constraints, and attempt to find an optimal timetable. The results will be displayed in the console and potentially saved to a JSON file (e.g., `timetable_solution.json`).

# Development Conventions

* **Language**: Python is the sole programming language used throughout the project.
* **Code Structure**: The project is organized into `ui/` for the GUI components and `core/` for shared logic and data models. The advanced solver components (`timetable_solver.py`, `large_timetable_generator.py`) exist independently at the root level, indicating a distinct, performance-focused module.
* **Data Models**: `core/data_models.py` defines `dataclasses` for managing entities within the GUI application (Teacher, Subject, Section, Room). The advanced solver (`timetable_solver.py`) uses its own internal data structures.
* **Documentation**: Extensive Markdown documentation (`.md` files in the root) covers mathematical models, algorithms, complexity analysis, and guides for large datasets, particularly for the advanced solver.
* **Error Handling**: The `large_timetable_generator.py` script serves as a pre-solver problem detection mechanism, emphasizing early identification of constraints issues.
