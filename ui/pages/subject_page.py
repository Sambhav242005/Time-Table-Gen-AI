
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton, QDialogButtonBox, QTableWidgetItem, QCheckBox
from .base_page import BasePage
from core.data_models import Subject

class SubjectDialog(QDialog):
    def __init__(self, subject=None):
        super().__init__()
        self.setWindowTitle("Add/Edit Subject")
        layout = QFormLayout()
        
        self.code_input = QLineEdit(subject.code if subject else "")
        self.name_input = QLineEdit(subject.name if subject else "")
        self.credits_input = QSpinBox()
        self.credits_input.setValue(subject.credits if subject else 3)
        self.theory_lectures_input = QSpinBox()
        self.theory_lectures_input.setValue(subject.theory_lectures_per_week if subject else 3)
        self.lab_hours_input = QSpinBox()
        self.lab_hours_input.setValue(subject.lab_hours_per_week if subject else 0)
        self.lab_batch_size_input = QSpinBox()
        self.lab_batch_size_input.setValue(subject.lab_batch_size if subject else 20)

        layout.addRow("Code:", self.code_input)
        layout.addRow("Name:", self.name_input)
        layout.addRow("Credits:", self.credits_input)
        layout.addRow("Theory Lectures per Week:", self.theory_lectures_input)
        layout.addRow("Lab Hours per Week:", self.lab_hours_input)
        layout.addRow("Lab Batch Size:", self.lab_batch_size_input)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_data(self):
        return {
            "code": self.code_input.text(),
            "name": self.name_input.text(),
            "credits": self.credits_input.value(),
            "theory_lectures_per_week": self.theory_lectures_input.value(),
            "lab_hours_per_week": self.lab_hours_input.value(),
            "lab_batch_size": self.lab_batch_size_input.value()
        }

class SubjectPage(BasePage):
    def __init__(self):
        super().__init__("Subjects Management")

    def update_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Credits", "Theory (hrs)", "Lab (hrs)", "Lab Batch Size"])
        self.table.setRowCount(len(self.data))
        for i, subject in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(subject.code))
            self.table.setItem(i, 1, QTableWidgetItem(subject.name))
            self.table.setItem(i, 2, QTableWidgetItem(str(subject.credits)))
            self.table.setItem(i, 3, QTableWidgetItem(str(subject.theory_lectures_per_week)))
            self.table.setItem(i, 4, QTableWidgetItem(str(subject.lab_hours_per_week)))
            self.table.setItem(i, 5, QTableWidgetItem(str(subject.lab_batch_size)))

    def add_item(self):
        dialog = SubjectDialog()
        if dialog.exec_():
            data = dialog.get_data()
            new_id = max([s.id for s in self.data]) + 1 if self.data else 1
            
            # Create theory subject
            theory_subject = Subject(id=new_id, **data)
            self.data.append(theory_subject)

            # Create lab subject if lab hours > 0
            if data['lab_hours_per_week'] > 0:
                lab_data = data.copy()
                lab_data['code'] = f"{data['code']}(p)"
                lab_data['name'] = f"{data['name']} (Lab)"
                lab_data['theory_lectures_per_week'] = 0
                lab_id = new_id + 1
                lab_subject = Subject(id=lab_id, **lab_data)
                self.data.append(lab_subject)

            self.update_table()

    def edit_item(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            subject = self.data[selected_row]
            dialog = SubjectDialog(subject)
            if dialog.exec_():
                data = dialog.get_data()
                subject.code = data['code']
                subject.name = data['name']
                subject.credits = data['credits']
                subject.theory_lectures_per_week = data['theory_lectures_per_week']
                subject.lab_hours_per_week = data['lab_hours_per_week']
                subject.lab_batch_size = data['lab_batch_size']
                self.update_table()
