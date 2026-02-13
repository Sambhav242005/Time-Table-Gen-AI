
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class GenerationPage(QWidget):
    def __init__(self, start_generation_callback):
        super().__init__()
        self.start_generation_callback = start_generation_callback
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title = QLabel("GENERATE TIMETABLES")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addStretch()

        self.generate_btn = QPushButton("GENERATE")
        self.generate_btn.setStyleSheet(self.get_button_style("#28a745"))
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setMinimumWidth(200)
        self.generate_btn.clicked.connect(self.start_generation_callback)
        layout.addWidget(self.generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(400)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #555; font-size: 13px; padding: 10px;")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

    def update_progress(self, value):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)

    def update_status(self, text):
        self.status_label.setText(text)

    def get_button_style(self, color):
        return f"""
        QPushButton {{
            background-color: {color};
            color: white;
            padding: 14px 32px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
        }}
        QPushButton:hover {{
            background-color: {color}dd;
        }}
        QPushButton:disabled {{
            background-color: #999;
        }}
        """
