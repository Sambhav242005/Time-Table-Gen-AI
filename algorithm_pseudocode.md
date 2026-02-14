# University Timetable Generator - Algorithm & Pseudocode

## Overview

This document provides detailed pseudocode for the **CLI Solver** (`timetable_solver.py`) automated timetable generation algorithm using Constraint Programming (CP-SAT).

## Algorithm Structure

The algorithm follows a multi-phase approach:

1. **Data Preparation** - Parse and validate input data
2. **Variable Creation** - Define decision variables
3. **Constraint Addition** - Add hard and soft constraints
4. **Optimization** - Solve using CP-SAT solver
5. **Solution Extraction** - Format and validate output

---

## Phase 1: Data Preparation

### Algorithm: Validate and Preprocess Data

```
FUNCTION PreprocessData(input_data):
    // Validate subjects
    FOR each subject s IN input_data.subjects:
        IF s.has_practical AND s.practical_code IS NULL:
            s.practical_code ← s.code + "(P)"
        ENDIF
    ENDFOR
    
    // Validate teacher assignments
    FOR each teacher t IN input_data.teachers:
        IF t.can_teach IS EMPTY:
            RAISE Error("Teacher " + t.name + " has no subjects assigned")
        ENDIF
        
        IF t.max_daily_hours > t.max_weekly_hours:
            RAISE Error("Invalid hour limits for teacher " + t.name)
        ENDIF
    ENDFOR
    
    // Calculate batches for labs
    batches ← empty dictionary
    FOR each subject s IN input_data.subjects:
        IF NOT s.has_practical:
            CONTINUE
        ENDIF
        
        lab_room ← input_data.lab_assignments[s.code]
        lab_capacity ← input_data.rooms[lab_room].capacity
        
        FOR each class c IN input_data.classes:
            IF s.code NOT IN c.subjects:
                CONTINUE
            ENDIF
            
            IF c.size <= lab_capacity:
                batches[(s.code, c.code)] ← 1
            ELSE:
                batches[(s.code, c.code)] ← CEIL(c.size / lab_capacity)
            ENDIF
        ENDFOR
    ENDFOR
    
    // Build lookup indexes
    subject_index ← MAP s.code → s FOR s IN input_data.subjects
    class_index ← MAP c.code → c FOR c IN input_data.classes
    teacher_index ← MAP t.code → t FOR t IN input_data.teachers
    room_index ← MAP r.code → r FOR r IN input_data.rooms
    
    RETURN {
        subjects: subject_index,
        classes: class_index,
        teachers: teacher_index,
        rooms: room_index,
        batches: batches,
        time_slots: input_data.time_slots,
        lab_assignments: input_data.lab_assignments
    }
ENDFUNCTION
```

---

## Phase 2: Variable Creation

### Algorithm: Create Decision Variables

```
FUNCTION CreateVariables(model, data):
    variables ← empty dictionary
    
    // Primary assignment variables: x[s,c,t,r,k]
    FOR each subject_code s IN data.subjects:
        FOR each class_code c IN data.classes:
            IF s NOT IN data.classes[c].subjects:
                CONTINUE
            ENDIF
            
            FOR each teacher_code t IN data.teachers:
                IF NOT CanTeach(t, s):
                    CONTINUE
                ENDIF
                
                FOR each room_code r IN data.rooms:
                    IF NOT IsRoomAppropriate(r, s, c, data):
                        CONTINUE
                    ENDIF
                    
                    FOR k ← 0 TO LENGTH(data.time_slots) - 1:
                        var_name ← "x_" + s + "_" + c + "_" + t + "_" + r + "_" + k
                        variables.x[(s,c,t,r,k)] ← model.NewBoolVar(var_name)
                    ENDFOR
                ENDFOR
            ENDFOR
        ENDFOR
    ENDFOR
    
    // Class busy indicators: y[c,k]
    FOR each class_code c IN data.classes:
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            var_name ← "y_" + c + "_" + k
            variables.y[(c,k)] ← model.NewBoolVar(var_name)
        ENDFOR
    ENDFOR
    
    // Teacher daily hours: w[t,d]
    num_days ← LENGTH(data.days)
    FOR each teacher_code t IN data.teachers:
        max_daily ← data.teachers[t].max_daily_hours
        FOR d ← 0 TO num_days - 1:
            var_name ← "w_" + t + "_" + d
            variables.w[(t,d)] ← model.NewIntVar(0, max_daily, var_name)
        ENDFOR
    ENDFOR
    
    RETURN variables
ENDFUNCTION


FUNCTION CanTeach(teacher_code, subject_code):
    RETURN subject_code IN teachers[teacher_code].can_teach
ENDFUNCTION


FUNCTION IsRoomAppropriate(room_code, subject_code, class_code, data):
    room ← data.rooms[room_code]
    subject ← data.subjects[subject_code]
    class ← data.classes[class_code]
    
    IF subject.has_practical:
        // Practical must use assigned lab
        assigned_lab ← data.lab_assignments[subject_code]
        IF room_code ≠ assigned_lab:
            RETURN False
        ENDIF
        // Capacity handled by batching
        RETURN True
    ELSE:
        // Theory must use lecture room
        IF room.room_type ≠ "lecture":
            RETURN False
        ENDIF
        // Check capacity
        IF room.capacity < class.size:
            RETURN False
        ENDIF
        RETURN True
    ENDIF
ENDFUNCTION
```

---

## Phase 3: Hard Constraints

### Algorithm: Add Class Conflict Constraint

```
FUNCTION AddClassConflictConstraints(model, variables, data):
    FOR each class_code c IN data.classes:
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            conflict_vars ← empty list
            
            FOR each subject_code s IN data.subjects:
                FOR each teacher_code t IN data.teachers:
                    FOR each room_code r IN data.rooms:
                        key ← (s, c, t, r, k)
                        IF key IN variables.x:
                            APPEND conflict_vars, variables.x[key]
                        ENDIF
                    ENDFOR
                ENDFOR
            ENDFOR
            
            IF LENGTH(conflict_vars) > 0:
                model.Add(SUM(conflict_vars) ≤ 1)
            ENDIF
        ENDFOR
    ENDFOR
ENDFUNCTION
```

### Algorithm: Add Teacher Conflict Constraint

```
FUNCTION AddTeacherConflictConstraints(model, variables, data):
    FOR each teacher_code t IN data.teachers:
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            conflict_vars ← empty list
            
            FOR each subject_code s IN data.subjects:
                FOR each class_code c IN data.classes:
                    FOR each room_code r IN data.rooms:
                        key ← (s, c, t, r, k)
                        IF key IN variables.x:
                            APPEND conflict_vars, variables.x[key]
                        ENDIF
                    ENDFOR
                ENDFOR
            ENDFOR
            
            IF LENGTH(conflict_vars) > 0:
                model.Add(SUM(conflict_vars) ≤ 1)
            ENDIF
        ENDFOR
    ENDFOR
ENDFUNCTION
```

### Algorithm: Add Room Conflict Constraint

```
FUNCTION AddRoomConflictConstraints(model, variables, data):
    FOR each room_code r IN data.rooms:
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            conflict_vars ← empty list
            
            FOR each subject_code s IN data.subjects:
                FOR each class_code c IN data.classes:
                    FOR each teacher_code t IN data.teachers:
                        key ← (s, c, t, r, k)
                        IF key IN variables.x:
                            APPEND conflict_vars, variables.x[key]
                        ENDIF
                    ENDFOR
                ENDFOR
            ENDFOR
            
            IF LENGTH(conflict_vars) > 0:
                model.Add(SUM(conflict_vars) ≤ 1)
            ENDIF
        ENDFOR
    ENDFOR
ENDFUNCTION
```

### Algorithm: Add Teacher Hour Constraints

```
FUNCTION AddTeacherHourConstraints(model, variables, data):
    num_days ← LENGTH(data.days)
    
    FOR each teacher_code t IN data.teachers:
        teacher ← data.teachers[t]
        
        FOR d ← 0 TO num_days - 1:
            daily_vars ← empty list
            
            FOR k ← 0 TO LENGTH(data.time_slots) - 1:
                IF data.time_slots[k].day ≠ d:
                    CONTINUE
                ENDIF
                
                FOR each subject_code s IN data.subjects:
                    FOR each class_code c IN data.classes:
                        FOR each room_code r IN data.rooms:
                            key ← (s, c, t, r, k)
                            IF key IN variables.x:
                                APPEND daily_vars, variables.x[key]
                            ENDIF
                        ENDFOR
                    ENDFOR
                ENDFOR
            ENDFOR
            
            IF LENGTH(daily_vars) > 0:
                model.Add(variables.w[(t,d)] == SUM(daily_vars))
            ELSE:
                model.Add(variables.w[(t,d)] == 0)
            ENDIF
            
            model.Add(variables.w[(t,d)] ≤ teacher.max_daily_hours)
        ENDFOR
        
        // Weekly limit
        weekly_sum ← SUM(variables.w[(t,d)] FOR d ← 0 TO num_days - 1)
        model.Add(weekly_sum ≤ teacher.max_weekly_hours)
    ENDFOR
ENDFUNCTION
```

### Algorithm: Add Required Session Constraints

```
FUNCTION AddRequiredSessionConstraints(model, variables, data):
    // Theory hours
    FOR each subject_code s IN data.subjects:
        subject ← data.subjects[s]
        
        FOR each class_code c IN data.classes:
            IF s NOT IN data.classes[c].subjects:
                CONTINUE
            ENDIF
            
            theory_vars ← empty list
            
            FOR k ← 0 TO LENGTH(data.time_slots) - 1:
                FOR each teacher_code t IN data.teachers:
                    FOR each room_code r IN data.rooms:
                        IF data.rooms[r].room_type ≠ "lecture":
                            CONTINUE
                        ENDIF
                        
                        key ← (s, c, t, r, k)
                        IF key IN variables.x:
                            APPEND theory_vars, variables.x[key]
                        ENDIF
                    ENDFOR
                ENDFOR
            ENDFOR
            
            IF LENGTH(theory_vars) > 0:
                model.Add(SUM(theory_vars) == subject.theory_hours_per_week)
            ENDIF
        ENDFOR
    ENDFOR
    
    // Practical sessions
    FOR each subject_code s IN data.subjects:
        subject ← data.subjects[s]
        IF NOT subject.has_practical:
            CONTINUE
        ENDIF
        
        lab_room ← data.lab_assignments[s]
        
        FOR each class_code c IN data.classes:
            IF s NOT IN data.classes[c].subjects:
                CONTINUE
            ENDIF
            
            // Calculate required sessions with batches
            class_size ← data.classes[c].size
            lab_capacity ← data.rooms[lab_room].capacity
            
            IF class_size ≤ lab_capacity:
                batches ← 1
            ELSE:
                batches ← CEIL(class_size / lab_capacity)
            ENDIF
            
            required_sessions ← subject.practical_sessions_per_week * batches
            
            practical_vars ← empty list
            
            FOR k ← 0 TO LENGTH(data.time_slots) - 1:
                FOR each teacher_code t IN data.teachers:
                    key ← (s, c, t, lab_room, k)
                    IF key IN variables.x:
                        APPEND practical_vars, variables.x[key]
                    ENDIF
                ENDFOR
            ENDFOR
            
            IF LENGTH(practical_vars) > 0:
                model.Add(SUM(practical_vars) == required_sessions)
            ENDIF
        ENDFOR
    ENDFOR
ENDFUNCTION
```

---

## Phase 4: Soft Constraints (Objective)

### Algorithm: Add Gap Minimization

```
FUNCTION AddGapMinimizationObjective(model, variables, data):
    gap_terms ← empty list
    
    FOR each class_code c IN data.classes:
        FOR k ← 1 TO LENGTH(data.time_slots) - 2:
            k_curr ← data.time_slots[k]
            k_prev ← data.time_slots[k - 1]
            k_next ← data.time_slots[k + 1]
            
            // Only consider gaps within same day
            IF k_curr.day ≠ k_prev.day OR k_curr.day ≠ k_next.day:
                CONTINUE
            ENDIF
            
            // Create gap indicator: busy at k-1 and k+1, free at k
            gap_var ← model.NewBoolVar("gap_" + c + "_" + k)
            
            // gap = 1 IMPLIES (y[c,k-1]=1 AND y[c,k]=0 AND y[c,k+1]=1)
            model.AddBoolAnd([
                variables.y[(c, k - 1)],
                variables.y[(c, k + 1)]
            ]).OnlyEnforceIf(gap_var)
            
            model.AddBoolOr([
                variables.y[(c, k - 1)].Not(),
                variables.y[(c, k + 1)].Not()
            ]).OnlyEnforceIf(gap_var.Not())
            
            model.Add(variables.y[(c, k)] == 0).OnlyEnforceIf(gap_var)
            
            APPEND gap_terms, WEIGHT_GAP * gap_var
        ENDFOR
    ENDFOR
    
    RETURN gap_terms
ENDFUNCTION
```

### Algorithm: Add Workload Balance Objective

```
FUNCTION AddWorkloadBalanceObjective(model, variables, data):
    balance_terms ← empty list
    num_days ← LENGTH(data.days)
    
    FOR each teacher_code t IN data.teachers:
        FOR d ← 0 TO num_days - 2:
            // |w[t,d] - w[t,d+1]|
            diff_var ← model.NewIntVar(-30, 30, "diff_" + t + "_" + d)
            abs_diff ← model.NewIntVar(0, 30, "abs_diff_" + t + "_" + d)
            
            model.Add(diff_var == variables.w[(t,d)] - variables.w[(t,d+1)])
            model.AddAbsEquality(abs_diff, diff_var)
            
            APPEND balance_terms, WEIGHT_BALANCE * abs_diff
        ENDFOR
    ENDFOR
    
    RETURN balance_terms
ENDFUNCTION
```

---

## Phase 5: Solution Extraction

### Algorithm: Extract and Format Solution

```
FUNCTION ExtractSolution(solver, variables, data):
    IF solver.Status() ≠ OPTIMAL AND solver.Status() ≠ FEASIBLE:
        RETURN NULL
    ENDIF
    
    solution ← {
        class_timetable: empty dictionary,
        teacher_timetable: empty dictionary,
        room_timetable: empty dictionary,
        statistics: empty dictionary
    }
    
    // Initialize empty timetables
    FOR each class_code c IN data.classes:
        solution.class_timetable[c] ← empty dictionary
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            solution.class_timetable[c][k] ← NULL
        ENDFOR
    ENDFOR
    
    FOR each teacher_code t IN data.teachers:
        solution.teacher_timetable[t] ← empty dictionary
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            solution.teacher_timetable[t][k] ← NULL
        ENDFOR
    ENDFOR
    
    FOR each room_code r IN data.rooms:
        solution.room_timetable[r] ← empty dictionary
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            solution.room_timetable[r][k] ← NULL
        ENDFOR
    ENDFOR
    
    // Fill in assignments
    FOR each key, var IN variables.x:
        IF solver.Value(var) == 1:
            s_code, c_code, t_code, r_code, k_idx ← key
            k ← data.time_slots[k_idx]
            
            session ← {
                subject: s_code,
                class: c_code,
                teacher: t_code,
                room: r_code,
                day: k.day_name,
                time: k.time
            }
            
            solution.class_timetable[c_code][k_idx] ← session
            solution.teacher_timetable[t_code][k_idx] ← session
            solution.room_timetable[r_code][k_idx] ← session
        ENDIF
    ENDFOR
    
    // Calculate statistics
    solution.statistics.objective_value ← solver.ObjectiveValue()
    solution.statistics.gap_count ← CountGaps(solution, data)
    solution.statistics.room_changes ← CountRoomChanges(solution, data)
    solution.statistics.teacher_utilization ← CalculateTeacherUtilization(solution, data)
    
    RETURN solution
ENDFUNCTION
```

---

## Main Algorithm

```
FUNCTION GenerateTimetable(input_data, time_limit_seconds):
    // Phase 1: Preprocessing
    data ← PreprocessData(input_data)
    
    // Phase 2: Create CP-SAT model
    model ← NewCpModel()
    variables ← CreateVariables(model, data)
    
    // Phase 3: Add hard constraints
    AddClassConflictConstraints(model, variables, data)
    AddTeacherConflictConstraints(model, variables, data)
    AddRoomConflictConstraints(model, variables, data)
    LinkBusyIndicators(model, variables, data)
    AddTeacherHourConstraints(model, variables, data)
    AddRequiredSessionConstraints(model, variables, data)
    AddUnavailabilityConstraints(model, variables, data)
    
    // Phase 4: Add objective
    objective_terms ← empty list
    APPEND objective_terms, AddGapMinimizationObjective(model, variables, data)
    APPEND objective_terms, AddWorkloadBalanceObjective(model, variables, data)
    APPEND objective_terms, AddConsecutiveSlotsObjective(model, variables, data)
    
    model.Minimize(SUM(objective_terms))
    
    // Phase 5: Solve
    solver ← NewCpSolver()
    solver.parameters.max_time_in_seconds ← time_limit_seconds
    solver.parameters.num_search_workers ← 8
    
    status ← solver.Solve(model)
    
    // Phase 6: Extract solution
    IF status == OPTIMAL OR status == FEASIBLE:
        solution ← ExtractSolution(solver, variables, data)
        RETURN solution
    ELSE:
        RETURN NULL
    ENDIF
ENDFUNCTION
```

---

## Helper Functions

```
FUNCTION CountGaps(solution, data):
    gap_count ← 0
    
    FOR each class_code c IN data.classes:
        FOR k ← 1 TO LENGTH(data.time_slots) - 2:
            k_curr ← data.time_slots[k]
            k_prev ← data.time_slots[k - 1]
            k_next ← data.time_slots[k + 1]
            
            // Must be same day
            IF k_curr.day ≠ k_prev.day OR k_curr.day ≠ k_next.day:
                CONTINUE
            ENDIF
            
            busy_prev ← solution.class_timetable[c][k - 1] ≠ NULL
            busy_curr ← solution.class_timetable[c][k] ≠ NULL
            busy_next ← solution.class_timetable[c][k + 1] ≠ NULL
            
            IF busy_prev AND NOT busy_curr AND busy_next:
                gap_count ← gap_count + 1
            ENDIF
        ENDFOR
    ENDFOR
    
    RETURN gap_count
ENDFUNCTION


FUNCTION CountRoomChanges(solution, data):
    changes ← 0
    
    FOR each teacher_code t IN data.teachers:
        FOR d ← 0 TO LENGTH(data.days) - 1:
            prev_room ← NULL
            
            FOR k ← 0 TO LENGTH(data.time_slots) - 1:
                IF data.time_slots[k].day ≠ d:
                    CONTINUE
                ENDIF
                
                session ← solution.teacher_timetable[t][k]
                IF session ≠ NULL:
                    IF prev_room ≠ NULL AND session.room ≠ prev_room:
                        changes ← changes + 1
                    ENDIF
                    prev_room ← session.room
                ENDIF
            ENDFOR
        ENDFOR
    ENDFOR
    
    RETURN changes
ENDFUNCTION


FUNCTION ValidateSolution(solution, data):
    errors ← empty list
    
    // Check all hard constraints
    FOR each class_code c IN data.classes:
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            sessions ← CountSessionsInSlot(solution, c, k)
            IF sessions > 1:
                APPEND errors, "Class conflict at " + c + " slot " + k
            ENDIF
        ENDFOR
    ENDFOR
    
    FOR each teacher_code t IN data.teachers:
        FOR k ← 0 TO LENGTH(data.time_slots) - 1:
            sessions ← CountTeacherSessionsInSlot(solution, t, k)
            IF sessions > 1:
                APPEND errors, "Teacher conflict at " + t + " slot " + k
            ENDIF
        ENDFOR
    ENDFOR
    
    // Check required hours
    FOR each subject_code s IN data.subjects:
        FOR each class_code c IN data.classes:
            scheduled ← CountScheduledHours(solution, s, c)
            required ← GetRequiredHours(data, s, c)
            IF scheduled ≠ required:
                APPEND errors, "Hour mismatch: " + s + " for " + c
            ENDIF
        ENDFOR
    ENDFOR
    
    RETURN LENGTH(errors) == 0, errors
ENDFUNCTION
```

---

## Complexity Summary

| Phase | Time Complexity | Space Complexity |
|-------|----------------|------------------|
| Preprocessing | O(\|S\|×\|C\|) | O(\|S\|+\|C\|+\|T\|+\|R\|) |
| Variable Creation | O(\|S\|×\|C\|×\|T\|×\|R\|×\|K\|) | O(\|S\|×\|C\|×\|T\|×\|R\|×\|K\|) |
| Constraint Addition | O((\|C\|+\|T\|+\|R\|)×\|K\|) | O((\|C\|+\|T\|+\|R\|)×\|K\|) |
| Solving | Exponential in worst case | O(variables + constraints) |
| Solution Extraction | O(\|S\|×\|C\|×\|T\|×\|R\|×\|K\|) | O(\|C\|×\|K\|) |

**Overall**: The problem is NP-hard, so solving time is exponential in the worst case. However, CP-SAT uses advanced propagation and search heuristics to solve practical instances efficiently.
