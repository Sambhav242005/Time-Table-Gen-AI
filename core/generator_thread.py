import math
import os
import random
import logging
import traceback
import json
import subprocess
import sys
import uuid
from PyQt5.QtCore import QThread, pyqtSignal
from ortools.sat.python import cp_model
from core.data_models import Teacher, Subject, Section, Room, RoomType

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("generator.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


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
        self.num_flat_slots = len(self.days) * self.slots_per_day  # 30

    def _safe_emit(self, signal, value):
        if os.getenv("TT_DISABLE_EMITS"):
            return
        signal.emit(value)

    def run(self):
        try:
            logger.info("Starting generation thread...")
            # Use isolated subprocess solving on Windows by default because some OR-Tools
            # builds can terminate the process at Solve() without a Python exception.
            use_isolated_solver = (
                os.name == "nt" and not os.getenv("TT_DISABLE_SOLVER_SUBPROCESS")
            )
            if use_isolated_solver:
                self._safe_emit(self.status_updated, "Initializing solver...")
                self._safe_emit(self.progress_updated, 10)
                result = self._solve_cpsat_in_subprocess()
            else:
                self._safe_emit(self.status_updated, "Initializing resources...")
                self._safe_emit(self.progress_updated, 5)
                self._initialize_resources()
                logger.info("Resources initialized")

                events = self._prepare_events()
                if not events:
                    logger.warning("No events to schedule")
                    self.generation_failed.emit(
                        "No events to schedule. Check subject/section assignments."
                    )
                    return

                logger.info(f"Prepared {len(events)} events to schedule")
                self._safe_emit(
                    self.status_updated,
                    f"Building CP-SAT model for {len(events)} events...",
                )
                self._safe_emit(self.progress_updated, 15)
                result = self._solve_cpsat(events)
            if result is not None:
                self._safe_emit(self.progress_updated, 100)
                self._safe_emit(self.status_updated, "Generation complete!")
                logger.info("Generation completed successfully")
                self.generation_completed.emit(result)
            else:
                logger.warning("Solver could not find a valid solution")
                self.generation_failed.emit(
                    "Could not find a valid timetable.\n"
                    "Try reducing sections or adding more teachers/rooms."
                )
        except MemoryError as e:
            logger.exception(f"Memory error during generation: {e}")
            self.generation_failed.emit(
                f"Memory error: {str(e)}\n\nTry reducing the number of sections or subjects."
            )
        except RuntimeError as e:
            logger.exception(f"OR-Tools solver runtime error: {e}")
            self.generation_failed.emit(
                f"Solver error: {str(e)}\n\nThis may be due to an issue with the OR-Tools library."
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error in generation: {e}\n{traceback.format_exc()}"
            )
            self.generation_failed.emit(
                f"Error: {str(e)}\n\nSee generator.log for details."
            )

    def _solve_cpsat_in_subprocess(self):
        self._safe_emit(self.status_updated, "Building CP-SAT model...")
        self._safe_emit(self.progress_updated, 25)
        temp_root = os.path.join(os.getcwd(), "output", "tmp")
        run_dir = os.path.join(temp_root, f"tt_solver_{uuid.uuid4().hex}")
        os.makedirs(run_dir, exist_ok=True)

        input_path = os.path.join(run_dir, "solver_input.json")
        output_path = os.path.join(run_dir, "solver_output.json")
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f)

        cmd = [sys.executable, "-m", "core.solver_worker", input_path, output_path]
        logger.info(f"CP-SAT: launching isolated solver subprocess: {cmd}")
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )
        logger.info(
            f"CP-SAT: solver subprocess finished with returncode={completed.returncode}"
        )
        if completed.stdout:
            logger.info(f"CP-SAT subprocess stdout:\n{completed.stdout}")
        if completed.stderr:
            logger.warning(f"CP-SAT subprocess stderr:\n{completed.stderr}")

        if completed.returncode != 0:
            message = (
                f"Solver subprocess crashed (exit code {completed.returncode}).\n"
                "This indicates a native OR-Tools crash on this machine.\n"
            )
            if completed.stderr:
                message += f"\nDetails:\n{completed.stderr.strip()[-1200:]}"
            raise RuntimeError(message)

        if not os.path.exists(output_path):
            raise RuntimeError(
                "Solver subprocess did not produce output. Check generator.log."
            )

        with open(output_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if not payload.get("ok"):
            raise RuntimeError(payload.get("error", "Unknown solver error"))
        return payload.get("result")

    def _initialize_resources(self):
        self.teachers = {}
        teachers_data = self.config.get("teachers", [])
        if not teachers_data:
            raise ValueError("No teachers provided in configuration")

        for t in teachers_data:
            if "id" not in t or "name" not in t:
                logger.warning(f"Skipping invalid teacher data: {t}")
                continue
            t_copy = {k: v for k, v in t.items() if k != "availability"}
            self.teachers[t_copy["id"]] = Teacher(**t_copy)

        logger.info(f"Loaded {len(self.teachers)} teachers")

        subjects_data = self.config.get("subjects", [])
        if not subjects_data:
            raise ValueError("No subjects provided in configuration")
        self.subjects = {s["id"]: Subject(**s) for s in subjects_data}
        logger.info(f"Loaded {len(self.subjects)} subjects")

        sections_data = self.config.get("sections", [])
        if not sections_data:
            raise ValueError("No sections provided in configuration")
        self.sections = {s["id"]: Section(**s) for s in sections_data}
        logger.info(f"Loaded {len(self.sections)} sections")

        rooms_data = self.config.get("rooms", [])
        if not rooms_data:
            raise ValueError("No rooms provided in configuration")
        self.rooms = {}
        for r in rooms_data:
            r_copy = dict(r)
            if isinstance(r_copy.get("type"), str):
                r_copy["type"] = RoomType(r_copy["type"])
            self.rooms[r_copy["id"]] = Room(**r_copy)
        logger.info(f"Loaded {len(self.rooms)} rooms")

        self.subject_teacher_assignments = self.config.get(
            "subject_teacher_assignments", {}
        )
        self.section_subject_assignments = self.config.get(
            "section_subject_assignments", {}
        )
        self.subject_lab_types = self.config.get("subject_lab_types", {})
        self.section_room_assignments = self.config.get("section_room_assignments", {})

    def _prepare_events(self):
        events = []
        logger.info(
            f"Preparing events for {len(self.section_subject_assignments)} sections"
        )

        if not self.section_subject_assignments:
            logger.warning("No section_subject_assignments found")
            return events

        for section_id_str, subject_ids in self.section_subject_assignments.items():
            if not subject_ids:
                logger.warning(f"No subjects assigned to section {section_id_str}")
                continue
            try:
                section = self.sections.get(int(section_id_str))
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid section_id {section_id_str}: {e}")
                continue
            if not section:
                logger.warning(f"Section {section_id_str} not found in sections dict")
                continue
            for subject_id in subject_ids:
                try:
                    subject = self.subjects.get(int(subject_id))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid subject_id {subject_id}: {e}")
                    continue
                if not subject:
                    logger.warning(f"Subject {subject_id} not found in subjects dict")
                    continue

                # Theory lectures (1 slot each)
                for _ in range(subject.theory_lectures_per_week):
                    teacher_ids = self.subject_teacher_assignments.get(
                        str(subject_id), []
                    )
                    if not teacher_ids:
                        logger.warning(f"No teacher assigned for subject {subject_id}")
                        continue
                    events.append(
                        {
                            "section_id": section.id,
                            "subject_id": subject.id,
                            "teacher_id": teacher_ids[0],  # Pre-assign teacher
                            "type": "theory",
                            "duration": 1,
                            "batch": None,
                        }
                    )

                # Lab sessions (2 consecutive slots each)
                if subject.lab_hours_per_week > 0 and subject.lab_batch_size > 0:
                    num_batches = max(
                        1, math.ceil(section.strength / subject.lab_batch_size)
                    )
                    lab_sessions = max(1, subject.lab_hours_per_week // 2)
                    teacher_ids = self.subject_teacher_assignments.get(
                        str(subject_id), []
                    )
                    if not teacher_ids:
                        continue
                    for batch in range(num_batches):
                        for _ in range(lab_sessions):
                            events.append(
                                {
                                    "section_id": section.id,
                                    "subject_id": subject.id,
                                    "teacher_id": teacher_ids[0],
                                    "type": "lab",
                                    "duration": 2,
                                    "batch": batch + 1,
                                }
                            )
        return events

    def _solve_cpsat(self, events):
        logger.info(f"Starting CP-SAT solver with {len(events)} events")
        model = cp_model.CpModel()
        num_slots = self.slots_per_day
        num_days = len(self.days)

        # Classify rooms
        lecture_rooms = {
            rid: r
            for rid, r in self.rooms.items()
            if self._room_type_str(r) == "CLASSROOM"
        }
        lab_rooms = {
            rid: r for rid, r in self.rooms.items() if self._room_type_str(r) == "LAB"
        }

        logger.info(
            f"Found {len(lecture_rooms)} lecture rooms and {len(lab_rooms)} lab rooms"
        )

        if not lecture_rooms and not lab_rooms:
            raise ValueError("No valid rooms found for scheduling")

        # For each event: binary vars x[event_idx, day, slot] = 1 if event starts at (day, slot)
        # Also assign a room from valid rooms
        x = {}
        room_assign = {}  # room_assign[event_idx] = IntVar for room id

        for i, ev in enumerate(events):
            section_id = ev.get("section_id")
            subject_id = ev.get("subject_id")
            if section_id not in self.sections:
                raise ValueError(f"Section {section_id} not found for event {i}")
            if subject_id not in self.subjects:
                raise ValueError(f"Subject {subject_id} not found for event {i}")
            section = self.sections[section_id]
            subject = self.subjects[subject_id]
            duration = ev["duration"]

            # Valid rooms — match lab_type for lab subjects
            if ev["type"] == "lab":
                required_lab_type = self.subject_lab_types.get(
                    str(ev["subject_id"]), None
                )
                valid_rooms = []
                for rid, r in lab_rooms.items():
                    if r.capacity < subject.lab_batch_size:
                        continue
                    if (
                        required_lab_type
                        and r.lab_type
                        and r.lab_type != required_lab_type
                    ):
                        continue
                    valid_rooms.append(rid)
            else:
                # Check for pre-assigned classroom
                pre_assigned = self.section_room_assignments.get(str(ev["section_id"]))
                if pre_assigned and pre_assigned in lecture_rooms:
                    valid_rooms = [pre_assigned]
                else:
                    valid_rooms = [
                        rid
                        for rid, r in lecture_rooms.items()
                        if r.capacity >= section.strength
                    ]

            if not valid_rooms:
                self._safe_emit(
                    self.status_updated, f"No room for {subject.name} ({ev['type']})"
                )
                return None

            # Create binary assignment vars for (day, slot)
            max_start_slot = num_slots - duration
            ev_vars = []
            for d in range(num_days):
                for s in range(max_start_slot + 1):
                    var = model.NewBoolVar(f"x_{i}_{d}_{s}")
                    x[(i, d, s)] = var
                    ev_vars.append(var)

            # Exactly one (day, slot) per event
            model.AddExactlyOne(ev_vars)

            # Room assignment
            if len(valid_rooms) == 1:
                room_assign[i] = valid_rooms[0]
            else:
                room_assign[i] = model.NewIntVarFromDomain(
                    cp_model.Domain.FromValues(valid_rooms), f"room_{i}"
                )

        self._safe_emit(self.status_updated, "Adding constraints...")
        self._safe_emit(self.progress_updated, 30)
        logger.info("CP-SAT model: adding section constraints")

        section_events = {}
        for i, ev in enumerate(events):
            section_events.setdefault(ev["section_id"], []).append(i)

        # ============================================================
        # CONSTRAINT: Section no-conflict (batch-aware)
        # Theory events and labs of the SAME batch conflict.
        # Labs of DIFFERENT batches (P1 vs P2) are ALLOWED to overlap.
        # ============================================================
        if not os.getenv("TT_DISABLE_SECTION_CONSTRAINTS"):
            for sec_id, ev_indices in section_events.items():
                # Group events by batch: None (theory) + each batch number
                batch_groups = {}  # batch_key -> list of event indices
                for i in ev_indices:
                    batch = events[i].get("batch")
                    if batch is None:
                        # Theory events conflict with ALL groups
                        batch_groups.setdefault("theory", []).append(i)
                    else:
                        batch_groups.setdefault(batch, []).append(i)

                # Within each batch group (and theory), events must not overlap
                # Also theory must not overlap with any batch group
                all_batch_keys = [k for k in batch_groups if k != "theory"]
                theory_indices = batch_groups.get("theory", [])

                for batch_key in all_batch_keys:
                    batch_indices = batch_groups[batch_key]
                    # Combine theory + this batch — they all conflict with each other
                    conflict_group = theory_indices + batch_indices
                    if len(conflict_group) <= 1:
                        continue
                    for d in range(num_days):
                        for s in range(num_slots):
                            overlapping = []
                            for i in conflict_group:
                                dur = events[i]["duration"]
                                for start_s in range(
                                    max(0, s - dur + 1), min(s + 1, num_slots - dur + 1)
                                ):
                                    key = (i, d, start_s)
                                    if key in x:
                                        overlapping.append(x[key])
                            if len(overlapping) > 1:
                                model.Add(sum(overlapping) <= 1)

                # If there are only theory events (no batches), still add conflict
                if not all_batch_keys and len(theory_indices) > 1:
                    for d in range(num_days):
                        for s in range(num_slots):
                            overlapping = []
                            for i in theory_indices:
                                dur = events[i]["duration"]
                                for start_s in range(
                                    max(0, s - dur + 1), min(s + 1, num_slots - dur + 1)
                                ):
                                    key = (i, d, start_s)
                                    if key in x:
                                        overlapping.append(x[key])
                            if len(overlapping) > 1:
                                model.Add(sum(overlapping) <= 1)

        self._safe_emit(self.progress_updated, 45)
        logger.info("CP-SAT model: adding teacher constraints")

        teacher_events = {}
        for i, ev in enumerate(events):
            teacher_id = ev.get("teacher_id")
            if teacher_id is None:
                logger.warning(f"Event {i} has no teacher_id")
                continue
            teacher_events.setdefault(teacher_id, []).append(i)

        # CONSTRAINT: Teacher no-conflict
        if not os.getenv("TT_DISABLE_TEACHER_CONSTRAINTS"):
            for tid, ev_indices in teacher_events.items():
                if tid not in self.teachers:
                    logger.warning(f"Teacher {tid} not found, skipping their events")
                    continue
                teacher = self.teachers[tid]
                for d in range(num_days):
                    # Daily load constraint
                    daily_slots = []
                    for s in range(num_slots):
                        overlapping = []
                        for i in ev_indices:
                            dur = events[i]["duration"]
                            for start_s in range(
                                max(0, s - dur + 1), min(s + 1, num_slots - dur + 1)
                            ):
                                key = (i, d, start_s)
                                if key in x:
                                    overlapping.append(x[key])
                        if len(overlapping) > 1:
                            model.Add(sum(overlapping) <= 1)

                    # Daily load: sum of durations on this day
                    for i in ev_indices:
                        dur = events[i]["duration"]
                        for s in range(num_slots - dur + 1):
                            key = (i, d, s)
                            if key in x:
                                daily_slots.append(x[key] * dur)

                    if daily_slots:
                        model.Add(sum(daily_slots) <= teacher.max_daily_load)

        self._safe_emit(self.progress_updated, 60)
        logger.info("CP-SAT model: adding room constraints")

        # CONSTRAINT: Room no-conflict (handles BOTH fixed and variable room assignments)
        # For variable room assignments, create boolean indicators: is_in_room[i, rid]
        is_in_room = {}  # (event_idx, room_id) -> BoolVar
        if not os.getenv("TT_DISABLE_ROOM_CONSTRAINTS"):
            for i, ev in enumerate(events):
                r = room_assign[i]
                if isinstance(r, int):
                    continue
                # Variable room assignment — determine which rooms are possible
                section = self.sections[ev["section_id"]]
                subject = self.subjects[ev["subject_id"]]
                if ev["type"] == "lab":
                    required_lab_type = self.subject_lab_types.get(
                        str(ev["subject_id"]), None
                    )
                    valid_rooms = [
                        rid
                        for rid, rm in lab_rooms.items()
                        if rm.capacity >= subject.lab_batch_size
                        and (
                            not required_lab_type
                            or not rm.lab_type
                            or rm.lab_type == required_lab_type
                        )
                    ]
                else:
                    valid_rooms = [
                        rid
                        for rid, rm in lecture_rooms.items()
                        if rm.capacity >= section.strength
                    ]

                for rid in valid_rooms:
                    bv = model.NewBoolVar(f"in_room_{i}_{rid}")
                    is_in_room[(i, rid)] = bv
                    # Link: bv == 1  iff  room_assign[i] == rid
                    model.Add(r == rid).OnlyEnforceIf(bv)
                    model.Add(r != rid).OnlyEnforceIf(bv.Not())

            # Build per-room event lists (both fixed and variable)
            all_room_ids = set(self.rooms.keys())
            room_event_map = {
                rid: [] for rid in all_room_ids
            }  # rid -> [(event_idx, is_fixed)]

            for i, ev in enumerate(events):
                r = room_assign[i]
                if isinstance(r, int):
                    room_event_map[r].append((i, True))
                else:
                    for (ei, rid), bv in is_in_room.items():
                        if ei == i:
                            room_event_map[rid].append((i, False))

            # For each room, enforce no two events occupy the same slot
            for rid, ev_list in room_event_map.items():
                if len(ev_list) <= 1:
                    continue
                for d in range(num_days):
                    for s in range(num_slots):
                        overlapping = []
                        for i, is_fixed in ev_list:
                            dur = events[i]["duration"]
                            for start_s in range(
                                max(0, s - dur + 1), min(s + 1, num_slots - dur + 1)
                            ):
                                key = (i, d, start_s)
                                if key not in x:
                                    continue
                                if is_fixed:
                                    overlapping.append(x[key])
                                else:
                                    # Event occupies this room at this time only if
                                    # x[key]==1 AND is_in_room[(i, rid)]==1
                                    bv = is_in_room[(i, rid)]
                                    combo = model.NewBoolVar(
                                        f"occ_{i}_{rid}_{d}_{start_s}"
                                    )
                                    # combo == x[key] AND bv (linearized form is more stable)
                                    model.Add(combo <= x[key])
                                    model.Add(combo <= bv)
                                    model.Add(combo >= x[key] + bv - 1)
                                    overlapping.append(combo)
                        if len(overlapping) > 1:
                            model.Add(sum(overlapping) <= 1)

        penalty_vars = []
        if not os.getenv("TT_DISABLE_SOFT_CONSTRAINTS"):
            # ============================================================
            # SOFT CONSTRAINT: Max 1 session of same subject per day per
            # section per batch (preferred but not required)
            # ============================================================
            section_subject_batch_events = {}
            for i, ev in enumerate(events):
                key = (ev["section_id"], ev["subject_id"], ev.get("batch"))
                section_subject_batch_events.setdefault(key, []).append(i)

            for (
                sec_id,
                subj_id,
                batch,
            ), ev_indices in section_subject_batch_events.items():
                if len(ev_indices) <= 1:
                    continue
                for d in range(num_days):
                    day_vars = []
                    for i in ev_indices:
                        dur = events[i]["duration"]
                        for s in range(num_slots - dur + 1):
                            key = (i, d, s)
                            if key in x:
                                day_vars.append(x[key])
                    if len(day_vars) > 1:
                        # Soft: penalize when sum > 1 but allow it
                        overflow = model.NewIntVar(
                            0, len(day_vars), f"overflow_{sec_id}_{subj_id}_{batch}_{d}"
                        )
                        model.Add(sum(day_vars) - 1 <= overflow)
                        penalty_vars.append(overflow)

            # ============================================================
            # SOFT CONSTRAINT: Max 1 lab session (any subject) per day
            # per section per batch (to avoid student stress)
            # ============================================================
            for sec_id, ev_indices in section_events.items():
                # Group lab events by batch
                batch_lab_events = {}
                for i in ev_indices:
                    if events[i]["type"] == "lab":
                        batch = events[i].get("batch", 1)
                        batch_lab_events.setdefault(batch, []).append(i)

                for batch, lab_indices in batch_lab_events.items():
                    if len(lab_indices) <= 1:
                        continue
                    for d in range(num_days):
                        day_vars = []
                        for i in lab_indices:
                            dur = events[i]["duration"]
                            for s in range(num_slots - dur + 1):
                                key = (i, d, s)
                                if key in x:
                                    day_vars.append(x[key])
                        if len(day_vars) > 1:
                            # Soft: penalize when a batch has more than 1 lab session per day
                            overflow = model.NewIntVar(
                                0, len(day_vars), f"lab_overflow_{sec_id}_{batch}_{d}"
                            )
                            model.Add(sum(day_vars) - 1 <= overflow)
                            penalty_vars.append(overflow)

        # ============================================================
        # OBJECTIVE: Minimize penalties (soft constraints) +
        # random weights for variety
        # ============================================================
        if penalty_vars and not os.getenv("TT_DISABLE_OBJECTIVE"):
            # Add random small weights to spread out the schedule
            objective_terms = []
            for pv in penalty_vars:
                # Heavy penalty for soft constraint violations
                objective_terms.append(pv * 100)

            # Add small random weights to event placement for variety
            rng = random.Random()
            for i, ev in enumerate(events):
                dur = ev["duration"]
                for d in range(num_days):
                    for s in range(num_slots - dur + 1):
                        key = (i, d, s)
                        if key in x:
                            w = rng.randint(0, 5)
                            if w > 0:
                                objective_terms.append(x[key] * w)

            model.Minimize(sum(objective_terms))
        elif not os.getenv("TT_DISABLE_OBJECTIVE"):
            # Just add random weights for variety even without penalties
            rng = random.Random()
            objective_terms = []
            for i, ev in enumerate(events):
                dur = ev["duration"]
                for d in range(num_days):
                    for s in range(num_slots - dur + 1):
                        key = (i, d, s)
                        if key in x:
                            w = rng.randint(0, 5)
                            if w > 0:
                                objective_terms.append(x[key] * w)
            if objective_terms:
                model.Minimize(sum(objective_terms))

        self._safe_emit(self.status_updated, "Solving...")
        self._safe_emit(self.progress_updated, 70)
        logger.info("CP-SAT model: starting solver")

        logger.info("CP-SAT: creating solver instance")
        solver = cp_model.CpSolver()
        logger.info("CP-SAT: solver instance created")
        solver.parameters.max_time_in_seconds = 60
        logger.info("CP-SAT: set max_time_in_seconds")
        # Multi-worker solving can crash on some Windows/OR-Tools builds.
        solver.parameters.num_search_workers = 1 if os.name == "nt" else 4
        logger.info("CP-SAT: set num_search_workers")
        # Random seed for schedule variety
        solver.parameters.random_seed = random.randint(0, 10000)
        logger.info("CP-SAT: set random_seed")

        validation_error = model.Validate()
        if validation_error:
            logger.error(f"CP-SAT model validation failed: {validation_error}")
            raise ValueError(f"Invalid CP-SAT model: {validation_error}")
        logger.info("CP-SAT: model validation passed")

        logger.info("CP-SAT: calling Solve()")
        try:
            status = solver.Solve(model)
        except Exception as e:
            logger.exception(f"CP-SAT Solve() raised an exception: {e}")
            raise RuntimeError(f"CP-SAT Solve() failed: {e}") from e
        logger.info(f"CP-SAT solver finished with status={status}")

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            self._safe_emit(self.status_updated, "Extracting solution...")
            self._safe_emit(self.progress_updated, 90)
            return self._extract_solution(solver, events, x, room_assign)
        else:
            return None

    def _extract_solution(self, solver, events, x, room_assign):
        # --- Build resolved event list ---
        resolved = []
        for i, ev in enumerate(events):
            section = self.sections[ev["section_id"]]
            subject = self.subjects[ev["subject_id"]]
            teacher = self.teachers[ev["teacher_id"]]
            dur = ev["duration"]

            for d in range(len(self.days)):
                for s in range(self.slots_per_day - dur + 1):
                    key = (i, d, s)
                    if key in x and solver.Value(x[key]) == 1:
                        r = room_assign[i]
                        room = (
                            self.rooms[r]
                            if isinstance(r, int)
                            else self.rooms[solver.Value(r)]
                        )
                        resolved.append(
                            {
                                "section": section.name,
                                "subject": subject.name,
                                "teacher": teacher.name,
                                "room": room.name,
                                "day": self.days[d],
                                "slot": s,
                                "duration": dur,
                                "type": ev["type"],
                                "batch": ev.get("batch"),
                            }
                        )

        # --- Section timetables (support multiple entries per slot for P1/P2 overlap) ---
        section_tt = {}
        for sec_id, sec in self.sections.items():
            section_tt[sec.name] = {
                day: [[] for _ in range(self.slots_per_day)] for day in self.days
            }
        for r in resolved:
            for offset in range(r["duration"]):
                slot = r["slot"] + offset
                if slot < self.slots_per_day:
                    entry = {
                        "subject": r["subject"],
                        "teacher": r["teacher"],
                        "room": r["room"],
                        "type": r["type"],
                    }
                    if r["batch"]:
                        entry["batch"] = f"P{r['batch']}"
                    section_tt[r["section"]][r["day"]][slot].append(entry)

        # Convert: slots with single entry → dict, empty → None, multiple → list
        for sec_name in section_tt:
            for day in section_tt[sec_name]:
                for idx, slot_entries in enumerate(section_tt[sec_name][day]):
                    if len(slot_entries) == 0:
                        section_tt[sec_name][day][idx] = None
                    elif len(slot_entries) == 1:
                        section_tt[sec_name][day][idx] = slot_entries[0]
                    else:
                        # Multiple entries (P1 + P2 overlap) — keep as list
                        section_tt[sec_name][day][idx] = slot_entries

        # --- Teacher timetables ---
        teacher_tt = {}
        for tid, t in self.teachers.items():
            teacher_tt[t.name] = {day: [None] * self.slots_per_day for day in self.days}
        for r in resolved:
            for offset in range(r["duration"]):
                slot = r["slot"] + offset
                if slot < self.slots_per_day:
                    entry = {
                        "subject": r["subject"],
                        "section": r["section"],
                        "room": r["room"],
                        "type": r["type"],
                    }
                    if r["batch"]:
                        entry["batch"] = f"P{r['batch']}"
                    teacher_tt[r["teacher"]][r["day"]][slot] = entry

        # --- Room timetables ---
        room_tt = {}
        for rid, rm in self.rooms.items():
            room_tt[rm.name] = {day: [None] * self.slots_per_day for day in self.days}
        for r in resolved:
            for offset in range(r["duration"]):
                slot = r["slot"] + offset
                if slot < self.slots_per_day:
                    entry = {
                        "subject": r["subject"],
                        "section": r["section"],
                        "teacher": r["teacher"],
                        "type": r["type"],
                    }
                    if r["batch"]:
                        entry["batch"] = f"P{r['batch']}"
                    room_tt[r["room"]][r["day"]][slot] = entry

        # --- Overlap validation ---
        errors = self._validate_no_overlaps(resolved)
        if errors:
            self._safe_emit(
                self.status_updated, f"WARNING: {len(errors)} overlap(s) detected!"
            )

        return {"sections": section_tt, "teachers": teacher_tt, "rooms": room_tt}

    def _validate_no_overlaps(self, resolved):
        """Post-solve validation: check no overlaps exist.
        Section overlaps between different batches are ALLOWED."""
        errors = []

        # Teacher and room must never overlap
        for dim in ("teacher", "room"):
            slots_used = {}
            for r in resolved:
                entity = r[dim]
                for offset in range(r["duration"]):
                    key = (entity, r["day"], r["slot"] + offset)
                    if key in slots_used:
                        errors.append(
                            f"{dim} conflict: {entity} on {r['day']} slot {r['slot'] + offset + 1}"
                        )
                    else:
                        slots_used[key] = r

        # Section: only same-batch or theory overlaps are conflicts
        section_slots = {}  # (section, day, slot) -> list of (batch, event)
        for r in resolved:
            for offset in range(r["duration"]):
                key = (r["section"], r["day"], r["slot"] + offset)
                section_slots.setdefault(key, []).append(r)
        for key, events_at_slot in section_slots.items():
            if len(events_at_slot) <= 1:
                continue
            # Check if there are conflicting events (same batch or theory)
            for idx_a in range(len(events_at_slot)):
                for idx_b in range(idx_a + 1, len(events_at_slot)):
                    a, b = events_at_slot[idx_a], events_at_slot[idx_b]
                    a_batch = a.get("batch")
                    b_batch = b.get("batch")
                    # Conflict if either is theory OR same batch
                    if a_batch is None or b_batch is None or a_batch == b_batch:
                        sec, day, slot = key
                        errors.append(
                            f"section conflict: {sec} on {day} slot {slot + 1}"
                        )

        return errors

    @staticmethod
    def _room_type_str(room):
        if isinstance(room.type, RoomType):
            return room.type.value
        return str(room.type)
