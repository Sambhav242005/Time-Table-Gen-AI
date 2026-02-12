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
from ui.pages.teacher_page import TeacherPage
from ui.pages.subject_page import SubjectPage
from ui.pages.section_page import SectionPage
from ui.pages.room_page import RoomPage
from ui.pages.generation_page import GenerationPage
from ui.pages.view_page import ViewPage
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
        self.home_page = self.create_home_page()
        self.setup_page = self.create_setup_page()
        self.teacher_page = TeacherPage()
        self.subject_page = SubjectPage()
        self.section_page = SectionPage()
        self.room_page = RoomPage()
        self.generate_page = GenerationPage(self.start_generation)
        self.view_page = ViewPage()

        self.content_stack.addWidget(self.home_page)      # 0
        self.content_stack.addWidget(self.setup_page)     # 1
        self.content_stack.addWidget(self.teacher_page)  # 2
        self.content_stack.addWidget(self.subject_page)  # 3
        self.content_stack.addWidget(self.section_page)  # 4
        self.content_stack.addWidget(self.room_page)     # 5
        self.content_stack.addWidget(self.generate_page)  # 6
        self.content_stack.addWidget(self.view_page)      # 7

    def navigate_to_page(self, page_index):
        self.content_stack.setCurrentIndex(page_index)
        if page_index == 7:  # View page
            self.view_page.update_view(self.generated_timetables)

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
                self.teacher_page.get_data(),
                self.subject_page.get_data(),
                self.section_page.get_data(),
                self.room_page.get_data()
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
            teachers, subjects, sections, rooms = TimetableJSONParser.deserialize_data(data)
            self.teacher_page.set_data(teachers)
            self.subject_page.set_data(subjects)
            self.section_page.set_data(sections)
            self.room_page.set_data(rooms)
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

    # ---------------- DATA UPDATES ----------------
    def setup_sample_data(self):
        """Sample data setup."""
        teachers = [
            Teacher(1, "Dr. John Smith", "JS", 6, 20),
            Teacher(2, "Prof. Sarah Wilson", "SW", 5, 18)
        ]
        
        subjects = [
            Subject(1, "MATH101", "Mathematics I", 4, theory_lectures_per_week=4, lab_hours_per_week=0, lab_batch_size=0),
            Subject(2, "PHY101", "Physics I", 3, theory_lectures_per_week=2, lab_hours_per_week=2, lab_batch_size=20),
            Subject(3, "PHY101(p)", "Physics I (Lab)", 3, theory_lectures_per_week=0, lab_hours_per_week=2, lab_batch_size=20),
            Subject(4, "CS101", "Computer Science I", 4, theory_lectures_per_week=3, lab_hours_per_week=2, lab_batch_size=25),
            Subject(5, "CS101(p)", "Computer Science I (Lab)", 4, theory_lectures_per_week=0, lab_hours_per_week=2, lab_batch_size=25),
        ]
        
        sections = [
            Section(1, "CSE-1A", 1, 60)
        ]
        
        rooms = [
            Room(1, "Room 101", 70, RoomType.CLASSROOM),
            Room(2, "Physics Lab", 30, RoomType.LAB, "Physics"),
            Room(3, "Computer Lab 1", 30, RoomType.LAB, "Computer Science"),
        ]
        
        self.teacher_page.set_data(teachers)
        self.subject_page.set_data(subjects)
        self.section_page.set_data(sections)
        self.room_page.set_data(rooms)

    def initialize_sample_data(self):
        self.setup_sample_data()
        QMessageBox.information(self, "Initialized", "Sample data created!")

    # ---------------- GENERATION THREAD ----------------
    def start_generation(self):
        teachers = self.teacher_page.get_data()
        subjects = self.subject_page.get_data()
        sections = self.section_page.get_data()
        rooms = self.room_page.get_data()

        if not teachers or not subjects or not sections or not rooms:
            QMessageBox.warning(self, "Missing Data", "Please setup all data before generation.")
            return

        config = {
            "teachers": teachers,
            "subjects": subjects,
            "sections": [s.name for s in sections],
            "rooms": rooms
        }
        self.generation_thread = TimetableGeneratorThread(config)
        self.generation_thread.generation_completed.connect(self.on_generation_completed)
        self.generation_thread.start()

    def on_generation_completed(self, timetables):
        self.generated_timetables = timetables
        TimetableJSONParser.save_to_json("output/generated_timetables.json", timetables)
        QMessageBox.information(self, "Success", "Timetables generated and saved to JSON!")
        self.view_page.update_view(self.generated_timetables)
        self.navigate_to_page(7)

    # ---------------- UTILS ----------------
    def get_button_style(self, color):
        return f"""
        QPushButton {
            background-color: {color};
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: {color}dd;
        }
        """


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main_win = AdvancedTimetableApp()
    main_win.show()
    sys.exit(app.exec_())
