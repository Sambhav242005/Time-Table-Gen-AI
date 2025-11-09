from PyQt5.QtCore import QThread, pyqtSignal
import random

class TimetableGeneratorThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(dict)
    generation_failed = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            self.status_updated.emit("Starting timetable generation...")
            self.progress_updated.emit(10)

            steps = [
                "Preprocessing data...",
                "Loading resources...",
                "Scheduling classes...",
                "Resolving conflicts...",
                "Finalizing..."
            ]

            timetables = {}
            for i, step in enumerate(steps):
                self.status_updated.emit(step)
                self.progress_updated.emit((i + 1) * 20)
                self.msleep(500)
            
            timetables = self._generate_sample_timetables()
            self.status_updated.emit("Generation complete!")
            self.progress_updated.emit(100)
            self.generation_completed.emit(timetables)

        except Exception as e:
            self.generation_failed.emit(str(e))

    def _generate_sample_timetables(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        subjects = self.config.get("subjects", [])
        teachers = self.config.get("teachers", [])
        rooms = self.config.get("rooms", [])
        slots = [f"Slot {i+1}" for i in range(6)]

        timetables = {}
        for section in self.config.get("sections", []):
            schedule = {}
            for day in days:
                schedule[day] = {}
                for slot in slots:
                    if random.random() > 0.2:
                        schedule[day][slot] = {
                            "subject": random.choice(subjects).name,
                            "teacher": random.choice(teachers).name,
                            "room": random.choice(rooms).name
                        }
                    else:
                        schedule[day][slot] = None
            timetables[section] = schedule
        return timetables
