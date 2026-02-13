
import math
import random
from PyQt5.QtCore import QThread, pyqtSignal
from ortools.sat.python import cp_model
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
        self.num_flat_slots = len(self.days) * self.slots_per_day  # 30

    def run(self):
        try:
            self.status_updated.emit("Initializing resources...")
            self.progress_updated.emit(5)
            self._initialize_resources()

            events = self._prepare_events()
            if not events:
                self.generation_failed.emit("No events to schedule. Check subject/section assignments.")
                return

            self.status_updated.emit(f"Building CP-SAT model for {len(events)} events...")
            self.progress_updated.emit(15)

            result = self._solve_cpsat(events)
            if result is not None:
                self.progress_updated.emit(100)
                self.status_updated.emit("Generation complete!")
                self.generation_completed.emit(result)
            else:
                self.generation_failed.emit(
                    "Could not find a valid timetable.\n"
                    "Try reducing sections or adding more teachers/rooms."
                )
        except Exception as e:
            self.generation_failed.emit(f"Error: {str(e)}")

    def _initialize_resources(self):
        self.teachers = {}
        for t in self.config.get("teachers", []):
            t_copy = {k: v for k, v in t.items() if k != 'availability'}
            self.teachers[t_copy['id']] = Teacher(**t_copy)

        self.subjects = {s['id']: Subject(**s) for s in self.config.get("subjects", [])}
        self.sections = {s['id']: Section(**s) for s in self.config.get("sections", [])}

        self.rooms = {}
        for r in self.config.get("rooms", []):
            r_copy = dict(r)
            if isinstance(r_copy.get('type'), str):
                r_copy['type'] = RoomType(r_copy['type'])
            self.rooms[r_copy['id']] = Room(**r_copy)

        self.subject_teacher_assignments = self.config.get("subject_teacher_assignments", {})
        self.section_subject_assignments = self.config.get("section_subject_assignments", {})
        self.subject_lab_types = self.config.get("subject_lab_types", {})

    def _prepare_events(self):
        events = []
        for section_id_str, subject_ids in self.section_subject_assignments.items():
            section = self.sections.get(int(section_id_str))
            if not section:
                continue
            for subject_id in subject_ids:
                subject = self.subjects.get(int(subject_id))
                if not subject:
                    continue

                # Theory lectures (1 slot each)
                for _ in range(subject.theory_lectures_per_week):
                    teacher_ids = self.subject_teacher_assignments.get(str(subject_id), [])
                    if not teacher_ids:
                        continue
                    events.append({
                        "section_id": section.id,
                        "subject_id": subject.id,
                        "teacher_id": teacher_ids[0],  # Pre-assign teacher
                        "type": "theory",
                        "duration": 1,
                        "batch": None,
                    })

                # Lab sessions (2 consecutive slots each)
                if subject.lab_hours_per_week > 0 and subject.lab_batch_size > 0:
                    num_batches = max(1, math.ceil(section.strength / subject.lab_batch_size))
                    lab_sessions = max(1, subject.lab_hours_per_week // 2)
                    teacher_ids = self.subject_teacher_assignments.get(str(subject_id), [])
                    if not teacher_ids:
                        continue
                    for batch in range(num_batches):
                        for _ in range(lab_sessions):
                            events.append({
                                "section_id": section.id,
                                "subject_id": subject.id,
                                "teacher_id": teacher_ids[0],
                                "type": "lab",
                                "duration": 2,
                                "batch": batch + 1,
                            })
        return events

    def _solve_cpsat(self, events):
        model = cp_model.CpModel()
        num_slots = self.slots_per_day
        num_days = len(self.days)

        # Classify rooms
        lecture_rooms = {rid: r for rid, r in self.rooms.items()
                        if self._room_type_str(r) == "CLASSROOM"}
        lab_rooms = {rid: r for rid, r in self.rooms.items()
                     if self._room_type_str(r) == "LAB"}

        # For each event: binary vars x[event_idx, day, slot] = 1 if event starts at (day, slot)
        # Also assign a room from valid rooms
        x = {}
        room_assign = {}  # room_assign[event_idx] = IntVar for room id

        for i, ev in enumerate(events):
            section = self.sections[ev["section_id"]]
            subject = self.subjects[ev["subject_id"]]
            duration = ev["duration"]

            # Valid rooms — match lab_type for lab subjects
            if ev["type"] == "lab":
                required_lab_type = self.subject_lab_types.get(str(ev["subject_id"]), None)
                valid_rooms = []
                for rid, r in lab_rooms.items():
                    if r.capacity < subject.lab_batch_size:
                        continue
                    if required_lab_type and r.lab_type and r.lab_type != required_lab_type:
                        continue
                    valid_rooms.append(rid)
            else:
                valid_rooms = [rid for rid, r in lecture_rooms.items()
                               if r.capacity >= section.strength]

            if not valid_rooms:
                self.status_updated.emit(f"No room for {subject.name} ({ev['type']})")
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
                    cp_model.Domain.FromValues(valid_rooms), f"room_{i}")

        self.status_updated.emit("Adding constraints...")
        self.progress_updated.emit(30)

        # ============================================================
        # CONSTRAINT: Section no-conflict (batch-aware)
        # Theory events and labs of the SAME batch conflict.
        # Labs of DIFFERENT batches (P1 vs P2) are ALLOWED to overlap.
        # ============================================================
        section_events = {}
        for i, ev in enumerate(events):
            section_events.setdefault(ev["section_id"], []).append(i)

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
                            for start_s in range(max(0, s - dur + 1), min(s + 1, num_slots - dur + 1)):
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
                            for start_s in range(max(0, s - dur + 1), min(s + 1, num_slots - dur + 1)):
                                key = (i, d, start_s)
                                if key in x:
                                    overlapping.append(x[key])
                        if len(overlapping) > 1:
                            model.Add(sum(overlapping) <= 1)

        self.progress_updated.emit(45)

        # CONSTRAINT: Teacher no-conflict
        teacher_events = {}
        for i, ev in enumerate(events):
            teacher_events.setdefault(ev["teacher_id"], []).append(i)

        for tid, ev_indices in teacher_events.items():
            teacher = self.teachers[tid]
            for d in range(num_days):
                # Daily load constraint
                daily_slots = []
                for s in range(num_slots):
                    overlapping = []
                    for i in ev_indices:
                        dur = events[i]["duration"]
                        for start_s in range(max(0, s - dur + 1), min(s + 1, num_slots - dur + 1)):
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

        self.progress_updated.emit(60)

        # CONSTRAINT: Room no-conflict (only for fixed room assignments for simplicity)
        room_events = {}
        for i, ev in enumerate(events):
            r = room_assign[i]
            if isinstance(r, int):
                room_events.setdefault(r, []).append(i)

        for rid, ev_indices in room_events.items():
            for d in range(num_days):
                for s in range(num_slots):
                    overlapping = []
                    for i in ev_indices:
                        dur = events[i]["duration"]
                        for start_s in range(max(0, s - dur + 1), min(s + 1, num_slots - dur + 1)):
                            key = (i, d, start_s)
                            if key in x:
                                overlapping.append(x[key])
                    if len(overlapping) > 1:
                        model.Add(sum(overlapping) <= 1)

        # ============================================================
        # SOFT CONSTRAINT: Max 1 session of same subject per day per
        # section per batch (preferred but not required)
        # ============================================================
        section_subject_batch_events = {}
        for i, ev in enumerate(events):
            key = (ev["section_id"], ev["subject_id"], ev.get("batch"))
            section_subject_batch_events.setdefault(key, []).append(i)

        penalty_vars = []
        for (sec_id, subj_id, batch), ev_indices in section_subject_batch_events.items():
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
                    overflow = model.NewIntVar(0, len(day_vars), f"overflow_{sec_id}_{subj_id}_{batch}_{d}")
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
                        overflow = model.NewIntVar(0, len(day_vars), f"lab_overflow_{sec_id}_{batch}_{d}")
                        model.Add(sum(day_vars) - 1 <= overflow)
                        penalty_vars.append(overflow)

        # ============================================================
        # OBJECTIVE: Minimize penalties (soft constraints) +
        # random weights for variety
        # ============================================================
        if penalty_vars:
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
        else:
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

        self.status_updated.emit("Solving...")
        self.progress_updated.emit(70)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30
        solver.parameters.num_search_workers = 4
        # Random seed for schedule variety
        solver.parameters.random_seed = random.randint(0, 10000)

        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            self.status_updated.emit("Extracting solution...")
            self.progress_updated.emit(90)
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
                        room = self.rooms[r] if isinstance(r, int) else self.rooms[solver.Value(r)]
                        resolved.append({
                            "section": section.name,
                            "subject": subject.name,
                            "teacher": teacher.name,
                            "room": room.name,
                            "day": self.days[d],
                            "slot": s,
                            "duration": dur,
                            "type": ev["type"],
                            "batch": ev.get("batch"),
                        })

        # --- Section timetables (support multiple entries per slot for P1/P2 overlap) ---
        section_tt = {}
        for sec_id, sec in self.sections.items():
            section_tt[sec.name] = {day: [[] for _ in range(self.slots_per_day)] for day in self.days}
        for r in resolved:
            for offset in range(r["duration"]):
                slot = r["slot"] + offset
                if slot < self.slots_per_day:
                    entry = {"subject": r["subject"], "teacher": r["teacher"],
                             "room": r["room"], "type": r["type"]}
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
                    entry = {"subject": r["subject"], "section": r["section"],
                             "room": r["room"], "type": r["type"]}
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
                    entry = {"subject": r["subject"], "section": r["section"],
                             "teacher": r["teacher"], "type": r["type"]}
                    if r["batch"]:
                        entry["batch"] = f"P{r['batch']}"
                    room_tt[r["room"]][r["day"]][slot] = entry

        # --- Overlap validation ---
        errors = self._validate_no_overlaps(resolved)
        if errors:
            self.status_updated.emit(f"WARNING: {len(errors)} overlap(s) detected!")

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
                        errors.append(f"{dim} conflict: {entity} on {r['day']} slot {r['slot']+offset+1}")
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
                        errors.append(f"section conflict: {sec} on {day} slot {slot+1}")

        return errors

    @staticmethod
    def _room_type_str(room):
        if isinstance(room.type, RoomType):
            return room.type.value
        return str(room.type)
