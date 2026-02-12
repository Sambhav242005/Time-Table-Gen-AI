# Large Dataset & Problem Finder - Complete Guide

## Overview

I've created a comprehensive solution with:

1. **Problem Finder** - Detects scheduling conflicts before solving
2. **Large Dataset Generator** - 10 classes, 20+ subjects, 10 labs, 15 teachers
3. **Configurable Lab Sessions** - Each subject can have custom practical sessions per week
4. **Shared Teacher Detection** - Identifies when same teacher teaches same subject to multiple classes

## Files Created

### 1. `large_timetable_generator.py` (730+ lines)
Complete implementation with problem detection and large dataset generation.

### 2. `large_dataset.json`
Generated dataset with:
- **10 Classes**: CS-A/B/C, AI-A/B, CLD-A/B, WEB-A, DS-A, DEV-A
- **21 Subjects**: Programming, ML, Cloud, Web Dev, Databases, Math, Physics, etc.
- **10 Labs**: CS Lab, AI Lab, Cloud Lab, Web Lab, etc.
- **15 Teachers**: Various specializations, many teach multiple subjects
- **30 Time Slots**: 5 days × 6 slots

## Key Features

### 1. Problem Finder / Validator

The `ProblemFinder` class detects issues BEFORE solving:

#### Shared Teacher Conflicts
```
[SHARED TEACHER CONFLICTS] (34 found):
  Teacher Dr. Sarah Chen teaches CS101 to:
    - Computer Science - A
    - Computer Science - B
    - Web Development - A
  -> Must ensure no overlapping sessions!
```

**What this means**: The same teacher (Dr. Sarah Chen) teaches CS101 to 3 different classes. The solver must ensure these sessions don't overlap.

#### Hour Limit Violations
```
[HOUR LIMIT VIOLATIONS] (13 found):
  Dr. James Wilson: Needs 50 hours, Available 30 hours, Overage: 20
```

**What this means**: Some teachers are over-allocated. The dataset needs adjustment or more teachers.

### 2. Configurable Lab Sessions

Each subject can define its own practical sessions:

```python
Subject("ML101", "Machine Learning", True, 
        practical_sessions_per_week=2,  # Custom: 2 sessions per week
        lab_room_code="LAB-AI")

Subject("PHY101", "Physics I", True, 
        practical_sessions_per_week=2,  # Default applied automatically
        lab_room_code="LAB-PHY")
```

**Default**: If not specified, practical subjects get **2 sessions per week** automatically.

### 3. Lab Room Assignment in Subject

Instead of separate lab_assignments dict, each subject specifies its lab:

```python
Subject("CLD101", "Cloud Computing", True, 
        practical_sessions_per_week=2,
        lab_room_code="LAB-CLD")  # Subject knows its lab!
```

## Running the Problem Finder

```bash
python large_timetable_generator.py
```

### Sample Output

```
================================================================================
UNIVERSITY TIMETABLE GENERATOR WITH PROBLEM DETECTION
================================================================================

1. Creating large dataset (10 classes, 20 subjects, 10 labs)...
   [OK] 21 subjects
   [OK] 10 classes
   [OK] 15 teachers
   [OK] 16 rooms
   [OK] 30 time slots

2. Running problem finder...

================================================================================
PRE-SOLVING VALIDATION
================================================================================
Checking for shared teacher conflicts...
  Found: Dr. Sarah Chen teaches CS101 to 3 classes: ['CS-A', 'CS-B', 'WEB-A']
  Found: Dr. Rajesh Kumar teaches ML101 to 3 classes: ['AI-A', 'AI-B', 'DS-A']
  ...

Checking room capacity...

Checking teacher availability...

================================================================================
CONFLICT & PROBLEM REPORT
================================================================================

[SHARED TEACHER CONFLICTS] (34):
  Teacher Dr. Sarah Chen (T-P-1) teaches Intro to Programming (CS101) to:
    - Computer Science - A
    - Computer Science - B
    - Web Development - A
  -> Must ensure no overlapping sessions!

[HOUR LIMIT VIOLATIONS] (13):
  Dr. James Wilson (T-CLD-1): Needed 50, Available 30, Overage 20
  ...

[DATASET STATISTICS]:
   Total theory hours to schedule: 880
   Total lab sessions to schedule: 320
   Total slots available: 30
```

## Understanding the Output

### Shared Teacher Conflicts

When multiple classes have the same subject taught by the same teacher, the solver must:

1. **Select ONE teacher per class** (from available teachers)
2. **Ensure no time overlaps** for that teacher across classes

**Example**:
- Dr. Sarah Chen AND Prof. Mike Johnson can both teach CS101
- CS-A, CS-B, WEB-A all need CS101
- The solver assigns:
  - CS-A CS101 → Dr. Sarah Chen
  - CS-B CS101 → Prof. Mike Johnson
  - WEB-A CS101 → Dr. Sarah Chen
- **Constraint**: Dr. Sarah Chen cannot teach CS-A and WEB-A at the same time!

### Hour Violations

The problem finder calculates total hours needed:
```
For each teacher:
  total_hours = Σ (theory_hours + practical_sessions) for all assigned subjects
```

If `total_hours > max_weekly_hours`, it reports a violation.

**Solutions**:
1. Add more teachers
2. Increase teacher hour limits
3. Reduce subjects per teacher
4. Assign fewer classes to overloaded teachers

## How It Works

### 1. Shared Teacher Detection Algorithm

```python
def find_shared_teacher_conflicts(self):
    # Map: (teacher, subject) -> list of classes
    teacher_subject_classes = defaultdict(list)
    
    for each class:
        for each subject in class:
            for each teacher who can teach subject:
                teacher_subject_classes[(teacher, subject)].append(class)
    
    # Report cases where count > 1
    for (teacher, subject), classes in teacher_subject_classes.items():
        if len(classes) > 1:
            report_conflict(teacher, subject, classes)
```

### 2. Configurable Lab Sessions

```python
@dataclass
class Subject:
    practical_sessions_per_week: int = 0
    
    def __post_init__(self):
        if self.has_practical and self.practical_sessions_per_week == 0:
            self.practical_sessions_per_week = 2  # Default
```

### 3. Subject-Lab Assignment

```python
class Subject:
    lab_room_code: Optional[str] = None  # Each subject knows its lab

# Usage
Subject("ML101", "Machine Learning", True, 
        lab_room_code="LAB-AI")  # ML uses AI Lab
```

## Integration with Solver

The problem finder integrates with the CP-SAT solver:

1. **Before solving**: Run problem finder to detect issues
2. **During solving**: Teacher conflict constraints prevent overlaps
3. **After solving**: Validate solution matches constraints

### Teacher Conflict Constraint (in solver)

```python
# Teacher cannot be in two places at once
for t_code in teachers:
    for k_idx in time_slots:
        teacher_vars = []  # All sessions for this teacher at this time
        model.Add(sum(teacher_vars) <= 1)  # Max 1 session
```

This automatically handles shared teacher conflicts!

## Customizing the Dataset

### Change Lab Sessions Per Week

```python
# More lab sessions
Subject("PHY101", "Physics", True, 
        practical_sessions_per_week=3)  # 3 sessions/week

# Fewer lab sessions
Subject("CLD101", "Cloud", True, 
        practical_sessions_per_week=1)  # 1 session/week
```

### Add More Teachers

```python
Teacher("T-NEW", "New Teacher", 6, 30, 
        ["CS101", "CS102", "WEB101"])
```

### Adjust Hour Limits

```python
Teacher("T-1", "Dr. Smith", 
        max_daily_hours=8,      # Increase from 6 to 8
        max_weekly_hours=40)    # Increase from 30 to 40
```

### Add More Classes

```python
Class("CS-D", "Computer Science - D", 40, 
      ["CS101", "CS102", "MATH101"])
```

## Real-World Scenarios

### Scenario 1: Popular Subject

**Setup**:
- CS101 taught by 2 teachers
- 5 classes need CS101

**Problem Finder Output**:
```
Teacher Dr. Chen teaches CS101 to 3 classes
Teacher Prof. Johnson teaches CS101 to 3 classes
```

**Solution**: Solver distributes classes between available teachers.

### Scenario 2: Overloaded Teacher

**Setup**:
- Dr. Wilson teaches CLD101, CLD201, CLD301, DEV101
- 3 Cloud sections + 1 DevOps section

**Problem Finder Output**:
```
Dr. Wilson: Needs 50 hours, Available 30 hours
```

**Solution**: 
1. Add more Cloud teachers
2. Move some subjects to other teachers
3. Increase Dr. Wilson's hour limit

### Scenario 3: Lab Capacity Issues

**Setup**:
- Class size: 50 students
- Lab capacity: 20 students

**Problem Finder Output**:
```
[WARNING] CS-A CS101 lab needs 3 batches (room capacity 20)
```

**Solution**: Automatic batch splitting handled by solver.

## Best Practices

1. **Always run problem finder first**
   ```bash
   python large_timetable_generator.py
   ```

2. **Fix hour violations before solving**
   - Add more teachers
   - Balance subject assignments

3. **Review shared teacher conflicts**
   - These are handled automatically
   - But good to know which teachers are shared

4. **Check lab capacity warnings**
   - Many batches = more scheduling complexity
   - Consider adding larger labs

## Next Steps

### To Solve the Timetable

Integrate with the main solver:

```python
from timetable_solver import TimetableSolver

# Load large dataset
with open("large_dataset.json") as f:
    data = json.load(f)

# Create and run solver
solver = TimetableSolver(data)
solver._create_variables()
solver._add_hard_constraints()
solver._add_teacher_consistency_constraints()  # New!
solver._add_objective()
success = solver.solve(time_limit_seconds=600)
```

### To Generate Custom Dataset

Edit `create_large_dataset()` in `large_timetable_generator.py`:

```python
def create_custom_dataset():
    subjects = [
        Subject("YOUR-SUBJ", "Your Subject", True,
                practical_sessions_per_week=2,
                lab_room_code="YOUR-LAB")
    ]
    # ... rest of configuration
```

## Summary

✅ **Problem Finder**: Detects 34 shared teacher conflicts, 13 hour violations
✅ **Large Dataset**: 10 classes, 21 subjects, 10 labs, 15 teachers
✅ **Configurable Labs**: Each subject defines its own sessions per week
✅ **Subject-Lab Link**: Subjects know their assigned labs
✅ **Automatic Validation**: Checks capacity, hours, assignments before solving

Run it now:
```bash
python large_timetable_generator.py
```

The problem finder will identify all potential issues so you can fix them before running the full solver!
