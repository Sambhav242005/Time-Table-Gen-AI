
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton, QDialogButtonBox, QTableWidgetItem, QComboBox
from .base_page import BasePage
from core.data_models import Room, RoomType

class RoomDialog(QDialog):
    def __init__(self, room=None):
        super().__init__()
        self.setWindowTitle("Add/Edit Room")
        layout = QFormLayout()
        
        self.name_input = QLineEdit(room.name if room else "")
        self.capacity_input = QSpinBox()
        self.capacity_input.setRange(1, 500)
        self.capacity_input.setValue(room.capacity if room else 70)
        self.type_input = QComboBox()
        self.type_input.addItems([t.value for t in RoomType])
        if room:
            self.type_input.setCurrentText(room.type.value)
        self.lab_type_input = QLineEdit(room.lab_type if room else "")
        
        layout.addRow("Name:", self.name_input)
        layout.addRow("Capacity:", self.capacity_input)
        layout.addRow("Type:", self.type_input)
        layout.addRow("Lab Type (if applicable):", self.lab_type_input)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "capacity": self.capacity_input.value(),
            "type": RoomType(self.type_input.currentText()),
            "lab_type": self.lab_type_input.text()
        }

class RoomPage(BasePage):
    def __init__(self):
        super().__init__("Rooms Management")

    def update_table(self):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Capacity", "Lab Type"])
        self.table.setRowCount(len(self.data))
        for i, room in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(room.name))
            self.table.setItem(i, 1, QTableWidgetItem(room.type.value))
            self.table.setItem(i, 2, QTableWidgetItem(str(room.capacity)))
            self.table.setItem(i, 3, QTableWidgetItem(room.lab_type or "N/A"))

    def add_item(self):
        dialog = RoomDialog()
        if dialog.exec_():
            data = dialog.get_data()
            new_id = max([r.id for r in self.data]) + 1 if self.data else 1
            room = Room(id=new_id, **data)
            self.data.append(room)
            self.update_table()

    def edit_item(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            room = self.data[selected_row]
            dialog = RoomDialog(room)
            if dialog.exec_():
                data = dialog.get_data()
                room.name = data['name']
                room.capacity = data['capacity']
                room.type = data['type']
                room.lab_type = data['lab_type']
                self.update_table()
