# University Timetable Generator - Mathematical Model

## Problem Overview

This document describes the mathematical formulation for the **CLI Solver** (`timetable_solver.py`), which uses a comprehensive Constraint Programming (CP-SAT) approach.

## Sets and Parameters

### Basic Sets

- **S**: Set of subjects, indexed by $s$
  - Each $s \in S$ has: code, has_practical flag, practical_sessions_per_week
  - If practical: practical_code = code + "(P)"
  
- **C**: Set of classes/student groups, indexed by $c$
  - Each $c \in C$ has: size(c) = number of students
  
- **T**: Set of teachers, indexed by $t$
  - Each $t \in T$ has: max_daily_hours(t), max_weekly_hours(t)
  - Optional: preferred_slots(t), unavailable_slots(t)
  
- **R**: Set of rooms, indexed by $r$
  - Each $r \in R$ has: type(r) ∈ {lecture, lab}, capacity(r), location(r)
  
- **L ⊆ R**: Set of lab rooms
  - For each subject s with practical: lab_of(s) ∈ L is fixed
  
- **K**: Set of time slots, indexed by $k$
  - K = {(day, slot) | day ∈ {1,...,D}, slot ∈ {1,...,S_per_day}}
  - |K| = D × S_per_day (e.g., 5 days × 6 slots = 30 slots)
  - Day(k) = day of slot k

### Derived Sets

- **B_{s,c}**: Batches for subject s and class c
  - If lab capacity < size(c): split into batches
  - Each batch b ∈ B_{s,c} has size batch_size(b)
  - Number of batches: ceil(size(c) / capacity(lab_of(s)))

## Decision Variables

### Primary Variables

```
x_{s,c,t,r,k} ∈ {0,1}  (Binary)
```

- = 1 if subject s is taught to class c by teacher t in room r at slot k
- For theory sessions: r is any lecture room
- For practical sessions: r = lab_of(s) (fixed)

### Auxiliary Variables

```
y_{s,c,k} ∈ {0,1}  (Binary)
```

- = 1 if class c has subject s scheduled at slot k (regardless of teacher/room)

```
z_{c,k} ∈ {0,1}  (Binary)
```

- = 1 if class c is busy (has any session) at slot k

```
w_{t,d} ∈ ℤ⁺  (Integer)
```

- Number of hours teacher t works on day d

```
g_{c,k} ∈ {0,1}  (Binary)
```

- = 1 if class c has a gap at slot k (free slot between busy slots)

```
room_changes_{t,d} ∈ ℤ⁺  (Integer)
```

- Number of room changes for teacher t on day d

## Hard Constraints

### 1. Class Conflict Constraint

A class can have at most one session per time slot:

$$
\sum_{s \in S} \sum_{t \in T} \sum_{r \in R} x_{s,c,t,r,k} \leq 1 \quad \forall c \in C, \forall k \in K
$$

### 2. Teacher Conflict Constraint

A teacher cannot be in two places at once:

$$
\sum_{s \in S} \sum_{c \in C} \sum_{r \in R} x_{s,c,t,r,k} \leq 1 \quad \forall t \in T, \forall k \in K
$$

### 3. Room Conflict Constraint

A room can host at most one session per time slot:

$$
\sum_{s \in S} \sum_{c \in C} \sum_{t \in T} x_{s,c,t,r,k} \leq 1 \quad \forall r \in R, \forall k \in K
$$

### 4. Room Capacity Constraint

For lectures: total students ≤ room capacity
For labs: each batch size ≤ lab capacity

$$
\sum_{s \in S} \sum_{t \in T} x_{s,c,t,r,k} \cdot \text{size}(c) \leq \text{capacity}(r) \quad \forall c \in C, \forall r \in R, \forall k \in K
$$

For labs with batches (simplified - ensure each batch fits):

$$
\text{batch\_size}(b) \leq \text{capacity}(\text{lab\_of}(s)) \quad \forall s \in S_{practical}, \forall b \in B_{s,c}
$$

### 5. Fixed Lab Constraint

Practicals must use their designated lab:

$$
x_{s,c,t,r,k} = 0 \quad \forall s \in S_{practical}, \forall c \in C, \forall t \in T, \forall r \neq \text{lab\_of}(s), \forall k \in K
$$

### 6. Teacher Eligibility

Teachers can only teach subjects they are qualified for:

Let A_{s,t} = 1 if teacher t can teach subject s

$$
\sum_{r \in R} x_{s,c,t,r,k} \leq A_{s,t} \quad \forall s \in S, \forall c \in C, \forall t \in T, \forall k \in K
$$

### 6a. Single Teacher Per Subject Per Class (Consistency Constraint)

Within each class-section, each subject must be taught by exactly one teacher throughout the semester. Different sections can have different teachers for the same subject.

Let $\tau_{s,c,t} \in \{0,1\}$ indicate whether teacher $t$ teaches subject $s$ to class $c$:

$$
\tau_{s,c,t} = 1 \iff \sum_{r \in R} \sum_{k \in K} x_{s,c,t,r,k} \geq 1 \quad \forall s \in S, \forall c \in C, \forall t \in T
$$

Exactly one teacher per subject-class pair:

$$
\sum_{t \in T} \tau_{s,c,t} = 1 \quad \forall s \in S, \forall c \in C \text{ where } s \in \text{subjects}(c)
$$

**Example**: If IT-A has ML taught by Dr. Sarah Chen, then ALL ML sessions for IT-A must be by Dr. Sarah Chen. However, IT-B ML could be taught by Prof. Rajesh Kumar.

### 7. Teacher Daily Hour Limits

$$
w_{t,d} = \sum_{s \in S} \sum_{c \in C} \sum_{r \in R} \sum_{k: \text{Day}(k)=d} x_{s,c,t,r,k} \quad \forall t \in T, \forall d \in \{1,..,D\}
$$

$$
w_{t,d} \leq \text{max\_daily\_hours}(t) \quad \forall t \in T, \forall d \in \{1,..,D\}
$$

### 8. Teacher Weekly Hour Limits

$$
\sum_{d=1}^{D} w_{t,d} \leq \text{max\_weekly\_hours}(t) \quad \forall t \in T
$$

### 9. Required Practical Sessions

Schedule exactly N practical sessions per week for subjects with practicals:

Let N_s = number of practical sessions required for subject s

$$
\sum_{c \in C} \sum_{t \in T} \sum_{k \in K} x_{s,c,t,\text{lab\_of}(s),k} = N_s \cdot |B_{s,c}| \quad \forall s \in S_{practical}
$$

### 10. Teacher Unavailability

$$
x_{s,c,t,r,k} = 0 \quad \forall (t,k) \in \text{UnavailablePairs}
$$

### 11. Room Unavailability

$$
x_{s,c,t,r,k} = 0 \quad \forall (r,k) \in \text{RoomUnavailablePairs}
$

## Soft Constraints (Objective Components)

### O1: Minimize Student Gaps
Define gap variable:

$$
g_{c,k} = \begin{cases}
1 & \text{if } z_{c,k-1} = 1 \land z_{c,k} = 0 \land z_{c,k+1} = 1 \\
0 & \text{otherwise}
\end{cases}
$$

Objective contribution:

$$
\text{Minimize } Z_1 = \sum_{c \in C} \sum_{k=2}^{|K|-1} g_{c,k}
$$

### O2: Balance Teacher Workload
Minimize variance in daily workload:

$$
\text{Minimize } Z_2 = \sum_{t \in T} \sum_{d=1}^{D-1} |w_{t,d} - w_{t,d+1}|
$$

Or equivalently using auxiliary variables:

$$
\text{Minimize } Z_2 = \sum_{t \in T} \sum_{d=1}^{D-1} \delta_{t,d}
$$

where:

$$
\delta_{t,d} \geq w_{t,d} - w_{t,d+1} \quad \forall t,d
$$

$$
\delta_{t,d} \geq w_{t,d+1} - w_{t,d} \quad \forall t,d
$$

### O3: Minimize Room Changes per Teacher per Day
Count when consecutive slots for same teacher use different rooms:

$$
\text{room\_changes}_{t,d} = \sum_{k: \text{Day}(k)=d} \sum_{r_1 \neq r_2} \mathbb{1}[\text{teacher in } r_1 \text{ at } k \land \text{teacher in } r_2 \text{ at } k+1]
$$

$$
\text{Minimize } Z_3 = \sum_{t \in T} \sum_{d=1}^{D} \text{room\_changes}_{t,d}
$$

### O4: Prefer Consecutive Slots
Reward consecutive scheduling for same class-subject:

$$
\text{Minimize } Z_4 = -\sum_{s \in S} \sum_{c \in C} \sum_{k=1}^{|K|-1} \mathbb{1}[y_{s,c,k} = 1 \land y_{s,c,k+1} = 1]
$$

(negative because we want to maximize consecutive slots)

## Objective Function

Weighted combination:

$$
\text{Minimize } Z = w_1 \cdot Z_1 + w_2 \cdot Z_2 + w_3 \cdot Z_3 + w_4 \cdot Z_4
$$

Suggested weights:
- $w_1 = 100$ (student gaps - high priority)
- $w_2 = 10$ (workload balance)
- $w_3 = 5$ (room changes)
- $w_4 = 1$ (consecutive slots)

## Solution Approach: CP-SAT

### Why CP-SAT over MILP?

1. **Logical Constraints**: CP-SAT handles logical implications (if-then) more naturally
2. **All-Different Constraints**: Efficient for "no two things at same time" constraints
3. **Cumulative Constraints**: Built-in support for resource capacity (teacher hours, room usage)
4. **Scalability**: Better performance on highly constrained discrete problems
5. **Search Strategies**: Can define custom search heuristics

### CP-SAT Specific Formulation

In OR-Tools CP-SAT:
- Variables are `IntVar` with domain {0,1} or [0, max]
- Use `Add()`, `AddBoolOr()`, `AddImplication()` for constraints
- Use `Minimize()` or `Maximize()` for objective
- Use `AddCumulative()` for teacher/room resource limits

## Complexity Analysis

### Problem Classification
- **Class**: NP-hard (generalization of Graph Coloring)
- **Special Cases**: Polynomial-time solvable only for trivial instances

### Variables and Constraints Count
For a typical university:
- |S| = 100-500 subjects
- |C| = 50-200 classes
- |T| = 50-200 teachers
- |R| = 30-100 rooms
- |K| = 30-40 slots/week

**Variables**: O(|S| × |C| × |T| × |R| × |K|) ≈ 10^7 - 10^9
**Constraints**: O(|C|×|K| + |T|×|K| + |R|×|K| + |T|×D) ≈ 10^5 - 10^6

### Scalability Strategies

1. **Decomposition**: Solve by department/day, then combine
2. **Pre-assignment**: Fix certain high-priority assignments first
3. **Rolling Horizon**: Solve week by week with frozen previous weeks
4. **Heuristics**: Use constraint relaxation when optimal is too slow
5. **Parallel Solving**: Split by independent subproblems

### Expected Runtime
- Small (10 subjects, 5 classes): < 1 minute
- Medium (100 subjects, 50 classes): 5-30 minutes
- Large (500+ subjects, 200+ classes): Hours, may need decomposition

## Output Format

The solution produces:
```
Timetable Matrix: class × slot → (subject, teacher, room, type)
Teacher Schedule: teacher × slot → (class, subject, room)
Room Schedule: room × slot → (class, subject, teacher)
```

## Validation

Solution must satisfy:
- [ ] All hard constraints met
- [ ] Objective value within acceptable bounds
- [ ] All required sessions scheduled
- [ ] No conflicts detected
