# How to Build the Snake Building Model From Scratch

A self-contained guide. No prior knowledge needed beyond basic Python.

---

## Step 1 — Understand what you are building

You have a fire station. Every week the same shifts need to be covered.
Instead of writing a new schedule every week, you create a **rotating template (snake)**.
Workers rotate through the template — the template never changes.

**Your goal:** find the templates that need the fewest workers total.

```
More workers in a snake  =  longer snake  =  more expensive
Fewer workers            =  shorter snake =  cheaper

Objective: minimise  sum of all snake lengths
```

---

## Step 2 — Define your shifts on paper first

Before writing any code, write down:

| What | Example |
|------|---------|
| What shifts exist? | Early, Late, Night, Whole-day |
| Which days does each occur? | Early = Mon-Fri, Night = every day |
| What time does each start and end? | Early = 06:00-14:00 |
| How many workers per shift? | Early = 2 people |
| What class is each shift? | Early = class 1 (attractive), Night = class 2 |

**Rule for time:** store everything in minutes from midnight.
```
06:00  =  360 min
14:00  =  840 min
22:00  = 1320 min
06:00 next day = 360 + 1440 = 1800 min   (overnight: add 1440)
```

---

## Step 3 — Expand shifts into instances

Each shift with `workers = 2` needs 2 separate slots (copy=0 and copy=1).
These individual slots are called **instances**.

```
EARLY_ on Monday, workers=2  →  instance (EARLY_, Mon, copy=0)
                                instance (EARLY_, Mon, copy=1)
```

Write down all instances. Count them. This is your set **I**.

```
|I| = sum of (days × workers) for each shift type
```

---

## Step 4 — Find incompatible pairs

Two instances are **incompatible** if putting them on consecutive days
in the same snake would violate the 11-hour rest rule.

For each pair (a, b) where b is on the day after a:
```
gap = 1440 + start[b] - end[a]

if gap < 660 (= 11 hours)  →  incompatible  →  write them down
```

These pairs will become your constraints C4, C5, C6.

---

## Step 5 — Write the mathematical model

### Sets
```
I  =  all instances
K  =  {0, 1, ..., n-1}  where n = number of snakes you want
J  =  {1, 2, ..., W_max}  week positions inside a snake
D  =  {1, 2, 3, 4, 5, 6, 7}  days of the week
```

### Parameters
```
day[i]    =  day of week for instance i
start[i]  =  start time in minutes
end[i]    =  end time in minutes
R         =  660  (minimum rest, 11 hours)
n         =  number of snakes  (you choose this)
W_max     =  maximum snake length  (you choose this, e.g. 14)
```

### Decision variables
```
x[i, k, j]  ∈ {0, 1}   →  is instance i in snake k at week j?
w[k]         ∈ Z≥0      →  how long is snake k?
y[k, j]      ∈ {0, 1}   →  is week j the last week of snake k?  (auxiliary)
```

### Objective
```
Minimise   w[0] + w[1] + ... + w[n-1]
```

### Constraints
```
C1  every instance assigned exactly once:
    sum over all k,j of x[i,k,j]  =  1      for each i

C2  at most one instance per (snake, week, day):
    sum of x[i,k,j] for all i with day[i]=d  ≤  1    for each k,j,d

C3  snake length covers all used weeks:
    w[k]  ≥  j × x[i,k,j]    for each i,k,j

C4  rest within a week (day d → day d+1):
    x[a,k,j] + x[b,k,j]  ≤  1    for each incompatible pair (a,b), each k,j

C5  rest across week boundary (Sunday j → Monday j+1):
    x[a,k,j] + x[b,k,j+1]  ≤  1    for each incompatible (a,b) where day[a]=7, day[b]=1

C6  cyclic rest (last week → week 1):
    x[a,k,j] + x[b,k,1] + y[k,j]  ≤  2    for each incompatible (a,b), each k,j
    sum of y[k,j] over j  =  1              for each k
    w[k]  =  sum of j×y[k,j] over j         for each k
```

---

## Step 6 — Translate to Python + Gurobi

```python
import gurobipy as gp
from gurobipy import GRB

m = gp.Model()

# Variables
x = m.addVars(I, K, J, vtype=GRB.BINARY)
w = m.addVars(K, vtype=GRB.INTEGER, lb=0, ub=W_max)
y = m.addVars(K, J, vtype=GRB.BINARY)

# Objective
m.setObjective(sum(w[k] for k in K), GRB.MINIMIZE)

# C1
for i in I:
    m.addConstr(sum(x[i,k,j] for k in K for j in J) == 1)

# C2
for k in K:
    for j in J:
        for d in D:
            m.addConstr(sum(x[i,k,j] for i in I if day[i]==d) <= 1)

# C3
for i in I:
    for k in K:
        for j in J:
            m.addConstr(w[k] >= j * x[i,k,j])

# C4
for (a,b) in incompat_intraweek:
    for k in K:
        for j in J:
            m.addConstr(x[a,k,j] + x[b,k,j] <= 1)

# C5
for (a,b) in incompat_cross:
    for k in K:
        for j in J[:-1]:
            m.addConstr(x[a,k,j] + x[b,k,j+1] <= 1)

# C6
for k in K:
    m.addConstr(sum(y[k,j] for j in J) == 1)
    m.addConstr(w[k] == sum(j * y[k,j] for j in J))
for (a,b) in incompat_cross:
    for k in K:
        for j in J:
            m.addConstr(x[a,k,j] + x[b,k,1] + y[k,j] <= 2)

m.optimize()
```

---

## Step 7 — Read the output

After solving, look for:

```
Optimal solution found   gap 0.0000%     ← proven optimal
Total workers needed: X                  ← your answer

Snake 1  length = Y                      ← Y workers on this snake
  Week 1: SHIFT(day=1), SHIFT(day=3)    ← what worker does in week 1
  Week 2: ...
```

**Gap = 0%** means no better solution exists mathematically.
**Gap > 0%** means solver ran out of time — solution is good but maybe not optimal.

---

## Step 8 — Check your result makes sense

Ask yourself:
- Does every shift appear exactly once across all snake weeks?
- Does every snake week have at most one shift per day?
- Are there at least 11 hours between any two consecutive shifts in the same snake?
- Does the last week connect back to week 1 without rest violations?

If yes → your solution is valid.

---

## Common mistakes

| Mistake | What happens | Fix |
|---------|-------------|-----|
| Wrong end time for overnight shifts | gap calculation wrong | end = start + duration, can exceed 1440 |
| n too small | no feasible solution | increase N_SNAKES |
| W_max too small | no feasible solution | increase W_max |
| Running from wrong folder | ModuleNotFoundError | cd into claude-modeling/ first |

---

## File to study

Read these in this order:

```
1. examples/README.md          ← why toy model exists
2. examples/toy_model.py       ← simple version, read every line
3. visual_guide.md             ← diagrams and tables
4. explanations.md             ← full formal math
5. model/ILP.py                ← real implementation
```
