# Snake Building – Visual Guide

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

---

## 2. Worker Rotation

The snake never changes. Workers rotate through it every calendar week.

```
Calendar     Worker A      Worker B      Worker C
─────────────────────────────────────────────────
week  t  →  [ Week 1 ]    [ Week 2 ]    [ Week 3 ]
week t+1 →  [ Week 2 ]    [ Week 3 ]    [ Week 1 ]
week t+2 →  [ Week 3 ]    [ Week 1 ]    [ Week 2 ]
week t+3 →  [ Week 1 ]    [ Week 2 ]    [ Week 3 ]  ← same as t
week t+4 →  [ Week 2 ]    [ Week 3 ]    [ Week 1 ]  ← same as t+1
```

> Snake length = 3  →  3 workers needed on this snake.

---

## 3. Multiple Snakes

All shifts must be split across snakes. Each snake is independent.

```
ALL SHIFTS
    │
    ├──────────────────► SNAKE 1 (day shifts only)
    │                    Week 1: EARLY Mon-Fri
    │                    Week 2: EARLY Mon-Fri
    │                    length = 2  →  2 workers
    │
    └──────────────────► SNAKE 2 (night shifts only)
                         Week 1: NIGHT Mon-Sun
                         Week 2: NIGHT Mon-Sun
                         length = 2  →  2 workers

                         TOTAL workers = 2 + 2 = 4
```

> Why not one big snake mixing day and night?
> See Section 6 (C6) — the cyclic boundary creates a rest violation.

---

## 4. Time Representation

All times are in **minutes from midnight**.

```
Midnight        06:00       14:00       22:00    Midnight
    │              │           │           │         │
    0            360         840        1320       1440
    │              │           │           │         │
    ├──────────────┼───────────┼───────────┼─────────┤
                   ╠═══════════╣           │
                      EARLY_              │
                   06:00 → 14:00          │
                                ╠═════════╣
                                   LATE__
                                14:00 → 22:00
                                           ╠═══════════════╣
                                              NIGHT_
                                           22:00 → 06:00+1d
                                                   (end = 2040)
```

---

## 5. Rest Gap — Why Some Shifts Cannot Follow Each Other

German law requires **≥ 660 minutes (11 hours)** rest between shifts.

```
gap(a → b) = 1440 + start[b] − end[a]
             (assuming b is on the next day after a)
```

```
NIGHT_ ends at 06:00 (= 2040 min)
    │
    ▼
────┼──────────────────────────────────────────────────────────
  06:00                                               next day
    │←── 0 min ──→│←──── 8 h ────→│←───── 16 h ─────→│
  06:00          14:00           22:00               06:00
  EARLY_         LATE__          NIGHT_
  start=360      start=840       start=1320

gap to EARLY_:  1440 + 360  − 2040 =  −240 min  ✗  (overlap!)
gap to LATE__:  1440 + 840  − 2040 =   240 min  ✗  (< 660)
gap to NIGHT_:  1440 + 1320 − 2040 =   720 min  ✓  (≥ 660)
```

**Incompatible consecutive-day pairs in our dataset:**

| Shift on day d | Shift on day d+1 | Gap (min) | OK? |
|---------------|-----------------|-----------|-----|
| NIGHT_  (ends 2040) | EARLY_ (starts  360) | −240 | ✗ |
| NIGHT_  (ends 2040) | LATE__ (starts  840) |  240 | ✗ |
| LATE__  (ends 1320) | EARLY_ (starts  360) |  480 | ✗ |
| EARLY_  (ends  840) | LATE__ (starts  840) | 1440 | ✓ |
| EARLY_  (ends  840) | NIGHT_ (starts 1320) | 1920 | ✓ |
| LATE__  (ends 1320) | NIGHT_ (starts 1320) | 1440 | ✓ |
| NIGHT_  (ends 2040) | NIGHT_ (starts 1320) |  720 | ✓ |

---

## 6. Where Each Constraint Applies

```
ONE SNAKE  (w = 3 weeks, 7 days each)

Week 1          Week 2          Week 3
Mon─Tue─Wed─Thu─Fri─Sat─Sun│Mon─Tue─Wed─Thu─Fri─Sat─Sun│Mon─Tue─...─Sun
 │   │                   │   │   │                   │   │   │
 └───┘                   └───┘   └───────────────────┘   └───┘
  C4                      C5               C5              C4
(within                (boundary       (boundary        (within
 week)                week1→week2)   week2→week3)        week)

                                                            │
              ┌─────────────────────────────────────────────┘
              │              C6
              ▼         (cyclic: last
         Week 1            Sun → first Mon)
```

| Constraint | Where it applies | What it prevents |
|-----------|-----------------|-----------------|
| **C4** | consecutive days *inside* one snake week | incompatible shifts in same week |
| **C5** | Sunday of week j → Monday of week j+1 | incompatible shifts across week boundary |
| **C6** | Sunday of *last* week → Monday of week 1 | incompatible shifts at cyclic wrap |

---

## 7. Decision Variable x[i, k, j]

Think of it as a 3-dimensional box. Each cell is 0 or 1.

```
           j=1      j=2      j=3      j=4  ...
         ┌────────┬────────┬────────┬────────┐
k=0      │  0/1   │  0/1   │  0/1   │  0/1   │
         ├────────┼────────┼────────┼────────┤
k=1      │  0/1   │  0/1   │  0/1   │  0/1   │
         └────────┴────────┴────────┴────────┘
              ▲
         one cell per (instance i, snake k, week j)
         = 1 if instance i is placed here
         = 0 if not
```

**C1** says: for each instance i, exactly one cell in its "slice" = 1, all others = 0.

```
Instance i=5, across all (k, j):

k=0: [ 0 ][ 0 ][ 1 ][ 0 ][ 0 ]...   ← assigned to snake 0, week 3
k=1: [ 0 ][ 0 ][ 0 ][ 0 ][ 0 ]...
k=2: [ 0 ][ 0 ][ 0 ][ 0 ][ 0 ]...

Sum of all cells = 1  ✓
```

---

## 8. Objective and Full Model at a Glance

```
                 ┌─────────────────────────────────┐
                 │  MINIMISE  w[0] + w[1] + ... + w[n]  │
                 │           (total workers)        │
                 └────────────────┬────────────────┘
                                  │
                        SUBJECT TO:
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
    C1: coverage           C2: one shift          C3: length
    every instance         per day per            w[k] ≥ max
    assigned once          snake week             week used
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
    C4: rest within        C5: rest across         C6: rest at
    snake week             week boundary           cyclic wrap
    (day d → d+1)         (Sun j → Mon j+1)      (last Sun → first Mon)
```
