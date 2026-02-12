# University Timetable Generator - Complexity Analysis & Scaling Guide

## Theoretical Complexity

### Problem Classification

The university timetable generation problem is classified as:
- **Complexity Class**: NP-hard
- **Reduction From**: Graph Coloring / Timetabling Problem
- **Special Cases**: 
  - Polynomial when \|S\|=1 (single subject)
  - Polynomial when \|K\| ≥ \|S\|×\|C\| (unlimited slots)
  - NP-complete for general case

### Why It's NP-Hard

The problem generalizes **Graph Coloring**:
- Each session is a node
- Conflicting sessions (same class/teacher/room) have edges
- Time slots are colors
- Finding a valid coloring is NP-complete
- Our problem adds capacity constraints and optimization objectives

## Variable and Constraint Scaling

### Variable Count

For a university with:
- \|S\| subjects
- \|C\| classes
- \|T\| teachers  
- \|R\| rooms
- \|K\| time slots

**Primary variables** (x[s,c,t,r,k]): 
```
O(|S| × |C| × |T| × |R| × |K|)
```

**Example scenarios**:

| Scale | \|S\| | \|C\| | \|T\| | \|R\| | \|K\| | Variables |
|-------|------|------|------|------|------|-----------|
| Small (Example) | 4 | 3 | 4 | 5 | 12 | ~2,880 |
| Medium Dept | 20 | 10 | 15 | 10 | 30 | ~900,000 |
| Large Dept | 50 | 25 | 30 | 20 | 30 | ~22,500,000 |
| University | 200 | 100 | 100 | 50 | 40 | ~400,000,000 |

### Constraint Count

**Hard constraints**:
- Class conflicts: O(\|C\| × \|K\|)
- Teacher conflicts: O(\|T\| × \|K\|)
- Room conflicts: O(\|R\| × \|K\|)
- Hour limits: O(\|T\| × D)
- Required sessions: O(\|S\| × \|C\|)

**Total**: O((\|C\|+\|T\|+\|R\|) × \|K\| + \|S\| × \|C\|)

## Time Complexity by Phase

### 1. Model Building
```
Time: O(|S| × |C| × |T| × |R| × |K|)
Space: O(|S| × |C| × |T| × |R| × |K|)
```

### 2. Constraint Propagation
```
Time: O(constraints × average_constraint_size)
Space: O(variables)
```

### 3. Search/Solving
```
Worst Case: O(2^variables) - exponential
Average Case: O(n^c) for some constant c
Best Case: O(constraints) - fully propagated
```

## Scaling Strategies

### Strategy 1: Problem Decomposition

**Department-Level Solving**
```
FOR each department d:
    subjects_d ← subjects in department d
    classes_d ← classes taking subjects_d
    teachers_d ← teachers in department d
    rooms_d ← preferred rooms for department d
    
    solution_d ← Solve(subproblem_d)
    
    // Check cross-department conflicts
    IF HasConflict(solution_d, global_solution):
        ResolveConflicts(solution_d, global_solution)
    ENDIF
    
    Merge(global_solution, solution_d)
ENDFOR
```

**Benefits**:
- Reduces problem size from O(N⁵) to O((N/k)⁵) for k departments
- Parallel solving possible
- Easier to manage

**Trade-offs**:
- May miss global optima
- Cross-department conflicts need resolution

### Strategy 2: Day-by-Day Solving

```
solution ← empty
FOR day ← 1 TO D:
    // Fix previous days
    FOR each assignment a IN solution:
        LockVariable(a)
    ENDFOR
    
    // Solve current day
    day_solution ← SolveDay(day)
    
    // Add to solution
    Merge(solution, day_solution)
ENDFOR
```

**Benefits**:
- Reduces \|K\| from 30 to 6 (for single day)
- Enables incremental solving
- Better memory usage

**Trade-offs**:
- Cannot optimize across day boundaries
- May create suboptimal weekly schedules

### Strategy 3: Hierarchical Assignment

```
// Phase 1: Fix high-priority assignments
high_priority ← Filter(assignments, priority=HIGH)
FOR each a IN high_priority:
    FixVariable(a)
ENDFOR

// Phase 2: Solve remaining with fixed assignments
remaining ← Filter(assignments, priority≠HIGH)
solution ← Solve(remaining)
```

**Priority criteria**:
1. Lab sessions (fixed rooms)
2. Large classes (harder to place)
3. Teachers with limited availability
4. Core subjects

### Strategy 4: Heuristic Relaxation

When optimal solution is too slow:

```
// Start with full constraints
FOR relaxation_level ← 0 TO MAX:
    solution ← SolveWithTimeout(time_limit)
    
    IF solution FOUND:
        RETURN solution
    ENDIF
    
    // Relax soft constraints
    IF relaxation_level == 1:
        DisableObjectiveComponent("consecutive_slots")
    ELSE IF relaxation_level == 2:
        DisableObjectiveComponent("workload_balance")
    ELSE IF relaxation_level == 3:
        DisableObjectiveComponent("room_changes")
    ELSE IF relaxation_level == 4:
        // Allow some hard constraint violations with penalty
        RelaxConstraint("teacher_daily_hours", penalty=1000)
    ENDIF
ENDFOR
```

### Strategy 5: Parallel Solving

```
// Split independent subproblems
subproblems ← Partition(data, independence_criteria)

// Solve in parallel
solutions ← ParallelMap(Solve, subproblems)

// Combine
global_solution ← Merge(solutions)
```

**Partitioning criteria**:
- Different room buildings
- Different years/programs
- Non-overlapping teacher sets

## Expected Performance

### Based on Problem Size

| Size | Subjects | Classes | Solving Time | Memory |
|------|----------|---------|--------------|---------|
| Tiny | ≤5 | ≤3 | <10s | <100MB |
| Small | ≤20 | ≤10 | 30s-2min | 500MB-1GB |
| Medium | ≤50 | ≤25 | 5-30min | 2-4GB |
| Large | ≤100 | ≤50 | 30min-2hrs | 4-8GB |
| Very Large | >100 | >50 | Hours | >8GB |

### With Optimizations

| Strategy | Speedup | Quality Impact |
|----------|---------|----------------|
| Decomposition | 5-10x | -5-10% |
| Day-by-day | 3-5x | -10-15% |
| Pre-assignment | 2-4x | Minimal |
| Parallel solving | Linear (cores) | None |
| Heuristic relaxation | 2-3x | -15-25% |

## Memory Optimization

### Memory Usage Breakdown

For 100 subjects, 50 classes, 50 teachers, 30 rooms, 30 slots:

```
Variables:     ~225 million × 4 bytes ≈ 900 MB
Constraints:   ~100,000 × 100 bytes ≈ 10 MB
Search tree:   ~50 million nodes × 8 bytes ≈ 400 MB
Overhead:      ~200 MB
Total:         ~1.5 GB
```

### Memory Reduction Techniques

1. **Lazy Variable Creation**
```python
# Instead of creating all variables upfront
def GetVariable(s, c, t, r, k):
    key = (s, c, t, r, k)
    if key not in variable_cache:
        variable_cache[key] = model.NewBoolVar(name)
    return variable_cache[key]
```

2. **Constraint Compression**
```python
# Use cumulative constraints instead of pairwise
# Reduces O(n²) to O(n) constraints
model.AddCumulative(tasks, capacities)
```

3. **Symmetry Breaking**
```python
# Remove equivalent solutions
# e.g., if rooms R1 and R2 are identical
model.Add(x[s,c,t,R1,k] <= x[s,c,t,R2,k])  # for all s,c,t,k
```

## Solver Parameter Tuning

### CP-SAT Parameters

```python
solver = cp_model.CpSolver()

# Search strategy
solver.parameters.search_branching = cp_model.AUTOMATIC_SEARCH

# Time limits
solver.parameters.max_time_in_seconds = 3600  # 1 hour
solver.parameters.max_memory_in_mb = 8192     # 8 GB

# Parallelization
solver.parameters.num_search_workers = 8

# Solution improvement
solver.parameters.optimize_with_core = True
solver.parameters.num_workers_for_core = 4

# Logging
solver.parameters.log_search_progress = True
solver.parameters.log_frequency_in_seconds = 10
```

### When to Use Different Strategies

**Use decomposition when**:
- Problem has >100 subjects
- Clear department boundaries exist
- Cross-department sharing is minimal

**Use day-by-day when**:
- Daily schedules are largely independent
- Memory is constrained
- Weekly optimization not critical

**Use relaxation when**:
- Hard deadline exists
- Some constraint violations acceptable
- Feasible solution better than no solution

**Use parallel solving when**:
- Multiple CPU cores available
- Independent subproblems identifiable
- Infrastructure supports distributed computing

## Validation and Testing

### Solution Validation

```python
def ValidateSolution(solution, data):
    errors = []
    
    # Check all hard constraints
    for constraint in HardConstraints:
        violations = CheckConstraint(solution, constraint)
        if violations:
            errors.extend(violations)
    
    # Verify completeness
    for subject in data.subjects:
        for class_ in data.classes:
            scheduled = CountScheduled(solution, subject, class_)
            required = GetRequired(subject, class_)
            if scheduled != required:
                errors.append(f"Hour mismatch: {subject} for {class_}")
    
    # Check objective bounds
    objective = CalculateObjective(solution)
    if objective > threshold:
        warnings.append(f"High objective: {objective}")
    
    return len(errors) == 0, errors, warnings
```

### Stress Testing

```python
def StressTest():
    sizes = [
        (5, 3, 4, 5, 12),    # Small
        (20, 10, 15, 10, 30), # Medium
        (50, 25, 30, 20, 30), # Large
    ]
    
    for S, C, T, R, K in sizes:
        data = GenerateRandomData(S, C, T, R, K)
        
        start = time.time()
        solution = GenerateTimetable(data, time_limit=600)
        elapsed = time.time() - start
        
        print(f"Size ({S},{C},{T},{R},{K}): {elapsed:.1f}s")
        
        if solution:
            valid, errors = ValidateSolution(solution, data)
            print(f"  Valid: {valid}, Errors: {len(errors)}")
        else:
            print(f"  No solution found")
```

## Recommendations

### For Small Universities (<50 subjects)
- Use full CP-SAT without decomposition
- Time limit: 10-30 minutes
- Expect optimal or near-optimal solutions

### For Medium Universities (50-200 subjects)
- Use department-level decomposition
- Solve departments in parallel
- Merge with conflict resolution
- Time limit: 1-2 hours total

### For Large Universities (>200 subjects)
- Use multi-level decomposition (dept → program → year)
- Pre-assign high-priority sessions
- Use heuristic relaxation for feasibility
- Consider rolling weekly schedules
- Time limit: 4-8 hours

### General Best Practices

1. **Always validate input data** - Many failures are data issues
2. **Use warm starts** - Start from previous semester's schedule
3. **Monitor solver progress** - Stop if no improvement for long periods
4. **Have fallback strategies** - Multiple solving approaches ready
5. **Cache solutions** - Save intermediate results
6. **Profile performance** - Identify bottlenecks in your specific case

## Future Improvements

### Potential Enhancements

1. **Machine Learning**:
   - Predict optimal search heuristics
   - Learn from past solutions
   - Estimate solving time

2. **Hybrid Approaches**:
   - CP-SAT + Local Search
   - Metaheuristics (Simulated Annealing, Genetic Algorithms)
   - Decomposition + Coordination

3. **Incremental Solving**:
   - Update schedule when small changes occur
   - Re-solve only affected parts
   - Maintain feasibility during changes

4. **Interactive Solving**:
   - Human-in-the-loop for preferences
   - Real-time constraint adjustment
   - Visual feedback

## Conclusion

The university timetable problem is computationally challenging but tractable with proper strategies:

- **Small instances**: Solve optimally with CP-SAT
- **Medium instances**: Use decomposition for efficiency
- **Large instances**: Combine multiple strategies
- **Always**: Validate solutions and have fallbacks

The key is matching the solving strategy to your problem size and constraints.
