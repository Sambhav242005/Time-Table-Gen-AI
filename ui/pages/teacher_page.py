
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton, QDialogButtonBox, QTableWidgetItem
from .base_page import BasePage
from core.data_models import Teacher

class TeacherDialog(QDialog):
    def __init__(self, teacher=None):
        super().__init__()
        self.setWindowTitle("Add/Edit Teacher")
        layout = QFormLayout()
        
        self.name_input = QLineEdit(teacher.name if teacher else "")
        self.code_input = QLineEdit(teacher.code if teacher else "")
        self.max_daily_load_input = QSpinBox()
        self.max_daily_load_input.setValue(teacher.max_daily_load if teacher else 6)
        self.max_weekly_load_input = QSpinBox()
        self.max_weekly_load_input.setValue(teacher.max_weekly_load if teacher else 20)
        
        layout.addRow("Name:", self.name_input)
        layout.addRow("Code:", self.code_input)
        layout.addRow("Max Daily Load:", self.max_daily_load_input)
        layout.addRow("Max Weekly Load:", self.max_weekly_load_input)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "code": self.code_input.text(),
            "max_daily_load": self.max_daily_load_input.value(),
            "max_weekly_load": self.max_weekly_load_input.value()
        }

class TeacherPage(BasePage):
    def __init__(self):
        super().__init__("Teachers Management")

    def update_table(self):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Code", "Max Daily", "Weekly"])
        self.table.setRowCount(len(self.data))
        for i, teacher in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(teacher.name))
            self.table.setItem(i, 1, QTableWidgetItem(teacher.code))
            self.table.setItem(i, 2, QTableWidgetItem(str(teacher.max_daily_load)))
            self.table.setItem(i, 3, QTableWidgetItem(str(teacher.max_weekly_load)))

    def add_item(self):
        dialog = TeacherDialog()
        if dialog.exec_():
            data = dialog.get_data()
            new_id = max([t.id for t in self.data]) + 1 if self.data else 1
            teacher = Teacher(id=new_id, **data)
            self.data.append(teacher)
            self.update_table()

    def edit_item(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            teacher = self.data[selected_row]
            dialog = TeacherDialog(teacher)
            if dialog.exec_():
                data = dialog.get_data()
                teacher.name = data['name']
                teacher.code = data['code']
                teacher.max_daily_load = data['max_daily_load']
                teacher.max_weekly_load = data['max_weekly_load']
                self.update_table()
