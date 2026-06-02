# examples/

This folder contains the toy model — a simplified version of the real ILP.

---

## Why does the toy model exist?

```
REAL PROBLEM                        TOY MODEL
─────────────────────────────────   ─────────────────────────────────
40 instances                        4 instances
hundreds of (snake, week) slots     4 × 4 = 16 slots
billions of combinations            4^4 = 256 combinations
needs Gurobi to solve               pure Python, no solver needed
hard to read and debug              easy to read line by line
```

The toy model exists so you can **understand the logic** before looking
at the real ILP. Same rules, same constraints — just tiny enough to follow.

---

## How they relate

```
toy_model.py                        model/ILP.py
────────────────────────────────    ────────────────────────────────
tries ALL combinations              finds optimal solution smartly
checks constraints manually         encodes constraints as math
prints the best it found            uses Gurobi solver
                │                               │
                └───── same idea, same rules ───┘
                   just different scale and method
```

---

## What the toy model does step by step

```
1. Define 4 shifts
        Morning_Mon  08:00-16:00
        Morning_Tue  08:00-16:00
        Evening_Mon  20:00-04:00+1d
        Evening_Tue  20:00-04:00+1d

2. Try every possible assignment (256 combinations)
        for each combination:
            build snakes from it
            check C2, C4, C5, C6
            if feasible → compare total length to best so far

3. Print the best feasible solution found
        Snake 1 → length 1 → 1 worker
        Snake 2 → length 1 → 1 worker
        Total: 2 workers
```

---

## Why 2 workers is optimal here

```
4 shifts to cover
2 days per week (Mon, Tue)
→ max 2 shifts per snake week (one per day)
→ minimum weeks needed = ceil(4 / 2) = 2
→ minimum workers = 2

Snake 1:  Week 1 = [Morning_Mon, Morning_Tue]   (1 worker does mornings)
Snake 2:  Week 1 = [Evening_Mon, Evening_Tue]   (1 worker does evenings)
```

---

## Documents for the full model

The files below explain the **real ILP** (model/ILP.py), not the toy model:

| File | What it covers |
|------|---------------|
| `visual_guide.md` | visual diagrams of snakes, rotation, constraints, tables |
| `explanations.md` | full formal definition with sets, parameters, variables, constraints |
| `problem_definition.md` | compact mathematical summary |
