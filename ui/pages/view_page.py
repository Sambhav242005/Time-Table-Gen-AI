
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class ViewPage(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title = QLabel("VIEW GENERATED TIMETABLES")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.view_tabs = QTabWidget()
        
        layout.addWidget(title)
        layout.addWidget(self.view_tabs)
        self.setLayout(layout)

    def update_view(self, generated_timetables):
        self.view_tabs.clear()
        if not generated_timetables:
            return

        for section_name, timetable in generated_timetables.items():
            table = self._create_timetable_table(timetable)
            self.view_tabs.addTab(table, section_name)

    def _create_timetable_table(self, timetable_data):
        if not timetable_data:
            return QLabel("No timetable generated for this section.")

        days = list(timetable_data.keys())
        if not days:
            return QLabel("Timetable data is empty.")
            
        slots = list(timetable_data[days[0]].keys())
        
        table = QTableWidget(len(slots), len(days))
        table.setHorizontalHeaderLabels(days)
        table.setVerticalHeaderLabels(slots)

        for day_idx, day in enumerate(days):
            for slot_idx, slot in enumerate(slots):
                entry = timetable_data[day][slot]
                if entry:
                    item_text = f"{entry['subject']}\n({entry['teacher']})\n[{entry['room']}]"
                    table.setItem(slot_idx, day_idx, QTableWidgetItem(item_text))
        
        table.resizeRowsToContents()
        table.resizeColumnsToContents()
        return table

