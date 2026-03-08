# Timetable Generator AI

PyQt5 desktop application for generating university timetables using Google OR-Tools CP-SAT.

## Requirements

- Windows
- Python 3.12+

## Setup

```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```powershell
.\venv\Scripts\activate
python main.py
```

## How to Use the App

1. Open `SETUP` and click `Initialize with Sample Data` (or manually add your own data).
2. Configure entities in pages: `TEACHERS`, `SUBJECTS`, `SECTIONS`, `ROOMS`.
3. Open `GENERATE` and click `GENERATE`.
4. After success, open `VIEW` to inspect section/teacher/room timetables.
5. Export results from the UI as needed (JSON/PDF features are available in the app).

## Development Commands

```powershell
# Lint
ruff check .

# Auto-fix lint issues
ruff check --fix .

# Check one file
ruff check ui/main_window.py

# Syntax check
python -m py_compile core/generator_thread.py
```

## Project Structure

```text
Time-Table-Gen-AI/
├── main.py
├── core/
│   ├── data_models.py
│   ├── generator_thread.py
│   ├── solver_worker.py
│   ├── json_parser.py
│   └── dataframe_parser.py
├── ui/
│   ├── main_window.py
│   └── pages/
├── output/
├── requirements.txt
└── README.md
```

## Troubleshooting

- If timetable generation fails with OR-Tools errors:
  - Confirm you are running inside the project `venv`.
  - Reinstall dependencies:

```powershell
.\venv\Scripts\activate
pip install --force-reinstall --no-cache-dir -r requirements.txt
```

- Logs:
  - `generator.log`: solver/generation logs
  - `app.log`: UI/application logs
