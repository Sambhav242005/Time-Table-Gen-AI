import random
import json
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMenu, QStackedWidget, QTextEdit, QMessageBox, QLineEdit,
    QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem, QDialog, QFileDialog,
    QScrollArea, QFrame, QComboBox, QTabWidget, QProgressBar, QSplitter,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QTimeEdit, QDateEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.generator_thread import TimetableGeneratorThread
from core.json_parser import TimetableJSONParser
from core.dataframe_parser import dataframe_to_objects
from core.data_models import Room, RoomType, Section, Subject, Teacher
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet


class AdvancedTimetableApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Timetable Generator")
        self.setGeometry(100, 100, 1200, 800)

        # Data storage
        self.teachers = []
        self.subjects = []
        self.sections = []
        self.rooms = []
        self.generated_timetables = {}

        # Thread for generation
        self.generation_thread = None

        self.initUI()
        self.setup_sample_data()

    # ---------------- UI SETUP ----------------
    def initUI(self):
        """Initialize user interface."""
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        # Header + Stack
        header = self.create_header()
        self.content_stack = QStackedWidget()
        self.populate_content_pages()

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(self.content_stack)
        layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(layout)

    def create_header(self):
        """Header with navigation."""
        header = QWidget()
        header_layout = QHBoxLayout()
        header.setStyleSheet("background-color: #301934; padding: 10px;")

        title_label = QLabel("ADVANCED TIMETABLE GENERATOR")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        nav_links = [
            ("HOME", 0), ("SETUP", 1), ("TEACHERS", 2), ("SUBJECTS", 3),
            ("SECTIONS", 4), ("ROOMS", 5), ("GENERATE", 6), ("VIEW", 7)
        ]
        for name, index in nav_links:
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    color: white; background: none; border: none;
                    font-size: 14px; padding: 8px 16px;
                }
                QPushButton:hover { background-color: rgba(255,255,255,0.1); }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, idx=index: self.navigate_to_page(idx))
            header_layout.addWidget(btn)

        header.setLayout(header_layout)
        return header

    def populate_content_pages(self):
        """Add content pages to the stack."""
        self.content_stack.addWidget(self.create_home_page())      # 0
        self.content_stack.addWidget(self.create_setup_page())     # 1
        self.content_stack.addWidget(self.create_teachers_page())  # 2
        self.content_stack.addWidget(self.create_subjects_page())  # 3
        self.content_stack.addWidget(self.create_sections_page())  # 4
        self.content_stack.addWidget(self.create_rooms_page())     # 5
        self.content_stack.addWidget(self.create_generate_page())  # 6
        self.content_stack.addWidget(self.create_view_page())      # 7

    def navigate_to_page(self, page_index):
        self.content_stack.setCurrentIndex(page_index)
        if page_index == 7:  # View page
            self.update_view_page()

    # ---------------- HOME PAGE ----------------
    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        title = QLabel("ADVANCED TIMETABLE GENERATOR")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc = QLabel("Automated scheduling with constraints, teacher loads, and optimization.")
        desc.setFont(QFont("Arial", 14))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()
        page.setLayout(layout)
        return page

    # ---------------- SETUP PAGE ----------------
    def create_setup_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        title = QLabel("INITIAL SETUP")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #301934; margin: 20px;")

        # Quick setup
        quick_setup = self.create_quick_setup_form()
        layout.addWidget(title)
        layout.addWidget(quick_setup)

        # JSON import/export buttons
        json_buttons = QHBoxLayout()
        export_btn = QPushButton("Export Data to JSON")
        export_btn.setStyleSheet(self.get_button_style("#007bff"))
        export_btn.clicked.connect(self.export_data_to_json)

        import_btn = QPushButton("Import Data from JSON")
        import_btn.setStyleSheet(self.get_button_style("#6f42c1"))
        import_btn.clicked.connect(self.import_data_from_json)

        json_buttons.addStretch()
        json_buttons.addWidget(export_btn)
        json_buttons.addWidget(import_btn)

        df_to_json_btn = QPushButton("Convert Teachers DataFrame to JSON")
        df_to_json_btn.setStyleSheet(self.get_button_style("#17a2b8"))
        df_to_json_btn.clicked.connect(self.convert_teachers_df_to_json)
        json_buttons.addWidget(df_to_json_btn)
        
        json_buttons.addStretch()

        layout.addLayout(json_buttons)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def create_quick_setup_form(self):
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; padding: 20px;")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.semesters_spin = QSpinBox()
        self.semesters_spin.setRange(1, 8)
        self.semesters_spin.setValue(4)
        self.sections_per_sem_spin = QSpinBox()
        self.sections_per_sem_spin.setRange(1, 10)
        self.sections_per_sem_spin.setValue(2)
        self.slots_per_day_spin = QSpinBox()
        self.slots_per_day_spin.setRange(4, 10)
        self.slots_per_day_spin.setValue(6)

        form_layout.addRow("Number of Semesters:", self.semesters_spin)
        form_layout.addRow("Sections per Semester:", self.sections_per_sem_spin)
        form_layout.addRow("Slots per Day:", self.slots_per_day_spin)

        init_button = QPushButton("Initialize with Sample Data")
        init_button.setStyleSheet(self.get_button_style("#301934"))
        init_button.clicked.connect(self.initialize_sample_data)

        layout.addLayout(form_layout)
        layout.addWidget(init_button)
        form_widget.setLayout(layout)
        return form_widget

    # ---------------- JSON IMPORT / EXPORT ----------------
    def export_data_to_json(self):
        """Export all timetable setup data to JSON file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Data as JSON", "", "JSON Files (*.json)"
            )
            if not file_path:
                return

            structured_data = TimetableJSONParser.serialize_data(
                self.teachers, self.subjects, self.sections, self.rooms
            )
            TimetableJSONParser.save_to_json(file_path, structured_data)
            QMessageBox.information(self, "Export Successful", f"Data saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def import_data_from_json(self):
        """Import timetable setup data from a JSON file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Data from JSON", "", "JSON Files (*.json)"
            )
            if not file_path:
                return

            data = TimetableJSONParser.load_from_json(file_path)
            self.teachers, self.subjects, self.sections, self.rooms = TimetableJSONParser.deserialize_data(data)
            self.update_all_tables()
            QMessageBox.information(self, "Import Successful", "Data imported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))

    def convert_teachers_df_to_json(self):
        """Demonstrates converting a DataFrame to JSON."""
        try:
            # 1. Create a sample DataFrame
            teacher_data = {
                "id": [3, 4],
                "name": ["Dr. Emily White", "Prof. David Green"],
                "code": ["EW", "DG"],
                "max_daily_load": [5, 6],
                "max_weekly_load": [18, 22],
            }
            teachers_df = pd.DataFrame(teacher_data)

            # 2. Convert DataFrame to objects
            teacher_objects = dataframe_to_objects(teachers_df, Teacher)

            # 3. Serialize objects to a JSON-compatible dict
            # We can reuse the existing serializer, but we'll just serialize teachers for this example
            structured_data = {
                "teachers": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "code": t.code,
                        "max_daily_load": t.max_daily_load,
                        "max_weekly_load": t.max_weekly_load
                    }
                    for t in teacher_objects
                ]
            }

            # 4. Save to JSON
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Teachers DF as JSON", "", "JSON Files (*.json)"
            )
            if not file_path:
                return

            TimetableJSONParser.save_to_json(file_path, structured_data)
            QMessageBox.information(
                self, "Conversion Successful", f"Teachers DataFrame data saved to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Conversion Failed", str(e))

    # ---------------- TABLE SETUP PAGES ----------------
    def create_teachers_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("TEACHERS MANAGEMENT")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title)
        self.teachers_table = QTableWidget()
        self.teachers_table.setColumnCount(4)
        self.teachers_table.setHorizontalHeaderLabels(["Name", "Code", "Max Daily", "Weekly"])
        layout.addWidget(self.teachers_table)
        self.update_teachers_table()
        page.setLayout(layout)
        return page

    def create_subjects_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("SUBJECTS MANAGEMENT")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title)
        self.subjects_table = QTableWidget()
        self.subjects_table.setColumnCount(5)
        self.subjects_table.setHorizontalHeaderLabels(["Code", "Name", "Credits", "Slots", "Lab"])
        layout.addWidget(self.subjects_table)
        self.update_subjects_table()
        page.setLayout(layout)
        return page

    def create_sections_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("SECTIONS MANAGEMENT")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title)
        self.sections_table = QTableWidget()
        self.sections_table.setColumnCount(3)
        self.sections_table.setHorizontalHeaderLabels(["Name", "Semester", "Strength"])
        layout.addWidget(self.sections_table)
        self.update_sections_table()
        page.setLayout(layout)
        return page

    def create_rooms_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("ROOMS MANAGEMENT")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title)
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(4)
        self.rooms_table.setHorizontalHeaderLabels(["Name", "Type", "Capacity", "Lab Type"])
        layout.addWidget(self.rooms_table)
        self.update_rooms_table()
        page.setLayout(layout)
        return page

    # ---------------- GENERATION PAGE ----------------
    def create_generate_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("GENERATE TIMETABLES")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        self.generate_btn = QPushButton("GENERATE")
        self.generate_btn.setStyleSheet(self.get_button_style("#28a745"))
        self.generate_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        page.setLayout(layout)
        return page

    def create_view_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title = QLabel("VIEW GENERATED TIMETABLES")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.view_tabs = QTabWidget()
        
        layout.addWidget(title)
        layout.addWidget(self.view_tabs)
        page.setLayout(layout)
        return page

    # ---------------- DATA UPDATES ----------------
    def setup_sample_data(self):
        """Sample data setup."""
        self.teachers = [
            Teacher(1, "Dr. John Smith", "JS", 6, 20),
            Teacher(2, "Prof. Sarah Wilson", "SW", 5, 18)
        ]
        self.subjects = [
            Subject(1, "MATH101", "Mathematics I", 4, 4),
            Subject(2, "PHY101", "Physics I", 3, 3)
        ]
        self.sections = [Section(1, "CSE-1A", 1, 60)]
        self.rooms = [Room(1, "Room 101", 70, RoomType.CLASSROOM)]
        self.update_all_tables()

    def initialize_sample_data(self):
        self.setup_sample_data()
        QMessageBox.information(self, "Initialized", "Sample data created!")

    def update_all_tables(self):
        self.update_teachers_table()
        self.update_subjects_table()
        self.update_sections_table()
        self.update_rooms_table()

    def update_teachers_table(self):
        self.teachers_table.setRowCount(len(self.teachers))
        for i, t in enumerate(self.teachers):
            self.teachers_table.setItem(i, 0, QTableWidgetItem(str(t.name)))
            self.teachers_table.setItem(i, 1, QTableWidgetItem(str(t.code)))
            self.teachers_table.setItem(i, 2, QTableWidgetItem(str(t.max_daily_load)))
            self.teachers_table.setItem(i, 3, QTableWidgetItem(str(t.max_weekly_load)))

    def update_subjects_table(self):
        self.subjects_table.setRowCount(len(self.subjects))
        for i, s in enumerate(self.subjects):
            self.subjects_table.setItem(i, 0, QTableWidgetItem(str(s.code)))
            self.subjects_table.setItem(i, 1, QTableWidgetItem(str(s.name)))
            self.subjects_table.setItem(i, 2, QTableWidgetItem(str(s.credits)))
            self.subjects_table.setItem(i, 3, QTableWidgetItem(str(s.weekly_lecture_slots)))
            self.subjects_table.setItem(i, 4, QTableWidgetItem("Yes" if s.is_lab else "No"))

    def update_sections_table(self):
        self.sections_table.setRowCount(len(self.sections))
        for i, s in enumerate(self.sections):
            self.sections_table.setItem(i, 0, QTableWidgetItem(str(s.name)))
            self.sections_table.setItem(i, 1, QTableWidgetItem(str(s.semester)))
            self.sections_table.setItem(i, 2, QTableWidgetItem(str(s.strength)))
            
    def update_rooms_table(self):
        self.rooms_table.setRowCount(len(self.rooms))
        for i, r in enumerate(self.rooms):
            self.rooms_table.setItem(i, 0, QTableWidgetItem(str(r.name)))
            self.rooms_table.setItem(i, 1, QTableWidgetItem(str(r.type.value)))
            self.rooms_table.setItem(i, 2, QTableWidgetItem(str(r.capacity)))
            self.rooms_table.setItem(i, 3, QTableWidgetItem(str(r.lab_type or "N/A")))

    def update_view_page(self):
        self.view_tabs.clear()
        if not self.generated_timetables:
            return

        for section_name, timetable in self.generated_timetables.items():
            table = self._create_timetable_table(timetable)
            self.view_tabs.addTab(table, section_name)

    def _create_timetable_table(self, timetable_data):
        if not timetable_data:
            return QLabel("No timetable generated for this section.")

        days = list(timetable_data.keys())
        if not days:
            return QLabel("Timetable data is empty.")
            
        slots = list(timetable_data[days[0]].keys())
        
        table = QTableWidget(len(slots), len(days))
        table.setHorizontalHeaderLabels(days)
        table.setVerticalHeaderLabels(slots)

        for day_idx, day in enumerate(days):
            for slot_idx, slot in enumerate(slots):
                entry = timetable_data[day][slot]
                if entry:
                    item_text = f"{entry['subject']}\n({entry['teacher']})\n[{entry['room']}]"
                    table.setItem(slot_idx, day_idx, QTableWidgetItem(item_text))
        
        table.resizeRowsToContents()
        table.resizeColumnsToContents()
        return table

    # ---------------- GENERATION THREAD ----------------
    def start_generation(self):
        if not self.teachers or not self.subjects or not self.sections or not self.rooms:
            QMessageBox.warning(self, "Missing Data", "Please setup all data before generation.")
            return

        config = {
            "teachers": self.teachers,
            "subjects": self.subjects,
            "sections": [s.name for s in self.sections],
            "rooms": self.rooms
        }
        self.generation_thread = TimetableGeneratorThread(config)
        self.generation_thread.generation_completed.connect(self.on_generation_completed)
        self.generation_thread.start()

    def on_generation_completed(self, timetables):
        self.generated_timetables = timetables
        TimetableJSONParser.save_to_json("output/generated_timetables.json", timetables)
        QMessageBox.information(self, "Success", "Timetables generated and saved to JSON!")
        self.update_view_page()
        self.navigate_to_page(7)

    # ---------------- UTILS ----------------
    def get_button_style(self, color):
        return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {color}dd;
        }}
        """
