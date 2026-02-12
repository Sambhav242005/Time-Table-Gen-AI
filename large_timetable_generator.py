#!/usr/bin/env python3
"""
Advanced University Timetable Generator with Problem Detection
Handles large datasets (10+ classes, 20+ subjects) with validation and conflict checking.
"""

from ortools.sat.python import cp_model
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import json
from datetime import datetime
from collections import defaultdict


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Subject:
    """
    Represents a subject/course

    Types:
    - Theory-only: has_theory=True, has_practical=False -> Only classroom sessions
    - Lab-only: has_theory=False, has_practical=True -> Only lab sessions
    - Mixed: has_theory=True, has_practical=True -> Both classroom + lab sessions
    """

    code: str
    name: str
    has_theory: bool = True  # Does this subject have theory sessions in classroom?
    has_practical: bool = False  # Does this subject have practical sessions in lab?
    practical_code: Optional[str] = None
    theory_hours_per_week: int = 3  # Sessions in classroom (if has_theory=True)
    practical_sessions_per_week: int = 0  # Sessions in lab (if has_practical=True)
    lab_room_code: Optional[str] = None  # Required if has_practical=True

    def __post_init__(self):
        if self.has_practical:
            if self.practical_code is None:
                self.practical_code = f"{self.code}(P)"
            # Set default practical sessions if not specified
            if self.practical_sessions_per_week == 0:
                self.practical_sessions_per_week = 2  # Default: 2 lab sessions per week

        # Validate: Must have at least theory or practical
        if not self.has_theory and not self.has_practical:
            raise ValueError(
                f"Subject {self.code} must have either theory or practical component"
            )

        # Validate: Practical subjects need lab room
        if self.has_practical and not self.lab_room_code:
            raise ValueError(
                f"Subject {self.code} has practical but no lab_room_code specified"
            )

    def get_type(self) -> str:
        """Return subject type"""
        if self.has_theory and self.has_practical:
            return "mixed"
        elif self.has_theory:
            return "theory-only"
        else:
            return "lab-only"


@dataclass
class Class:
    """Represents a student group/class"""

    code: str
    name: str
    size: int
    subjects: List[str] = field(default_factory=list)
    program: str = ""
    year: int = 1


@dataclass
class Teacher:
    """Represents a teacher"""

    code: str
    name: str
    max_daily_hours: int = 6
    max_weekly_hours: int = 30
    can_teach: List[str] = field(default_factory=list)
    preferred_slots: List[int] = field(default_factory=list)
    unavailable_slots: List[int] = field(default_factory=list)


@dataclass
class Room:
    """Represents a room"""

    code: str
    name: str
    room_type: str  # 'lecture' or 'lab'
    capacity: int
    location: str = "main"


@dataclass
class TimeSlot:
    """Represents a time slot"""

    index: int
    day: int
    slot: int
    day_name: str
    time: str


@dataclass
class ConflictReport:
    """Report of scheduling conflicts and issues"""

    teacher_overlaps: List[Dict] = field(default_factory=list)
    room_overlaps: List[Dict] = field(default_factory=list)
    capacity_issues: List[Dict] = field(default_factory=list)
    hour_violations: List[Dict] = field(default_factory=list)
    shared_teacher_conflicts: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def has_issues(self) -> bool:
        return (
            len(self.teacher_overlaps) > 0
            or len(self.room_overlaps) > 0
            or len(self.capacity_issues) > 0
            or len(self.hour_violations) > 0
            or len(self.shared_teacher_conflicts) > 0
        )

    def print_report(self):
        print("\n" + "=" * 80)
        print("CONFLICT & PROBLEM REPORT")
        print("=" * 80)

        if not self.has_issues() and len(self.warnings) == 0:
            print("[OK] No issues found!")
            return

        if self.shared_teacher_conflicts:
            print(
                f"\n[SHARED TEACHER CONFLICTS] ({len(self.shared_teacher_conflicts)}):"
            )
            for conflict in self.shared_teacher_conflicts:
                print(
                    f"  Teacher {conflict['teacher']} teaches {conflict['subject']} to:"
                )
                for cls in conflict["classes"]:
                    print(f"    - {cls}")
                print(f"  -> Must ensure no overlapping sessions!")

        if self.teacher_overlaps:
            print(f"\n[TEACHER OVERLAPS] ({len(self.teacher_overlaps)}):")
            for overlap in self.teacher_overlaps:
                print(f"  {overlap}")

        if self.room_overlaps:
            print(f"\n[ROOM OVERLAPS] ({len(self.room_overlaps)}):")
            for overlap in self.room_overlaps:
                print(f"  {overlap}")

        if self.capacity_issues:
            print(f"\n[CAPACITY ISSUES] ({len(self.capacity_issues)}):")
            for issue in self.capacity_issues:
                print(f"  {issue}")

        if self.hour_violations:
            print(f"\n[HOUR LIMIT VIOLATIONS] ({len(self.hour_violations)}):")
            for violation in self.hour_violations:
                print(f"  {violation}")

        if self.warnings:
            print(f"\n[WARNINGS] ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")


# ============================================================================
# PROBLEM FINDER / VALIDATOR
# ============================================================================


class ProblemFinder:
    """Finds potential scheduling problems before solving"""

    def __init__(self, data: dict):
        self.data = data
        self.subjects = {s.code: s for s in data["subjects"]}
        self.classes = {c.code: c for c in data["classes"]}
        self.teachers = {t.code: t for t in data["teachers"]}
        self.rooms = {r.code: r for r in data["rooms"]}
        self.report = ConflictReport()

    def find_shared_teacher_conflicts(self):
        """
        Find cases where same teacher teaches same subject to multiple classes.
        This is fine, but we need to ensure no time overlaps.
        """
        print("Checking for shared teacher conflicts...")

        # Map: (teacher, subject) -> list of classes
        teacher_subject_classes = defaultdict(list)

        for c_code, cls in self.classes.items():
            for s_code in cls.subjects:
                # Find eligible teachers for this subject
                for t_code, teacher in self.teachers.items():
                    if s_code in teacher.can_teach:
                        teacher_subject_classes[(t_code, s_code)].append(c_code)

        # Find cases where same teacher teaches same subject to multiple classes
        for (t_code, s_code), class_list in teacher_subject_classes.items():
            if len(class_list) > 1:
                teacher = self.teachers[t_code]
                subject = self.subjects[s_code]

                self.report.shared_teacher_conflicts.append(
                    {
                        "teacher": f"{teacher.name} ({t_code})",
                        "subject": f"{subject.name} ({s_code})",
                        "classes": [self.classes[c].name for c in class_list],
                        "class_codes": class_list,
                        "count": len(class_list),
                    }
                )

                print(
                    f"  Found: {teacher.name} teaches {s_code} to {len(class_list)} classes: {class_list}"
                )

    def check_capacity_fit(self):
        """Check if class sizes fit in rooms"""
        print("Checking room capacity...")

        for c_code, cls in self.classes.items():
            for s_code in cls.subjects:
                subject = self.subjects[s_code]

                # Check lecture rooms
                lecture_rooms = [
                    r for r in self.rooms.values() if r.room_type == "lecture"
                ]
                fits_lecture = any(r.capacity >= cls.size for r in lecture_rooms)

                if not fits_lecture:
                    self.report.capacity_issues.append(
                        {
                            "type": "lecture",
                            "class": f"{cls.name} ({c_code})",
                            "size": cls.size,
                            "issue": "No lecture room large enough",
                        }
                    )

                # Check lab rooms
                if subject.has_practical and subject.lab_room_code:
                    lab_room = self.rooms.get(subject.lab_room_code)
                    if lab_room:
                        if lab_room.capacity < cls.size:
                            # Need batches
                            batches_needed = (
                                cls.size + lab_room.capacity - 1
                            ) // lab_room.capacity
                            if batches_needed > 3:  # Warning if too many batches
                                self.report.warnings.append(
                                    f"{cls.name} {s_code} lab needs {batches_needed} batches (room capacity {lab_room.capacity})"
                                )

    def check_teacher_availability(self):
        """Check if teachers have enough hours"""
        print("Checking teacher availability...")

        for t_code, teacher in self.teachers.items():
            total_hours_needed = 0

            for c_code, cls in self.classes.items():
                for s_code in cls.subjects:
                    if s_code in teacher.can_teach:
                        subject = self.subjects[s_code]
                        total_hours_needed += subject.theory_hours_per_week
                        if subject.has_practical:
                            total_hours_needed += subject.practical_sessions_per_week

            if total_hours_needed > teacher.max_weekly_hours:
                self.report.hour_violations.append(
                    {
                        "teacher": f"{teacher.name} ({t_code})",
                        "needed": total_hours_needed,
                        "available": teacher.max_weekly_hours,
                        "overage": total_hours_needed - teacher.max_weekly_hours,
                    }
                )

    def validate_data(self):
        """Run all validation checks"""
        print("\n" + "=" * 80)
        print("PRE-SOLVING VALIDATION")
        print("=" * 80)

        self.find_shared_teacher_conflicts()
        self.check_capacity_fit()
        self.check_teacher_availability()

        # Additional checks
        self._check_subject_assignments()
        self._check_lab_assignments()

        return self.report

    def _check_subject_assignments(self):
        """Check if all subjects have teachers"""
        for s_code, subject in self.subjects.items():
            has_teacher = any(s_code in t.can_teach for t in self.teachers.values())
            if not has_teacher:
                self.report.warnings.append(
                    f"Subject {s_code} has no eligible teachers!"
                )

    def _check_lab_assignments(self):
        """Check if lab subjects have room assignments"""
        for s_code, subject in self.subjects.items():
            if subject.has_practical:
                if not subject.lab_room_code:
                    self.report.warnings.append(
                        f"Subject {s_code} has practical but no lab room assigned!"
                    )
                elif subject.lab_room_code not in self.rooms:
                    self.report.warnings.append(
                        f"Subject {s_code} assigned to non-existent lab {subject.lab_room_code}!"
                    )


# ============================================================================
# LARGE DATASET GENERATOR
# ============================================================================


def create_large_dataset():
    """
    Create a large dataset:
    - 10 classes
    - 20 subjects
    - 10 labs
    - 15 teachers
    - 30 time slots (5 days × 6 slots)
    """

    # 20 Subjects with different types (theory-only, lab-only, mixed)
    subjects = [
        # === MIXED SUBJECTS (Theory + Lab) ===
        # CS Core - Mixed
        Subject(
            "CS101",
            "Intro to Programming",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-CS-1",
        ),
        Subject(
            "CS102",
            "Data Structures",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-CS-1",
        ),
        Subject(
            "CS301",
            "Operating Systems",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-OS",
        ),
        Subject(
            "CS302",
            "Computer Networks",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-NET",
        ),
        # AI/ML - Mixed
        Subject(
            "ML101",
            "Machine Learning Basics",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-AI",
        ),
        Subject(
            "ML201",
            "Deep Learning",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-AI",
        ),
        Subject(
            "DS101",
            "Data Science",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-DS",
        ),
        # Cloud - Mixed
        Subject(
            "CLD101",
            "Cloud Computing",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-CLD",
        ),
        # === THEORY-ONLY SUBJECTS (Classroom only) ===
        Subject(
            "CS201",
            "Algorithms",
            has_theory=True,
            has_practical=False,
            theory_hours_per_week=3,
        ),
        Subject(
            "AI101",
            "Artificial Intelligence",
            has_theory=True,
            has_practical=False,
            theory_hours_per_week=3,
        ),
        Subject(
            "MAT101",
            "Mathematics I",
            has_theory=True,
            has_practical=False,
            theory_hours_per_week=4,
        ),
        Subject(
            "MAT201",
            "Discrete Math",
            has_theory=True,
            has_practical=False,
            theory_hours_per_week=3,
        ),
        # === LAB-ONLY SUBJECTS (Lab only, no theory classroom) ===
        Subject(
            "CLD201",
            "Private Cloud Lab",
            has_theory=False,
            has_practical=True,
            practical_sessions_per_week=3,
            lab_room_code="LAB-CLD",
        ),
        Subject(
            "CLD301",
            "Cloud Deployment Lab",
            has_theory=False,
            has_practical=True,
            practical_sessions_per_week=3,
            lab_room_code="LAB-CLD",
        ),
        Subject(
            "WEB201",
            "Web Development Lab",
            has_theory=False,
            has_practical=True,
            practical_sessions_per_week=3,
            lab_room_code="LAB-WEB",
        ),
        Subject(
            "DB201",
            "Advanced DB Lab",
            has_theory=False,
            has_practical=True,
            practical_sessions_per_week=3,
            lab_room_code="LAB-DB",
        ),
        Subject(
            "PHY201",
            "Physics Practical",
            has_theory=False,
            has_practical=True,
            practical_sessions_per_week=3,
            lab_room_code="LAB-PHY",
        ),
        Subject(
            "STAT201",
            "Statistics Lab",
            has_theory=False,
            has_practical=True,
            practical_sessions_per_week=3,
            lab_room_code="LAB-STAT",
        ),
        # === MORE MIXED SUBJECTS ===
        Subject(
            "DEV101",
            "DevOps",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-DEV",
        ),
        Subject(
            "WEB101",
            "Web Development",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-WEB",
        ),
        Subject(
            "MOB101",
            "Mobile App Dev",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-MOB",
        ),
        Subject(
            "DB101",
            "Database Systems",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-DB",
        ),
        Subject(
            "PHY101",
            "Physics I",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-PHY",
        ),
        Subject(
            "STA101",
            "Statistics",
            has_theory=True,
            has_practical=True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
            lab_room_code="LAB-STAT",
        ),
    ]

    # 10 Classes with mix of theory-only, lab-only, and mixed subjects
    classes = [
        # CS Year 1 - Mixed subjects
        Class(
            "CS-A",
            "Computer Science - A",
            45,
            ["CS101", "CS102", "CS201", "MAT101", "PHY101"],
            "CS",
            1,
        ),
        Class(
            "CS-B",
            "Computer Science - B",
            42,
            ["CS101", "CS102", "CS201", "MAT101", "PHY101"],
            "CS",
            1,
        ),
        # CS Year 2 - With lab-only subjects
        Class(
            "CS-C",
            "Computer Science - C",
            48,
            ["CS102", "CS301", "CS302", "MAT201", "DB101", "PHY201"],
            "CS",
            2,
        ),
        # AI - With lab-only practicals
        Class(
            "AI-A",
            "AI & ML - A",
            40,
            ["ML101", "ML201", "AI101", "DS101", "MAT101", "STAT201"],
            "AI",
            3,
        ),
        Class(
            "AI-B",
            "AI & ML - B",
            38,
            ["ML101", "ML201", "AI101", "DS101", "MAT201", "STAT201"],
            "AI",
            3,
        ),
        # Cloud - With lab-only deployment subjects
        Class(
            "CLD-A",
            "Cloud Computing - A",
            35,
            ["CLD101", "CLD201", "CLD301", "DEV101", "CS302", "DB101"],
            "Cloud",
            3,
        ),
        Class(
            "CLD-B",
            "Cloud Computing - B",
            36,
            ["CLD101", "CLD201", "CLD301", "DEV101", "CS302", "DB201"],
            "Cloud",
            3,
        ),
        # Web - With lab-only web dev
        Class(
            "WEB-A",
            "Web Development - A",
            50,
            ["WEB101", "WEB201", "MOB101", "CS101", "DB101", "MAT101"],
            "Web",
            2,
        ),
        # DS - With lab-only stats
        Class(
            "DS-A",
            "Data Science - A",
            32,
            ["DS101", "ML101", "STA101", "DB201", "MAT201", "STAT201"],
            "Data Science",
            3,
        ),
        # DevOps - With lab-only cloud deployment
        Class(
            "DEV-A",
            "DevOps - A",
            30,
            ["DEV101", "CLD101", "CLD301", "CS301", "DB101", "MAT101"],
            "DevOps",
            3,
        ),
    ]

    # 15 Teachers (some teach multiple subjects)
    teachers = [
        # Programming teachers (can teach multiple)
        Teacher("T-P-1", "Dr. Sarah Chen", 6, 30, ["CS101", "CS102", "WEB101"]),
        Teacher("T-P-2", "Prof. Mike Johnson", 6, 28, ["CS101", "CS102", "MOB101"]),
        Teacher("T-P-3", "Dr. Lisa Wang", 6, 25, ["CS201", "CS301", "DEV101"]),
        # ML/AI teachers
        Teacher("T-ML-1", "Dr. Rajesh Kumar", 6, 24, ["ML101", "ML201", "AI101"]),
        Teacher("T-ML-2", "Prof. Emily Zhang", 6, 24, ["ML101", "DS101", "AI101"]),
        # Cloud teachers (multi-subject)
        Teacher(
            "T-CLD-1",
            "Dr. James Wilson",
            6,
            30,
            ["CLD101", "CLD201", "CLD301", "DEV101"],
        ),
        Teacher("T-CLD-2", "Prof. Maria Garcia", 6, 24, ["CLD101", "CS302"]),
        # Database teachers
        Teacher("T-DB-1", "Dr. Ahmed Hassan", 6, 26, ["DB101", "DB201", "DS101"]),
        Teacher("T-DB-2", "Prof. Anna Smith", 6, 22, ["DB101", "DB201"]),
        # Network/Systems
        Teacher("T-NET", "Dr. David Lee", 6, 24, ["CS302", "CS301"]),
        # Web/Mobile
        Teacher("T-WEB", "Prof. Sophie Brown", 6, 24, ["WEB101", "MOB101"]),
        # Science & Math
        Teacher("T-MATH-1", "Dr. Robert Taylor", 6, 30, ["MAT101", "MAT201", "STA101"]),
        Teacher("T-MATH-2", "Prof. Jennifer White", 6, 24, ["MAT101", "MAT201"]),
        Teacher("T-PHY", "Dr. Michael Brown", 6, 20, ["PHY101"]),
        Teacher("T-STAT", "Prof. Laura Davis", 6, 22, ["STA101", "DS101"]),
    ]

    # 10 Labs + 4 Lecture halls
    rooms = [
        # Lecture halls
        Room("LH-1", "Lecture Hall 1", "lecture", 100),
        Room("LH-2", "Lecture Hall 2", "lecture", 80),
        Room("LH-3", "Lecture Hall 3", "lecture", 60),
        Room("LH-4", "Lecture Hall 4", "lecture", 60),
        # Labs (10 different labs)
        Room("LAB-CS-1", "CS Programming Lab", "lab", 25),
        Room("LAB-OS", "OS & Systems Lab", "lab", 20),
        Room("LAB-NET", "Networking Lab", "lab", 20),
        Room("LAB-AI", "AI & ML Lab", "lab", 20),
        Room("LAB-DS", "Data Science Lab", "lab", 25),
        Room("LAB-CLD", "Cloud Computing Lab", "lab", 30),
        Room("LAB-DEV", "DevOps Lab", "lab", 25),
        Room("LAB-WEB", "Web Development Lab", "lab", 30),
        Room("LAB-MOB", "Mobile Dev Lab", "lab", 25),
        Room("LAB-DB", "Database Lab", "lab", 30),
        Room("LAB-PHY", "Physics Lab", "lab", 20),
        Room("LAB-STAT", "Statistics Lab", "lab", 25),
    ]

    # Time slots: 5 days × 6 slots = 30 slots
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    slots_per_day = 6
    time_slots = []

    slot_idx = 0
    for day_idx, day_name in enumerate(days):
        for slot_num in range(slots_per_day):
            time_str = f"{9 + slot_num}:00"
            time_slots.append(TimeSlot(slot_idx, day_idx, slot_num, day_name, time_str))
            slot_idx += 1

    return {
        "subjects": subjects,
        "classes": classes,
        "teachers": teachers,
        "rooms": rooms,
        "time_slots": time_slots,
        "days": days,
        "slots_per_day": slots_per_day,
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Main execution with problem detection"""
    print("=" * 80)
    print("UNIVERSITY TIMETABLE GENERATOR WITH PROBLEM DETECTION")
    print("=" * 80)

    # Create large dataset
    print("\n1. Creating large dataset (10 classes, 20 subjects, 10 labs)...")
    data = create_large_dataset()

    print(f"   [OK] {len(data['subjects'])} subjects")
    print(f"   [OK] {len(data['classes'])} classes")
    print(f"   [OK] {len(data['teachers'])} teachers")
    print(f"   [OK] {len(data['rooms'])} rooms")
    print(f"   [OK] {len(data['time_slots'])} time slots")

    # Run problem finder
    print("\n2. Running problem finder...")
    problem_finder = ProblemFinder(data)
    report = problem_finder.validate_data()
    report.print_report()

    # Count statistics
    total_theory_hours = sum(s.theory_hours_per_week for s in data["subjects"])
    total_lab_sessions = sum(
        s.practical_sessions_per_week for s in data["subjects"] if s.has_practical
    )

    print(f"\n[DATASET STATISTICS]:")
    print(
        f"   Total theory hours to schedule: {total_theory_hours * len(data['classes'])}"
    )
    print(
        f"   Total lab sessions to schedule: {total_lab_sessions * len(data['classes'])}"
    )
    print(f"   Total slots available: {len(data['time_slots'])}")

    if report.shared_teacher_conflicts:
        print(f"\n[Shared teacher conflicts]: {len(report.shared_teacher_conflicts)}")
        print("   These will be handled automatically by the solver")

    print("\n" + "=" * 80)
    print("Validation complete! Ready for solving.")
    print("=" * 80)

    # Save dataset
    with open("large_dataset.json", "w") as f:
        # Convert to serializable format
        serializable_data = {
            "subjects": [
                {
                    "code": s.code,
                    "name": s.name,
                    "has_theory": s.has_theory,
                    "has_practical": s.has_practical,
                    "subject_type": s.get_type(),
                    "theory_hours_per_week": s.theory_hours_per_week,
                    "practical_sessions_per_week": s.practical_sessions_per_week,
                    "lab_room_code": s.lab_room_code,
                }
                for s in data["subjects"]
            ],
            "classes": [
                {
                    "code": c.code,
                    "name": c.name,
                    "size": c.size,
                    "subjects": c.subjects,
                    "program": c.program,
                    "year": c.year,
                }
                for c in data["classes"]
            ],
            "teachers": [
                {
                    "code": t.code,
                    "name": t.name,
                    "max_daily_hours": t.max_daily_hours,
                    "max_weekly_hours": t.max_weekly_hours,
                    "can_teach": t.can_teach,
                }
                for t in data["teachers"]
            ],
            "rooms": [
                {
                    "code": r.code,
                    "name": r.name,
                    "room_type": r.room_type,
                    "capacity": r.capacity,
                }
                for r in data["rooms"]
            ],
            "time_slots": len(data["time_slots"]),
            "validation_report": {
                "shared_teacher_conflicts": report.shared_teacher_conflicts,
                "capacity_issues": report.capacity_issues,
                "hour_violations": report.hour_violations,
                "warnings": report.warnings,
            },
        }
        json.dump(serializable_data, f, indent=2)

    print(f"\nDataset saved to: large_dataset.json")


if __name__ == "__main__":
    main()
