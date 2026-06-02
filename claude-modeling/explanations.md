# Snake Building – Model Explanation

This document explains the full mathematical model step by step,
with small examples at each stage so you can see exactly what each symbol means.

---

## 1. The Idea in One Sentence

We have a list of shifts that a fire station needs to cover every week.
We want to group those shifts into **rotating schedules (snakes)**
so that the **total number of workers is as small as possible**.

---

## 2. From Shifts to Instances

A shift type says *what* the shift is and *how many workers* it needs.
A shift **instance** is one individual worker-slot.

**Example:** NIGHT_ occurs every day, requires 2 workers.
That creates 14 instances (7 days × 2 workers).

| Instance ID | Shift type | Day | Worker copy |
|-------------|-----------|-----|-------------|
| 0  | NIGHT_ | Mon (1) | copy 0 |
| 1  | NIGHT_ | Mon (1) | copy 1 |
| 2  | NIGHT_ | Tue (2) | copy 0 |
| 3  | NIGHT_ | Tue (2) | copy 1 |
| ... | ... | ... | ... |
| 13 | NIGHT_ | Sun (7) | copy 1 |

The ILP works with instances, not shift types.
Every instance must end up in exactly one snake week.

---

## 3. Sets

Sets define *who* and *what* is in the model. They are not numbers — they are collections.

| Symbol | Name | Description | Example |
|--------|------|-------------|---------|
| **I** | Instances | All individual worker-slots | {0, 1, 2, ..., 39} |
| **K** | Snakes | Index of each snake | {0, 1} if n=2 |
| **J** | Week positions | Possible positions inside a snake | {1, 2, ..., 14} |
| **D** | Days | Days of the week | {1=Mon, ..., 7=Sun} |

---

## 4. Parameters

Parameters are **fixed input data** — the model reads them but never changes them.

| Symbol | Type | Description | Example value |
|--------|------|-------------|---------------|
| day[i] | integer ∈ D | Day of week for instance i | day[3] = 2 (Tuesday) |
| start[i] | integer (min) | Start time from midnight | start[0] = 1320 (22:00) |
| end[i] | integer (min) | End time from midnight | end[0] = 2040 (06:00+1d) |
| R | integer (min) | Minimum rest between shifts | 660 (= 11 hours) |
| n | integer | Number of snakes | 2 |
| W_max | integer | Max allowed snake length | 14 |

**Time in minutes from midnight:**
```
06:00  =   360 min
14:00  =   840 min
22:00  = 1320 min
06:00 next day = 2040 min   (overnight: 22*60 + 8*60)
```

**Rest gap formula** between instance a (ends on day d) and instance b (starts on day d+1):
```
gap(a, b) = 1 × 1440  +  start[b]  −  end[a]
```

| Transition | gap (min) | ≥ 660? | Compatible? |
|-----------|-----------|--------|-------------|
| EARLY_(ends 14:00=840) → LATE__(starts 14:00=840 next day) | 1440+840−840 = 1440 | Yes | ✓ |
| LATE__(ends 22:00=1320) → NIGHT_(starts 22:00=1320 next day) | 1440+1320−1320 = 1440 | Yes | ✓ |
| NIGHT_(ends 06:00=2040) → EARLY_(starts 06:00=360 next day) | 1440+360−2040 = −240 | No | ✗ |
| NIGHT_(ends 06:00=2040) → LATE__(starts 14:00=840 next day) | 1440+840−2040 = 240 | No | ✗ |
| LATE__(ends 22:00=1320) → EARLY_(starts 06:00=360 next day) | 1440+360−1320 = 480 | No | ✗ |

---

## 5. Decision Variables

Decision variables are what the model **chooses**. The solver sets their values.

### x[i, k, j]  ∈  {0, 1}
> "Is instance i placed in snake k at week position j?"

| x[i, k, j] | Meaning |
|-------------|---------|
| 1 | instance i is assigned to snake k, week j |
| 0 | it is not |

**Example** (snake k=0, week j=1):

| Instance | day | x[inst, 0, 1] | Meaning |
|----------|-----|---------------|---------|
| NIGHT_ Mon copy0 | 1 | 1 | assigned here |
| NIGHT_ Mon copy1 | 1 | 0 | assigned elsewhere |
| EARLY_ Mon copy0 | 1 | 0 | assigned elsewhere |

---

### w[k]  ∈  {0, 1, 2, ..., W_max}
> "How many weeks (= workers) does snake k have?"

| k | w[k] | Meaning |
|---|------|---------|
| 0 | 3 | snake 0 has 3 weeks → needs 3 workers |
| 1 | 2 | snake 1 has 2 weeks → needs 2 workers |

---

### y[k, j]  ∈  {0, 1}  (auxiliary)
> "Is week j the **last** week of snake k?"

Used only to enforce the cyclic rest constraint (C6).

| y[k, j] | Meaning |
|---------|---------|
| 1 | snake k ends at week j |
| 0 | it does not |

Exactly one j per snake has y[k, j] = 1.

---

## 6. Objective Function

```
Minimise   Σ_{k ∈ K}  w[k]
```

Sum of all snake lengths = total number of workers needed.

**Example:**
| Snake | Length w[k] | Workers |
|-------|-------------|---------|
| k=0 | 3 | 3 |
| k=1 | 2 | 2 |
| **Total** | **5** | **5** |

We want this total to be as small as possible.

---

## 7. Constraints

### C1 – Every instance is assigned exactly once

```
Σ_{k ∈ K}  Σ_{j ∈ J}  x[i, k, j]  =  1       for all i ∈ I
```

No shift slot can be left uncovered, and no slot can be assigned twice.

| Situation | Allowed? |
|-----------|---------|
| Instance 5 assigned to snake 0 week 2 only | ✓ |
| Instance 5 not assigned anywhere | ✗ |
| Instance 5 assigned to two different snakes | ✗ |

---

### C2 – At most one instance per (snake, week, day)

```
Σ_{i : day[i] = d}  x[i, k, j]  ≤  1       for all k, j, d
```

One worker cannot work two shifts on the same day.

| Snake k=0, Week j=1, Monday | Allowed? |
|-----------------------------|---------|
| EARLY_ Mon assigned here | ✓ |
| EARLY_ Mon + NIGHT_ Mon both assigned here | ✗ |

---

### C3 – Snake length covers all assigned weeks

```
w[k]  ≥  j · x[i, k, j]       for all i, k, j
```

If any instance is placed at week position j, the snake must be at least j weeks long.

| x[inst, k, j=5] | w[k] ≥ ? |
|-----------------|----------|
| 1 | w[k] ≥ 5 |
| 0 | no constraint from this |

---

### C4 – Rest within a week (day d → day d+1, inside one snake week)

```
x[a, k, j]  +  x[b, k, j]  ≤  1

    for all k, j,
    for all incompatible pairs (a, b) where day[b] = day[a] + 1
```

If NIGHT_(Mon) and EARLY_(Tue) are both in the same snake week,
a worker would go from night shift ending 06:00 Tue to early shift starting 06:00 Tue — 0 min rest. Forbidden.

| Snake k=0, Week j=2 | Allowed? |
|--------------------|---------|
| NIGHT_ Mon + EARLY_ Tue | ✗ (gap = 0 min < 660) |
| NIGHT_ Mon + LATE__ Tue | ✗ (gap = 240 min < 660) |
| NIGHT_ Mon + NIGHT_ Tue | ✓ (gap = 720 min ≥ 660) |
| EARLY_ Mon + LATE__ Tue | ✓ (gap = 1440 min ≥ 660) |

---

### C5 – Rest across week boundary (Sunday of week j → Monday of week j+1)

```
x[a, k, j]  +  x[b, k, j+1]  ≤  1

    for all k, j < W_max,
    for all incompatible pairs (a, b) where day[a]=7, day[b]=1
```

Same logic as C4 but the two days are in **different snake weeks**.

| x[NIGHT_ Sun, k, j=2] | x[EARLY_ Mon, k, j=3] | Allowed? |
|-----------------------|-----------------------|---------|
| 1 | 1 | ✗ (gap = 0 min) |
| 1 | 0 | ✓ |
| 0 | 1 | ✓ |

---

### C6 – Cyclic rest (last week → week 1)

The snake is a **cycle**: after the last week, it wraps back to week 1.
The same rest rule must hold across this boundary.

```
x[a, k, j]  +  x[b, k, 1]  +  y[k, j]  ≤  2

    for all k, j,
    for all incompatible pairs (a, b) where day[a]=7, day[b]=1
```

If all three equal 1 → sum = 3 > 2 → infeasible (forbidden by solver).

| y[k,j]=1 (week j is last) | x[NIGHT_ Sun, k, j]=1 | x[EARLY_ Mon, k, 1]=1 | Sum | Allowed? |
|--------------------------|----------------------|-----------------------|-----|---------|
| Yes | Yes | Yes | 3 | ✗ |
| Yes | Yes | No  | 2 | ✓ |
| No  | Yes | Yes | 2 | ✓ (j is not the last week) |

---

## 8. Complete model summary

```
Sets:       I, K, J, D
Parameters: day[i], start[i], end[i], R, n, W_max

Variables:
  x[i,k,j] ∈ {0,1}    — assign instance i to snake k week j
  w[k]      ∈ Z≥0      — length of snake k
  y[k,j]    ∈ {0,1}    — 1 iff snake k ends at week j  (auxiliary)

Minimise:   Σ_k  w[k]

Subject to:
  C1   Σ_{k,j} x[i,k,j] = 1                          ∀ i
  C2   Σ_{i: day[i]=d} x[i,k,j] ≤ 1                  ∀ k,j,d
  C3   w[k] ≥ j · x[i,k,j]                            ∀ i,k,j
  C4   x[a,k,j] + x[b,k,j]   ≤ 1                     ∀ k,j, incompat. (a,b) same week
  C5   x[a,k,j] + x[b,k,j+1] ≤ 1                     ∀ k,j, incompat. (a,b) cross week
  C6   x[a,k,j] + x[b,k,1] + y[k,j] ≤ 2              ∀ k,j, incompat. (a,b) cyclic
       Σ_j y[k,j] = 1                                  ∀ k
       w[k] = Σ_j j·y[k,j]                             ∀ k
```
