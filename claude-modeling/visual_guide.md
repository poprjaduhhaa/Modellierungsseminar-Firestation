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


---

## 9. Concrete Tables From Our Dataset

### TABLE 1 — All shift instances (the set I)

Each row is one `i`. These are what the ILP assigns to snakes.

| i | name | day (d) | copy | start | end | class |
|---|------|---------|------|-------|-----|-------|
|  0 | EARLY_ | Mon | 0 | 06:00 | 14:00    | 1 |
|  1 | EARLY_ | Mon | 1 | 06:00 | 14:00    | 1 |
|  2 | EARLY_ | Tue | 0 | 06:00 | 14:00    | 1 |
|  3 | EARLY_ | Tue | 1 | 06:00 | 14:00    | 1 |
|  4 | EARLY_ | Wed | 0 | 06:00 | 14:00    | 1 |
|  5 | EARLY_ | Wed | 1 | 06:00 | 14:00    | 1 |
|  6 | EARLY_ | Thu | 0 | 06:00 | 14:00    | 1 |
|  7 | EARLY_ | Thu | 1 | 06:00 | 14:00    | 1 |
|  8 | EARLY_ | Fri | 0 | 06:00 | 14:00    | 1 |
|  9 | EARLY_ | Fri | 1 | 06:00 | 14:00    | 1 |
| 10 | LATE__ | Mon | 0 | 14:00 | 22:00    | 1 |
| 11 | LATE__ | Mon | 1 | 14:00 | 22:00    | 1 |
| 12 | LATE__ | Tue | 0 | 14:00 | 22:00    | 1 |
| 13 | LATE__ | Tue | 1 | 14:00 | 22:00    | 1 |
| 14 | LATE__ | Wed | 0 | 14:00 | 22:00    | 1 |
| 15 | LATE__ | Wed | 1 | 14:00 | 22:00    | 1 |
| 16 | LATE__ | Thu | 0 | 14:00 | 22:00    | 1 |
| 17 | LATE__ | Thu | 1 | 14:00 | 22:00    | 1 |
| 18 | LATE__ | Fri | 0 | 14:00 | 22:00    | 1 |
| 19 | LATE__ | Fri | 1 | 14:00 | 22:00    | 1 |
| 20 | NIGHT_ | Mon | 0 | 22:00 | 10:00+1d | 2 |
| 21 | NIGHT_ | Mon | 1 | 22:00 | 10:00+1d | 2 |
| 22 | NIGHT_ | Tue | 0 | 22:00 | 10:00+1d | 2 |
| 23 | NIGHT_ | Tue | 1 | 22:00 | 10:00+1d | 2 |
| 24 | NIGHT_ | Wed | 0 | 22:00 | 10:00+1d | 2 |
| 25 | NIGHT_ | Wed | 1 | 22:00 | 10:00+1d | 2 |
| 26 | NIGHT_ | Thu | 0 | 22:00 | 10:00+1d | 2 |
| 27 | NIGHT_ | Thu | 1 | 22:00 | 10:00+1d | 2 |
| 28 | NIGHT_ | Fri | 0 | 22:00 | 10:00+1d | 2 |
| 29 | NIGHT_ | Fri | 1 | 22:00 | 10:00+1d | 2 |
| 30 | NIGHT_ | Sat | 0 | 22:00 | 10:00+1d | 2 |
| 31 | NIGHT_ | Sat | 1 | 22:00 | 10:00+1d | 2 |
| 32 | NIGHT_ | Sun | 0 | 22:00 | 10:00+1d | 2 |
| 33 | NIGHT_ | Sun | 1 | 22:00 | 10:00+1d | 2 |
| 34 | WHOLE_ | Sat | 0 | 08:00 | 08:00+1d | 1 |
| 35 | WHOLE_ | Sat | 1 | 08:00 | 08:00+1d | 1 |
| 36 | WHOLE_ | Sat | 2 | 08:00 | 08:00+1d | 1 |
| 37 | WHOLE_ | Sun | 0 | 08:00 | 08:00+1d | 1 |
| 38 | WHOLE_ | Sun | 1 | 08:00 | 08:00+1d | 1 |
| 39 | WHOLE_ | Sun | 2 | 08:00 | 08:00+1d | 1 |

> **i** = instance index used in x[i,k,j]  
> **copy** = 0 or 1 because workers=2 (two identical slots per shift per day)  
> **class** = 1 (day/attractive) or 2 (night/unattractive)  
> **+1d** = shift ends the next day (overnight)

---

### TABLE 2 — Incompatible consecutive-day pairs (sample)

These are the pairs that trigger constraints C4, C5, C6.
If (a,b) is here, instances a and b **cannot be adjacent in a snake**.

| a.id | a.name | a.day | → | b.id | b.name | b.day | gap (min) | R=660? |
|------|--------|-------|---|------|--------|-------|-----------|--------|
| 10 | LATE__ | Mon | → | 2 | EARLY_ | Tue | 480 | ✗ |
| 18 | LATE__ | Fri | → | 8 | EARLY_ | Sat | 480 | ✗ |
| 20 | NIGHT_ | Mon | → | 2 | EARLY_ | Tue | -240 | ✗ |
| 20 | NIGHT_ | Mon | → | 10 | LATE__ | Tue | 240 | ✗ |
| 30 | NIGHT_ | Sat | → | 34 | WHOLE_ | Sun | -480 | ✗ |
| 34 | WHOLE_ | Sat | → | 37 | WHOLE_ | Sun | 0 | ✗ |

> **gap** = 1440 + start[b] − end[a]  
> If gap < R=660 → this pair is incompatible → constraints C4/C5/C6 apply to them

---

### TABLE 3 — x[i, k, j]: which instance goes where (first 20 rows)

This is what a **solution** looks like as a table.
Each row means: x[i, k, j] = 1 (all other cells for this i are 0).

| i | name | day | copy | assignment |
|---|------|-----|------|------------|
|  0 | EARLY_ | Mon | 0 | x[0,0,1] = 1 |
|  1 | EARLY_ | Mon | 1 | x[1,0,6] = 1 |
|  2 | EARLY_ | Tue | 0 | x[2,0,2] = 1 |
|  3 | EARLY_ | Tue | 1 | x[3,0,7] = 1 |
|  4 | EARLY_ | Wed | 0 | x[4,0,3] = 1 |
|  5 | EARLY_ | Wed | 1 | x[5,0,8] = 1 |
|  6 | EARLY_ | Thu | 0 | x[6,0,4] = 1 |
|  7 | EARLY_ | Thu | 1 | x[7,0,9] = 1 |
|  8 | EARLY_ | Fri | 0 | x[8,0,5] = 1 |
|  9 | EARLY_ | Fri | 1 | x[9,0,10] = 1 |
| 10 | LATE__ | Mon | 0 | x[10,0,1] = 1 |
| 11 | LATE__ | Mon | 1 | x[11,0,6] = 1 |
| 12 | LATE__ | Tue | 0 | x[12,0,2] = 1 |
| 13 | LATE__ | Tue | 1 | x[13,0,7] = 1 |
| 14 | LATE__ | Wed | 0 | x[14,0,3] = 1 |
| 15 | LATE__ | Wed | 1 | x[15,0,8] = 1 |
| 16 | LATE__ | Thu | 0 | x[16,0,4] = 1 |
| 17 | LATE__ | Thu | 1 | x[17,0,9] = 1 |
| 18 | LATE__ | Fri | 0 | x[18,0,5] = 1 |
| 19 | LATE__ | Fri | 1 | x[19,0,10] = 1 |
| ... | ... | ... | ... | ... (40 rows total) |

> **k** = which snake (0, 1, or 2)  
> **j** = which week position inside that snake  
> Reading row 1: instance 0 (EARLY_ Mon copy0) is placed in snake 0 at week 1

---

### TABLE 4 — Snake lengths w[k]

Summary of the solution above.

| snake k | week positions used (j) | w[k] = max(j) | workers |
|---------|------------------------|---------------|---------|
| k=0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | 10 | 10 workers |
| k=1 | [1, 2, 3, 4, 5, 6, 7] | 7 | 7 workers |
| k=2 | [1, 2, 3, 4, 5, 6] | 6 | 6 workers |
| **total** | | | **23 workers** |

> **w[k]** = the highest week index used in snake k  
> This is what the objective minimises: w[0] + w[1] + w[2] = 23  
> The ILP finds the assignment that makes this sum as small as possible
