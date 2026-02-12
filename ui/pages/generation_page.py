
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
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
        
        self.generate_btn = QPushButton("GENERATE")
        self.generate_btn.setStyleSheet(self.get_button_style("#28a745"))
        self.generate_btn.clicked.connect(self.start_generation_callback)
        layout.addWidget(self.generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)

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
