
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton,
    QDialogButtonBox, QTableWidgetItem, QVBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QHBoxLayout
)
from PyQt5.QtCore import Qt
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


class SubjectAssignDialog(QDialog):
    """Dialog to assign subjects a teacher can teach."""

    def __init__(self, teacher_name, all_subjects, assigned_subject_ids):
        super().__init__()
        self.setWindowTitle(f"Assign Subjects — {teacher_name}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Select subjects that <b>{teacher_name}</b> can teach:"))

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

        # Select All / Deselect All buttons
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


class TeacherPage(BasePage):
    def __init__(self):
        # teacher_id -> list of subject_ids they can teach
        self.teacher_subject_map = {}
        # reference to all subjects (set externally by main_window)
        self._all_subjects = []
        super().__init__("Teachers Management")
        self._add_assign_button()

    def _add_assign_button(self):
        """Add an 'Assign Subjects' button next to the existing buttons."""
        assign_btn = QPushButton("Assign Subjects")
        assign_btn.setStyleSheet(
            "QPushButton { background-color: #6f42c1; color: white; "
            "padding: 6px 14px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #5a32a3; }"
        )
        assign_btn.clicked.connect(self.assign_subjects)
        # Insert into the button layout (layout -> last item is the button QHBoxLayout)
        main_layout = self.layout()
        # The button layout is the last layout item
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Code", "Max Daily", "Weekly", "Assigned Subjects"])
        self.table.setRowCount(len(self.data))
        for i, teacher in enumerate(self.data):
            self.table.setItem(i, 0, QTableWidgetItem(teacher.name))
            self.table.setItem(i, 1, QTableWidgetItem(teacher.code))
            self.table.setItem(i, 2, QTableWidgetItem(str(teacher.max_daily_load)))
            self.table.setItem(i, 3, QTableWidgetItem(str(teacher.max_weekly_load)))
            # Show assigned subject codes
            assigned_ids = self.teacher_subject_map.get(teacher.id, [])
            subj_codes = []
            for subj in self._all_subjects:
                if subj.id in assigned_ids:
                    subj_codes.append(subj.code)
            self.table.setItem(i, 4, QTableWidgetItem(", ".join(subj_codes) if subj_codes else "—"))
        self.table.resizeColumnsToContents()

    def assign_subjects(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return
        teacher = self.data[selected_row]
        assigned = self.teacher_subject_map.get(teacher.id, [])
        dialog = SubjectAssignDialog(teacher.name, self._all_subjects, assigned)
        if dialog.exec_():
            self.teacher_subject_map[teacher.id] = dialog.get_selected_ids()
            self.update_table()

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
