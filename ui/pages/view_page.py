
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt


# Batch color palette
BATCH_COLORS = {
    "P1": {"bg": "#90CAF9", "fg": "#000000"},   # Light blue
    "P2": {"bg": "#1565C0", "fg": "#FFFFFF"},   # Dark blue
    "P3": {"bg": "#7E57C2", "fg": "#FFFFFF"},   # Purple (if 3 batches)
    "P4": {"bg": "#00897B", "fg": "#FFFFFF"},   # Teal  (if 4 batches)
}
LAB_DEFAULT_COLOR = {"bg": "#00E5FF", "fg": "#000000"}  # Cyan fallback
THEORY_COLOR = {"bg": "#E8F5E9", "fg": "#000000"}       # Light green


class ViewPage(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title = QLabel("VIEW GENERATED TIMETABLES")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.category_tabs = QTabWidget()
        self.no_data_label = QLabel("No timetable generated yet. Go to GENERATE page first.")
        self.no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_data_label.setStyleSheet("color: #666; font-size: 14px; padding: 40px;")

        layout.addWidget(title)
        layout.addWidget(self.no_data_label)
        layout.addWidget(self.category_tabs)
        self.setLayout(layout)

    def update_view(self, generated_timetables):
        self.category_tabs.clear()

        # Handle both old format (flat dict) and new format (dict with sections/teachers/rooms)
        if not generated_timetables:
            self.no_data_label.show()
            self.category_tabs.hide()
            return

        self.no_data_label.hide()
        self.category_tabs.show()

        if "sections" in generated_timetables:
            # New multi-view format
            section_data = generated_timetables.get("sections", {})
            teacher_data = generated_timetables.get("teachers", {})
            room_data = generated_timetables.get("rooms", {})

            # Sections tab
            section_tabs = QTabWidget()
            for name, tt in section_data.items():
                table = self._create_timetable_table(tt, mode="section")
                section_tabs.addTab(table, name)
            self.category_tabs.addTab(section_tabs, f"📋 Sections ({len(section_data)})")

            # Teachers tab
            teacher_tabs = QTabWidget()
            for name, tt in teacher_data.items():
                table = self._create_timetable_table(tt, mode="teacher")
                teacher_tabs.addTab(table, name)
            self.category_tabs.addTab(teacher_tabs, f"👨‍🏫 Teachers ({len(teacher_data)})")

            # Rooms tab
            room_tabs = QTabWidget()
            for name, tt in room_data.items():
                table = self._create_timetable_table(tt, mode="room")
                room_tabs.addTab(table, name)
            self.category_tabs.addTab(room_tabs, f"🏫 Rooms ({len(room_data)})")
        else:
            # Legacy flat format (section-only)
            for section_name, timetable in generated_timetables.items():
                table = self._create_timetable_table(timetable, mode="section")
                self.category_tabs.addTab(table, section_name)

    def _create_timetable_table(self, timetable_data, mode="section"):
        if not timetable_data:
            return QLabel("No data.")

        days = list(timetable_data.keys())
        if not days:
            return QLabel("Timetable data is empty.")

        first_day_data = timetable_data[days[0]]
        if isinstance(first_day_data, list):
            num_slots = len(first_day_data)
            slot_labels = [f"Slot {i+1}" for i in range(num_slots)]
        else:
            slot_labels = list(first_day_data.keys())
            num_slots = len(slot_labels)

        table = QTableWidget(num_slots, len(days))
        table.setHorizontalHeaderLabels(days)
        table.setVerticalHeaderLabels([str(s) for s in slot_labels])

        for day_idx, day in enumerate(days):
            day_data = timetable_data[day]
            for slot_idx in range(num_slots):
                if isinstance(day_data, list):
                    entry = day_data[slot_idx] if slot_idx < len(day_data) else None
                else:
                    entry = day_data.get(slot_labels[slot_idx])

                if entry is None:
                    continue

                # Handle multi-entry slots (P1 + P2 overlapping)
                if isinstance(entry, list):
                    item_text, bg_color, fg_color = self._format_multi_entry(entry, mode)
                elif isinstance(entry, dict):
                    item_text, bg_color, fg_color = self._format_single_entry(entry, mode)
                else:
                    continue

                item = QTableWidgetItem(item_text)
                item.setBackground(QColor(bg_color))
                item.setForeground(QColor(fg_color))
                table.setItem(slot_idx, day_idx, item)

        table.resizeRowsToContents()
        table.resizeColumnsToContents()
        return table

    def _format_single_entry(self, entry, mode):
        """Format a single timetable entry and return (text, bg_color, fg_color)."""
        parts = [entry.get('subject', '')]

        if mode == "section":
            if entry.get('teacher'):
                parts.append(f"({entry['teacher']})")
            if entry.get('room'):
                parts.append(f"[{entry['room']}]")
        elif mode == "teacher":
            if entry.get('section'):
                parts.append(f"({entry['section']})")
            if entry.get('room'):
                parts.append(f"[{entry['room']}]")
        elif mode == "room":
            if entry.get('section'):
                parts.append(f"({entry['section']})")
            if entry.get('teacher'):
                parts.append(f"[{entry['teacher']}]")

        if entry.get('batch'):
            parts.append(f"{{{entry['batch']}}}")

        item_text = "\n".join(parts)

        # Color by type and batch
        if entry.get('type') == 'lab':
            batch = entry.get('batch', '')
            colors = BATCH_COLORS.get(batch, LAB_DEFAULT_COLOR)
            return item_text, colors["bg"], colors["fg"]
        else:
            return item_text, THEORY_COLOR["bg"], THEORY_COLOR["fg"]

    def _format_multi_entry(self, entries, mode):
        """Format multiple overlapping entries (e.g. P1 + P2) into one cell."""
        all_parts = []
        # Use the first entry's batch color as a split background
        # We'll use a gradient-style approach: show both with a separator
        for entry in entries:
            parts = [entry.get('subject', '')]

            if mode == "section":
                if entry.get('teacher'):
                    parts.append(f"({entry['teacher']})")
                if entry.get('room'):
                    parts.append(f"[{entry['room']}]")
            elif mode == "teacher":
                if entry.get('section'):
                    parts.append(f"({entry['section']})")
                if entry.get('room'):
                    parts.append(f"[{entry['room']}]")
            elif mode == "room":
                if entry.get('section'):
                    parts.append(f"({entry['section']})")
                if entry.get('teacher'):
                    parts.append(f"[{entry['teacher']}]")

            if entry.get('batch'):
                parts.append(f"{{{entry['batch']}}}")

            all_parts.append("\n".join(parts))

        item_text = "\n━━━━━━━━━━━━\n".join(all_parts)

        # For multi-entry, use a blended color (medium blue)
        return item_text, "#42A5F5", "#000000"
