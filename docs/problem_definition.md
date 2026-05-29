# Snake Building – Formal Problem Definition

## Context

A fire station must staff all shifts 24/7. Rather than fixing workers to permanent
shifts, a **snake (cycle)** defines a rotating weekly schedule. Workers cycle through
the snake so that every worker eventually covers every shift type, ensuring a fair
distribution of attractive and unattractive shifts.

---

## Sets

| Symbol | Description |
|--------|-------------|
| S | Set of shift *types* (e.g. DAY, NIGHT) |
| I | Set of shift **instances** — each type s expanded into q[s] identical copies, one per required worker |
| D = {1,…,7} | Days of the week (1 = Monday, 7 = Sunday) |
| C | Set of shift classes (e.g. 1 = day, 2 = night) |
| K = {1,…,n} | Set of snakes |
| J = {1,…,W_max} | Possible week positions within a snake |

---

## Parameters

| Symbol | Type | Description |
|--------|------|-------------|
| day[i] | ∈ D | Day of week on which instance i occurs |
| start[i] | ∈ ℤ≥0 | Start time in minutes from midnight (e.g. 360 = 06:00) |
| end[i] | ∈ ℤ≥0 | End time in minutes from midnight; overnight shifts have end[i] > 1440 (e.g. 06:00 next day = 1800) |
| dur[i] | ∈ ℤ>0 | Duration = end[i] − start[i] (minutes) |
| class[i] | ∈ C | Shift class of instance i |
| q[s] | ∈ ℤ>0 | Workers required for shift type s — determines how many instances are created |
| R | ∈ ℤ>0 | **Minimum rest time** between consecutive shifts (minutes). German labour law: 660 min = 11 h |
| n | ∈ ℤ>0 | Number of snakes (user-specified, or a decision variable itself) |
| W_max | ∈ ℤ>0 | Upper bound on any single snake length |

### Derived parameter: consecutive-day compatibility

Two instances i and i' are **compatible in sequence** (i → i') if the rest gap
between the end of i and the start of i' — where i' occurs on the day immediately
after i — is at least R.

```
gap(i, i') = Δday × 1440  +  start[i']  −  end[i]

where  Δday = day[i'] − day[i]  (add 7 if ≤ 0, to handle Sunday → Monday wrap)

can_follow(i, i') = 1   iff   gap(i, i') ≥ R
```

**Example (our synthetic dataset, R = 660):**

| Transition | gap (min) | Compatible? |
|-----------|-----------|-------------|
| DAY (ends 18:00) → DAY next day (starts 06:00) | 720 | Yes |
| NIGHT (ends 06:00+1d) → NIGHT next day (starts 18:00) | 720 | Yes |
| NIGHT (ends 06:00+1d) → DAY next day (starts 06:00) | 0 | **No** |
| DAY (ends 18:00) → NIGHT next day (starts 18:00) | 1440 | Yes |

---

## Decision Variables

| Symbol | Domain | Description |
|--------|--------|-------------|
| x[i, k, j] | {0, 1} | **1** if instance i is assigned to snake k in week j |
| w[k] | ℤ≥0 | Length (number of weeks) of snake k |
| y[k, j] | {0, 1} | Auxiliary: **1** iff snake k has exactly length j (used to linearise C6) |

---

## Objective Function

Minimise the total number of workers = sum of all snake lengths:

```
Min   Σ_{k ∈ K}  w[k]
```

---

## Constraints

### C1 – Full coverage: every instance assigned exactly once
```
Σ_{k ∈ K}  Σ_{j ∈ J}  x[i, k, j]  =  1      ∀ i ∈ I
```

### C2 – At most one instance per (snake, week, day)
A worker works at most one shift per day.
```
Σ_{i ∈ I : day[i] = d}  x[i, k, j]  ≤  1      ∀ k ∈ K, j ∈ J, d ∈ D
```

### C3 – Snake length covers all assigned week positions
```
w[k]  ≥  j · x[i, k, j]      ∀ i ∈ I, k ∈ K, j ∈ J
```

### C4 – Rest time within a week (consecutive days d → d+1, d < 7)
If instances i and i' are incompatible (can_follow = 0) and i' is on the day after i
(within the same week), they cannot both appear in the same snake week.
```
x[i, k, j]  +  x[i', k, j]  ≤  1

    ∀ k ∈ K, j ∈ J,
    ∀ (i, i') : day[i'] = day[i]+1  and  can_follow(i, i') = 0
```

### C5 – Rest time across weeks (Sunday of week j → Monday of week j+1)
```
x[i, k, j]  +  x[i', k, j+1]  ≤  1

    ∀ k ∈ K, j ∈ {1,…,W_max−1},
    ∀ (i, i') : day[i] = 7, day[i'] = 1, can_follow(i, i') = 0
```

### C6 – Cyclic rest (last week → week 1)
The snake is cyclic: after week w[k] comes week 1 again. Since w[k] is a variable,
we use the auxiliary y[k, j] to identify the last week.

**Auxiliary links:**
```
Σ_{j ∈ J}  y[k, j]  =  1                       ∀ k  (exactly one last week)
w[k]  =  Σ_{j ∈ J}  j · y[k, j]               ∀ k  (links y to w)
```

**Cyclic rest enforcement:** for each incompatible pair (i, i') with day[i]=7, day[i']=1:
```
x[i, k, j]  +  x[i', k, 1]  +  y[k, j]  ≤  2

    ∀ k ∈ K, j ∈ J
```
(All three can equal 1 only if week j is the last week, instance i is there, AND i' is
in week 1 — which would be a rest violation. The constraint forbids this combination.)

---

## Lower bound on objective

Every snake week holds at most 7 instances (one per day).  
Therefore: `Σ w[k] ≥ ceil(|I| / 7)`

For our synthetic dataset: |I| = 28, lower bound = 4 workers.

---

## Secondary objectives (from specification, not yet implemented)

- **MaxW**: limit total work hours per snake week
- **Work-time deviation**: minimise max|W(a_i) − W(a_j)| across weeks
- **Shift jumps**: minimise transitions between different shift types
- **Class distribution**: spread attractive/unattractive shifts equally across snakes
