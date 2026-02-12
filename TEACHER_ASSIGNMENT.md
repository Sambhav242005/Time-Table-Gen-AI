# Teacher Assignment Features

## Overview

The timetable generator now supports advanced teacher assignment scenarios common in universities:

## Key Features

### 1. Different Sections Have Different Subjects

Each class section can have its own set of subjects:

```
IT-A: ML, DSA, WEB, CLOUD, DBMS
IT-B: ML, DSA, WEB, DBMS, NETWORK
IT-C: ML, DSA, CLOUD, DBMS, NETWORK
IT-D: DSA, WEB, CLOUD, DBMS, NETWORK (No ML!)
```

### 2. Single Teacher Per Subject Per Section

**Constraint**: Within a section, each subject has exactly ONE teacher.

✅ **Valid Scenario**:
- IT-A ML: Always Dr. Sarah Chen (all sessions)
- IT-B ML: Always Prof. Rajesh Kumar (all sessions)
- IT-C ML: Always Dr. Sarah Chen (all sessions)

❌ **Invalid Scenario** (Prevented by constraint):
- IT-A ML: Dr. Sarah Chen on Monday, Prof. Rajesh Kumar on Wednesday

### 3. Same Subject Across Sections Can Have Different Teachers

Different sections are independent - they can have different teachers:

```
IT-A ML: Dr. Sarah Chen
IT-B ML: Prof. Rajesh Kumar
IT-C ML: Dr. Sarah Chen
```

### 4. One Teacher Can Teach Multiple Subjects

A teacher can be qualified to teach multiple subjects:

```
Dr. Emily Zhang: Can teach WEB and CLOUD
- She might teach IT-A WEB
- And also IT-C CLOUD
- But NOT IT-A CLOUD (if assigned to different teacher)
```

## Implementation

### Teacher Consistency Constraint

The constraint is implemented using indicator variables:

```python
# For each subject s, class c, and eligible teacher t
if teacher t teaches subject s to class c:
    tau[s,c,t] = 1
else:
    tau[s,c,t] = 0

# Constraint: Exactly one teacher per subject-class pair
sum(tau[s,c,t] for all eligible t) = 1
```

### Example Data Structure

```json
{
  "classes": [
    {
      "code": "IT-A",
      "subjects": ["ML", "DSA", "WEB", "CLOUD", "DBMS"]
    },
    {
      "code": "IT-D",
      "subjects": ["DSA", "WEB", "CLOUD", "DBMS", "NETWORK"]
    }
  ],
  "teachers": [
    {
      "code": "T-ML-1",
      "name": "Dr. Sarah Chen",
      "can_teach": ["ML"]
    },
    {
      "code": "T-ML-2",
      "name": "Prof. Rajesh Kumar",
      "can_teach": ["ML"]
    },
    {
      "code": "T-MULTI",
      "name": "Dr. Emily Zhang",
      "can_teach": ["WEB", "CLOUD"]
    }
  ]
}
```

## Real-World Scenarios

### Scenario 1: Large Subject with Multiple Teachers

**Machine Learning** is taught in 3 sections (IT-A, IT-B, IT-C) with 2 available teachers:

**Solution**: 
- Solver assigns Dr. Sarah Chen to IT-A and IT-C
- Solver assigns Prof. Rajesh Kumar to IT-B
- Each section gets exactly one ML teacher

**Benefit**: 
- Balanced workload across teachers
- Students get consistent instruction within their section

### Scenario 2: Multi-Skilled Teacher

**Dr. Emily Zhang** can teach both WEB and CLOUD:

**Possible Assignment**:
- IT-A WEB: Dr. Emily Zhang
- IT-C CLOUD: Dr. Emily Zhang
- IT-A CLOUD: Dr. James Wilson (different teacher)

**Benefit**:
- Maximizes teacher utilization
- Provides scheduling flexibility

### Scenario 3: Specialized Teacher

**Dr. Michael Brown** only teaches DSA:

**Result**:
- All sections (IT-A, B, C, D) that have DSA get Dr. Brown
- Only one teacher available, so no choice

**Benefit**:
- Ensures specialized subjects taught by experts

## How It Works

### Step 1: Teacher Eligibility Check

```python
def _get_teacher_can_teach(teacher_code, subject_code):
    teacher = self.teachers[teacher_code]
    return subject_code in teacher.can_teach
```

### Step 2: Teacher Selection Variable

For each (subject, class, teacher) combination, create an indicator:

```python
# tau[s,c,t] = 1 if teacher t teaches subject s to class c
tau = model.NewBoolVar(f"teaches_{s}_{c}_{t}")
```

### Step 3: Link to Assignment Variables

```python
# tau = 1 implies sum of all sessions by this teacher >= 1
model.Add(sum(all_sessions) >= 1).OnlyEnforceIf(tau)

# tau = 0 implies no sessions by this teacher
model.Add(sum(all_sessions) == 0).OnlyEnforceIf(tau.Not())
```

### Step 4: Enforce Single Teacher

```python
# Exactly one teacher must be selected
model.Add(sum(teacher_vars) == 1)
```

## Validation

The solver automatically validates:

1. ✅ Each section has consistent teachers per subject
2. ✅ No mixed teachers within a section-subject
3. ✅ Teachers only teach subjects they're qualified for
4. ✅ Different sections can independently choose teachers
5. ✅ Multi-skilled teachers can teach multiple subjects

## Examples

### Example 1: IT Department Sections

See `example_it_sections.json` for a complete example with:
- 4 IT sections with different subject combinations
- 9 teachers with various specializations
- Multiple teachers available for popular subjects (ML, DBMS)
- Multi-skilled teachers (WEB + CLOUD)

### Example 2: Expected Output

```
IT-A Timetable:
  ML: Dr. Sarah Chen (all sessions)
  DSA: Dr. Michael Brown (all sessions)
  WEB: Dr. Emily Zhang (all sessions)
  CLOUD: Dr. James Wilson (all sessions)
  DBMS: Prof. Maria Garcia (all sessions)

IT-B Timetable:
  ML: Prof. Rajesh Kumar (all sessions) ← Different from IT-A!
  DSA: Dr. Michael Brown (all sessions)
  WEB: Prof. Lisa Wang (all sessions)
  DBMS: Dr. Ahmed Hassan (all sessions) ← Different from IT-A!
  NETWORK: Prof. David Lee (all sessions)
```

## Running the Example

```bash
python timetable_solver.py
```

The solver will:
1. Load the dataset
2. Enforce teacher consistency constraints
3. Optimize for best teacher assignments
4. Generate timetables respecting all constraints

## Benefits

1. **Consistency**: Students have the same teacher throughout the semester
2. **Flexibility**: Different sections can optimize independently
3. **Balanced Workload**: Multi-skilled teachers can take on appropriate load
4. **Expert Assignment**: Specialized teachers teach their subjects
5. **Scheduling Efficiency**: Better resource utilization across sections

## Troubleshooting

### "No solution found" for teacher assignment

**Cause**: Too few teachers for popular subjects

**Solutions**:
- Add more teachers who can teach the subject
- Reduce number of sections taking that subject
- Increase teacher weekly hour limits

### "Unbalanced teacher workload"

**Cause**: All sections want the same popular teacher

**Solutions**:
- Add workload balancing to objective function
- Set maximum sections per teacher
- Use preferred teacher assignments

## Mathematical Formulation

See `mathematical_model.md` Section 6a for the complete mathematical formulation of the teacher consistency constraint.
