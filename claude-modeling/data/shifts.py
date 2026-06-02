"""
Fire station shift dataset.

Based on the team's template (docs/template_ShiftDataSet.xlsx).

Shift types
-----------
EARLY_  06:00-14:00  Mon-Fri   class 1 (attractive, daytime)
LATE__  14:00-22:00  Mon-Fri   class 1 (attractive, daytime)
NIGHT_  22:00-06:00  every day class 2 (unattractive, night)
WHOLE_  08:00-08:00  Sat-Sun   class 1 (24h weekend shift)

Time representation: minutes from midnight.
  06:00 =  360,  14:00 =  840,  22:00 = 1320
  06:00 next day = 2040  (= 22*60 + 8*60),  08:00 next day = 1920

Overnight shifts have end > 1440 so rest-gap arithmetic stays simple.
"""

from dataclasses import dataclass
from typing import List, Optional


MIN_REST: int = 660  # 11 hours — German labour law minimum (ArbZG)


@dataclass
class ShiftType:
    """
    One recurring shift pattern.
    PARAMETER — fixed input data, not a decision variable.
    """
    code:        str            # unique 6-digit identifier
    name:        str            # 6-character abbreviation
    days:        List[int]      # days it occurs (1=Mon ... 7=Sun)
    start1:      int            # start of subshift 1 (minutes from midnight)
    end1:        int            # end   of subshift 1 (minutes; >1440 if overnight)
    start2:      Optional[int]  # start of subshift 2, or None
    end2:        Optional[int]  # end   of subshift 2, or None
    workers:     int            # q[s] — workers required per occurrence
    shift_class: int            # 1-10; here 1=day (attractive), 2=night (unattractive)

    @property
    def duration(self) -> int:
        d = self.end1 - self.start1
        if self.start2 is not None:
            d += self.end2 - self.start2
        return d


@dataclass
class ShiftInstance:
    """
    One individual worker-slot for a specific (type, day).
    DECISION TARGET — x[i,k,j] in the ILP refers to instances.
    """
    id:         int
    shift_type: ShiftType
    day:        int   # 1=Mon ... 7=Sun
    copy:       int   # 0-based worker copy within same (type, day)

    @property
    def start(self) -> int:
        return self.shift_type.start1

    @property
    def end(self) -> int:
        return self.shift_type.end1


# ── Dataset ────────────────────────────────────────────────────────────────────

SHIFT_TYPES: List[ShiftType] = [
    ShiftType(
        code="000001", name="EARLY_",
        days=[1, 2, 3, 4, 5],          # Mon-Fri
        start1=360,  end1=840,          # 06:00-14:00
        start2=None, end2=None,
        workers=2,   shift_class=1,
    ),
    ShiftType(
        code="000002", name="LATE__",
        days=[1, 2, 3, 4, 5],          # Mon-Fri
        start1=840,  end1=1320,         # 14:00-22:00
        start2=None, end2=None,
        workers=2,   shift_class=1,
    ),
    ShiftType(
        code="000003", name="NIGHT_",
        days=[1, 2, 3, 4, 5, 6, 7],    # every day
        start1=1320, end1=2040,         # 22:00-06:00 next day
        start2=None, end2=None,
        workers=2,   shift_class=2,
    ),
    ShiftType(
        code="000004", name="WHOLE_",
        days=[6, 7],                    # Sat-Sun (24h weekend shift)
        start1=480,  end1=1920,         # 08:00-08:00 next day
        start2=None, end2=None,
        workers=3,   shift_class=1,
    ),
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def build_instances(shift_types: List[ShiftType]) -> List[ShiftInstance]:
    """Expand types into individual worker-slots."""
    instances, idx = [], 0
    for st in shift_types:
        for day in st.days:
            for copy in range(st.workers):
                instances.append(ShiftInstance(id=idx, shift_type=st, day=day, copy=copy))
                idx += 1
    return instances


def gap_minutes(a: ShiftInstance, b: ShiftInstance) -> int:
    """Rest time (min) between end of a and start of b (b is next day after a)."""
    day_diff = b.day - a.day
    if day_diff <= 0:
        day_diff += 7
    return day_diff * 1440 + b.start - a.end


def can_follow(a: ShiftInstance, b: ShiftInstance, min_rest: int = MIN_REST) -> bool:
    """True iff b can directly follow a (next day, enough rest)."""
    if b.day != (a.day % 7) + 1:
        return True   # not consecutive days
    return gap_minutes(a, b) >= min_rest


def build_compatibility(instances: List[ShiftInstance]) -> dict:
    """Return {(a.id, b.id): bool} for all consecutive-day pairs."""
    compat = {}
    for a in instances:
        next_day = (a.day % 7) + 1
        for b in instances:
            if b.day == next_day:
                compat[(a.id, b.id)] = can_follow(a, b)
    return compat


if __name__ == "__main__":
    insts  = build_instances(SHIFT_TYPES)
    compat = build_compatibility(insts)
    print(f"Shift types : {len(SHIFT_TYPES)}")
    print(f"Total instances : {len(insts)}")
    for st in SHIFT_TYPES:
        n = sum(1 for i in insts if i.shift_type.code == st.code)
        print(f"  {st.name} : {n}")
    bad = [(k,v) for k,v in compat.items() if not v]
    print(f"Incompatible consecutive-day pairs: {len(bad)}")
