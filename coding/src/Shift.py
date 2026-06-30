from dataclasses import dataclass, field   # Import the dataclass decorator and field helper to define lightweight immutable or mutable data containers and to provide default factory for mutable defaults
import pandas as pd                       # Import pandas under the conventional alias pd to read the CSV into a DataFrame and to work with tabular data
import datetime as dt


# Dataclass definition -------------------------------------------------------

@dataclass
class Shift:
    # data type class for shifts
    shift_id: str                           # unique shift ID
    description: str                            # clear-text description of the shif
    weekdays: list[str]                     # weekdays for which the shift is relevant
    start: dt.time                   # start time of the shift (hh:mm)
    end: dt.time                     # end time of the shift (hh:mm)
    required_staff: int           # number of worker required for the shift
    shift_class: int              # shift class relecting attractiveness of the shift (values 1-10)
    shift_work_time_assignment: int  # 
    is_work_shift: bool           # boolean to reflect if a shift is treated as work-shift or not (eg "free_day" is False)
    required_qualification: str  # qualification needs for the shift (relevant for mapping suitable staff members)

    
def shift_duration_hours(shift) -> float:
    # calculate gross shift duration in hours (handles overnight shifts)
    start_min = shift.start.hour * 60 + shift.start.minute
    end_min   = shift.end.hour * 60 + shift.end.minute
    if end_min <= start_min:  # overnight shift (e.g. 16:15 -> 07:00)
        duration_min = (24 * 60 - start_min) + end_min
    else:
        duration_min = end_min - start_min
    return duration_min / 60


# Calculates minutes of rest between end of sh1 and start of sh2 on the next day.
# Handles overnight shifts (e.g. 16:15->07:00) by adding 24h to end time.
# Used to pre-compute incompatible shift pairs for MIN_REST constraint.
def rest_minutes_between(sh1, sh2) -> int:
    end_min = sh1.end.hour * 60 + sh1.end.minute
    if sh1.end <= sh1.start:  # overnight shift
        end_min += 24 * 60
    next_start_min = 24 * 60 + sh2.start.hour * 60 + sh2.start.minute
    return next_start_min - end_min

