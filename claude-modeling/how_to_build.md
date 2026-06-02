# How to Build the Snake Building Model From Scratch

---

## TASK 1 — Understand the problem

### 1.1 — Understand what a snake is
- A snake is a fixed weekly template (not a real week, a pattern)
- Workers rotate through the template cyclically — the template never changes
- A snake of length w needs exactly w workers

### 1.2 — Understand why multiple snakes
- One snake is often not enough because of rest constraints at the cyclic boundary
- Example: mixing night and morning shifts in one snake creates a rest violation
  when the last week wraps back to the first week
- Multiple snakes = split incompatible shift types into separate templates

### 1.3 — Understand the objective
- Every snake of length w needs w workers
- Total workers = sum of all snake lengths
- Goal: make this sum as small as possible
```
Minimise   w[0] + w[1] + ... + w[n-1]
```

### 1.4 — Understand the constraints
Ask yourself for each constraint: why does this rule exist in real life?
- C1: every shift must be covered → you cannot leave the station understaffed
- C2: one person cannot work twice in one day → physically impossible
- C3: technical → snake length = highest week position used
- C4, C5, C6: German labour law → minimum 11 hours rest between shifts
  - C4 = within the same snake week
  - C5 = between two consecutive snake weeks
  - C6 = between the last week and week 1 (cyclic boundary)

### 1.5 — Understand the difference between shift type and instance
- Shift type = the pattern (e.g. EARLY_, 06:00-14:00, Mon-Fri, 2 workers)
- Instance = one individual worker-slot
- If workers=2 → one shift type on one day creates 2 instances (copy=0, copy=1)
- The ILP assigns instances, not shift types

---

## TASK 2 — Define your data on paper

### 2.1 — List all shift types
For each shift write down:
```
name        (6 characters, e.g. EARLY_)
code        (6 digits, unique, e.g. 000001)
days        which days of the week it occurs (1=Mon ... 7=Sun)
start time  in minutes from midnight
end time    in minutes from midnight (add 1440 if it ends next day)
workers     how many people needed per occurrence
class       1 = attractive (day), 2 = unattractive (night)
```

### 2.2 — Convert times to minutes
```
multiply hours by 60, add minutes
06:00  = 6×60       =  360
14:00  = 14×60      =  840
22:00  = 22×60      = 1320

overnight: add 1440 for each day the shift crosses midnight
22:00 → 06:00 next day  =  1320 + 480  =  1800
08:00 → 08:00 next day  =   480 + 1440 =  1920
```

### 2.3 — Choose your parameters
```
R       = 660  (11 hours minimum rest — German law)
n       = number of snakes (start with 2, adjust if no solution found)
W_max   = maximum snake length (start with 14)
```

### 2.4 — Write the data into shifts.py
- Open claude-modeling/data/shifts.py
- Add your shift types to the SHIFT_TYPES list
- Follow the existing format exactly

---

## TASK 3 — Build the instance list

### 3.1 — Calculate how many instances you will have
```
for each shift type:
    instances += len(days) × workers

example:
  EARLY_  5 days × 2 workers  = 10
  NIGHT_  7 days × 2 workers  = 14
  total = 24
```

### 3.2 — Run the data file to verify
```bash
cd ~/projects/snake-building/claude-modeling
python3 data/shifts.py
```
Check: does the printed count match your calculation from 3.1?

### 3.3 — Understand what build_instances() does
Read the function in data/shifts.py line by line.
It loops over shift types → days → worker copies and creates one ShiftInstance per combination.

---

## TASK 4 — Find incompatible pairs

### 4.1 — Understand the gap formula
```
gap(a, b) = 1440 + start[b] − end[a]

where:
  a = shift on day d
  b = shift on day d+1  (the very next day)
  1440 = one full day in minutes

if gap < R (660 min)  →  pair (a, b) is incompatible
```

### 4.2 — Work through one example by hand
Pick any night shift and the morning shift on the next day.
Calculate the gap. Is it below 660?

```
example:
  NIGHT_ ends at 1800 (06:00 next day)
  EARLY_ starts at 360 (06:00)
  gap = 1440 + 360 - 1800 = 0 min  →  incompatible ✗
```

### 4.3 — Run compatibility check
```bash
python3 data/shifts.py
```
Check: how many incompatible pairs are printed?
Split them mentally into:
- intraweek pairs  (day[a] < 7 or day[b] > 1)  → used in C4
- cross pairs      (day[a]=7 and day[b]=1)       → used in C5 and C6

---

## TASK 5 — Write the mathematical model

### 5.1 — Write the sets
On paper, list:
```
I  = {0, 1, 2, ..., |I|-1}     all instance indices
K  = {0, 1, ..., n-1}          snake indices
J  = {1, 2, ..., W_max}        week positions
D  = {1, 2, 3, 4, 5, 6, 7}    days of the week
```

### 5.2 — Write the parameters
On paper, for 2-3 instances write out their actual values:
```
instance i=0:  day=1, start=360, end=840
instance i=14: day=1, start=1320, end=1800
...
```

### 5.3 — Write the decision variables
```
x[i, k, j] ∈ {0,1}   one variable per (instance, snake, week)
w[k]        ∈ Z≥0     one variable per snake
y[k, j]     ∈ {0,1}   one variable per (snake, week)  — auxiliary for C6
```
Count how many x variables you will have: |I| × n × W_max

### 5.4 — Write the objective
```
Minimise   Σ_{k} w[k]
```

### 5.5 — Write constraint C1
One constraint per instance.
```
Σ_{k,j} x[i,k,j] = 1    for each i ∈ I
```
Pick instance i=0 and write it out with actual numbers.

### 5.6 — Write constraint C2
One constraint per (snake, week, day).
```
Σ_{i: day[i]=d} x[i,k,j] ≤ 1    for each k,j,d
```
Pick k=0, j=1, d=1 and write it out.

### 5.7 — Write constraint C3
```
w[k] ≥ j × x[i,k,j]    for each i,k,j
```
What does this mean in plain words?
→ if x[i,k,5]=1 then w[k] must be at least 5.

### 5.8 — Write constraints C4, C5, C6
For each incompatible pair (a,b) you found in Task 4:
```
C4:  x[a,k,j] + x[b,k,j]   ≤ 1    same week
C5:  x[a,k,j] + x[b,k,j+1] ≤ 1    across week boundary
C6:  x[a,k,j] + x[b,k,1] + y[k,j] ≤ 2    cyclic
```

---

## TASK 6 — Implement in Python

### 6.1 — Read model/ILP.py from top to bottom
Do not change anything yet. Just read. For each block ask:
- Which constraint from Task 5 does this implement?
- Can I find the matching formula?

### 6.2 — Match code to math
Fill in this table yourself:

| Code block | Constraint |
|-----------|-----------|
| `m.addConstr(sum(x[i,k,j]...) == 1)` | C1 |
| `m.addConstr(sum(x[i,k,j] for i if day...) <= 1)` | ? |
| `m.addConstr(w[k] >= j * x[i,k,j])` | ? |
| `m.addConstr(x[a,k,j] + x[b,k,j] <= 1)` | ? |
| `m.addConstr(x[a,k,j] + x[b,k,j+1] <= 1)` | ? |
| `m.addConstr(x[a,k,j] + x[b,k,1] + y[k,j] <= 2)` | ? |

### 6.3 — Run the model
```bash
cd ~/projects/snake-building/claude-modeling
python3 model/ILP.py
```

### 6.4 — Try changing N_SNAKES
In model/ILP.py change `N_SNAKES = 2` to `N_SNAKES = 3`.
Run again. Does the total workers change? Why or why not?

---

## TASK 7 — Read and understand the output

### 7.1 — Read the solver log
```
Instances        : 40     ← how many slots to assign
Incompat (intra) : 75     ← pairs generating C4 constraints
Incompat (cross) : 20     ← pairs generating C5 and C6 constraints

Found heuristic solution: 28    ← first valid solution found (not optimal)
Root relaxation: 3.5            ← mathematical lower bound (cannot be less)

Incumbent   BestBd   Gap
28.0        3.5      87.5%      ← current best vs lower bound
 9.0        9.0       0.0%      ← proven optimal

Total workers needed: 9
```

### 7.2 — Understand Incumbent and BestBd
- Incumbent = best solution found so far
- BestBd = proven lower bound (mathematically impossible to do better)
- Gap = (Incumbent - BestBd) / Incumbent
- Gap = 0% means proven optimal

### 7.3 — Read the snake output
For each snake week listed:
- Write down which shifts appear
- Check: is there at most one shift per day?
- Check: are all shifts for that day compatible with the next day's shifts?

### 7.4 — Count workers manually
```
Snake 1 length = 5  →  5 workers
Snake 2 length = 4  →  4 workers
Total = 9
```
Does this match the objective value?

---

## TASK 8 — Verify your solution is correct

### 8.1 — Check C1 (coverage)
Pick 5 random instances from the list.
Find each one in the output. Is each assigned exactly once?

### 8.2 — Check C2 (one per day per week)
Pick one snake week from the output.
List all shifts and their days. Are any two on the same day?

### 8.3 — Check C4 (rest within week)
Pick one snake week. Take two shifts on consecutive days.
Calculate the gap. Is it ≥ 660?

### 8.4 — Check C6 (cyclic)
Take the last week of each snake.
Take the first week of the same snake.
Find the Sunday shift in the last week and the Monday shift in week 1.
Calculate the gap. Is it ≥ 660?

---

## TASK 9 — Experiment

### 9.1 — Change the number of snakes
Try N_SNAKES = 1, 2, 3, 4. What is the minimum workers for each?

### 9.2 — Change the dataset
Add a new shift type. How does the number of workers change?

### 9.3 — Make it infeasible on purpose
Set W_max = 1. What happens? Why?

### 9.4 — Think about secondary objectives
The current model only minimises workers.
What else could you optimise? Look at the list in explanations.md.
Which would you implement first for the presentation?
