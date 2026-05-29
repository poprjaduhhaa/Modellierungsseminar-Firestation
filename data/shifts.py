"""
Synthetic fire-station shift dataset.

Shift *types* describe a recurring shift pattern (which days, what times, how many
workers).  Shift *instances* are the individual worker-slots that must be placed
into a snake — if a type requires q workers, it produces q identical instances per
day it occurs.

Time representation
-------------------
All times are in **minutes from midnight**.
  06:00  ->  360
  18:00  -> 1080
Overnight shifts have end > 1440.
  Night 18:00-06:00 next day  ->  end = 1800  (= 18*60 + 12*60)

This makes rest-gap arithmetic straightforward (see gap_minutes).
"""

from dataclasses import dataclass
from typing import List, Optional


# ── Constants (parameters) ─────────────────────────────────────────────────────

MIN_REST: int = 660  # R — minimum rest between consecutive shifts (minutes = 11 h)


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class ShiftType:
    """
    One recurring shift pattern.  This is *input data* (a parameter), not a
    decision variable.

    Attributes
    ----------
    code        : unique 6-digit string identifier (from spec format)
    name        : 6-character abbreviation
    days        : days of the week the shift occurs  (1=Mon … 7=Sun)
    start1      : start of first subshift  (minutes from midnight)
    end1        : end of first subshift    (minutes from midnight; >1440 if overnight)
    start2      : start of second subshift, or None for single-subshift shifts
    end2        : end of second subshift,   or None
    workers     : q[s] — number of workers required per occurrence
    shift_class : shift class integer (1..10)
    """
    code:        str
    name:        str
    days:        List[int]
    start1:      int
    end1:        int
    start2:      Optional[int]
    end2:        Optional[int]
    workers:     int
    shift_class: int

    @property
    def duration(self) -> int:
        """Total working time in minutes (subshift 1 + optional subshift 2)."""
        d = self.end1 - self.start1
        if self.start2 is not None:
            d += self.end2 - self.start2
        return d


@dataclass
class ShiftInstance:
    """
    One individual worker-slot for a specific shift type on a specific day.
    These are the objects x[i,k,j] refers to in the ILP.

    Attributes
    ----------
    id         : unique integer index (used as key in the ILP)
    shift_type : parent ShiftType
    day        : day of week this instance occurs  (1=Mon … 7=Sun)
    copy       : worker-copy index within the same (type, day)  (0-based)
    """
    id:         int
    shift_type: ShiftType
    day:        int
    copy:       int

    @property
    def start(self) -> int:
        return self.shift_type.start1

    @property
    def end(self) -> int:
        return self.shift_type.end1


# ── Synthetic dataset ──────────────────────────────────────────────────────────
#
# Simple fire station with two 12-hour shift types, 7 days a week, 2 workers each.
# Total instances per week: 7 * 2 + 7 * 2 = 28  ->  lower bound: ceil(28/7) = 4 workers.
#
# Class 1 = day shifts (attractive)
# Class 2 = night shifts (unattractive)

SHIFT_TYPES: List[ShiftType] = [
    ShiftType(
        code="010100",
        name="DAY___",
        days=[1, 2, 3, 4, 5, 6, 7],
        start1=360,    # 06:00
        end1=1080,     # 18:00
        start2=None,
        end2=None,
        workers=2,
        shift_class=1,
    ),
    ShiftType(
        code="010200",
        name="NIGHT_",
        days=[1, 2, 3, 4, 5, 6, 7],
        start1=1080,   # 18:00
        end1=1800,     # 06:00 next day  (18*60 + 12*60 = 1800)
        start2=None,
        end2=None,
        workers=2,
        shift_class=2,
    ),
]


# ── Helper functions ───────────────────────────────────────────────────────────

def build_instances(shift_types: List[ShiftType]) -> List[ShiftInstance]:
    """
    Expand shift types into individual worker instances.
    A type with workers=2 occurring on 7 days produces 14 instances.
    """
    instances, idx = [], 0
    for st in shift_types:
        for day in st.days:
            for copy in range(st.workers):
                instances.append(ShiftInstance(id=idx, shift_type=st, day=day, copy=copy))
                idx += 1
    return instances


def gap_minutes(a: ShiftInstance, b: ShiftInstance) -> int:
    """
    Rest time (minutes) between end of a and start of b, assuming b occurs on
    the day immediately following a (handles the Sunday -> Monday wrap).

    Formula:
        gap = Δday * 1440 + start[b] - end[a]
        where Δday = day[b] - day[a], adjusted to be exactly 1 for consecutive days.
    """
    day_diff = b.day - a.day
    if day_diff <= 0:
        day_diff += 7  # Sunday(7) -> Monday(1): 1-7 = -6  ->  -6+7 = 1
    return day_diff * 1440 + b.start - a.end


def can_follow(a: ShiftInstance, b: ShiftInstance, min_rest: int = MIN_REST) -> bool:
    """
    Return True iff instance b can directly follow a in a snake
    (b is on the next day and the rest gap is >= min_rest).
    """
    next_day = (a.day % 7) + 1          # Mon=1,...,Sun=7 wraps back to Mon=1
    if b.day != next_day:
        return False                    # not a consecutive-day pair
    return gap_minutes(a, b) >= min_rest


def build_compatibility(instances: List[ShiftInstance]) -> dict:
    """
    Return a dict  {(a.id, b.id): bool}  for every consecutive-day pair (a, b).
    Only pairs where day[b] == (day[a] % 7) + 1 are included.
    """
    compat = {}
    for a in instances:
        next_day = (a.day % 7) + 1
        for b in instances:
            if b.day == next_day:
                compat[(a.id, b.id)] = can_follow(a, b)
    return compat


# ── Quick sanity check ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    insts  = build_instances(SHIFT_TYPES)
    compat = build_compatibility(insts)

    print(f"Shift types : {len(SHIFT_TYPES)}")
    print(f"Instances   : {len(insts)}")
    print(f"  DAY___    : {sum(1 for i in insts if i.shift_type.name == 'DAY___')}")
    print(f"  NIGHT_    : {sum(1 for i in insts if i.shift_type.name == 'NIGHT_')}")

    incompatible = [(k, v) for k, v in compat.items() if not v]
    print(f"\nIncompatible consecutive-day pairs: {len(incompatible)}")
    inst_map = {i.id: i for i in insts}
    a_id, b_id = incompatible[0][0]
    a, b = inst_map[a_id], inst_map[b_id]
    print(f"  Example: {a.shift_type.name}(day={a.day}) -> "
          f"{b.shift_type.name}(day={b.day})  gap={gap_minutes(a,b)} min")
