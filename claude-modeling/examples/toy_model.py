"""
Toy Snake Building model.

No solver needed — pure Python brute force.
This is a stripped-down version of the real problem so you can see
every single step clearly before looking at the full ILP.

Setup
-----
- 2 shift types: Morning (08:00-16:00) and Evening (20:00-04:00 next day)
- 2 days:        Monday and Tuesday
- 1 worker per shift, so 4 shift instances total
- Min rest between consecutive shifts: 8 hours

Goal
----
Group the 4 instances into snakes.
Minimise total workers = sum of all snake lengths.

How it works
------------
We try every possible way to assign 4 instances to (snake, week) slots.
For each assignment we check all constraints.
We keep the one with the lowest total snake length.
"""

from itertools import product


# ── Input data (these are PARAMETERS — fixed, not decisions) ──────────────────

# Each shift: (name, day, start_minutes, end_minutes)
# Day 1 = Monday,  Day 2 = Tuesday
# Times in minutes from midnight  (e.g. 08:00 = 8*60 = 480)
SHIFTS = [
    ("Morning_Mon", 1,  480,  960),   # 08:00 – 16:00  Monday
    ("Morning_Tue", 2,  480,  960),   # 08:00 – 16:00  Tuesday
    ("Evening_Mon", 1, 1200, 1680),   # 20:00 – 04:00+ Monday  (ends next day: 20*60+8*60=1680)
    ("Evening_Tue", 2, 1200, 1680),   # 20:00 – 04:00+ Tuesday
]

MIN_REST = 480   # R = 8 hours in minutes
N_DAYS   = 2     # our toy uses only 2 days per week
N_SNAKES = 2     # number of snakes we try to fill
W_MAX    = 2     # maximum allowed snake length


# ── Compatibility check ────────────────────────────────────────────────────────

def gap_minutes(a, b):
    """
    Rest time (minutes) between end of shift a and start of shift b.
    b must be on the day immediately after a.
    """
    _, day_a, _,       end_a   = a
    _, day_b, start_b, _       = b
    day_diff = day_b - day_a
    if day_diff <= 0:
        day_diff += N_DAYS          # Tuesday(2) -> Monday(1): 1-2=-1 -> +2=1
    return day_diff * 1440 + start_b - end_a


def can_follow(a, b):
    """
    Returns True if shift b can come right after shift a.
    b must be on the next day AND the rest gap must be >= MIN_REST.
    """
    _, day_a, _, _ = a
    _, day_b, _, _ = b
    next_day = (day_a % N_DAYS) + 1    # Mon(1)->Tue(2), Tue(2)->Mon(1)
    if day_b != next_day:
        return True                     # not consecutive days — no constraint
    return gap_minutes(a, b) >= MIN_REST


# ── Feasibility check for one snake ───────────────────────────────────────────

def snake_ok(weeks):
    """
    weeks: list of week-slots, each slot is a list of shifts.
    Example: [ [Morning_Mon, Morning_Tue], [Evening_Mon, Evening_Tue] ]

    Checks:
      C2 — at most one shift per day within a week
      C4 — rest between consecutive days inside a week
      C5 — rest at the boundary between week j and week j+1
      C6 — rest from last week back to week 1 (cyclic closure)
    """
    non_empty = [w for w in weeks if w]
    if not non_empty:
        return True

    for week in non_empty:

        # C2: two shifts on the same day would mean one worker works twice that day
        days_used = [s[1] for s in week]
        if len(days_used) != len(set(days_used)):
            return False

        # C4: consecutive shifts within the week must respect rest time
        by_day = sorted(week, key=lambda s: s[1])
        for i in range(len(by_day) - 1):
            if not can_follow(by_day[i], by_day[i + 1]):
                return False

    # C5: last shift of week j must be compatible with first shift of week j+1
    for j in range(len(weeks) - 1):
        if weeks[j] and weeks[j + 1]:
            last_in_week  = max(weeks[j],     key=lambda s: s[1])
            first_in_next = min(weeks[j + 1], key=lambda s: s[1])
            if not can_follow(last_in_week, first_in_next):
                return False

    # C6: last shift of the last week must loop back to first shift of week 1
    if weeks[-1] and weeks[0]:
        last_shift  = max(weeks[-1], key=lambda s: s[1])
        first_shift = min(weeks[0],  key=lambda s: s[1])
        if not can_follow(last_shift, first_shift):
            return False

    return True


# ── Brute force over all assignments ──────────────────────────────────────────
# Each of the 4 shifts gets one slot: (snake index, week index).
# N_SNAKES=2, W_MAX=2  ->  4 possible slots per shift  ->  4^4 = 256 combinations.

best_workers  = float("inf")
best_solution = None

for assignment in product(range(N_SNAKES * W_MAX), repeat=len(SHIFTS)):

    # Build snakes[snake_index][week_index] = list of shifts
    snakes = [[[] for _ in range(W_MAX)] for _ in range(N_SNAKES)]
    for shift_idx, slot in enumerate(assignment):
        k = slot // W_MAX    # which snake
        j = slot  % W_MAX    # which week inside the snake
        snakes[k][j].append(SHIFTS[shift_idx])

    # Evaluate
    total_workers = 0
    feasible      = True

    for k in range(N_SNAKES):
        used_week_indices = [j for j in range(W_MAX) if snakes[k][j]]
        if not used_week_indices:
            continue
        length = max(used_week_indices) + 1   # snake length = highest week used + 1
        if not snake_ok(snakes[k][:length]):
            feasible = False
            break
        total_workers += length

    if feasible and total_workers < best_workers:
        best_workers  = total_workers
        best_solution = [list(week) for snake in snakes for week in [snake]]
        best_solution = snakes[:]


# ── Print result ───────────────────────────────────────────────────────────────

print("=" * 50)
print(f"  Minimum workers needed: {best_workers}")
print("=" * 50)

for k, snake in enumerate(best_solution):
    used = [(j + 1, week) for j, week in enumerate(snake) if week]
    if not used:
        continue
    print(f"\nSnake {k + 1}  ->  length {len(used)}  ->  {len(used)} worker(s)")
    for week_num, week in used:
        names = ",  ".join(s[0] for s in sorted(week, key=lambda s: s[1]))
        print(f"  Week {week_num}: {names}")

print()
print("Each worker is assigned one week of their snake.")
print("After the last week they rotate back to week 1 — forever.")
print(f"\nTotal workers = sum of snake lengths = {best_workers}")
