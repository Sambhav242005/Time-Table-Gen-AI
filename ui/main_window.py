import random
import json
import math
import logging
import traceback
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QMenu,
    QStackedWidget,
    QTextEdit,
    QMessageBox,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QFileDialog,
    QScrollArea,
    QFrame,
    QComboBox,
    QTabWidget,
    QProgressBar,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QFormLayout,
    QTimeEdit,
    QDateEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


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
            ("HOME", 0),
            ("SETUP", 1),
            ("TEACHERS", 2),
            ("SUBJECTS", 3),
            ("SECTIONS", 4),
            ("ROOMS", 5),
            ("GENERATE", 6),
            ("VIEW", 7),
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

        self.content_stack.addWidget(self.home_page)  # 0
        self.content_stack.addWidget(self.setup_page)  # 1
        self.content_stack.addWidget(self.teacher_page)  # 2
        self.content_stack.addWidget(self.subject_page)  # 3
        self.content_stack.addWidget(self.section_page)  # 4
        self.content_stack.addWidget(self.room_page)  # 5
        self.content_stack.addWidget(self.generate_page)  # 6
        self.content_stack.addWidget(self.view_page)  # 7

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
        desc = QLabel(
            "Automated scheduling with constraints, teacher loads, and optimization."
        )
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
        form_widget.setStyleSheet(
            "background-color: #f8f9fa; border-radius: 10px; padding: 20px;"
        )

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.semesters_spin = QSpinBox()
        self.semesters_spin.setRange(1, 8)
        self.semesters_spin.setValue(5)
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
                self.room_page.get_data(),
            )
            TimetableJSONParser.save_to_json(file_path, structured_data)
            QMessageBox.information(
                self, "Export Successful", f"Data saved to:\n{file_path}"
            )
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
            teachers, subjects, sections, rooms = TimetableJSONParser.deserialize_data(
                data
            )
            self.teacher_page.set_data(teachers)
            self.subject_page.set_data(subjects)
            self.section_page.set_data(sections)
            self.room_page.set_data(rooms)
            QMessageBox.information(
                self, "Import Successful", "Data imported successfully!"
            )
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
                        "max_weekly_load": t.max_weekly_load,
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
                self,
                "Conversion Successful",
                f"Teachers DataFrame data saved to:\n{file_path}",
            )

        except Exception as e:
            QMessageBox.critical(self, "Conversion Failed", str(e))

    # ---------------- DATA UPDATES ----------------
    def setup_sample_data(self):
        """Sample data setup using spin-box values."""
        num_semesters = self.semesters_spin.value()
        sections_per_sem = self.sections_per_sem_spin.value()

        # 15 teachers with varied load capacities
        teachers = [
            Teacher(1, "Dr. John Smith", "JS", 6, 24),
            Teacher(2, "Prof. Sarah Wilson", "SW", 6, 24),
            Teacher(3, "Dr. Alan Turing", "AT", 6, 24),
            Teacher(4, "Prof. Grace Hopper", "GH", 6, 24),
            Teacher(5, "Dr. Ada Lovelace", "AL", 6, 24),
            Teacher(6, "Prof. Linus Torvalds", "LT", 6, 24),
            Teacher(7, "Dr. Dennis Ritchie", "DR", 6, 24),
            Teacher(8, "Prof. Barbara Liskov", "BL", 6, 24),
            Teacher(9, "Dr. Tim Berners-Lee", "TB", 6, 24),
            Teacher(10, "Prof. Donald Knuth", "DK", 6, 24),
            Teacher(11, "Dr. Vint Cerf", "VC", 6, 24),
            Teacher(12, "Prof. Shafi Goldwasser", "SG", 6, 24),
            Teacher(13, "Dr. Raj Patel", "RP", 6, 24),
            Teacher(14, "Prof. Emily Chen", "EC", 6, 24),
            Teacher(15, "Dr. James Brown", "JB", 6, 24),
        ]

        # 20 theory subjects + 10 lab subjects = 30 total
        subjects = [
            Subject(
                1,
                "MATH101",
                "Mathematics I",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                2,
                "MATH102",
                "Mathematics II",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                3,
                "PHY101",
                "Physics I",
                3,
                theory_lectures_per_week=2,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                4,
                "PHY101P",
                "Physics I Lab",
                3,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                5,
                "PHY102",
                "Physics II",
                3,
                theory_lectures_per_week=2,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                6,
                "PHY102P",
                "Physics II Lab",
                3,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                7,
                "CS101",
                "Programming in C",
                4,
                theory_lectures_per_week=2,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                8,
                "CS101P",
                "Programming in C Lab",
                4,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                9,
                "CS201",
                "Data Structures",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                10,
                "CS201P",
                "Data Structures Lab",
                4,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                11,
                "CS301",
                "Database Systems",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                12,
                "CS301P",
                "Database Systems Lab",
                4,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                13,
                "CS401",
                "Operating Systems",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                14,
                "CS401P",
                "Operating Systems Lab",
                4,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                15,
                "EC101",
                "Electronics I",
                3,
                theory_lectures_per_week=2,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                16,
                "EC101P",
                "Electronics I Lab",
                3,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                17,
                "ENG101",
                "English Communication",
                3,
                theory_lectures_per_week=2,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                18,
                "ME101",
                "Engineering Drawing",
                3,
                theory_lectures_per_week=2,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                19,
                "MATH201",
                "Discrete Mathematics",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                20,
                "CS501",
                "Computer Networks",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                21,
                "CS501P",
                "Computer Networks Lab",
                4,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                22,
                "CS601",
                "AI & Machine Learning",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                23,
                "CS601P",
                "AI & ML Lab",
                4,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                24,
                "MATH301",
                "Probability & Stats",
                3,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                25,
                "CS701",
                "Software Engineering",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                26,
                "CS801",
                "Compiler Design",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                27,
                "CS802",
                "Cloud Computing",
                4,
                theory_lectures_per_week=2,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                28,
                "CHEM101",
                "Chemistry I",
                3,
                theory_lectures_per_week=2,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
            Subject(
                29,
                "CHEM101P",
                "Chemistry I Lab",
                3,
                theory_lectures_per_week=0,
                lab_hours_per_week=2,
                lab_batch_size=30,
            ),
            Subject(
                30,
                "CS901",
                "Cyber Security",
                4,
                theory_lectures_per_week=3,
                lab_hours_per_week=0,
                lab_batch_size=0,
            ),
        ]

        # Generate sections across semesters
        sections = []
        section_id = 1
        for sem in range(1, num_semesters + 1):
            for sec_idx in range(sections_per_sem):
                sec_letter = chr(ord("A") + sec_idx)
                sections.append(Section(section_id, f"CSE-{sem}{sec_letter}", sem, 60))
                section_id += 1

        # 8 classrooms + 10 labs = 18 rooms
        rooms = [
            Room(1, "Room 101", 70, RoomType.CLASSROOM),
            Room(2, "Room 102", 70, RoomType.CLASSROOM),
            Room(3, "Room 103", 70, RoomType.CLASSROOM),
            Room(4, "Room 104", 70, RoomType.CLASSROOM),
            Room(5, "Room 201", 70, RoomType.CLASSROOM),
            Room(6, "Room 202", 70, RoomType.CLASSROOM),
            Room(7, "Room 203", 70, RoomType.CLASSROOM),
            Room(8, "Room 204", 70, RoomType.CLASSROOM),
            Room(9, "Physics Lab 1", 35, RoomType.LAB, "Physics"),
            Room(10, "Physics Lab 2", 35, RoomType.LAB, "Physics"),
            Room(11, "Computer Lab 1", 35, RoomType.LAB, "Computer Science"),
            Room(12, "Computer Lab 2", 35, RoomType.LAB, "Computer Science"),
            Room(13, "Computer Lab 3", 35, RoomType.LAB, "Computer Science"),
            Room(14, "Electronics Lab 1", 35, RoomType.LAB, "Electronics"),
            Room(15, "Electronics Lab 2", 35, RoomType.LAB, "Electronics"),
            Room(16, "Chemistry Lab 1", 35, RoomType.LAB, "Chemistry"),
            Room(17, "AI Lab", 35, RoomType.LAB, "AI"),
            Room(18, "Networks Lab", 35, RoomType.LAB, "Networks"),
        ]

        # Assign semester-appropriate subjects (not all subjects to all sections)
        # Each semester gets a different subset of ~6 subjects
        semester_subjects = {
            1: [
                1,
                3,
                4,
                7,
                8,
                15,
                16,
                28,
                29,
            ],  # Sem 1: Math I, Phy I + lab, C + lab, EC + lab, Chem + lab
            2: [
                2,
                5,
                6,
                9,
                10,
                17,
                18,
            ],  # Sem 2: Math II, Phy II + lab, DS + lab, English, ED
            3: [
                11,
                12,
                13,
                14,
                19,
                20,
                21,
            ],  # Sem 3: DBMS + lab, OS + lab, Discrete Math, CN + lab
            4: [22, 23, 24, 25, 26],  # Sem 4: AI + lab, Prob & Stats, SE, Compiler
            5: [
                27,
                30,
                20,
                21,
                25,
                26,
            ],  # Sem 5: Cloud, Cyber Sec, CN + lab, SE, Compiler
        }

        self.teacher_page.set_data(teachers)
        self.subject_page.set_data(subjects)
        self.section_page.set_data(sections)
        self.room_page.set_data(rooms)

        # Provide subjects list to teacher page and section page for the assign-subjects UI
        self.teacher_page.set_all_subjects(subjects)
        self.section_page.set_all_subjects(subjects)
        # Provide sections list to room page for assign-section UI
        self.room_page.set_all_sections(sections)

        # Store semester-subject mapping for generation
        self._semester_subjects = semester_subjects

        # Map lab subjects to their required lab room type
        self._subject_lab_types = {
            "4": "Physics",  # PHY101P → Physics Lab
            "6": "Physics",  # PHY102P → Physics Lab
            "8": "Computer Science",  # CS101P → Computer Lab
            "10": "Computer Science",  # CS201P → Computer Lab
            "12": "Computer Science",  # CS301P → Computer Lab
            "14": "Computer Science",  # CS401P → Computer Lab
            "16": "Electronics",  # EC101P → Electronics Lab
            "21": "Networks",  # CS501P → Networks Lab
            "23": "AI",  # CS601P → AI Lab
            "29": "Chemistry",  # CHEM101P → Chemistry Lab
        }

        # ── Teacher Specializations ──
        # Maps subject_id → list of eligible teacher_ids
        # Specialists ONLY teach their domain subjects.
        # A few flexible teachers handle general / lighter subjects.
        self._teacher_specializations = {
            # ── Mathematics (Dr. John Smith, Prof. Sarah Wilson) ──
            1: [1, 2],  # Mathematics I
            2: [1, 2],  # Mathematics II
            19: [1, 2],  # Discrete Mathematics
            24: [1, 2],  # Probability & Stats
            # ── Physics (Prof. Grace Hopper, Dr. James Brown) ──
            3: [4, 15],  # Physics I
            4: [4, 15],  # Physics I Lab
            5: [4, 15],  # Physics II
            6: [4, 15],  # Physics II Lab
            # ── Programming / Compilers (Dr. Dennis Ritchie, Prof. Barbara Liskov) ──
            7: [7, 8],  # Programming in C
            8: [7, 8],  # Programming in C Lab
            26: [7, 8],  # Compiler Design
            # ── Data Structures / Algorithms (Dr. Alan Turing, Prof. Donald Knuth) ──
            9: [3, 10],  # Data Structures
            10: [3, 10],  # Data Structures Lab
            # ── OS & DB (Dr. Ada Lovelace, Prof. Linus Torvalds) ──
            11: [5, 6],  # Database Systems
            12: [5, 6],  # Database Systems Lab
            13: [5, 6],  # Operating Systems
            14: [5, 6],  # Operating Systems Lab
            # ── Electronics (Dr. Alan Turing, Dr. James Brown) ──
            15: [3, 15],  # Electronics I
            16: [3, 15],  # Electronics I Lab
            # ── Networks / Cloud (Dr. Tim Berners-Lee, Dr. Vint Cerf) ──
            20: [9, 11],  # Computer Networks
            21: [9, 11],  # Computer Networks Lab
            27: [9, 11],  # Cloud Computing
            # ── AI & ML / Cyber Security (Prof. Shafi Goldwasser, Prof. Donald Knuth) ──
            22: [12, 10],  # AI & Machine Learning
            23: [12, 10],  # AI & ML Lab
            30: [12, 11],  # Cyber Security
            # ── General subjects (Dr. Raj Patel, Prof. Emily Chen) ──
            17: [13, 14],  # English Communication
            18: [13, 14],  # Engineering Drawing
            25: [13, 14],  # Software Engineering
            28: [13, 14],  # Chemistry I
            29: [13, 14],  # Chemistry I Lab
        }

        # ── Populate teacher page's subject map from specializations ──
        # Convert subject_id→[teacher_ids] into teacher_id→[subject_ids]
        teacher_subj_map = {}
        for subj_id, tids in self._teacher_specializations.items():
            for tid in tids:
                teacher_subj_map.setdefault(tid, []).append(subj_id)
        self.teacher_page.teacher_subject_map = teacher_subj_map
        self.teacher_page.update_table()

        # ── Populate section page's subject map from semester mapping ──
        for sec in sections:
            sem_subjs = semester_subjects.get(sec.semester, [])
            self.section_page.section_subject_map[sec.id] = list(sem_subjs)
        self.section_page.update_table()

        # ── Section → Classroom pre-assignment ──
        # Assign each section its own dedicated classroom (in order)
        classroom_rooms = [r for r in rooms if r.type == RoomType.CLASSROOM]
        self._section_room_assignments = {}
        for idx, sec in enumerate(sections):
            if idx < len(classroom_rooms):
                self._section_room_assignments[str(sec.id)] = classroom_rooms[idx].id

        # Populate room page's section map from section-room assignments
        # section_id -> room_id (int) ==> room_id -> section_id (int)
        for sec_id_str, room_id in self._section_room_assignments.items():
            self.room_page.room_section_map[room_id] = int(sec_id_str)
        self.room_page.update_table()

    def initialize_sample_data(self):
        self.setup_sample_data()
        sections = self.section_page.get_data()
        subjects = self.subject_page.get_data()
        rooms = self.room_page.get_data()
        teachers = self.teacher_page.get_data()
        QMessageBox.information(
            self,
            "Initialized",
            f"Sample data created!\n"
            f"{len(sections)} sections, {len(subjects)} subjects,\n"
            f"{len(teachers)} teachers, {len(rooms)} rooms",
        )

    # ---------------- GENERATION THREAD ----------------
    def start_generation(self):
        try:
            logger.info("Starting generation process...")

            teachers = self.teacher_page.get_data()
            subjects = self.subject_page.get_data()
            sections = self.section_page.get_data()
            rooms = self.room_page.get_data()

            if not teachers:
                QMessageBox.warning(
                    self,
                    "Missing Data",
                    "No teachers found. Please add teachers before generation.",
                )
                return
            if not subjects:
                QMessageBox.warning(
                    self,
                    "Missing Data",
                    "No subjects found. Please add subjects before generation.",
                )
                return
            if not sections:
                QMessageBox.warning(
                    self,
                    "Missing Data",
                    "No sections found. Please add sections before generation.",
                )
                return
            if not rooms:
                QMessageBox.warning(
                    self,
                    "Missing Data",
                    "No rooms found. Please add rooms before generation.",
                )
                return

            logger.info(
                f"Data loaded: {len(teachers)} teachers, {len(subjects)} subjects, {len(sections)} sections, {len(rooms)} rooms"
            )

            # Validate data structures
            if not hasattr(teachers, "__iter__") or not hasattr(subjects, "__iter__"):
                raise ValueError("Invalid data structure for teachers or subjects")

            # Validate teacher data
            for t in teachers:
                if not hasattr(t, "id") or not hasattr(t, "name"):
                    raise ValueError(f"Invalid teacher object: {t}")

            # Validate subject data
            for s in subjects:
                if not hasattr(s, "id") or not hasattr(s, "name"):
                    raise ValueError(f"Invalid subject object: {s}")

            # Validate section data
            for sec in sections:
                if not hasattr(sec, "id") or not hasattr(sec, "name"):
                    raise ValueError(f"Invalid section object: {sec}")

            # Validate room data
            for r in rooms:
                if not hasattr(r, "id") or not hasattr(r, "name"):
                    raise ValueError(f"Invalid room object: {r}")

            # Serialize dataclass objects to dicts for the generator thread
            teachers_dicts = [
                {
                    "id": t.id,
                    "name": t.name,
                    "code": t.code,
                    "max_daily_load": t.max_daily_load,
                    "max_weekly_load": t.max_weekly_load,
                }
                for t in teachers
            ]
            subjects_dicts = [
                {
                    "id": s.id,
                    "code": s.code,
                    "name": s.name,
                    "credits": s.credits,
                    "theory_lectures_per_week": s.theory_lectures_per_week,
                    "lab_hours_per_week": s.lab_hours_per_week,
                    "lab_batch_size": s.lab_batch_size,
                }
                for s in subjects
            ]
            sections_dicts = [
                {
                    "id": s.id,
                    "name": s.name,
                    "semester": s.semester,
                    "strength": s.strength,
                }
                for s in sections
            ]
            rooms_dicts = [
                {
                    "id": r.id,
                    "name": r.name,
                    "capacity": r.capacity,
                    "type": r.type if isinstance(r.type, str) else r.type.value,
                    "lab_type": r.lab_type,
                }
                for r in rooms
            ]

            # ── Specialization-aware teacher assignment ──
            # Build subject_id → [teacher_ids] from teacher page's UI map
            specializations = {}
            if hasattr(self, "teacher_page") and self.teacher_page.teacher_subject_map:
                for tid, subj_ids in self.teacher_page.teacher_subject_map.items():
                    for sid in subj_ids:
                        specializations.setdefault(sid, []).append(tid)
            else:
                specializations = getattr(self, "_teacher_specializations", {})

            if not specializations:
                logger.warning(
                    "No teacher specializations found, using all teachers for all subjects"
                )
                specializations = {s.id: [t.id for t in teachers] for s in subjects}

            subject_teacher_assignments = {}
            teacher_ids = [t.id for t in teachers]
            teacher_load = {t.id: 0 for t in teachers}

            # Use semester-subject mapping if available
            semester_subjects = getattr(self, "_semester_subjects", None)

            # Count how many sections will use each subject
            subject_usage_count = {}
            if semester_subjects:
                for sec in sections:
                    sem_subjs = semester_subjects.get(sec.semester, [])
                    for sid in sem_subjs:
                        subject_usage_count[sid] = subject_usage_count.get(sid, 0) + 1
            else:
                for subj in subjects:
                    subject_usage_count[subj.id] = len(sections)

            for subj in subjects:
                usage = subject_usage_count.get(subj.id, 0)
                if usage == 0:
                    continue
                slots_per_section = subj.theory_lectures_per_week
                if subj.lab_hours_per_week > 0 and subj.lab_batch_size > 0:
                    batches = max(1, math.ceil(60 / subj.lab_batch_size))
                    lab_sessions = max(1, subj.lab_hours_per_week // 2)
                    slots_per_section += batches * lab_sessions * 2
                total_load = slots_per_section * usage

                # Pick from eligible specialists (or fall back to all teachers)
                eligible = specializations.get(subj.id, teacher_ids)
                if not eligible:
                    logger.warning(f"No teachers found for subject {subj.id}, skipping")
                    continue
                best_tid = min(eligible, key=lambda tid: teacher_load.get(tid, 0))
                subject_teacher_assignments[str(subj.id)] = [best_tid]
                teacher_load[best_tid] = teacher_load.get(best_tid, 0) + total_load

            # Section-subject assignments from section page's UI map
            section_subject_assignments = {}
            if hasattr(self, "section_page") and self.section_page.section_subject_map:
                for sec in sections:
                    assigned = self.section_page.section_subject_map.get(sec.id, [])
                    if assigned:
                        section_subject_assignments[str(sec.id)] = assigned
            if not section_subject_assignments:
                # Fallback to semester mapping or all subjects
                semester_subjects = getattr(self, "_semester_subjects", None)
                if semester_subjects:
                    for sec in sections:
                        sem_subjs = semester_subjects.get(sec.semester, [])
                        section_subject_assignments[str(sec.id)] = sem_subjs
                else:
                    all_subject_ids = [s.id for s in subjects]
                    for sec in sections:
                        section_subject_assignments[str(sec.id)] = all_subject_ids

            # Validate section_subject_assignments
            if not section_subject_assignments:
                QMessageBox.warning(
                    self,
                    "Missing Data",
                    "No subjects assigned to any section. Please assign subjects to sections.",
                )
                return

            # Build subject → lab_type mapping
            subject_lab_types = getattr(self, "_subject_lab_types", {})

            # Section → classroom pre-assignment
            # Read from room page's UI map (room_id -> section_id) ==> (section_id -> room_id)
            section_room_assignments = {}
            if hasattr(self, "room_page") and self.room_page.room_section_map:
                for rid, sid in self.room_page.room_section_map.items():
                    section_room_assignments[str(sid)] = rid
            else:
                section_room_assignments = getattr(
                    self, "_section_room_assignments", {}
                )

            config = {
                "teachers": teachers_dicts,
                "subjects": subjects_dicts,
                "sections": sections_dicts,
                "rooms": rooms_dicts,
                "subject_teacher_assignments": subject_teacher_assignments,
                "section_subject_assignments": section_subject_assignments,
                "subject_lab_types": subject_lab_types,
                "section_room_assignments": section_room_assignments,
            }

            logger.info("Starting generation thread...")
            self.generation_thread = TimetableGeneratorThread(config)
            self.generation_thread.generation_completed.connect(
                self.on_generation_completed
            )
            self.generation_thread.generation_failed.connect(self.on_generation_failed)
            if hasattr(self, "generate_page") and hasattr(
                self.generate_page, "progress_bar"
            ):
                self.generation_thread.progress_updated.connect(
                    self.generate_page.update_progress
                )
                self.generation_thread.status_updated.connect(
                    self.generate_page.update_status
                )
            self.generate_page.generate_btn.setEnabled(False)
            self.generate_page.generate_btn.setText("Generating...")
            self.generation_thread.start()

        except Exception as e:
            logger.exception(f"Error in start_generation: {e}")
            error_details = traceback.format_exc()
            QMessageBox.critical(
                self,
                "Generation Error",
                f"An error occurred while preparing generation:\n\n{str(e)}\n\nSee app.log for details.",
            )
            if hasattr(self, "generate_page") and hasattr(
                self.generate_page, "generate_btn"
            ):
                self.generate_page.generate_btn.setEnabled(True)
                self.generate_page.generate_btn.setText("GENERATE")

    def on_generation_completed(self, timetables):
        try:
            logger.info("Generation completed successfully")
            self.generated_timetables = timetables
            try:
                TimetableJSONParser.save_to_json(
                    "output/generated_timetables.json", timetables
                )
            except Exception as save_err:
                logger.warning(f"Failed to save timetable: {save_err}")

            self.generate_page.generate_btn.setEnabled(True)
            self.generate_page.generate_btn.setText("GENERATE")

            # Count items for summary
            num_sec = (
                len(timetables.get("sections", {}))
                if isinstance(timetables, dict) and "sections" in timetables
                else len(timetables)
            )
            QMessageBox.information(
                self,
                "Success",
                f"Timetables generated successfully!\n{num_sec} section timetables created.",
            )
            self.view_page.update_view(self.generated_timetables)
            self.room_page.update_table()
            self.navigate_to_page(7)
        except Exception as e:
            logger.exception(f"Error in on_generation_completed: {e}")
            self.generate_page.generate_btn.setEnabled(True)
            self.generate_page.generate_btn.setText("GENERATE")
            QMessageBox.critical(
                self, "Error", f"An error occurred after generation:\n\n{str(e)}"
            )

    def on_generation_failed(self, error_message):
        logger.error(f"Generation failed: {error_message}")
        self.generate_page.generate_btn.setEnabled(True)
        self.generate_page.generate_btn.setText("GENERATE")
        QMessageBox.critical(
            self,
            "Generation Failed",
            f"Could not generate timetable:\n\n{error_message}\n\nSee app.log for details.",
        )

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


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    main_win = AdvancedTimetableApp()
    main_win.show()
    sys.exit(app.exec_())
