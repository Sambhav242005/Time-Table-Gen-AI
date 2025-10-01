from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMenu, QStackedWidget, QTextEdit, QMessageBox, QLineEdit,
    QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem, QDialog, QFileDialog,
    QScrollArea, QFrame, QComboBox, QTabWidget, QProgressBar, QSplitter,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QTimeEdit, QDateEdit,
    QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QTime, QDate
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import sys
import random
import json
from datetime import datetime, time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor


# Data Classes and Enums (simplified for UI)
class CourseType(Enum):
    SUBJECT = "SUBJECT"
    LAB = "LAB"

class RoomType(Enum):
    CLASSROOM = "CLASSROOM"
    LAB = "LAB"

@dataclass
class Teacher:
    id: int
    name: str
    code: str
    max_daily_load: int = 6
    max_weekly_load: int = 20
    availability: Dict[str, List[int]] = field(default_factory=dict)

@dataclass
class Subject:
    id: int
    code: str
    name: str
    credits: int
    weekly_lecture_slots: int
    is_lab: bool = False

@dataclass
class Section:
    id: int
    name: str
    semester: int
    strength: int

@dataclass
class Room:
    id: int
    name: str
    capacity: int
    type: RoomType
    lab_type: Optional[str] = None


class TimetableGeneratorThread(QThread):
    """Background thread for timetable generation"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(dict)
    generation_failed = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    def run(self):
        try:
            self.status_updated.emit("Initializing generation...")
            self.progress_updated.emit(10)
            
            # Simulate timetable generation steps
            steps = [
                "Preprocessing demands...",
                "Loading resources...",
                "Scheduling sections...",
                "Resolving conflicts...",
                "Optimizing placement...",
                "Finalizing timetables..."
            ]
            
            timetables = {}
            for i, step in enumerate(steps):
                self.status_updated.emit(step)
                self.progress_updated.emit(20 + (i * 13))
                self.msleep(1000)  # Simulate work
                
                # Generate sample timetable data
                if i == len(steps) - 1:
                    timetables = self._generate_sample_timetables()
            
            self.progress_updated.emit(100)
            self.status_updated.emit("Generation completed successfully!")
            self.generation_completed.emit(timetables)
            
        except Exception as e:
            self.generation_failed.emit(str(e))
    
    def _generate_sample_timetables(self):
        """Generate sample timetable data"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        subjects = ["Math", "Physics", "Chemistry", "English", "Computer Science"]
        
        timetables = {}
        for section in self.config.get('sections', []):
            section_schedule = {}
            for day in days:
                daily_schedule = []
                for slot in range(6):  # 6 slots per day
                    if random.random() > 0.2:  # 80% chance of having a class
                        subject = random.choice(subjects)
                        teacher = f"T{random.randint(1, 10)}"
                        room = f"R{random.randint(101, 120)}"
                        daily_schedule.append(f"{subject} - {teacher} ({room})")
                    else:
                        daily_schedule.append("Free")
                section_schedule[day] = daily_schedule
            timetables[section] = section_schedule
        
        return timetables


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
        self.lab_courses = []
        self.generated_timetables = {}
        
        # Generation thread
        self.generation_thread = None
        
        self.initUI()
        self.setup_sample_data()

    def initUI(self):
        """Initialize the user interface."""
        # Main Widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        # Header Section
        header = self.create_header()

        # Content Section
        self.content_stack = QStackedWidget()
        self.populate_content_pages()

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(header)
        main_layout.addWidget(self.content_stack)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(main_layout)

    def create_header(self):
        """Create the header section with navigation."""
        header = QWidget()
        header_layout = QHBoxLayout()
        header.setStyleSheet("background-color: #301934; padding: 10px;")

        # Logo/Title
        title_label = QLabel("ADVANCED TIMETABLE GENERATOR")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        # Navigation buttons
        nav_links = [
            ("HOME", 0), ("SETUP", 1), ("TEACHERS", 2), ("SUBJECTS", 3), 
            ("SECTIONS", 4), ("ROOMS", 5), ("GENERATE", 6), ("VIEW", 7)
        ]
        
        header_layout.addStretch()
        
        for link_name, page_index in nav_links:
            button = QPushButton(link_name)
            button.setStyleSheet(
                """
                QPushButton {
                    color: white; 
                    background: none; 
                    border: none; 
                    font-size: 14px; 
                    padding: 8px 16px;
                    margin: 2px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.2);
                }
                """
            )
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _, idx=page_index: self.navigate_to_page(idx))
            header_layout.addWidget(button)

        header.setLayout(header_layout)
        return header

    def populate_content_pages(self):
        """Populate the stacked widget with content pages."""
        self.content_stack.addWidget(self.create_home_page())           # 0
        self.content_stack.addWidget(self.create_setup_page())          # 1
        self.content_stack.addWidget(self.create_teachers_page())       # 2
        self.content_stack.addWidget(self.create_subjects_page())       # 3
        self.content_stack.addWidget(self.create_sections_page())       # 4
        self.content_stack.addWidget(self.create_rooms_page())          # 5
        self.content_stack.addWidget(self.create_generate_page())       # 6
        self.content_stack.addWidget(self.create_view_page())           # 7

    def navigate_to_page(self, page_index):
        """Navigate to the specified page."""
        self.content_stack.setCurrentIndex(page_index)

    def create_home_page(self):
        """Create the Home page with the same design."""
        home_page = QWidget()
        layout = QVBoxLayout()

        # Welcome Box
        welcome_box = QWidget()
        welcome_box.setStyleSheet(
            """
            QWidget {
                background-color: #301934; 
                color: white; 
                border-radius: 15px; 
                padding: 40px;
            }
            """
        )
        welcome_box.setFixedSize(1000, 500)

        welcome_layout = QVBoxLayout()
        
        # Main title
        welcome_label = QLabel("ADVANCED TIMETABLE GENERATOR")
        welcome_label.setFont(QFont("Arial", 28, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("margin-bottom: 20px;")

        # Subtitle
        description_label = QLabel(
            "Intelligent scheduling with multi-constraint optimization\n"
            "• Section, Teacher & Lab Timetables\n"
            "• Parallel Processing & Conflict Resolution\n"
            "• Advanced Constraint Management"
        )
        description_label.setFont(QFont("Arial", 16))
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("line-height: 1.6; margin-bottom: 30px;")

        # Feature highlights
        features_layout = QHBoxLayout()
        features = [
            ("🎯", "Smart\nScheduling"),
            ("⚡", "Parallel\nProcessing"),
            ("🔧", "Conflict\nResolution"),
            ("📊", "Multiple\nViews")
        ]
        
        for icon, text in features:
            feature_widget = QWidget()
            feature_layout = QVBoxLayout()
            
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Arial", 24))
            icon_label.setAlignment(Qt.AlignCenter)
            
            text_label = QLabel(text)
            text_label.setFont(QFont("Arial", 12))
            text_label.setAlignment(Qt.AlignCenter)
            
            feature_layout.addWidget(icon_label)
            feature_layout.addWidget(text_label)
            feature_widget.setLayout(feature_layout)
            features_layout.addWidget(feature_widget)

        # Action buttons
        button_layout = QHBoxLayout()
        
        setup_button = QPushButton("SETUP DATA")
        setup_button.clicked.connect(lambda: self.navigate_to_page(1))
        
        generate_button = QPushButton("GENERATE TIMETABLE")
        generate_button.clicked.connect(lambda: self.navigate_to_page(6))
        
        view_button = QPushButton("VIEW RESULTS")
        view_button.clicked.connect(lambda: self.navigate_to_page(7))

        for button in [setup_button, generate_button, view_button]:
            button.setStyleSheet(
                """
                QPushButton {
                    background-color: white; 
                    color: #301934; 
                    padding: 15px 25px; 
                    border: none; 
                    border-radius: 8px; 
                    font-size: 14px; 
                    font-weight: bold;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                    transform: translateY(-2px);
                }
                QPushButton:pressed {
                    background-color: #e9ecef;
                }
                """
            )
            button.setCursor(Qt.PointingHandCursor)
            button_layout.addWidget(button)

        # Layout assembly
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addWidget(description_label)
        welcome_layout.addLayout(features_layout)
        welcome_layout.addStretch()
        welcome_layout.addLayout(button_layout)
        welcome_box.setLayout(welcome_layout)

        # Center the welcome box
        layout.addStretch()
        layout.addWidget(welcome_box, alignment=Qt.AlignCenter)
        layout.addStretch()
        
        home_page.setLayout(layout)
        return home_page

    def create_setup_page(self):
        """Create the initial setup page."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Page title
        title = QLabel("INITIAL SETUP")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #301934; margin: 20px;")
        
        # Setup cards
        cards_layout = QHBoxLayout()
        
        setup_items = [
            ("Teachers", "Manage faculty information", lambda: self.navigate_to_page(2)),
            ("Subjects", "Configure courses & labs", lambda: self.navigate_to_page(3)),
            ("Sections", "Setup class sections", lambda: self.navigate_to_page(4)),
            ("Rooms", "Manage facilities", lambda: self.navigate_to_page(5))
        ]
        
        for title_text, desc_text, click_handler in setup_items:
            card = self.create_setup_card(title_text, desc_text, click_handler)
            cards_layout.addWidget(card)
        
        # Quick setup form
        quick_setup = self.create_quick_setup_form()
        
        layout.addWidget(title)
        layout.addLayout(cards_layout)
        layout.addWidget(quick_setup)
        layout.addStretch()
        
        page.setLayout(layout)
        return page

    def create_setup_card(self, title, description, click_handler):
        """Create a setup card widget."""
        card = QWidget()
        card.setStyleSheet(
            """
            QWidget {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
            QWidget:hover {
                border-color: #301934;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            """
        )
        card.setFixedSize(200, 150)
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #301934;")
        
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 12))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #6c757d;")
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        
        card.setLayout(layout)
        card.mousePressEvent = lambda e: click_handler()
        
        return card

    def create_quick_setup_form(self):
        """Create quick setup form."""
        form_widget = QWidget()
        form_widget.setStyleSheet(
            """
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
            """
        )
        
        layout = QVBoxLayout()
        
        title = QLabel("Quick Setup")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #301934; margin-bottom: 15px;")
        
        form_layout = QFormLayout()
        
        # Basic configuration
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
        
        # Initialize button
        init_button = QPushButton("Initialize with Sample Data")
        init_button.setStyleSheet(
            """
            QPushButton {
                background-color: #301934;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #4a2654;
            }
            """
        )
        init_button.clicked.connect(self.initialize_sample_data)
        
        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addWidget(init_button)
        
        form_widget.setLayout(layout)
        return form_widget

    def create_teachers_page(self):
        """Create teachers management page."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Page header
        header_layout = QHBoxLayout()
        title = QLabel("TEACHERS MANAGEMENT")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #301934;")
        
        add_teacher_btn = QPushButton("Add Teacher")
        add_teacher_btn.setStyleSheet(self.get_button_style())
        add_teacher_btn.clicked.connect(self.add_teacher_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_teacher_btn)
        
        # Teachers table
        self.teachers_table = QTableWidget()
        self.teachers_table.setColumnCount(5)
        self.teachers_table.setHorizontalHeaderLabels([
            "Name", "Code", "Max Daily Load", "Max Weekly Load", "Actions"
        ])
        self.teachers_table.horizontalHeader().setStretchLastSection(True)
        self.update_teachers_table()
        
        layout.addLayout(header_layout)
        layout.addWidget(self.teachers_table)
        
        page.setLayout(layout)
        return page

    def create_subjects_page(self):
        """Create subjects management page."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Page header
        header_layout = QHBoxLayout()
        title = QLabel("SUBJECTS & LABS MANAGEMENT")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #301934;")
        
        add_subject_btn = QPushButton("Add Subject")
        add_subject_btn.setStyleSheet(self.get_button_style())
        add_subject_btn.clicked.connect(self.add_subject_dialog)
        
        add_lab_btn = QPushButton("Add Lab Course")
        add_lab_btn.setStyleSheet(self.get_button_style())
        add_lab_btn.clicked.connect(self.add_lab_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_subject_btn)
        header_layout.addWidget(add_lab_btn)
        
        # Tabs for subjects and labs
        tabs = QTabWidget()
        
        # Subjects tab
        subjects_widget = QWidget()
        subjects_layout = QVBoxLayout()
        
        self.subjects_table = QTableWidget()
        self.subjects_table.setColumnCount(5)
        self.subjects_table.setHorizontalHeaderLabels([
            "Code", "Name", "Credits", "Weekly Slots", "Actions"
        ])
        self.subjects_table.horizontalHeader().setStretchLastSection(True)
        
        subjects_layout.addWidget(self.subjects_table)
        subjects_widget.setLayout(subjects_layout)
        tabs.addTab(subjects_widget, "Subjects")
        
        # Labs tab
        labs_widget = QWidget()
        labs_layout = QVBoxLayout()
        
        self.labs_table = QTableWidget()
        self.labs_table.setColumnCount(5)
        self.labs_table.setHorizontalHeaderLabels([
            "Code", "Name", "Weekly Blocks", "Block Length", "Lab Type"
        ])
        self.labs_table.horizontalHeader().setStretchLastSection(True)
        
        labs_layout.addWidget(self.labs_table)
        labs_widget.setLayout(labs_layout)
        tabs.addTab(labs_widget, "Lab Courses")
        
        self.update_subjects_tables()
        
        layout.addLayout(header_layout)
        layout.addWidget(tabs)
        
        page.setLayout(layout)
        return page

    def create_sections_page(self):
        """Create sections management page."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Page header
        header_layout = QHBoxLayout()
        title = QLabel("SECTIONS MANAGEMENT")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #301934;")
        
        add_section_btn = QPushButton("Add Section")
        add_section_btn.setStyleSheet(self.get_button_style())
        add_section_btn.clicked.connect(self.add_section_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_section_btn)
        
        # Sections table
        self.sections_table = QTableWidget()
        self.sections_table.setColumnCount(4)
        self.sections_table.setHorizontalHeaderLabels([
            "Name", "Semester", "Strength", "Actions"
        ])
        self.sections_table.horizontalHeader().setStretchLastSection(True)
        self.update_sections_table()
        
        layout.addLayout(header_layout)
        layout.addWidget(self.sections_table)
        
        page.setLayout(layout)
        return page

    def create_rooms_page(self):
        """Create rooms management page."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Page header
        header_layout = QHBoxLayout()
        title = QLabel("ROOMS MANAGEMENT")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #301934;")
        
        add_room_btn = QPushButton("Add Room")
        add_room_btn.setStyleSheet(self.get_button_style())
        add_room_btn.clicked.connect(self.add_room_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_room_btn)
        
        # Rooms table
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(5)
        self.rooms_table.setHorizontalHeaderLabels([
            "Name", "Type", "Capacity", "Lab Type", "Actions"
        ])
        self.rooms_table.horizontalHeader().setStretchLastSection(True)
        self.update_rooms_table()
        
        layout.addLayout(header_layout)
        layout.addWidget(self.rooms_table)
        
        page.setLayout(layout)
        return page

    def create_generate_page(self):
        """Create timetable generation page."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Page title
        title = QLabel("GENERATE TIMETABLES")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #301934; margin: 20px;")
        
        # Generation configuration
        config_widget = QWidget()
        config_widget.setStyleSheet(
            """
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 30px;
                margin: 20px;
            }
            """
        )
        
        config_layout = QVBoxLayout()
        
        # Configuration form
        form_layout = QFormLayout()
        
        self.gen_semesters_combo = QComboBox()
        self.gen_semesters_combo.addItems(["All Semesters", "Semester 1-2", "Semester 3-4", "Custom"])
        
        self.working_days_group = QGroupBox("Working Days")
        working_days_layout = QHBoxLayout()
        self.day_checkboxes = {}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            checkbox = QCheckBox(day)
            checkbox.setChecked(day != "Saturday")  # Saturday unchecked by default
            self.day_checkboxes[day] = checkbox
            working_days_layout.addWidget(checkbox)
        self.working_days_group.setLayout(working_days_layout)
        
        self.optimization_combo = QComboBox()
        self.optimization_combo.addItems([
            "Balanced Optimization",
            "Minimize Teacher Gaps",
            "Even Distribution",
            "Compact Schedule"
        ])
        
        form_layout.addRow("Semesters to Generate:", self.gen_semesters_combo)
        form_layout.addRow("Optimization Strategy:", self.optimization_combo)
        
        # Progress section
        progress_group = QGroupBox("Generation Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("Ready to generate timetables")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        
        # Generate button
        self.generate_btn = QPushButton("GENERATE TIMETABLES")
        self.generate_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                margin: 20px 0;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
            """
        )
        self.generate_btn.clicked.connect(self.start_generation)
        
        # Assembly
        config_layout.addLayout(form_layout)
        config_layout.addWidget(self.working_days_group)
        config_layout.addWidget(progress_group)
        config_layout.addWidget(self.generate_btn, alignment=Qt.AlignCenter)
        
        config_widget.setLayout(config_layout)
        
        layout.addWidget(title)
        layout.addWidget(config_widget)
        layout.addStretch()
        
        page.setLayout(layout)
        return page

    def create_view_page(self):
        """Create timetable viewing page."""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Page header
        header_layout = QHBoxLayout()
        title = QLabel("TIMETABLE VIEWS")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #301934;")
        
        export_btn = QPushButton("Export All PDFs")
        export_btn.setStyleSheet(self.get_button_style("#dc3545"))
        export_btn.clicked.connect(self.export_all_timetables)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(export_btn)
        
        # View tabs
        self.view_tabs = QTabWidget()
        
        # Section timetables tab
        self.section_view_tab = QWidget()
        section_layout = QVBoxLayout()
        
        section_selector_layout = QHBoxLayout()
        section_selector_layout.addWidget(QLabel("Select Section:"))
        
        self.section_combo = QComboBox()
        self.section_combo.currentTextChanged.connect(self.update_section_view)
        section_selector_layout.addWidget(self.section_combo)
        section_selector_layout.addStretch()
        
        self.section_table = QTableWidget()
        self.setup_timetable_table(self.section_table)
        
        section_layout.addLayout(section_selector_layout)
        section_layout.addWidget(self.section_table)
        self.section_view_tab.setLayout(section_layout)
        
        # Teacher timetables tab
        self.teacher_view_tab = QWidget()
        teacher_layout = QVBoxLayout()
        
        teacher_selector_layout = QHBoxLayout()
        teacher_selector_layout.addWidget(QLabel("Select Teacher:"))
        
        self.teacher_combo = QComboBox()
        self.teacher_combo.currentTextChanged.connect(self.update_teacher_view)
        teacher_selector_layout.addWidget(self.teacher_combo)
        teacher_selector_layout.addStretch()
        
        self.teacher_table = QTableWidget()
        self.setup_timetable_table(self.teacher_table)
        
        teacher_layout.addLayout(teacher_selector_layout)
        teacher_layout.addWidget(self.teacher_table)
        self.teacher_view_tab.setLayout(teacher_layout)
        
        # Room timetables tab
        self.room_view_tab = QWidget()
        room_layout = QVBoxLayout()
        
        room_selector_layout = QHBoxLayout()
        room_selector_layout.addWidget(QLabel("Select Room:"))
        
        self.room_combo = QComboBox()
        self.room_combo.currentTextChanged.connect(self.update_rooms_table)
        room_selector_layout.addWidget(self.room_combo)
        room_selector_layout.addStretch()
        
        self.room_table = QTableWidget()
        self.setup_timetable_table(self.room_table)
        
        room_layout.addLayout(room_selector_layout)
        room_layout.addWidget(self.room_table)
        self.room_view_tab.setLayout(room_layout)
        
        # Add tabs
        self.view_tabs.addTab(self.section_view_tab, "Section Timetables")
        self.view_tabs.addTab(self.teacher_view_tab, "Teacher Timetables")
        self.view_tabs.addTab(self.room_view_tab, "Room Timetables")
        
        # Update view data
        self.update_view_combos()
        
        layout.addLayout(header_layout)
        layout.addWidget(self.view_tabs)
        
        page.setLayout(layout)
        return page

    def setup_timetable_table(self, table):
        """Setup a timetable display table."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        slots = [f"Slot {i+1}" for i in range(6)]
        
        table.setRowCount(len(days))
        table.setColumnCount(len(slots))
        table.setHorizontalHeaderLabels(slots)
        table.setVerticalHeaderLabels(days)
        
        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            QHeaderView::section {
                background-color: #301934;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Make table read-only
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectItems)
        
        # Resize columns to content
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)

    def get_button_style(self, color="#301934"):
        """Get standard button styling."""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}bb;
            }}
        """

    def setup_sample_data(self):
        """Initialize with sample data."""
        # Sample teachers
        self.teachers = [
            Teacher(1, "Dr. John Smith", "JS", 6, 20),
            Teacher(2, "Prof. Sarah Wilson", "SW", 5, 18),
            Teacher(3, "Dr. Mike Johnson", "MJ", 6, 22),
            Teacher(4, "Prof. Lisa Brown", "LB", 4, 16),
            Teacher(5, "Dr. David Lee", "DL", 6, 20)
        ]
        
        # Sample subjects
        self.subjects = [
            Subject(1, "MATH101", "Mathematics I", 4, 4),
            Subject(2, "PHY101", "Physics I", 3, 3),
            Subject(3, "CHEM101", "Chemistry I", 3, 3),
            Subject(4, "ENG101", "English I", 2, 2),
            Subject(5, "CS101", "Computer Science I", 4, 4),
            Subject(6, "CS102", "Programming Lab", 2, 1, True)
        ]
        
        # Sample sections
        self.sections = [
            Section(1, "CSE-1A", 1, 60),
            Section(2, "CSE-1B", 1, 55),
            Section(3, "CSE-2A", 2, 58),
            Section(4, "CSE-2B", 2, 62)
        ]
        
        # Sample rooms
        self.rooms = [
            Room(1, "Room 101", 70, RoomType.CLASSROOM),
            Room(2, "Room 102", 65, RoomType.CLASSROOM),
            Room(3, "Room 103", 60, RoomType.CLASSROOM),
            Room(4, "CS Lab 1", 40, RoomType.LAB, "Computer Science"),
            Room(5, "Physics Lab", 35, RoomType.LAB, "Physics"),
            Room(6, "Chemistry Lab", 30, RoomType.LAB, "Chemistry")
        ]

    def initialize_sample_data(self):
        """Initialize with user-configured sample data."""
        semesters = self.semesters_spin.value()
        sections_per_sem = self.sections_per_sem_spin.value()
        
        # Clear existing data
        self.teachers.clear()
        self.subjects.clear()
        self.sections.clear()
        self.rooms.clear()
        
        # Generate sample data based on configuration
        for i in range(10):  # 10 teachers
            self.teachers.append(
                Teacher(i+1, f"Teacher {i+1}", f"T{i+1:02d}", 6, 20)
            )
        
        # Generate subjects for each semester
        subject_id = 1
        for sem in range(1, semesters + 1):
            for j in range(5):  # 5 subjects per semester
                self.subjects.append(
                    Subject(subject_id, f"SUB{sem}{j+1:02d}", f"Subject {sem}.{j+1}", 3, 3)
                )
                subject_id += 1
        
        # Generate sections
        section_id = 1
        for sem in range(1, semesters + 1):
            for sec in range(sections_per_sem):
                section_name = f"SEM{sem}-{chr(65+sec)}"  # A, B, C, etc.
                self.sections.append(
                    Section(section_id, section_name, sem, 60)
                )
                section_id += 1
        
        # Generate rooms
        for i in range(15):  # 15 rooms
            room_type = RoomType.LAB if i < 5 else RoomType.CLASSROOM
            lab_type = "General" if room_type == RoomType.LAB else None
            self.rooms.append(
                Room(i+1, f"Room {i+101}", 60, room_type, lab_type)
            )
        
        # Update all tables
        self.update_all_tables()
        
        QMessageBox.information(self, "Success", "Sample data initialized successfully!")

    def update_all_tables(self):
        """Update all data tables."""
        self.update_teachers_table()
        self.update_subjects_tables()
        self.update_sections_table()
        self.update_rooms_table()
        self.update_view_combos()

    def update_teachers_table(self):
        """Update teachers table display."""
        self.teachers_table.setRowCount(len(self.teachers))
        
        for i, teacher in enumerate(self.teachers):
            self.teachers_table.setItem(i, 0, QTableWidgetItem(teacher.name))
            self.teachers_table.setItem(i, 1, QTableWidgetItem(teacher.code))
            self.teachers_table.setItem(i, 2, QTableWidgetItem(str(teacher.max_daily_load)))
            self.teachers_table.setItem(i, 3, QTableWidgetItem(str(teacher.max_weekly_load)))
            
            # Actions button
            action_btn = QPushButton("Edit")
            action_btn.setStyleSheet(self.get_button_style("#17a2b8"))
            action_btn.clicked.connect(lambda _, idx=i: self.edit_teacher(idx))
            self.teachers_table.setCellWidget(i, 4, action_btn)

    def update_subjects_tables(self):
        """Update subjects and labs tables."""
        # Regular subjects
        regular_subjects = [s for s in self.subjects if not s.is_lab]
        self.subjects_table.setRowCount(len(regular_subjects))
        
        for i, subject in enumerate(regular_subjects):
            self.subjects_table.setItem(i, 0, QTableWidgetItem(subject.code))
            self.subjects_table.setItem(i, 1, QTableWidgetItem(subject.name))
            self.subjects_table.setItem(i, 2, QTableWidgetItem(str(subject.credits)))
            self.subjects_table.setItem(i, 3, QTableWidgetItem(str(subject.weekly_lecture_slots)))
            
            action_btn = QPushButton("Edit")
            action_btn.setStyleSheet(self.get_button_style("#17a2b8"))
            self.subjects_table.setCellWidget(i, 4, action_btn)
        
        # Lab subjects
        lab_subjects = [s for s in self.subjects if s.is_lab]
        self.labs_table.setRowCount(len(lab_subjects))
        
        for i, lab in enumerate(lab_subjects):
            self.labs_table.setItem(i, 0, QTableWidgetItem(lab.code))
            self.labs_table.setItem(i, 1, QTableWidgetItem(lab.name))
            self.labs_table.setItem(i, 2, QTableWidgetItem(str(lab.weekly_lecture_slots)))
            self.labs_table.setItem(i, 3, QTableWidgetItem("2"))  # Default block length
            self.labs_table.setItem(i, 4, QTableWidgetItem("General"))
            
            action_btn = QPushButton("Edit")
            action_btn.setStyleSheet(self.get_button_style("#17a2b8"))
            self.labs_table.setCellWidget(i, 4, action_btn)

    def update_sections_table(self):
        """Update sections table display."""
        self.sections_table.setRowCount(len(self.sections))
        
        for i, section in enumerate(self.sections):
            self.sections_table.setItem(i, 0, QTableWidgetItem(section.name))
            self.sections_table.setItem(i, 1, QTableWidgetItem(str(section.semester)))
            self.sections_table.setItem(i, 2, QTableWidgetItem(str(section.strength)))
            
            action_btn = QPushButton("Edit")
            action_btn.setStyleSheet(self.get_button_style("#17a2b8"))
            action_btn.clicked.connect(lambda _, idx=i: self.edit_section(idx))
            self.sections_table.setCellWidget(i, 3, action_btn)

    def update_rooms_table(self):
        """Update rooms table display."""
        self.rooms_table.setRowCount(len(self.rooms))
        
        for i, room in enumerate(self.rooms):
            self.rooms_table.setItem(i, 0, QTableWidgetItem(room.name))
            self.rooms_table.setItem(i, 1, QTableWidgetItem(room.type.value))
            self.rooms_table.setItem(i, 2, QTableWidgetItem(str(room.capacity)))
            self.rooms_table.setItem(i, 3, QTableWidgetItem(room.lab_type or "N/A"))
            
            action_btn = QPushButton("Edit")
            action_btn.setStyleSheet(self.get_button_style("#17a2b8"))
            action_btn.clicked.connect(lambda _, idx=i: self.edit_room(idx))
            self.rooms_table.setCellWidget(i, 4, action_btn)

    def update_view_combos(self):
        """Update combo boxes in view page."""
        # Update section combo
        self.section_combo.clear()
        self.section_combo.addItems([section.name for section in self.sections])
        
        # Update teacher combo  
        self.teacher_combo.clear()
        self.teacher_combo.addItems([teacher.name for teacher in self.teachers])
        
        # Update room combo
        self.room_combo.clear()
        self.room_combo.addItems([room.name for room in self.rooms])

    def add_teacher_dialog(self):
        """Show dialog to add new teacher."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Teacher")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        name_edit = QLineEdit()
        code_edit = QLineEdit()
        daily_spin = QSpinBox()
        daily_spin.setRange(1, 10)
        daily_spin.setValue(6)
        weekly_spin = QSpinBox()
        weekly_spin.setRange(5, 30)
        weekly_spin.setValue(20)
        
        form_layout.addRow("Name:", name_edit)
        form_layout.addRow("Code:", code_edit)
        form_layout.addRow("Max Daily Load:", daily_spin)
        form_layout.addRow("Max Weekly Load:", weekly_spin)
        
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.setStyleSheet(self.get_button_style("#28a745"))
        cancel_btn.setStyleSheet(self.get_button_style("#6c757d"))
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        
        def save_teacher():
            if name_edit.text() and code_edit.text():
                new_id = len(self.teachers) + 1
                teacher = Teacher(
                    new_id, name_edit.text(), code_edit.text(),
                    daily_spin.value(), weekly_spin.value()
                )
                self.teachers.append(teacher)
                self.update_teachers_table()
                self.update_view_combos()
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Error", "Please fill all fields!")
        
        save_btn.clicked.connect(save_teacher)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def add_subject_dialog(self):
        """Show dialog to add new subject."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Subject")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        code_edit = QLineEdit()
        name_edit = QLineEdit()
        credits_spin = QSpinBox()
        credits_spin.setRange(1, 6)
        credits_spin.setValue(3)
        slots_spin = QSpinBox()
        slots_spin.setRange(1, 6)
        slots_spin.setValue(3)
        
        form_layout.addRow("Code:", code_edit)
        form_layout.addRow("Name:", name_edit)
        form_layout.addRow("Credits:", credits_spin)
        form_layout.addRow("Weekly Slots:", slots_spin)
        
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.setStyleSheet(self.get_button_style("#28a745"))
        cancel_btn.setStyleSheet(self.get_button_style("#6c757d"))
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        
        def save_subject():
            if code_edit.text() and name_edit.text():
                new_id = len(self.subjects) + 1
                subject = Subject(
                    new_id, code_edit.text(), name_edit.text(),
                    credits_spin.value(), slots_spin.value()
                )
                self.subjects.append(subject)
                self.update_subjects_tables()
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Error", "Please fill all fields!")
        
        save_btn.clicked.connect(save_subject)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def add_lab_dialog(self):
        """Show dialog to add new lab course."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Lab Course")
        dialog.setFixedSize(400, 350)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        code_edit = QLineEdit()
        name_edit = QLineEdit()
        blocks_spin = QSpinBox()
        blocks_spin.setRange(1, 3)
        blocks_spin.setValue(1)
        length_spin = QSpinBox()
        length_spin.setRange(2, 4)
        length_spin.setValue(2)
        lab_type_combo = QComboBox()
        lab_type_combo.addItems(["Computer Science", "Physics", "Chemistry", "Electronics", "General"])
        
        form_layout.addRow("Code:", code_edit)
        form_layout.addRow("Name:", name_edit)
        form_layout.addRow("Weekly Blocks:", blocks_spin)
        form_layout.addRow("Block Length:", length_spin)
        form_layout.addRow("Lab Type:", lab_type_combo)
        
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.setStyleSheet(self.get_button_style("#28a745"))
        cancel_btn.setStyleSheet(self.get_button_style("#6c757d"))
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        
        def save_lab():
            if code_edit.text() and name_edit.text():
                new_id = len(self.subjects) + 1
                lab = Subject(
                    new_id, code_edit.text(), name_edit.text(),
                    blocks_spin.value(), blocks_spin.value(), True
                )
                self.subjects.append(lab)
                self.update_subjects_tables()
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Error", "Please fill all fields!")
        
        save_btn.clicked.connect(save_lab)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def add_section_dialog(self):
        """Show dialog to add new section."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Section")
        dialog.setFixedSize(400, 250)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        name_edit = QLineEdit()
        semester_spin = QSpinBox()
        semester_spin.setRange(1, 8)
        semester_spin.setValue(1)
        strength_spin = QSpinBox()
        strength_spin.setRange(20, 100)
        strength_spin.setValue(60)
        
        form_layout.addRow("Name:", name_edit)
        form_layout.addRow("Semester:", semester_spin)
        form_layout.addRow("Strength:", strength_spin)
        
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.setStyleSheet(self.get_button_style("#28a745"))
        cancel_btn.setStyleSheet(self.get_button_style("#6c757d"))
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        
        def save_section():
            if name_edit.text():
                new_id = len(self.sections) + 1
                section = Section(
                    new_id, name_edit.text(),
                    semester_spin.value(), strength_spin.value()
                )
                self.sections.append(section)
                self.update_sections_table()
                self.update_view_combos()
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Error", "Please enter section name!")
        
        save_btn.clicked.connect(save_section)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def add_room_dialog(self):
        """Show dialog to add new room."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Room")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        name_edit = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems(["CLASSROOM", "LAB"])
        capacity_spin = QSpinBox()
        capacity_spin.setRange(20, 100)
        capacity_spin.setValue(60)
        lab_type_combo = QComboBox()
        lab_type_combo.addItems(["N/A", "Computer Science", "Physics", "Chemistry", "Electronics"])
        lab_type_combo.setEnabled(False)
        
        # Enable/disable lab type based on room type
        def on_type_changed():
            is_lab = type_combo.currentText() == "LAB"
            lab_type_combo.setEnabled(is_lab)
            if not is_lab:
                lab_type_combo.setCurrentText("N/A")
        
        type_combo.currentTextChanged.connect(on_type_changed)
        
        form_layout.addRow("Name:", name_edit)
        form_layout.addRow("Type:", type_combo)
        form_layout.addRow("Capacity:", capacity_spin)
        form_layout.addRow("Lab Type:", lab_type_combo)
        
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.setStyleSheet(self.get_button_style("#28a745"))
        cancel_btn.setStyleSheet(self.get_button_style("#6c757d"))
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        
        def save_room():
            if name_edit.text():
                new_id = len(self.rooms) + 1
                room_type = RoomType.LAB if type_combo.currentText() == "LAB" else RoomType.CLASSROOM
                lab_type = lab_type_combo.currentText() if lab_type_combo.isEnabled() and lab_type_combo.currentText() != "N/A" else None
                
                room = Room(
                    new_id, name_edit.text(),
                    capacity_spin.value(), room_type, lab_type
                )
                self.rooms.append(room)
                self.update_rooms_table()
                self.update_view_combos()
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "Error", "Please enter room name!")
        
        save_btn.clicked.connect(save_room)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def edit_teacher(self, index):
        """Edit teacher at given index."""
        QMessageBox.information(self, "Edit Teacher", f"Edit functionality for teacher {index+1} will be implemented.")

    def edit_section(self, index):
        """Edit section at given index."""
        QMessageBox.information(self, "Edit Section", f"Edit functionality for section {index+1} will be implemented.")

    def edit_room(self, index):
        """Edit room at given index."""
        QMessageBox.information(self, "Edit Room", f"Edit functionality for room {index+1} will be implemented.")

    def start_generation(self):
        """Start timetable generation process."""
        if not self.teachers or not self.subjects or not self.sections or not self.rooms:
            QMessageBox.warning(self, "Insufficient Data", 
                              "Please setup teachers, subjects, sections, and rooms before generating timetables.")
            return
        
        # Get selected working days
        working_days = [day for day, checkbox in self.day_checkboxes.items() if checkbox.isChecked()]
        
        if not working_days:
            QMessageBox.warning(self, "No Working Days", "Please select at least one working day.")
            return
        
        # Prepare configuration
        config = {
            'teachers': self.teachers,
            'subjects': self.subjects,
            'sections': [section.name for section in self.sections],
            'rooms': self.rooms,
            'working_days': working_days,
            'optimization': self.optimization_combo.currentText()
        }
        
        # Start generation thread
        self.generation_thread = TimetableGeneratorThread(config)
        self.generation_thread.progress_updated.connect(self.progress_bar.setValue)
        self.generation_thread.status_updated.connect(self.status_label.setText)
        self.generation_thread.generation_completed.connect(self.on_generation_completed)
        self.generation_thread.generation_failed.connect(self.on_generation_failed)
        
        # Update UI for generation
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("GENERATING...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.generation_thread.start()

    def on_generation_completed(self, timetables):
        """Handle successful timetable generation."""
        self.generated_timetables = timetables
        
        # Reset UI
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("GENERATE TIMETABLES")
        self.progress_bar.setVisible(False)
        
        # Update timetable views
        self.update_timetable_displays()
        
        # Switch to view page
        self.navigate_to_page(7)
        
        QMessageBox.information(self, "Success", 
                              f"Timetables generated successfully for {len(timetables)} sections!")

    def on_generation_failed(self, error):
        """Handle failed timetable generation."""
        # Reset UI
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("GENERATE TIMETABLES")
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Generation Failed", f"Timetable generation failed:\n{error}")

    def update_timetable_displays(self):
        """Update all timetable display tables."""
        if self.generated_timetables:
            # Update section view by default with first section
            if self.section_combo.count() > 0:
                self.update_section_view(self.section_combo.currentText())

    def update_section_view(self, section_name):
        """Update section timetable view."""
        if section_name in self.generated_timetables:
            schedule = self.generated_timetables[section_name]
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            
            for day_idx, day in enumerate(days):
                if day in schedule:
                    day_schedule = schedule[day]
                    for slot_idx, class_info in enumerate(day_schedule):
                        if slot_idx < self.section_table.columnCount():
                            item = QTableWidgetItem(class_info)
                            item.setTextAlignment(Qt.AlignCenter)
                            # Color code different types of classes
                            if "Free" in class_info:
                                item.setBackground(QColor("#f8f9fa"))
                            elif "Lab" in class_info:
                                item.setBackground(QColor("#e3f2fd"))
                            else:
                                item.setBackground(QColor("#e8f5e8"))
                            self.section_table.setItem(day_idx, slot_idx, item)

    def update_teacher_view(self, teacher_name):
        """Update teacher timetable view."""
        # Simulate teacher view - in real implementation, this would merge 
        # all sections where the teacher teaches
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        for day_idx, day in enumerate(days):
            for slot_idx in range(6):
                # Sample teacher schedule
                if random.random() > 0.3:  # 70% chance of having a class
                    sections = [s.name for s in self.sections]
                    section = random.choice(sections)
                    subjects = [s.name for s in self.subjects]
                    subject = random.choice(subjects)
                    class_info = f"{section}\n{subject}"
                else:
                    class_info = "Free"
                
                item = QTableWidgetItem(class_info)
                item.setTextAlignment(Qt.AlignCenter)
                self.room_table.setItem(day_idx, slot_idx, item)

    def export_all_timetables(self):
        """Export all timetables as PDF files."""
        if not self.generated_timetables:
            QMessageBox.warning(self, "No Timetables", "Please generate timetables first!")
            return
        
        folder_path = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if not folder_path:
            return
        
        try:
            # Export section timetables
            for section_name, schedule in self.generated_timetables.items():
                self.export_section_pdf(section_name, schedule, folder_path)
            
            # Export teacher timetables (simulated)
            for teacher in self.teachers:
                self.export_teacher_pdf(teacher, folder_path)
            
            # Export room timetables (simulated)
            for room in self.rooms:
                self.export_room_pdf(room, folder_path)
            
            QMessageBox.information(self, "Export Complete", 
                                  f"All timetables exported successfully to:\n{folder_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export timetables:\n{str(e)}")

    def export_section_pdf(self, section_name, schedule, folder_path):
        """Export individual section timetable as PDF."""
        file_path = f"{folder_path}/Timetable_{section_name}.pdf"
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"Timetable - {section_name}", styles["Title"])
        elements.append(title)
        elements.append(Paragraph("<br/>", styles["Normal"]))
        
        # Table data
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        table_data = [["Day"] + [f"Slot {i+1}" for i in range(6)]]
        
        for day in days:
            if day in schedule:
                row_data = [day] + schedule[day]
            else:
                row_data = [day] + ["Free"] * 6
            table_data.append(row_data)
        
        # Create and style table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("BACKGROUND", (0, 1), (0, -1), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        
        elements.append(table)
        doc.build(elements)

    def export_teacher_pdf(self, teacher, folder_path):
        """Export individual teacher timetable as PDF."""
        file_path = f"{folder_path}/Teacher_{teacher.code}_{teacher.name.replace(' ', '_')}.pdf"
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"Teacher Timetable - {teacher.name} ({teacher.code})", styles["Title"])
        elements.append(title)
        elements.append(Paragraph("<br/>", styles["Normal"]))
        
        # Sample teacher schedule
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        table_data = [["Day"] + [f"Slot {i+1}" for i in range(6)]]
        
        for day in days:
            row_data = [day]
            for slot in range(6):
                if random.random() > 0.3:
                    section = random.choice([s.name for s in self.sections])
                    subject = random.choice([s.name for s in self.subjects])
                    row_data.append(f"{subject}\n({section})")
                else:
                    row_data.append("Free")
            table_data.append(row_data)
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("BACKGROUND", (0, 1), (0, -1), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        doc.build(elements)

    def export_room_pdf(self, room, folder_path):
        """Export individual room timetable as PDF."""
        file_path = f"{folder_path}/Room_{room.name.replace(' ', '_')}.pdf"
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        room_info = f"Room Timetable - {room.name} ({room.type.value}"
        if room.lab_type:
            room_info += f" - {room.lab_type}"
        room_info += f", Capacity: {room.capacity})"
        
        title = Paragraph(room_info, styles["Title"])
        elements.append(title)
        elements.append(Paragraph("<br/>", styles["Normal"]))
        
        # Sample room schedule
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        table_data = [["Day"] + [f"Slot {i+1}" for i in range(6)]]
        
        for day in days:
            row_data = [day]
            for slot in range(6):
                if random.random() > 0.4:
                    section = random.choice([s.name for s in self.sections])
                    subject = random.choice([s.name for s in self.subjects])
                    row_data.append(f"{section}\n{subject}")
                else:
                    row_data.append("Free")
            table_data.append(row_data)
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("BACKGROUND", (0, 1), (0, -1), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        doc.build(elements)


def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Advanced Timetable Generator")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Academic Solutions")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Apply global stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background-color: #f1f1f1;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #c1c1c1;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #a8a8a8;
        }
        
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        
        QTabWidget::tab-bar {
            alignment: left;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            color: #555;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            color: #301934;
            border-bottom: 2px solid #301934;
        }
        
        QTabBar::tab:hover {
            background-color: #e6e6e6;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
            color: #301934;
        }
        
        QComboBox {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
            min-width: 120px;
        }
        
        QComboBox:hover {
            border-color: #301934;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #666;
            margin-right: 5px;
        }
        
        QSpinBox {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }
        
        QSpinBox:hover {
            border-color: #301934;
        }
        
        QLineEdit {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }
        
        QLineEdit:focus {
            border-color: #301934;
            outline: none;
        }
        
        QCheckBox {
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #ddd;
            border-radius: 3px;
            background-color: white;
        }
        
        QCheckBox::indicator:hover {
            border-color: #301934;
        }
        
        QCheckBox::indicator:checked {
            background-color: #301934;
            border-color: #301934;
        }
        
        QCheckBox::indicator:checked:hover {
            background-color: #4a2654;
        }
        
        QProgressBar {
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
            background-color: #f8f9fa;
        }
        
        QProgressBar::chunk {
            background-color: #301934;
            border-radius: 3px;
        }
        
        QMessageBox {
            background-color: white;
        }
        
        QDialog {
            background-color: white;
        }
    """)
    
    # Create and show main window
    window = AdvancedTimetableApp()
    window.show()
    
    # Center window on screen
    screen = app.desktop().screenGeometry()
    window.move((screen.width() - window.width()) // 2, 
                (screen.height() - window.height()) // 2)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 