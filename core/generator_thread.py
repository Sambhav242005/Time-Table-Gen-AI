
import random
import math
from PyQt5.QtCore import QThread, pyqtSignal
from collections import defaultdict
from core.data_models import Teacher, Subject, Section, Room, RoomType

class TimetableGeneratorThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(dict)
    generation_failed = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.slots_per_day = 6
        self.timetable = {}
        self.teacher_availability = {}
        self.room_availability = {}
        self.section_availability = {}
        self.teacher_load = {}

    def run(self):
        try:
            self.status_updated.emit("Starting timetable generation...")
            self.progress_updated.emit(10)

            self._initialize_resources()
            self.status_updated.emit("Initialized resources.")
            self.progress_updated.emit(20)

            events_to_schedule = self._prepare_events()
            self.status_updated.emit(f"Prepared {len(events_to_schedule)} events to schedule.")
            self.progress_updated.emit(40)

            self.status_updated.emit("Solving...")
            if self._solve(events_to_schedule):
                self.status_updated.emit("Generation complete!")
                self.progress_updated.emit(100)
                self.generation_completed.emit(self.timetable)
            else:
                self.generation_failed.emit("Could not find a valid timetable.")

        except Exception as e:
            self.generation_failed.emit(f"An error occurred: {str(e)}")

    def _initialize_resources(self):
        self.teachers = {t['id']: Teacher(**t) for t in self.config.get("teachers", [])}
        self.subjects = {s['id']: Subject(**s) for s in self.config.get("subjects", [])}
        self.sections = {s['id']: Section(**s) for s in self.config.get("sections", [])}
        self.rooms = {r['id']: Room(**r) for r in self.config.get("rooms", [])}
        
        self.subject_teacher_assignments = self.config.get("subject_teacher_assignments", {})
        self.section_subject_assignments = self.config.get("section_subject_assignments", {})

        for teacher_id in self.teachers:
            self.teacher_availability[teacher_id] = {day: [True] * self.slots_per_day for day in self.days}
            self.teacher_load[teacher_id] = {'weekly': 0, 'daily': {day: 0 for day in self.days}}
        for room_id in self.rooms:
            self.room_availability[room_id] = {day: [True] * self.slots_per_day for day in self.days}
        for section_id, section in self.sections.items():
            self.section_availability[section_id] = {day: [True] * self.slots_per_day for day in self.days}
            self.timetable[section.name] = {day: [None] * self.slots_per_day for day in self.days}

    def _prepare_events(self):
        events = []
        for section_id, subject_ids in self.section_subject_assignments.items():
            section = self.sections.get(int(section_id))
            if not section: continue

            for subject_id in subject_ids:
                subject = self.subjects.get(int(subject_id))
                if not subject: continue

                for _ in range(subject.theory_lectures_per_week):
                    events.append({"section_id": section.id, "subject_id": subject.id, "type": "theory", "duration": 1})

                if subject.lab_hours_per_week > 0 and subject.lab_batch_size > 0:
                    num_batches = math.ceil(section.strength / subject.lab_batch_size)
                    lab_sessions = subject.lab_hours_per_week // 2
                    for i in range(num_batches):
                        for _ in range(lab_sessions):
                            events.append({"section_id": section.id, "subject_id": subject.id, "type": "lab", "duration": 2, "batch": i + 1})
        
        random.shuffle(events)
        return events

    def _solve(self, events):
        if not events:
            return True

        event = events[0]
        section_id = event["section_id"]
        subject_id = event["subject_id"]
        
        section = self.sections[section_id]
        subject = self.subjects[subject_id]
        possible_teacher_ids = self.subject_teacher_assignments.get(str(subject_id), [])

        for teacher_id in possible_teacher_ids:
            teacher = self.teachers[teacher_id]
            for day in self.days:
                for slot in range(self.slots_per_day - event["duration"] + 1):
                    if self._is_valid_placement(day, slot, event, section, teacher):
                        
                        room = self._find_available_room(day, slot, event, section)
                        if room:
                            self._place_event(day, slot, event, section, subject, teacher, room)
                            
                            if self._solve(events[1:]):
                                return True
                            
                            self._remove_event(day, slot, event, section, teacher, room)
        return False

    def _is_valid_placement(self, day, slot, event, section, teacher):
        duration = event["duration"]
        
        for i in range(duration):
            if not (self.section_availability[section.id][day][slot + i] and 
                    self.teacher_availability[teacher.id][day][slot + i]):
                return False

        # Check teacher load
        if (self.teacher_load[teacher.id]['weekly'] + duration > teacher.max_weekly_load or
            self.teacher_load[teacher.id]['daily'][day] + duration > teacher.max_daily_load):
            return False
        
        return True

    def _find_available_room(self, day, slot, event, section):
        duration = event["duration"]
        event_type = event["type"]
        
        required_capacity = section.strength
        if event_type == "lab":
            required_capacity = self.subjects[event["subject_id"]].lab_batch_size

        room_type_needed = RoomType.LAB if event_type == "lab" else RoomType.CLASSROOM
        
        for room_id, room in self.rooms.items():
            if room.type == room_type_needed.value and room.capacity >= required_capacity:
                is_available = all(self.room_availability[room_id][day][slot + i] for i in range(duration))
                if is_available:
                    return room
        return None

    def _place_event(self, day, slot, event, section, subject, teacher, room):
        duration = event["duration"]
        for i in range(duration):
            entry = {
                "subject": subject.name,
                "teacher": teacher.name,
                "room": room.name,
                "type": event["type"]
            }
            if "batch" in event:
                entry["batch"] = f"P{event['batch']}"
            
            self.timetable[section.name][day][slot + i] = entry
            self.section_availability[section.id][day][slot + i] = False
            self.teacher_availability[teacher.id][day][slot + i] = False
            self.room_availability[room.id][day][slot + i] = False
        
        self.teacher_load[teacher.id]['weekly'] += duration
        self.teacher_load[teacher.id]['daily'][day] += duration

    def _remove_event(self, day, slot, event, section, teacher, room):
        duration = event["duration"]
        for i in range(duration):
            self.timetable[section.name][day][slot + i] = None
            self.section_availability[section.id][day][slot + i] = True
            self.teacher_availability[teacher.id][day][slot + i] = True
            self.room_availability[room.id][day][slot + i] = True
            
        self.teacher_load[teacher.id]['weekly'] -= duration
        self.teacher_load[teacher.id]['daily'][day] -= duration
