
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton,
    QDialogButtonBox, QTableWidgetItem, QVBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QHBoxLayout
)
from PyQt5.QtCore import Qt
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


class SubjectAssignDialog(QDialog):
    """Dialog to assign subjects to a section."""

    def __init__(self, section_name, all_subjects, assigned_subject_ids):
        super().__init__()
        self.setWindowTitle(f"Assign Subjects — {section_name}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Select subjects for <b>{section_name}</b>:"))

        self.list_widget = QListWidget()
        for subj in all_subjects:
            item = QListWidgetItem(f"{subj.code} — {subj.name}")
            item.setData(Qt.UserRole, subj.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Checked if subj.id in assigned_subject_ids else Qt.Unchecked
            )
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_row.addWidget(select_all_btn)
        btn_row.addWidget(deselect_all_btn)
        layout.addLayout(btn_row)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def _select_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def _deselect_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def get_selected_ids(self):
        ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                ids.append(item.data(Qt.UserRole))
        return ids


class SectionPage(BasePage):
    def __init__(self):
        # section_id -> list of subject_ids assigned to it
        self.section_subject_map = {}
        # reference to all subjects (set externally by main_window)
        self._all_subjects = []
        super().__init__("Sections Management")
        self._add_assign_button()

    def _add_assign_button(self):
        """Add an 'Assign Subjects' button."""
        assign_btn = QPushButton("Assign Subjects")
        assign_btn.setStyleSheet(
            "QPushButton { background-color: #28a745; color: white; "
            "padding: 6px 14px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #218838; }"
        )
        assign_btn.clicked.connect(self.assign_subjects)
        main_layout = self.layout()
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item.layout() is not None:
                item.layout().addWidget(assign_btn)
                break

    def set_all_subjects(self, subjects):
        """Called by main_window to provide the list of all subjects."""
        self._all_subjects = subjects
        self.update_table()

    def update_table(self):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Semester", "Strength", "Assigned Subjects"])
        self.table.setRowCount(len(self.data))
        for i, section in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(section.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(section.semester)))
            self.table.setItem(i, 2, QTableWidgetItem(str(section.strength)))
            # Show assigned subject codes
            assigned_ids = self.section_subject_map.get(section.id, [])
            subj_codes = []
            for subj in self._all_subjects:
                if subj.id in assigned_ids:
                    subj_codes.append(subj.code)
            self.table.setItem(i, 3, QTableWidgetItem(
                ", ".join(subj_codes) if subj_codes else "—"
            ))
        self.table.resizeColumnsToContents()

    def assign_subjects(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        section = self.data[selected_row]
        assigned = self.section_subject_map.get(section.id, [])
        dialog = SubjectAssignDialog(section.name, self._all_subjects, assigned)
        if dialog.exec_():
            self.section_subject_map[section.id] = dialog.get_selected_ids()
            self.update_table()

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
