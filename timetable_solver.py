#!/usr/bin/env python3
"""
University Timetable Generator using OR-Tools CP-SAT
Complete implementation with all hard and soft constraints.

Author: Automated Timetable System
"""

from ortools.sat.python import cp_model
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import json
from datetime import datetime


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Subject:
    """Represents a subject/course"""

    code: str
    name: str
    has_practical: bool
    practical_code: Optional[str] = None
    theory_hours_per_week: int = 3
    practical_sessions_per_week: int = 0

    def __post_init__(self):
        if self.has_practical and self.practical_code is None:
            self.practical_code = f"{self.code}(P)"


@dataclass
class Class:
    """Represents a student group/class"""

    code: str
    name: str
    size: int
    subjects: List[str] = field(default_factory=list)  # Subject codes they take


@dataclass
class Teacher:
    """Represents a teacher"""

    code: str
    name: str
    max_daily_hours: int = 6
    max_weekly_hours: int = 30
    can_teach: List[str] = field(default_factory=list)  # Subject codes
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
    day: int  # 0-indexed day (0=Monday, etc.)
    slot: int  # 0-indexed slot within day
    day_name: str
    time: str


# ============================================================================
# EXAMPLE DATASET
# ============================================================================


def create_example_dataset():
    """
    Create example dataset:
    - 3 classes (CS-A, CS-B, EC-A)
    - 4 subjects (CS101, CS102, MA101, PH101)
    - 2 labs (Lab1, Lab2)
    - 4 teachers (T1, T2, T3, T4)
    - 12 slots (2 days × 6 slots)
    """

    # Subjects
    subjects = [
        Subject(
            "CS101",
            "Intro to Programming",
            True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
        ),
        Subject(
            "CS102",
            "Data Structures",
            True,
            theory_hours_per_week=3,
            practical_sessions_per_week=2,
        ),
        Subject("MA101", "Mathematics I", False, theory_hours_per_week=4),
        Subject(
            "PH101",
            "Physics I",
            True,
            theory_hours_per_week=3,
            practical_sessions_per_week=1,
        ),
    ]

    # Classes
    classes = [
        Class("C1", "CS-A", 30, ["CS101", "CS102", "MA101", "PH101"]),
        Class("C2", "CS-B", 35, ["CS101", "CS102", "MA101", "PH101"]),
        Class("C3", "EC-A", 40, ["MA101", "PH101"]),  # Electronics class
    ]

    # Teachers
    teachers = [
        Teacher("T1", "Prof. Smith", 6, 24, ["CS101", "CS102"]),
        Teacher("T2", "Prof. Johnson", 6, 24, ["CS101", "MA101"]),
        Teacher("T3", "Prof. Williams", 6, 24, ["CS102", "MA101", "PH101"]),
        Teacher("T4", "Prof. Brown", 6, 24, ["PH101"]),
    ]

    # Rooms
    rooms = [
        Room("R1", "Room 101", "lecture", 50),
        Room("R2", "Room 102", "lecture", 50),
        Room("R3", "Room 103", "lecture", 40),
        Room("L1", "Lab 1", "lab", 20),  # CS Lab
        Room("L2", "Lab 2", "lab", 25),  # Physics Lab
    ]

    # Fixed lab assignments
    lab_assignments = {
        "CS101": "L1",
        "CS102": "L1",
        "PH101": "L2",
    }

    # Time slots: 2 days × 6 slots = 12 slots
    days = ["Monday", "Tuesday"]
    slots_per_day = 6
    time_slots = []

    slot_idx = 0
    for day_idx, day_name in enumerate(days):
        for slot_num in range(slots_per_day):
            time_str = f"{9 + slot_num}:00"  # 9 AM to 2 PM
            time_slots.append(TimeSlot(slot_idx, day_idx, slot_num, day_name, time_str))
            slot_idx += 1

    return {
        "subjects": subjects,
        "classes": classes,
        "teachers": teachers,
        "rooms": rooms,
        "lab_assignments": lab_assignments,
        "time_slots": time_slots,
        "days": days,
        "slots_per_day": slots_per_day,
    }


# ============================================================================
# TIMETABLE SOLVER
# ============================================================================


class TimetableSolver:
    """CP-SAT based timetable solver"""

    def __init__(self, data: dict):
        self.data = data
        self.subjects = {s.code: s for s in data["subjects"]}
        self.classes = {c.code: c for c in data["classes"]}
        self.teachers = {t.code: t for t in data["teachers"]}
        self.rooms = {r.code: r for r in data["rooms"]}
        self.lab_assignments = data["lab_assignments"]
        self.time_slots = data["time_slots"]
        self.days = data["days"]
        self.slots_per_day = data["slots_per_day"]

        # CP-SAT model
        self.model = cp_model.CpModel()
        self.solver = None

        # Decision variables
        self.x = {}  # x[s,c,t,r,k] - main assignment variable
        self.y = {}  # y[c,k] - class busy indicator
        self.w = {}  # w[t,d] - teacher daily hours
        self.gaps = {}  # g[c,k] - gap indicator

        # Objective weights
        self.W_GAP = 100
        self.W_BALANCE = 10
        self.W_ROOM_CHANGE = 5
        self.W_CONSECUTIVE = 1

    def _get_teacher_can_teach(self, teacher_code: str, subject_code: str) -> bool:
        """Check if teacher can teach subject"""
        teacher = self.teachers[teacher_code]
        return subject_code in teacher.can_teach

    def _get_lab_for_subject(self, subject_code: str) -> Optional[str]:
        """Get fixed lab for subject if it has practical"""
        subject = self.subjects[subject_code]
        if subject.has_practical:
            # Use lab_room_code from subject directly
            return subject.lab_room_code
        return None

    def _create_variables(self):
        """Create all decision variables"""
        print("Creating decision variables...")

        # Main assignment variables: x[s,c,t,r,k]
        for s_code in self.subjects:
            for c_code in self.classes:
                cls = self.classes[c_code]
                if s_code not in cls.subjects:
                    continue

                for t_code in self.teachers:
                    if not self._get_teacher_can_teach(t_code, s_code):
                        continue

                    for r_code in self.rooms:
                        room = self.rooms[r_code]
                        subject = self.subjects[s_code]

                        # Determine appropriate rooms based on subject type
                        if subject.has_theory and not subject.has_practical:
                            # THEORY-ONLY: Can only use lecture rooms
                            if room.room_type != "lecture":
                                continue
                            if room.capacity < cls.size:
                                continue

                        elif not subject.has_theory and subject.has_practical:
                            # LAB-ONLY: Can only use assigned lab
                            if r_code != self._get_lab_for_subject(s_code):
                                continue
                            if room.capacity < cls.size:
                                # Will need batches - handled in constraints
                                pass

                        elif subject.has_theory and subject.has_practical:
                            # MIXED: Can use lecture rooms OR assigned lab
                            # (Both theory and practical sessions use appropriate rooms)
                            if room.room_type == "lecture":
                                # Theory session in lecture room
                                if room.capacity < cls.size:
                                    continue
                            elif room.room_type == "lab":
                                # Practical session in assigned lab
                                if r_code != self._get_lab_for_subject(s_code):
                                    continue
                            else:
                                continue
                        else:
                            # Invalid subject (neither theory nor practical)
                            continue

                        for k_idx, k in enumerate(self.time_slots):
                            var_name = f"x_{s_code}_{c_code}_{t_code}_{r_code}_{k_idx}"
                            self.x[(s_code, c_code, t_code, r_code, k_idx)] = (
                                self.model.NewBoolVar(var_name)
                            )

        # Class busy indicator: y[c,k]
        for c_code in self.classes:
            for k_idx, k in enumerate(self.time_slots):
                var_name = f"y_{c_code}_{k_idx}"
                self.y[(c_code, k_idx)] = self.model.NewBoolVar(var_name)

        # Teacher daily hours: w[t,d]
        for t_code in self.teachers:
            for d_idx in range(len(self.days)):
                var_name = f"w_{t_code}_{d_idx}"
                max_hours = self.teachers[t_code].max_daily_hours
                self.w[(t_code, d_idx)] = self.model.NewIntVar(0, max_hours, var_name)

        print(f"Created {len(self.x)} assignment variables")
        print(f"Created {len(self.y)} busy indicators")
        print(f"Created {len(self.w)} teacher daily hour variables")

    def _add_teacher_consistency_constraints(self):
        """
        Add constraint: Within a class-section, each subject has only ONE teacher.
        This ensures that IT-C ML is always taught by the same teacher,
        even though IT-A ML might have a different teacher.
        """
        print("Adding teacher consistency constraints...")

        for c_code in self.classes:
            for s_code in self.subjects:
                cls = self.classes[c_code]
                if s_code not in cls.subjects:
                    continue

                # Get all teachers who can teach this subject
                eligible_teachers = [
                    t_code
                    for t_code in self.teachers
                    if self._get_teacher_can_teach(t_code, s_code)
                ]

                if len(eligible_teachers) <= 1:
                    continue  # Only one teacher can teach, no choice needed

                # Create teacher selection variable: which teacher teaches this subject to this class
                teacher_vars = []
                for t_code in eligible_teachers:
                    # Check if this teacher has any variables for this subject-class
                    has_any_session = False
                    for k_idx in range(len(self.time_slots)):
                        for r_code in self.rooms:
                            key = (s_code, c_code, t_code, r_code, k_idx)
                            if key in self.x:
                                has_any_session = True
                                break
                        if has_any_session:
                            break

                    if has_any_session:
                        # Create indicator: does this teacher teach this subject to this class?
                        t_indicator = self.model.NewBoolVar(
                            f"teaches_{s_code}_{c_code}_{t_code}"
                        )
                        teacher_vars.append(t_indicator)

                        # t_indicator = 1 iff sum of all x[s,c,t,*,*] >= 1
                        all_sessions = []
                        for k_idx in range(len(self.time_slots)):
                            for r_code in self.rooms:
                                key = (s_code, c_code, t_code, r_code, k_idx)
                                if key in self.x:
                                    all_sessions.append(self.x[key])

                        if all_sessions:
                            # t_indicator implies at least one session
                            self.model.Add(sum(all_sessions) >= 1).OnlyEnforceIf(
                                t_indicator
                            )
                            # Not t_indicator implies no sessions
                            self.model.Add(sum(all_sessions) == 0).OnlyEnforceIf(
                                t_indicator.Not()
                            )

                # Exactly one teacher must be selected for this subject-class pair
                if len(teacher_vars) > 1:
                    self.model.Add(sum(teacher_vars) == 1)
                    print(
                        f"  Enforcing single teacher for {s_code} in {c_code} ({len(teacher_vars)} eligible teachers)"
                    )

    def _add_hard_constraints(self):
        """Add all hard constraints"""
        print("Adding hard constraints...")

        # 1. Class conflict: At most one session per class per slot
        for c_code in self.classes:
            for k_idx, k in enumerate(self.time_slots):
                class_vars = []
                for s_code in self.subjects:
                    for t_code in self.teachers:
                        for r_code in self.rooms:
                            key = (s_code, c_code, t_code, r_code, k_idx)
                            if key in self.x:
                                class_vars.append(self.x[key])

                if class_vars:
                    self.model.Add(sum(class_vars) <= 1)

        # 2. Teacher conflict: Teacher in at most one place at a time
        for t_code in self.teachers:
            for k_idx, k in enumerate(self.time_slots):
                teacher_vars = []
                for s_code in self.subjects:
                    for c_code in self.classes:
                        for r_code in self.rooms:
                            key = (s_code, c_code, t_code, r_code, k_idx)
                            if key in self.x:
                                teacher_vars.append(self.x[key])

                if teacher_vars:
                    self.model.Add(sum(teacher_vars) <= 1)

        # 3. Room conflict: At most one session per room per slot
        for r_code in self.rooms:
            for k_idx, k in enumerate(self.time_slots):
                room_vars = []
                for s_code in self.subjects:
                    for c_code in self.classes:
                        for t_code in self.teachers:
                            key = (s_code, c_code, t_code, r_code, k_idx)
                            if key in self.x:
                                room_vars.append(self.x[key])

                if room_vars:
                    self.model.Add(sum(room_vars) <= 1)

        # 4. Link y[c,k] with x variables (class busy indicator)
        for c_code in self.classes:
            for k_idx, k in enumerate(self.time_slots):
                class_vars = []
                for s_code in self.subjects:
                    for t_code in self.teachers:
                        for r_code in self.rooms:
                            key = (s_code, c_code, t_code, r_code, k_idx)
                            if key in self.x:
                                class_vars.append(self.x[key])

                if class_vars:
                    # y[c,k] = 1 iff sum of class_vars >= 1
                    self.model.Add(self.y[(c_code, k_idx)] == sum(class_vars))
                else:
                    self.model.Add(self.y[(c_code, k_idx)] == 0)

        # 5. Teacher daily hour limits
        for t_code in self.teachers:
            teacher = self.teachers[t_code]
            for d_idx in range(len(self.days)):
                daily_vars = []
                for k_idx, k in enumerate(self.time_slots):
                    if k.day == d_idx:
                        for s_code in self.subjects:
                            for c_code in self.classes:
                                for r_code in self.rooms:
                                    key = (s_code, c_code, t_code, r_code, k_idx)
                                    if key in self.x:
                                        daily_vars.append(self.x[key])

                if daily_vars:
                    self.model.Add(self.w[(t_code, d_idx)] == sum(daily_vars))
                    self.model.Add(self.w[(t_code, d_idx)] <= teacher.max_daily_hours)
                else:
                    self.model.Add(self.w[(t_code, d_idx)] == 0)

        # 6. Teacher weekly hour limits
        for t_code in self.teachers:
            teacher = self.teachers[t_code]
            weekly_sum = sum(self.w[(t_code, d_idx)] for d_idx in range(len(self.days)))
            self.model.Add(weekly_sum <= teacher.max_weekly_hours)

        # 7. Required theory hours per subject per class
        for s_code, subject in self.subjects.items():
            # Skip if subject has no theory component
            if not subject.has_theory:
                continue

            for c_code, cls in self.classes.items():
                if s_code not in cls.subjects:
                    continue

                # Count theory hours (lecture room sessions)
                theory_vars = []
                for k_idx, k in enumerate(self.time_slots):
                    for t_code in self.teachers:
                        for r_code in self.rooms:
                            room = self.rooms[r_code]
                            if room.room_type == "lecture":
                                key = (s_code, c_code, t_code, r_code, k_idx)
                                if key in self.x:
                                    theory_vars.append(self.x[key])

                if theory_vars:
                    self.model.Add(sum(theory_vars) == subject.theory_hours_per_week)

        # 8. Required practical sessions per subject per class
        for s_code, subject in self.subjects.items():
            # Skip if subject has no practical component
            if not subject.has_practical:
                continue

            lab_room = self._get_lab_for_subject(s_code)
            if lab_room is None:
                continue

            for c_code, cls in self.classes.items():
                if s_code not in cls.subjects:
                    continue

                # Calculate batches needed
                lab_capacity = self.rooms[lab_room].capacity
                if cls.size <= lab_capacity:
                    batches_needed = 1
                else:
                    batches_needed = (cls.size + lab_capacity - 1) // lab_capacity

                # Total practical slots needed
                total_practical_slots = (
                    subject.practical_sessions_per_week * batches_needed
                )

                # Count practical hours
                practical_vars = []
                for k_idx, k in enumerate(self.time_slots):
                    for t_code in self.teachers:
                        key = (s_code, c_code, t_code, lab_room, k_idx)
                        if key in self.x:
                            practical_vars.append(self.x[key])

                if practical_vars:
                    self.model.Add(sum(practical_vars) == total_practical_slots)

        # 9. Teacher unavailability (example: T4 unavailable on Tuesday slot 0)
        for t_code, teacher in self.teachers.items():
            for k_idx in teacher.unavailable_slots:
                if k_idx < len(self.time_slots):
                    for s_code in self.subjects:
                        for c_code in self.classes:
                            for r_code in self.rooms:
                                key = (s_code, c_code, t_code, r_code, k_idx)
                                if key in self.x:
                                    self.model.Add(self.x[key] == 0)

        print("Hard constraints added successfully")

    def _add_objective(self):
        """Add soft constraints as objective function"""
        print("Adding objective function...")

        objective_terms = []

        # O1: Minimize student gaps
        # Gap = busy at k-1, free at k, busy at k+1
        for c_code in self.classes:
            for k_idx in range(1, len(self.time_slots) - 1):
                # Check if slots are on same day
                k_curr = self.time_slots[k_idx]
                k_prev = self.time_slots[k_idx - 1]
                k_next = self.time_slots[k_idx + 1]

                if k_curr.day == k_prev.day == k_next.day:
                    # Create gap indicator variable
                    gap_var = self.model.NewBoolVar(f"gap_{c_code}_{k_idx}")

                    # gap = 1 if y[c,k-1]=1 and y[c,k]=0 and y[c,k+1]=1
                    # Use AddBoolAnd for this
                    self.model.AddBoolAnd(
                        [self.y[(c_code, k_idx - 1)], self.y[(c_code, k_idx + 1)]]
                    ).OnlyEnforceIf(gap_var)

                    self.model.AddBoolOr(
                        [
                            self.y[(c_code, k_idx - 1)].Not(),
                            self.y[(c_code, k_idx + 1)].Not(),
                        ]
                    ).OnlyEnforceIf(gap_var.Not())

                    self.model.Add(self.y[(c_code, k_idx)] == 0).OnlyEnforceIf(gap_var)

                    objective_terms.append(self.W_GAP * gap_var)

        # O2: Balance teacher workload (minimize daily hour variance)
        for t_code in self.teachers:
            for d_idx in range(len(self.days) - 1):
                # |w[t,d] - w[t,d+1]|
                diff_var = self.model.NewIntVar(-30, 30, f"diff_{t_code}_{d_idx}")
                abs_diff = self.model.NewIntVar(0, 30, f"abs_diff_{t_code}_{d_idx}")

                self.model.Add(
                    diff_var == self.w[(t_code, d_idx)] - self.w[(t_code, d_idx + 1)]
                )
                self.model.AddAbsEquality(abs_diff, diff_var)

                objective_terms.append(self.W_BALANCE * abs_diff)

        # O3: Prefer consecutive slots (maximize consecutive scheduling)
        # For each class-subject pair, reward consecutive slots
        for c_code in self.classes:
            for s_code in self.subjects:
                cls = self.classes[c_code]
                if s_code not in cls.subjects:
                    continue

                for k_idx in range(len(self.time_slots) - 1):
                    k_curr = self.time_slots[k_idx]
                    k_next = self.time_slots[k_idx + 1]

                    # Only consecutive slots on same day
                    if k_curr.day == k_next.day and k_next.slot == k_curr.slot + 1:
                        # Create consecutive indicator
                        consec_var = self.model.NewBoolVar(
                            f"consec_{c_code}_{s_code}_{k_idx}"
                        )

                        # Check if subject s is scheduled at k and k+1 for class c
                        vars_at_k = []
                        vars_at_k1 = []

                        for t_code in self.teachers:
                            for r_code in self.rooms:
                                key_k = (s_code, c_code, t_code, r_code, k_idx)
                                key_k1 = (s_code, c_code, t_code, r_code, k_idx + 1)

                                if key_k in self.x:
                                    vars_at_k.append(self.x[key_k])
                                if key_k1 in self.x:
                                    vars_at_k1.append(self.x[key_k1])

                        if vars_at_k and vars_at_k1:
                            # consec = 1 if scheduled at both k and k+1
                            self.model.Add(sum(vars_at_k) >= 1).OnlyEnforceIf(
                                consec_var
                            )
                            self.model.Add(sum(vars_at_k1) >= 1).OnlyEnforceIf(
                                consec_var
                            )

                            self.model.Add(sum(vars_at_k) == 0).OnlyEnforceIf(
                                consec_var.Not()
                            )

                            # We want to maximize, so subtract from objective
                            objective_terms.append(-self.W_CONSECUTIVE * consec_var)

        # Set objective
        self.model.Minimize(sum(objective_terms))
        print("Objective function added")

    def solve(self, time_limit_seconds: int = 300):
        """Solve the timetable problem"""
        print(f"\nSolving with time limit: {time_limit_seconds}s...")

        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = time_limit_seconds
        self.solver.parameters.num_search_workers = 8

        # Add solution callback for progress
        callback = SolutionPrinter()
        status = self.solver.Solve(self.model, callback)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"\nSolution found!")
            print(f"Objective value: {self.solver.ObjectiveValue()}")
            return True
        else:
            print(f"\nNo solution found. Status: {status}")
            return False

    def extract_solution(self) -> Dict:
        """Extract solution into readable format"""
        if not self.solver:
            return {}

        solution = {
            "class_timetable": {},  # class -> slot -> session
            "teacher_timetable": {},  # teacher -> slot -> session
            "room_timetable": {},  # room -> slot -> session
        }

        # Initialize empty timetables
        for c_code in self.classes:
            solution["class_timetable"][c_code] = {}
            for k_idx, k in enumerate(self.time_slots):
                solution["class_timetable"][c_code][k_idx] = None

        for t_code in self.teachers:
            solution["teacher_timetable"][t_code] = {}
            for k_idx, k in enumerate(self.time_slots):
                solution["teacher_timetable"][t_code][k_idx] = None

        for r_code in self.rooms:
            solution["room_timetable"][r_code] = {}
            for k_idx, k in enumerate(self.time_slots):
                solution["room_timetable"][r_code][k_idx] = None

        # Fill in assignments
        for key, var in self.x.items():
            if self.solver.Value(var) == 1:
                s_code, c_code, t_code, r_code, k_idx = key
                k = self.time_slots[k_idx]

                session = {
                    "subject": s_code,
                    "class": c_code,
                    "teacher": t_code,
                    "room": r_code,
                    "day": k.day_name,
                    "time": k.time,
                    "slot_index": k_idx,
                }

                solution["class_timetable"][c_code][k_idx] = session
                solution["teacher_timetable"][t_code][k_idx] = session
                solution["room_timetable"][r_code][k_idx] = session

        return solution

    def print_timetable(self, solution: Dict):
        """Print formatted timetable"""
        print("\n" + "=" * 80)
        print("CLASS TIMETABLE")
        print("=" * 80)

        for c_code in sorted(self.classes.keys()):
            cls = self.classes[c_code]
            print(f"\n{cls.name} ({cls.code}) - {cls.size} students:")
            print("-" * 80)

            # Group by day
            for d_idx, day_name in enumerate(self.days):
                day_sessions = []
                for k_idx, k in enumerate(self.time_slots):
                    if k.day == d_idx:
                        session = solution["class_timetable"][c_code][k_idx]
                        if session:
                            day_sessions.append(
                                f"  {k.time}: {session['subject']} ({session['teacher']}, {session['room']})"
                            )

                if day_sessions:
                    print(f"\n  {day_name}:")
                    for s in day_sessions:
                        print(s)

        print("\n" + "=" * 80)
        print("TEACHER SCHEDULE")
        print("=" * 80)

        for t_code in sorted(self.teachers.keys()):
            teacher = self.teachers[t_code]
            print(f"\n{teacher.name} ({teacher.code}):")
            print("-" * 80)

            weekly_hours = 0
            for d_idx, day_name in enumerate(self.days):
                day_hours = self.solver.Value(self.w[(t_code, d_idx)])
                weekly_hours += day_hours

                if day_hours > 0:
                    print(f"  {day_name}: {day_hours} hours")
                    for k_idx, k in enumerate(self.time_slots):
                        if k.day == d_idx:
                            session = solution["teacher_timetable"][t_code][k_idx]
                            if session:
                                print(
                                    f"    {k.time}: {session['subject']} - {session['class']} @ {session['room']}"
                                )

            print(f"  Weekly total: {weekly_hours}/{teacher.max_weekly_hours} hours")

        print("\n" + "=" * 80)
        print("ROOM UTILIZATION")
        print("=" * 80)

        for r_code in sorted(self.rooms.keys()):
            room = self.rooms[r_code]
            utilization = sum(
                1
                for k_idx in range(len(self.time_slots))
                if solution["room_timetable"][r_code][k_idx] is not None
            )
            print(
                f"{room.name} ({r_code}): {utilization}/{len(self.time_slots)} slots used"
            )


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Callback to print solution progress"""

    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.solution_count = 0
        self.start_time = datetime.now()

    def on_solution_callback(self):
        self.solution_count += 1
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if self.solution_count % 100 == 0:
            print(
                f"  Solutions found: {self.solution_count}, "
                f"Objective: {self.ObjectiveValue():.0f}, "
                f"Time: {elapsed:.1f}s"
            )


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Main execution"""
    print("=" * 80)
    print("UNIVERSITY TIMETABLE GENERATOR")
    print("OR-Tools CP-SAT Implementation")
    print("=" * 80)

    # Create example dataset
    print("\n1. Creating example dataset...")
    data = create_example_dataset()

    print(f"   - {len(data['subjects'])} subjects")
    print(f"   - {len(data['classes'])} classes")
    print(f"   - {len(data['teachers'])} teachers")
    print(f"   - {len(data['rooms'])} rooms ({len(data['lab_assignments'])} labs)")
    print(
        f"   - {len(data['time_slots'])} time slots ({len(data['days'])} days × {data['slots_per_day']} slots)"
    )

    # Create and solve
    print("\n2. Initializing solver...")
    solver = TimetableSolver(data)

    print("\n3. Creating variables...")
    solver._create_variables()

    print("\n4. Adding constraints...")
    solver._add_hard_constraints()
    solver._add_teacher_consistency_constraints()  # Single teacher per subject per class

    print("\n5. Adding objective...")
    solver._add_objective()

    print("\n6. Solving...")
    success = solver.solve(time_limit_seconds=60)

    if success:
        print("\n7. Extracting and displaying solution...")
        solution = solver.extract_solution()
        solver.print_timetable(solution)

        # Save solution to JSON
        output_file = "timetable_solution.json"
        with open(output_file, "w") as f:
            # Convert to serializable format
            serializable_solution = {}
            for key, value in solution.items():
                serializable_solution[key] = {str(k): v for k, v in value.items()}
            json.dump(serializable_solution, f, indent=2)
        print(f"\nSolution saved to: {output_file}")
    else:
        print("\nFailed to find a feasible solution.")
        print("Suggestions:")
        print("  - Increase time limit")
        print("  - Relax some constraints")
        print("  - Check if problem is over-constrained")

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    main()
