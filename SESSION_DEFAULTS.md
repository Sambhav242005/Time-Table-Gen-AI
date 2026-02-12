# Subject Session Defaults - Quick Reference

## Default Sessions Per Week

### Theory Subjects (No Practical)
```python
theory_hours_per_week: int = 3  # DEFAULT: 3 sessions per week
```

**Example**:
```python
Subject("CS201", "Algorithms", False)  # No practical
# Automatically gets:
# - theory_hours_per_week = 3
# - No practical sessions
```

### Practical Subjects
```python
theory_hours_per_week: int = 3           # DEFAULT: 3 theory sessions
practical_sessions_per_week: int = 2     # DEFAULT: 2 lab sessions (if has_practical=True)
```

**Example**:
```python
Subject("CS101", "Intro to Programming", True)
# Automatically gets:
# - theory_hours_per_week = 3
# - practical_sessions_per_week = 2
# - practical_code = "CS101(P)"
```

## Complete Subject Configuration

### Minimal Configuration (Uses All Defaults)
```python
# Theory-only subject
Subject("MATH101", "Mathematics I", False)
# Result: 3 theory sessions/week

# Practical subject
Subject("CS101", "Intro to Programming", True, lab_room_code="LAB-CS")
# Result: 3 theory + 2 practical sessions/week
```

### Custom Configuration
```python
# Theory subject with custom hours
Subject("CS201", "Algorithms", False, 
        theory_hours_per_week=4)  # Custom: 4 sessions/week

# Practical subject with custom sessions
Subject("PHY101", "Physics I", True,
        theory_hours_per_week=3,           # Default: 3 theory
        practical_sessions_per_week=3,      # Custom: 3 lab sessions (not 2!)
        lab_room_code="LAB-PHY")
```

## Current Large Dataset Configuration

### Theory-Only Subjects (3 sessions/week)
```python
Subject("CS201", "Algorithms", False)                    # 3 theory
Subject("AI101", "Artificial Intelligence", False)       # 3 theory
Subject("MAT101", "Mathematics I", False)                # 3 theory
Subject("MAT201", "Discrete Math", False)                # 3 theory
```

### Practical Subjects (3 theory + 2 practical = 5 total/week)
```python
Subject("CS101", "Intro to Programming", True,
        lab_room_code="LAB-CS-1")                        # 3 + 2 = 5 sessions
        
Subject("ML101", "Machine Learning", True,
        lab_room_code="LAB-AI")                          # 3 + 2 = 5 sessions
        
Subject("CLD101", "Cloud Computing", True,
        lab_room_code="LAB-CLD")                         # 3 + 2 = 5 sessions
        
Subject("PHY101", "Physics I", True,
        lab_room_code="LAB-PHY")                         # 3 + 2 = 5 sessions
```

## How It Works

### In Subject Dataclass
```python
@dataclass
class Subject:
    theory_hours_per_week: int = 3        # Always defaults to 3
    practical_sessions_per_week: int = 0   # Defaults to 0, but...
    
    def __post_init__(self):
        if self.has_practical:
            if self.practical_sessions_per_week == 0:
                self.practical_sessions_per_week = 2  # Set to 2 if practical
```

### Logic Flow
1. **Create Subject** with `has_practical=True` or `False`
2. **If theory-only**: Gets 3 theory sessions/week
3. **If practical**: Gets 3 theory + 2 practical = 5 total sessions/week
4. **Override anytime**: Specify custom values to replace defaults

## Calculation Example

### CS-A Class Subjects
```python
Subjects: CS101, CS102, CS201, MAT101, PHY101

CS101 (Practical):  3 theory + 2 practical = 5 sessions/week
CS102 (Practical):  3 theory + 2 practical = 5 sessions/week
CS201 (Theory):     3 theory + 0 practical = 3 sessions/week
MAT101 (Theory):    3 theory + 0 practical = 3 sessions/week
PHY101 (Practical): 3 theory + 2 practical = 5 sessions/week

Total per week: 5 + 5 + 3 + 3 + 5 = 21 sessions
```

### For 10 Classes
```
Average sessions per class: ~20-25/week
Total sessions to schedule: ~220/week
Available slots: 30 slots/week (5 days × 6 slots)
Utilization: ~73% (good!)
```

## Modifying Defaults

### Change Theory Default
Edit Subject dataclass:
```python
theory_hours_per_week: int = 4  # Change from 3 to 4
```

### Change Practical Default
Edit __post_init__:
```python
if self.practical_sessions_per_week == 0:
    self.practical_sessions_per_week = 3  # Change from 2 to 3
```

### Per-Subject Override (Recommended)
```python
Subject("INTENSIVE", "Intensive Course", True,
        theory_hours_per_week=5,           # More theory
        practical_sessions_per_week=4)      # More practical
```

## Summary Table

| Subject Type | Theory | Practical | Total | Configuration |
|--------------|--------|-----------|-------|---------------|
| Theory-only | 3 | 0 | 3 | `Subject("X", "Name", False)` |
| Practical (default) | 3 | 2 | 5 | `Subject("X", "Name", True, lab_room_code="LAB")` |
| Practical (custom) | 3 | 3 | 6 | `Subject("X", "Name", True, practical_sessions_per_week=3, ...)` |
| Theory (custom) | 4 | 0 | 4 | `Subject("X", "Name", False, theory_hours_per_week=4)` |

## Validation

The solver automatically validates:
- ✅ Total required sessions fit in available time slots
- ✅ Theory + practical hours don't exceed teacher limits
- ✅ Room capacity accommodates class size

**Current setup**: Theory=3, Practical=2 is optimized for 30-slot week! ✅
