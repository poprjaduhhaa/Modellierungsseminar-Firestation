# Snake Building – Visual Guide

---

## 0. Master Legend (all symbols used in this file)

| Symbol | What it is | Example |
|--------|-----------|---------|
| **i** | index of one shift instance (one worker-slot) | i = 5 means "the 5th slot" |
| **k** | index of a snake | k = 0 is the first snake |
| **j** | week position inside a snake | j = 3 means "the 3rd week of the snake" |
| **w** | snake length = number of weeks = number of workers on that snake | w = 3 → 3 workers |
| **n** | total number of snakes | n = 2 |
| **d** | day of the week (1=Mon … 7=Sun) | d = 1 is Monday |
| **R** | minimum rest time between shifts in minutes | R = 660 (= 11 hours) |
| **W_max** | maximum allowed snake length | W_max = 14 |
| **x[i,k,j]** | decision variable: is instance i in snake k at week j? | x[5,0,3] = 1 means yes |
| **y[k,j]** | auxiliary variable: is week j the last week of snake k? | y[0,3] = 1 means snake 0 ends at week 3 |
| **C1–C6** | constraint numbers (rules the model must follow) | C4 = rest rule inside a week |

---

## 1. What is a Snake?

A snake is a fixed weekly template that workers rotate through cyclically.

```
        THE SNAKE  (length w = 3)
        ┌────────────┬────────────┬────────────┐
        │   Week 1   │   Week 2   │   Week 3   │
        │  Mon EARLY │  Mon NIGHT │  Mon LATE  │
        │  Tue EARLY │  Tue NIGHT │  Tue LATE  │
        │  Wed EARLY │  Wed NIGHT │  Wed LATE  │
        │  Thu EARLY │  Thu NIGHT │  Thu LATE  │
        │  Fri EARLY │  Fri NIGHT │  Fri LATE  │
        │  Sat OFF   │  Sat NIGHT │  Sat OFF   │
        │  Sun OFF   │  Sun NIGHT │  Sun OFF   │
        └────────────┴────────────┴────────────┘
              ↑                          │
              └──────── cycles back ─────┘
```

> **Legend:**
> `w = 3` — this snake has 3 weeks, so it needs **3 workers**
> `Week 1, 2, 3` — these are the **j** positions (j=1, j=2, j=3)
> `EARLY / NIGHT / LATE / OFF` — shift types assigned to each day

---

## 2. Worker Rotation

The snake never changes. Workers rotate through it every calendar week.

```
Calendar     Worker A      Worker B      Worker C
─────────────────────────────────────────────────────────────
week  t  →  [ Week j=1 ]  [ Week j=2 ]  [ Week j=3 ]
week t+1 →  [ Week j=2 ]  [ Week j=3 ]  [ Week j=1 ]
week t+2 →  [ Week j=3 ]  [ Week j=1 ]  [ Week j=2 ]
week t+3 →  [ Week j=1 ]  [ Week j=2 ]  [ Week j=3 ]  ← same as t
```

> **Legend:**
> `t` — any calendar week (e.g. week 23 of the year)
> `j` — position inside the snake (not a calendar week, a fixed slot)
> After `w` calendar weeks the cycle repeats. Here w=3, so it repeats every 3 weeks.

---

## 3. Multiple Snakes

All shifts must be split across snakes. Each snake is independent.

```
ALL SHIFTS
    │
    ├──────────────► SNAKE k=0  (day shifts only)
    │                  Week j=1: EARLY Mon–Fri
    │                  Week j=2: EARLY Mon–Fri
    │                  w[0] = 2  →  2 workers
    │
    └──────────────► SNAKE k=1  (night shifts only)
                       Week j=1: NIGHT Mon–Sun
                       Week j=2: NIGHT Mon–Sun
                       w[1] = 2  →  2 workers

              TOTAL workers = w[0] + w[1] = 2 + 2 = 4
```

> **Legend:**
> `k=0, k=1` — snake indices (first snake, second snake)
> `w[k]` — length of snake k = workers needed on snake k
> Objective: minimise `w[0] + w[1] + ... + w[n-1]`

---

## 4. Time Representation

All times are stored as **minutes from midnight**.

```
Midnight        06:00       14:00       22:00    Midnight    06:00+1day
    │              │           │           │         │            │
    0            360         840        1320       1440         2040
    │              │           │           │         │            │
    ├──────────────┼───────────┼───────────┼─────────┼────────────┤
                   ╠═══════════╣
                      EARLY_
                   start=360, end=840
                               ╠═══════════╣
                                  LATE__
                               start=840, end=1320
                                           ╠════════════════════╣
                                                NIGHT_
                                           start=1320, end=2040
```

> **Legend:**
> `start[i]` — when shift i begins (minutes from midnight)
> `end[i]`   — when shift i ends (minutes from midnight)
> `end > 1440` means the shift ends the **next day** (e.g. 2040 = 06:00 next day)
> `1440` = one full day in minutes (24 × 60)

---

## 5. Rest Gap — Why Some Shifts Cannot Follow Each Other

German law: **R = 660 minutes (11 hours)** minimum rest between shifts.

```
gap(a, b) = 1440 + start[b] − end[a]
            (b is on the day immediately after a)
```

```
NIGHT_ ends at end[a] = 2040  (= 06:00 next day)
    │
    ▼
────┼──────────────────────────────────────────────────
  06:00                                         22:00
  start=360    start=840                      start=1320
  EARLY_       LATE__                          NIGHT_
    │              │                              │
    │←  −240 min →│←    240 min    →│←   720 min →│
    ✗              ✗                              ✓
  (overlap)    (< 660 min)                   (≥ 660 min)
```

**Full compatibility table for our dataset:**

| Shift a (day d) | Shift b (day d+1) | end[a] | start[b] | gap (min) | ≥ R=660? |
|----------------|------------------|--------|----------|-----------|---------|
| NIGHT_  | EARLY_ |  2040 |  360 | −240 | ✗ |
| NIGHT_  | LATE__ |  2040 |  840 |  240 | ✗ |
| LATE__  | EARLY_ |  1320 |  360 |  480 | ✗ |
| EARLY_  | LATE__ |   840 |  840 | 1440 | ✓ |
| EARLY_  | NIGHT_ |   840 | 1320 | 1920 | ✓ |
| LATE__  | NIGHT_ |  1320 | 1320 | 1440 | ✓ |
| NIGHT_  | NIGHT_ |  2040 | 1320 |  720 | ✓ |

> **Legend:**
> `a` — the earlier shift (on day d)
> `b` — the later shift (on day d+1, the next day)
> `end[a]` — when shift a ends
> `start[b]` — when shift b starts
> `gap` — minutes of rest between them
> `R` — minimum required rest (660 min = 11 h)

---

## 6. Where Each Constraint Applies

```
ONE SNAKE  (w = 3 weeks, 7 days each)

   j=1                  j=2                  j=3
┌────────────────────┬────────────────────┬────────────────────┐
│Mon Tue Wed Thu Fri │Mon Tue Wed Thu Fri │Mon Tue Wed Thu Fri │
│Sat Sun             │Sat Sun             │Sat Sun             │
└────────────────────┴────────────────────┴────────────────────┘
  │   │          │    │  │   │         │   │  │   │
  └───┘          └────┘  └───┘         └───┘  └───┘
   C4              C5      C4            C5     C4
(within          (cross  (within       (cross (within
 week j=1)       j=1→2)  week j=2)    j=2→3)  week j=3)

                                                    │
              ┌─────────────────────────────────────┘
              ▼
         Week j=1
          C6 (cyclic: last Sun of j=3 → first Mon of j=1)
```

| Constraint | Location in snake | Rule |
|-----------|-----------------|------|
| **C4** | days d and d+1 within the **same** week j | if gap(a,b) < R → cannot both be in same week j |
| **C5** | Sun of week j → Mon of week **j+1** | if gap(a,b) < R → cannot have a in week j AND b in week j+1 |
| **C6** | Sun of **last** week → Mon of **week 1** | if gap(a,b) < R → cannot have a in last week AND b in week 1 |

> **Legend:**
> `d` — day of week (1=Mon … 7=Sun)
> `j` — week position in the snake
> `a` — the shift on Sunday (day d=7)
> `b` — the shift on Monday (day d=1)
> `gap(a,b)` — rest minutes between end of a and start of b

---

## 7. Decision Variable x[i, k, j]

Think of it as a 3D box. One cell per (instance, snake, week). Each cell = 0 or 1.

```
                    j=1    j=2    j=3    j=4
                  ┌──────┬──────┬──────┬──────┐
           k=0   │  0   │  0   │  1   │  0   │  ← instance i=5 is here (k=0, j=3)
                  ├──────┼──────┼──────┼──────┤
           k=1   │  0   │  0   │  0   │  0   │
                  └──────┴──────┴──────┴──────┘
                  (one row per snake, one column per week position)
```

**C1** says the sum across ALL cells for one instance = exactly 1:

```
For instance i=5:   0+0+1+0  +  0+0+0+0  = 1  ✓
                    (k=0 row)    (k=1 row)
```

> **Legend:**
> `i` — which instance (one worker-slot for one shift on one day)
> `k` — which snake
> `j` — which week position inside the snake
> `x[i,k,j] = 1` — instance i is placed in snake k at week j
> `x[i,k,j] = 0` — it is not

---

## 8. Objective and Full Model at a Glance

```
         GOAL
          │
          ▼
    MINIMISE  w[0] + w[1] + ... + w[n-1]
              ─────────────────────────
                  total workers


    SUBJECT TO these rules:

    C1  ──── every instance assigned exactly once
              (no shift left uncovered, no double assignment)

    C2  ──── at most one shift per (snake k, week j, day d)
              (one worker cannot work twice in one day)

    C3  ──── w[k] ≥ j  for every used week position j in snake k
              (snake length must cover all assigned weeks)

    C4  ──── incompatible pairs cannot share the same snake week
              (rest rule within one week)

    C5  ──── incompatible pairs cannot straddle a week boundary
              (rest rule: Sunday of week j → Monday of week j+1)

    C6  ──── incompatible pairs cannot straddle the cyclic boundary
              (rest rule: Sunday of last week → Monday of week 1)
```

> **Legend:**
> `w[k]` — length of snake k (also = workers on snake k)
> `n` — number of snakes
> `j` — week position index (1 to W_max)
> `d` — day of week (1 to 7)
> `C1–C6` — the six constraints the solver must satisfy simultaneously
