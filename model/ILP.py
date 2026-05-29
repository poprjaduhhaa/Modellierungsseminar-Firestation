"""
ILP model for the Snake Building problem.

Full mathematical formulation: docs/problem_definition.md

Implemented constraints
-----------------------
C1  each instance assigned to exactly one (snake, week)
C2  at most one instance per (snake, week, day)
C3  snake length w[k] >= every used week index
C4  rest within week: incompatible consecutive-day pairs cannot share a snake week
C5  rest across weeks: Sunday of week j -> Monday of week j+1
C6  cyclic rest: Sunday of last week -> Monday of week 1  (linearised via y[k,j])

Usage
-----
    python model/ILP.py
"""

import sys
import gurobipy as gp
from gurobipy import GRB

sys.path.insert(0, ".")
from data.shifts import SHIFT_TYPES, build_instances, build_compatibility, MIN_REST


# ── Parameters ─────────────────────────────────────────────────────────────────
# These are fixed inputs, not decision variables.

N_SNAKES: int = 2   # n   — number of snakes (try 1, 2, 3 to compare objectives)
W_MAX:    int = 14  # upper bound on any single snake length


# ── Build data structures ──────────────────────────────────────────────────────

instances  = build_instances(SHIFT_TYPES)
compat     = build_compatibility(instances)       # {(a_id, b_id): bool}
inst_map   = {inst.id: inst for inst in instances}

I = [inst.id for inst in instances]   # set of instance ids
K = list(range(N_SNAKES))             # snake indices  {0, ..., n-1}
J = list(range(1, W_MAX + 1))         # week positions {1, ..., W_max}
D = list(range(1, 8))                 # days of week   {1, ..., 7}

# Split incompatible pairs into two groups used by different constraints.
all_incompat = [(a, b) for (a, b), ok in compat.items() if not ok]

# C4: pairs within a week  (day[a] < 7, so a and b are in the same 7-day block)
incompat_intraweek = [
    (a, b) for (a, b) in all_incompat
    if not (inst_map[a].day == 7 and inst_map[b].day == 1)
]

# C5 + C6: Sunday -> Monday pairs (span a week boundary)
incompat_cross = [
    (a, b) for (a, b) in all_incompat
    if inst_map[a].day == 7 and inst_map[b].day == 1
]

print(f"Instances        : {len(I)}")
print(f"Incompat (intra) : {len(incompat_intraweek)}")
print(f"Incompat (cross) : {len(incompat_cross)}")


# ── Model ──────────────────────────────────────────────────────────────────────

m = gp.Model("SnakeBuilding")


# ── Decision variables ─────────────────────────────────────────────────────────

# x[i, k, j] in {0,1}
#   = 1  iff  instance i is placed in snake k at week position j
x = m.addVars(I, K, J, vtype=GRB.BINARY, name="x")

# w[k] in Z>=0
#   length (number of weeks) of snake k  ->  equals number of workers on snake k
w = m.addVars(K, vtype=GRB.INTEGER, lb=0, ub=W_MAX, name="w")

# y[k, j] in {0,1}   (auxiliary, used only for C6)
#   = 1  iff  snake k has exactly length j  (i.e. w[k] = j)
y = m.addVars(K, J, vtype=GRB.BINARY, name="y")


# ── Objective ──────────────────────────────────────────────────────────────────
# Minimise total workers = sum of snake lengths.

m.setObjective(gp.quicksum(w[k] for k in K), GRB.MINIMIZE)


# ── Constraints ────────────────────────────────────────────────────────────────

# C1 — each instance appears exactly once across all (snake, week) pairs
for i in I:
    m.addConstr(
        gp.quicksum(x[i, k, j] for k in K for j in J) == 1,
        name=f"C1_{i}"
    )

# C2 — at most one instance per (snake, week, day)
for k in K:
    for j in J:
        for d in D:
            ids_on_day = [i for i in I if inst_map[i].day == d]
            m.addConstr(
                gp.quicksum(x[i, k, j] for i in ids_on_day) <= 1,
                name=f"C2_{k}_{j}_{d}"
            )

# C3 — snake length must cover every week position that has an assigned instance
for i in I:
    for k in K:
        for j in J:
            m.addConstr(w[k] >= j * x[i, k, j], name=f"C3_{i}_{k}_{j}")

# C4 — rest within week: incompatible pairs cannot share the same snake week
for (a, b) in incompat_intraweek:
    for k in K:
        for j in J:
            m.addConstr(
                x[a, k, j] + x[b, k, j] <= 1,
                name=f"C4_{a}_{b}_{k}_{j}"
            )

# C5 — rest across week boundary: Sunday of week j cannot be followed by
#       incompatible Monday of week j+1
for (a, b) in incompat_cross:
    for k in K:
        for j in J[:-1]:                          # j+1 must stay within J
            m.addConstr(
                x[a, k, j] + x[b, k, j + 1] <= 1,
                name=f"C5_{a}_{b}_{k}_{j}"
            )

# C6 — cyclic rest: last week of snake -> week 1  (linearised via y[k,j])
#
# Link y to w:
#   Exactly one j is the "last week" of each snake.
#   w[k] = sum_j  j * y[k,j]
for k in K:
    m.addConstr(gp.quicksum(y[k, j] for j in J) == 1, name=f"C6_ysum_{k}")
    m.addConstr(
        w[k] == gp.quicksum(j * y[k, j] for j in J),
        name=f"C6_wlink_{k}"
    )

# Enforce rest: if y[k,j]=1 (week j is last) AND x[a,k,j]=1 AND x[b,k,1]=1
# then all three equal 1 -> sum = 3 > 2 -> infeasible.
# Constraint:  x[a,k,j] + x[b,k,1] + y[k,j] <= 2
for (a, b) in incompat_cross:
    for k in K:
        for j in J:
            m.addConstr(
                x[a, k, j] + x[b, k, 1] + y[k, j] <= 2,
                name=f"C6_{a}_{b}_{k}_{j}"
            )


# ── Solve ──────────────────────────────────────────────────────────────────────

m.Params.TimeLimit = 120   # seconds
m.optimize()


# ── Output ─────────────────────────────────────────────────────────────────────

if m.status in (GRB.OPTIMAL, GRB.TIME_LIMIT) and m.SolCount > 0:
    total = int(round(m.ObjVal))
    print(f"\n=== Total workers needed: {total} ===")
    for k in K:
        snake_len = int(round(w[k].X))
        print(f"\nSnake {k + 1}  (length = {snake_len})")
        for j in J:
            week_insts = sorted(
                [inst_map[i] for i in I if x[i, k, j].X > 0.5],
                key=lambda s: s.day
            )
            if week_insts:
                line = ", ".join(
                    f"{s.shift_type.name}(day={s.day},copy={s.copy})"
                    for s in week_insts
                )
                print(f"  Week {j:2d}: {line}")
else:
    print("No feasible solution found within time limit.")
