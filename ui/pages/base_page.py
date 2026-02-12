
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QLabel, QAbstractItemView
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class BasePage(QWidget):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.data = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title_label)
        
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)
        
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_item)
        button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_item)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_item)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def set_data(self, data):
        self.data = data
        self.update_table()

    def update_table(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def add_item(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def edit_item(self):
        raise NotImplementedError("This method should be implemented by subclasses.")

    def delete_item(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            del self.data[selected_row]
            self.update_table()

    def get_data(self):
        return self.data
