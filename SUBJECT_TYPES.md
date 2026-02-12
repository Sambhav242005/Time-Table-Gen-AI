# Subject Types: Theory-Only, Lab-Only, and Mixed

## Overview

The timetable generator now supports three distinct subject types:

1. **Theory-Only**: Classroom sessions only (no lab)
2. **Lab-Only**: Lab sessions only (no classroom theory)
3. **Mixed**: Both classroom theory + lab practical sessions

## Subject Type Definitions

### 1. Theory-Only Subjects
**Definition**: Subjects taught entirely in lecture/classroom rooms

```python
Subject(
    "CS201",
    "Algorithms",
    has_theory=True,           # Has theory component
    has_practical=False,       # No lab component
    theory_hours_per_week=3    # 3 sessions in classroom
)
```

**Characteristics**:
- Uses only **lecture rooms** (not labs)
- Scheduled in classrooms with capacity >= class size
- No lab equipment needed
- Examples: Mathematics, Algorithms, AI Theory

**In Dataset** (4 subjects):
- CS201: Algorithms (3 sessions/week)
- AI101: Artificial Intelligence (3 sessions/week)
- MAT101: Mathematics I (4 sessions/week)
- MAT201: Discrete Math (3 sessions/week)

---

### 2. Lab-Only Subjects
**Definition**: Subjects taught entirely in labs (hands-on practical only)

```python
Subject(
    "CLD201",
    "Private Cloud Lab",
    has_theory=False,              # No theory classroom sessions
    has_practical=True,            # Has lab component
    practical_sessions_per_week=3, # 3 sessions in lab
    lab_room_code="LAB-CLD"        # Specific lab room
)
```

**Characteristics**:
- Uses only **assigned lab rooms** (not classrooms)
- All sessions are hands-on practical
- Requires specific lab equipment
- May need batch splitting if lab capacity < class size
- Examples: Cloud Deployment Lab, Web Development Lab

**In Dataset** (6 subjects):
- CLD201: Private Cloud Lab (3 lab sessions/week) → LAB-CLD
- CLD301: Cloud Deployment Lab (3 lab sessions/week) → LAB-CLD
- WEB201: Web Development Lab (3 lab sessions/week) → LAB-WEB
- DB201: Advanced DB Lab (3 lab sessions/week) → LAB-DB
- PHY201: Physics Practical (3 lab sessions/week) → LAB-PHY
- STAT201: Statistics Lab (3 lab sessions/week) → LAB-STAT

---

### 3. Mixed Subjects
**Definition**: Subjects with both theory (classroom) and practical (lab) components

```python
Subject(
    "CS101",
    "Intro to Programming",
    has_theory=True,              # Has theory component
    has_practical=True,           # Has lab component
    theory_hours_per_week=3,      # 3 sessions in classroom
    practical_sessions_per_week=2, # 2 sessions in lab
    lab_room_code="LAB-CS-1"      # Lab for practical
)
```

**Characteristics**:
- Uses **both lecture rooms AND labs**
- Theory sessions in classrooms
- Practical sessions in assigned lab
- Total sessions = theory + practical
- Examples: Programming, Machine Learning, Cloud Computing

**In Dataset** (14 subjects):
- CS101: Intro to Programming (3 theory + 2 lab = 5 total/week)
- CS102: Data Structures (3 theory + 2 lab = 5 total/week)
- ML101: Machine Learning (3 theory + 2 lab = 5 total/week)
- CLD101: Cloud Computing (3 theory + 2 lab = 5 total/week)
- And 10 more...

---

## How Room Assignment Works

### Variable Creation Logic

The solver creates assignment variables based on subject type:

```python
for each room:
    if subject is THEORY-ONLY:
        # Only create variables for lecture rooms
        if room.room_type == "lecture":
            create_assignment_variable()
    
    elif subject is LAB-ONLY:
        # Only create variables for assigned lab
        if room.code == subject.lab_room_code:
            create_assignment_variable()
    
    elif subject is MIXED:
        # Create variables for BOTH lecture rooms AND lab
        if room.room_type == "lecture":
            create_assignment_variable()  # Theory sessions
        elif room.code == subject.lab_room_code:
            create_assignment_variable()  # Practical sessions
```

### Examples

**Theory-Only (CS201 - Algorithms)**:
```
Can be scheduled in: LH-1, LH-2, LH-3, LH-4 (lecture halls)
Cannot be scheduled in: Any lab
```

**Lab-Only (CLD201 - Private Cloud Lab)**:
```
Can be scheduled in: LAB-CLD only
Cannot be scheduled in: Lecture halls or other labs
```

**Mixed (CS101 - Programming)**:
```
Theory sessions: LH-1, LH-2, LH-3, LH-4 (lecture halls)
Practical sessions: LAB-CS-1 only
```

---

## Constraint Handling

### Theory Hours Constraint

```python
# Only applies to subjects with has_theory=True
if subject.has_theory:
    theory_vars = count_sessions_in_lecture_rooms()
    constraint: sum(theory_vars) == subject.theory_hours_per_week
```

### Practical Sessions Constraint

```python
# Only applies to subjects with has_practical=True
if subject.has_practical:
    lab_vars = count_sessions_in_lab()
    total_sessions = lab_vars * batches_needed
    constraint: sum(lab_vars) == subject.practical_sessions_per_week * batches
```

---

## Statistics for Current Dataset

```
Total Subjects: 24

Theory-Only: 4 subjects (17%)
  - Total theory hours: 13 hours/week per class

Lab-Only: 6 subjects (25%)
  - Total lab sessions: 18 sessions/week per class
  - Uses specialized labs

Mixed: 14 subjects (58%)
  - Total theory hours: 42 hours/week per class
  - Total lab sessions: 28 sessions/week per class
  - Total: 70 hours/week per class

Overall per class:
  - Theory hours: 55 hours/week
  - Lab sessions: 46 sessions/week
  - Grand total: 101 hours/week to schedule
```

---

## Class Schedule Example

### CS-A (Computer Science - A)
**Subjects**: CS101, CS102, CS201, MAT101, PHY101

```
CS101 (Mixed - Programming):
  - Theory: 3 sessions in LH-1/2/3/4
  - Lab: 2 sessions in LAB-CS-1
  
CS102 (Mixed - Data Structures):
  - Theory: 3 sessions in LH-1/2/3/4
  - Lab: 2 sessions in LAB-CS-1
  
CS201 (Theory-Only - Algorithms):
  - Theory: 3 sessions in LH-1/2/3/4
  - No lab sessions
  
MAT101 (Theory-Only - Math):
  - Theory: 4 sessions in LH-1/2/3/4
  - No lab sessions
  
PHY101 (Mixed - Physics):
  - Theory: 3 sessions in LH-1/2/3/4
  - Lab: 2 sessions in LAB-PHY
```

### CLD-A (Cloud Computing - A)
**Subjects**: CLD101, CLD201, CLD301, DEV101, CS302, DB101

```
CLD101 (Mixed - Cloud Computing):
  - Theory: 3 sessions in lecture halls
  - Lab: 2 sessions in LAB-CLD
  
CLD201 (Lab-Only - Private Cloud):
  - Lab only: 3 sessions in LAB-CLD
  
CLD301 (Lab-Only - Cloud Deployment):
  - Lab only: 3 sessions in LAB-CLD
  
DEV101 (Mixed - DevOps):
  - Theory: 3 sessions in lecture halls
  - Lab: 2 sessions in LAB-DEV
  
CS302 (Mixed - Networks):
  - Theory: 3 sessions in lecture halls
  - Lab: 2 sessions in LAB-NET
  
DB101 (Mixed - Databases):
  - Theory: 3 sessions in lecture halls
  - Lab: 2 sessions in LAB-DB
```

---

## Benefits of This Design

### 1. Flexibility
- Same subject code can be theory-only in one context, lab-only in another
- Easy to adjust based on curriculum requirements

### 2. Resource Optimization
- Theory-only subjects don't compete for lab space
- Lab-only subjects don't compete for lecture halls
- Mixed subjects use both efficiently

### 3. Real-World Alignment
- Matches actual university course structures
- Some courses are pure lecture, pure lab, or hybrid

### 4. Batch Management
- Lab-only subjects automatically handled with batch splitting
- Theory-only subjects don't need batch considerations

---

## Customization

### Convert Theory-Only to Mixed
```python
# Before
Subject("CS201", "Algorithms", has_theory=True, has_practical=False)

# After (adding practical component)
Subject("CS201", "Algorithms", 
        has_theory=True, 
        has_practical=True,           # Now has lab!
        theory_hours_per_week=3,
        practical_sessions_per_week=2, # Add 2 lab sessions
        lab_room_code="LAB-ALGO")
```

### Convert Mixed to Lab-Only
```python
# Before
Subject("CS101", "Programming",
        has_theory=True, has_practical=True,
        theory_hours_per_week=3,
        practical_sessions_per_week=2)

# After (remove theory)
Subject("CS101", "Programming Lab",
        has_theory=False,             # No theory now
        has_practical=True,           # Only lab
        practical_sessions_per_week=5) # All 5 sessions in lab
```

### Create Pure Theory Course
```python
Subject("HIST101", "History", 
        has_theory=True,
        has_practical=False,
        theory_hours_per_week=3)
# Will only be scheduled in lecture halls
```

---

## Validation

The system validates:
- ✅ Theory-only uses only lecture rooms
- ✅ Lab-only uses only assigned lab
- ✅ Mixed uses both appropriately
- ✅ Room capacity respected for all types
- ✅ Batch splitting only for lab components

---

## Summary

| Type | Theory | Lab | Room Usage | Example |
|------|--------|-----|------------|---------|
| **Theory-Only** | ✅ Yes | ❌ No | Lecture halls only | Math, Algorithms |
| **Lab-Only** | ❌ No | ✅ Yes | Assigned lab only | Cloud Deployment Lab |
| **Mixed** | ✅ Yes | ✅ Yes | Both lecture + lab | Programming, ML |

All three types work seamlessly together in the same timetable!
