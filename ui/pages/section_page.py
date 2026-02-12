
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton, QDialogButtonBox, QTableWidgetItem
from .base_page import BasePage
from core.data_models import Section

class SectionDialog(QDialog):
    def __init__(self, section=None):
        super().__init__()
        self.setWindowTitle("Add/Edit Section")
        layout = QFormLayout()
        
        self.name_input = QLineEdit(section.name if section else "")
        self.semester_input = QSpinBox()
        self.semester_input.setValue(section.semester if section else 1)
        self.strength_input = QSpinBox()
        self.strength_input.setRange(1, 200)
        self.strength_input.setValue(section.strength if section else 60)
        
        layout.addRow("Name:", self.name_input)
        layout.addRow("Semester:", self.semester_input)
        layout.addRow("Strength:", self.strength_input)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "semester": self.semester_input.value(),
            "strength": self.strength_input.value()
        }

class SectionPage(BasePage):
    def __init__(self):
        super().__init__("Sections Management")

    def update_table(self):
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Semester", "Strength"])
        self.table.setRowCount(len(self.data))
        for i, section in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(section.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(section.semester)))
            self.table.setItem(i, 2, QTableWidgetItem(str(section.strength)))

    def add_item(self):
        dialog = SectionDialog()
        if dialog.exec_():
            data = dialog.get_data()
            new_id = max([s.id for s in self.data]) + 1 if self.data else 1
            section = Section(id=new_id, **data)
            self.data.append(section)
            self.update_table()

    def edit_item(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            section = self.data[selected_row]
            dialog = SectionDialog(section)
            if dialog.exec_():
                data = dialog.get_data()
                section.name = data['name']
                section.semester = data['semester']
                section.strength = data['strength']
                self.update_table()
