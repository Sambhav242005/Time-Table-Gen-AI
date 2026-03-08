# AGENTS.md - Timetable Generator AI

## Project Overview

A PyQt5-based desktop application for automatically generating university timetables using Google OR-Tools CP-SAT solver. The project is located in `C:\Users\NPC\Desktop\Time-Table-Gen-AI`.

## Build & Run Commands

### Running the Application
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows

# Run the application
python main.py
```

### Linting & Type Checking
```bash
# Run ruff linter (recommended)
ruff check .

# Run ruff with auto-fix
ruff check --fix .

# Check specific file
ruff check ui/main_window.py

# Run ruff on a directory
ruff check core/
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Python Syntax Check
```bash
python -m py_compile <file.py>
```

---

## Code Style Guidelines

### General Principles
- Keep code concise and readable
- Avoid unnecessary comments (code should be self-documenting)
- Prefer explicit over implicit
- Handle errors gracefully with logging

### Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `class AdvancedTimetableApp` |
| Functions | snake_case | `def start_generation(self):` |
| Variables | snake_case | `teachers_dicts = []` |
| Constants | UPPER_SNAKE | `MAX_DAILY_LOAD = 6` |
| Private methods | _snake_case | `def _initialize_resources(self):` |

### Import Order (PEP 8)
```python
# 1. Standard library
import json
import math
import logging
import traceback

# 2. Third-party
from PyQt5.QtWidgets import QMainWindow, QWidget
from ortools.sat.python import cp_model

# 3. Local application
from core.data_models import Teacher, Subject, Room
from ui.pages.generation_page import GenerationPage
```

### Type Hints
- Use type hints for function parameters and return values
- Use `Optional[X]` instead of `X | None`
- Use `Dict`, `List` from typing (or modern `dict`, `list` with Python 3.9+)

```python
# Preferred
def get_data(self) -> list[Teacher]:
def process_config(config: dict) -> Optional[dict]:
```

### Dataclasses for Data Models
Use `@dataclass` for simple data containers:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Room:
    id: int
    name: str
    capacity: int
    type: RoomType
    lab_type: Optional[str] = None
```

### Error Handling
- Use try/except with specific exception types
- Always log errors with meaningful context
- Never let exceptions propagate silently in UI code

```python
try:
    self.generation_thread = TimetableGeneratorThread(config)
    self.generation_thread.start()
except ValueError as e:
    logger.error(f"Invalid configuration: {e}")
    QMessageBox.warning(self, "Error", str(e))
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
```

### Logging
- Use the `logging` module
- Create logger at module level: `logger = logging.getLogger(__name__)`
- Use appropriate log levels: DEBUG, INFO, WARNING, ERROR
- Include context in log messages

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Usage
logger.info("Starting generation process...")
logger.warning(f"Missing data for subject {subject_id}")
logger.error(f"Failed to parse data: {e}")
logger.exception(f"Unexpected error: {e}")  # Includes traceback
```

### PyQt5 Patterns
- Use signals/slots for thread-safe communication
- Always disable UI elements during long operations
- Re-enable UI in finally blocks or callbacks
- Use QThread for background tasks

```python
# Thread definition
class TimetableGeneratorThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(dict)
    generation_failed = pyqtSignal(str)

# Usage in main window
self.generation_thread.generation_completed.connect(self.on_generation_completed)
self.generation_thread.generation_failed.connect(self.on_generation_failed)
```

### File Organization
```
Time-Table-Gen-AI/
├── main.py                  # Application entry point
├── core/                    # Core business logic
│   ├── data_models.py       # Dataclasses
│   ├── generator_thread.py # Timetable generation
│   ├── json_parser.py      # JSON handling
│   └── ...
├── ui/                      # PyQt5 UI code
│   ├── main_window.py      # Main window
│   └── pages/              # Page widgets
├── output/                  # Generated timetables
└── requirements.txt         # Dependencies
```

### Key Dependencies
- `PyQt5` - GUI framework
- `ortools` - CP-SAT solver for scheduling
- `pandas` - Data handling
- `reportlab` - PDF generation

### Testing
- Currently no test framework configured
- To add tests, create `tests/` directory with pytest
- Run single test: `pytest tests/test_generator.py::test_name`
- Run with coverage: `pytest --cov=. --cov-report=html`

---

## Common Development Tasks

### Adding a New Page
1. Create `ui/pages/<name>_page.py` inheriting from `BasePage`
2. Implement required methods: `update_table()`, `add_item()`, `edit_item()`
3. Add page to `main_window.py:populate_content_pages()`
4. Add navigation button in `main_window.py:create_header()`

### Adding a New Data Model
1. Add dataclass in `core/data_models.py`
2. Add corresponding UI in relevant page class
3. Update serialization in `core/json_parser.py`

### Modifying Generation Algorithm
- Main logic in `core/generator_thread.py:_solve_cpsat()`
- Uses OR-Tools CP-SAT for constraint solving
- Constraints: teacher no-conflict, room no-conflict, section no-conflict

---

## Environment
- Python 3.12+
- Windows platform
- Virtual environment: `venv/`
