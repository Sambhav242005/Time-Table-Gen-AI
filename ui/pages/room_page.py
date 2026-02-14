
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton,
    QDialogButtonBox, QTableWidgetItem, QComboBox, QVBoxLayout,
    QLabel, QHBoxLayout
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
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


class AssignSectionDialog(QDialog):
    """Dialog to pre-assign a classroom to a section."""

    def __init__(self, room_name, all_sections, current_section_id):
        super().__init__()
        self.setWindowTitle(f"Assign Section — {room_name}")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Assign a section to <b>{room_name}</b>:"))

        self.combo = QComboBox()
        self.combo.addItem("— None (unassigned) —", None)
        for sec in all_sections:
            self.combo.addItem(sec.name, sec.id)
            if sec.id == current_section_id:
                self.combo.setCurrentIndex(self.combo.count() - 1)

        layout.addWidget(self.combo)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_selected_section_id(self):
        return self.combo.currentData()


class RoomPage(BasePage):
    def __init__(self):
        # room_id -> section_id (pre-assigned section for classrooms)
        self.room_section_map = {}
        # reference to all sections (set externally)
        self._all_sections = []
        super().__init__("Rooms Management")
        self._add_assign_button()

    def _add_assign_button(self):
        """Add an 'Assign Section' button."""
        assign_btn = QPushButton("Assign Section")
        assign_btn.setStyleSheet(
            "QPushButton { background-color: #007bff; color: white; "
            "padding: 6px 14px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #0056b3; }"
        )
        assign_btn.clicked.connect(self.assign_section)
        main_layout = self.layout()
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item.layout() is not None:
                item.layout().addWidget(assign_btn)
                break

    def set_all_sections(self, sections):
        """Called by main_window to provide the list of all sections."""
        self._all_sections = sections
        self.update_table()

    def update_table(self):
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Type", "Capacity", "Lab Type", "Assigned Section"]
        )
        self.table.setRowCount(len(self.data))
        for i, room in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(room.name))
            self.table.setItem(i, 1, QTableWidgetItem(room.type.value))
            self.table.setItem(i, 2, QTableWidgetItem(str(room.capacity)))
            self.table.setItem(i, 3, QTableWidgetItem(room.lab_type or "N/A"))

            # Show assigned section name
            assigned_sid = self.room_section_map.get(room.id)
            sec_name = "—"
            if assigned_sid is not None:
                for sec in self._all_sections:
                    if sec.id == assigned_sid:
                        sec_name = sec.name
                        break
            item = QTableWidgetItem(sec_name)
            if sec_name != "—":
                item.setForeground(QColor("#007bff"))
            self.table.setItem(i, 4, item)

        self.table.resizeColumnsToContents()

    def assign_section(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        room = self.data[selected_row]
        if room.type != RoomType.CLASSROOM:
            return  # Only classrooms can be assigned to sections
        current = self.room_section_map.get(room.id)
        dialog = AssignSectionDialog(room.name, self._all_sections, current)
        if dialog.exec_():
            sec_id = dialog.get_selected_section_id()
            if sec_id is not None:
                self.room_section_map[room.id] = sec_id
            elif room.id in self.room_section_map:
                del self.room_section_map[room.id]
            self.update_table()

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
