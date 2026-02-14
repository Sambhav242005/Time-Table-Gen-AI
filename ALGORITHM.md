# University Timetable Generator - Algorithm Documentation

A comprehensive automated university timetable generation system using Constraint Programming (CP-SAT).

## Overview

This document describes the algorithms used in the University Timetable Generator system. The system employs two distinct CP-SAT approaches: A comprehensive mathematical formulation for the **CLI Solver** and an optimized event-based model for the **GUI Application**.

## CLI Solver Algorithm

The following sections describe the complete mathematical formulation used in `timetable_solver.py`.

## Features

### Hard Constraints (Must Satisfy)

- **Class Conflict**: No class can have multiple sessions at the same time
- **Teacher Conflict**: Teachers cannot be in two places simultaneously  
- **Room Conflict**: Rooms can only host one session per slot
- **Room Capacity**: Room capacity must accommodate all students
- **Fixed Labs**: Practical subjects use assigned lab rooms
- **Teacher Eligibility**: Teachers only teach assigned subjects
- **Hour Limits**: Daily and weekly teacher hour limits enforced
- **Required Sessions**: All theory and practical hours must be scheduled
- **Unavailability**: Respects teacher and room unavailability windows

### Soft Objectives (Optimized)

- **Minimize Student Gaps**: Reduce consecutive free slots between classes
- **Balance Teacher Workload**: Equalize daily hours across the week
- **Minimize Room Changes**: Keep teachers in the same room when possible
- **Prefer Consecutive Slots**: Schedule related sessions back-to-back

## Deliverables Created

1. **mathematical_model.md** - Complete mathematical formulation with LaTeX notation
2. **timetable_solver.py** - Full Python/OR-Tools implementation (500+ lines)
3. **example_dataset.json** - Example data (3 classes, 4 subjects, 2 labs, 4 teachers, 12 slots)
4. **algorithm_pseudocode.md** - Detailed pseudocode for all algorithm phases
5. **complexity_analysis.md** - Complexity analysis and scaling strategies

## Quick Start

### Prerequisites

```bash
pip install ortools
```

### Run the Solver

```bash
python timetable_solver.py
```

This will:

1. Load the example dataset
2. Build the CP-SAT model with all constraints
3. Solve the optimization problem
4. Display the generated timetable
5. Save results to `timetable_solution.json`

## Mathematical Model

The problem is formulated as a **Constraint Satisfaction and Optimization Problem**:

### Decision Variables

- **x[s,c,t,r,k]** ∈ {0,1}: Assignment variable
  - = 1 if subject s is taught to class c by teacher t in room r at slot k

### Hard Constraints

```
Class Conflict:    Σ x[s,c,t,r,k] ≤ 1  ∀c,k
Teacher Conflict:  Σ x[s,c,t,r,k] ≤ 1  ∀t,k  
Room Conflict:     Σ x[s,c,t,r,k] ≤ 1  ∀r,k
Teacher Hours:     Σ x[...] ≤ max_hours  ∀t,d
Required Sessions: Σ x[...] = required   ∀s,c
```

### Objective Function

```
Minimize: w₁·(student gaps) + w₂·(workload imbalance) + 
          w₃·(room changes) - w₄·(consecutive slots)
```

## Algorithm Design

### Why CP-SAT?

1. **Logical Constraints**: Natural handling of if-then logic
2. **Discrete Domains**: Efficient for binary/integer variables
3. **Cumulative Constraints**: Built-in resource capacity support
4. **Search Heuristics**: Advanced propagation and pruning
5. **Scalability**: Better than MILP for highly constrained problems

### Algorithm Phases

1. **Data Preprocessing** - Validate inputs, calculate batches
2. **Variable Creation** - Define decision variables
3. **Constraint Addition** - Add all hard constraints
4. **Objective Setup** - Configure weighted soft constraints
5. **Optimization** - Solve using CP-SAT solver
6. **Solution Extraction** - Format and validate output

## Complexity Analysis

### Problem Classification

- **Class**: NP-hard (generalization of Graph Coloring)
- **Variables**: O(|S|×|C|×|T|×|R|×|K|)
- **Constraints**: O((|C|+|T|+|R|)×|K|)

### Scalability

| Size | Subjects | Time | Strategy |
|------|----------|------|----------|
| Small | ≤20 | <2 min | Direct solving |
| Medium | 20-100 | 5-30 min | Department decomposition |
| Large | >100 | 1-8 hrs | Multi-level decomposition + heuristics |

### Scaling Strategies

1. **Decomposition**: Solve by department, then merge
2. **Day-by-Day**: Rolling horizon approach
3. **Pre-assignment**: Fix high-priority sessions first
4. **Heuristic Relaxation**: Gradually relax soft constraints
5. **Parallel Solving**: Use multiple CPU cores

## Example Dataset

The included example demonstrates:

- **3 Classes**: CS-A (30 students), CS-B (35 students), EC-A (40 students)
- **4 Subjects**: CS101, CS102 (with practicals), MA101, PH101 (with practical)
- **2 Labs**: Lab1 (CS, capacity 20), Lab2 (Physics, capacity 25)
- **4 Teachers**: Various specializations and hour limits
- **12 Slots**: 2 days × 6 slots (9 AM - 2 PM)

### Batch Calculation Example

CS-A has 30 students, CS Lab (L1) has capacity 20:

- Batches needed: ⌈30/20⌉ = 2 batches
- Each batch: 15 students
- CS101 requires 2 practical sessions per week
- Total slots needed: 2 batches × 2 sessions = 4 slots for CS101 practical

## Key Files

- **mathematical_model.md** - Complete mathematical formulation
- **timetable_solver.py** - Python/OR-Tools implementation
- **example_dataset.json** - Example input data
- **algorithm_pseudocode.md** - Algorithm pseudocode
- **complexity_analysis.md** - Complexity and scaling guide

## References

1. OR-Tools Documentation: <https://developers.google.com/optimization>
2. CP-SAT Solver Guide: <https://developers.google.com/optimization/cp/cp_solver>
3. University Timetabling Survey: Academic papers on timetabling algorithms

## Implementation Notes

The solver handles:

- Automatic batch calculation for labs with limited capacity
- Theory and practical session scheduling
- Teacher availability and hour limits
- Room capacity and type constraints
- Multiple optimization objectives with weights

Run `python timetable_solver.py` to generate a complete timetable from the example dataset!

## GUI Application Algorithm

The GUI application (`core/generator_thread.py`) uses a specialized **Event-Based CP-SAT Model** designed for interactivity and specific user-defined constraints.

### distinct Features

- **Event-Based Variables**: Instead of a 5-dimensional grid, it creates variables for each "Event" (e.g., "Math Class for Section A").
  - `x[event_index, day, slot]`: Binary variable indicating when an event starts.
- **Pre-calculation**:
  - Theory classes are treated as single-slot events.
  - Lab sessions are pre-calculated into batches based on room capacity.
- **Constraints**:
  - **Conflict Detection**: Explicitly prevents events for the same section or teacher from overlapping.
  - **Room Assignment**: Dynamically assigns rooms based on type and capacity, or uses pre-assigned rooms.
  - **Soft Constraints**: Minimizes gaps and balances workload using penalty terms.
