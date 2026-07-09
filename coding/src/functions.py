import pandas as pd
import datetime as dt
from pathlib import Path
import src.Shift as Shift # tailor-made data type for shift definitions


# LOGS / for process transparency 
def writeToLogs(yourStatusMessage:str, file, deleteHistory=False):
    try:
        if deleteHistory:
            with file.open("w") as log:
                log.write(dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                log.write(" // ")
                log.write(yourStatusMessage+"\n")
        else:
            with file.open("a") as log:
                log.write(dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                log.write(" // ")
                log.write(yourStatusMessage+"\n")
    except FileNotFoundError:
        print(f"file '{file}' not found - I skip logging and go on with my work...")
    except PermissionError:
        print(f"file '{file}' is locked for editing - I skip logging and go on with my work...")


# read user input (parameters, objectives,...)
def readParameters(filename, mySep=";") -> dict:
    try:
        df = pd.read_csv(filename, sep=mySep, dtype=str)
        params = dict(zip(df["parameter"], df["value"]))
        return params
    except FileNotFoundError:
        print(f"file {filename} not available")
    

# LOG / for transparency write shift objects into a file:
def writeDataToLogs(data, filename):
    try:
        pd.DataFrame(data).to_csv(filename, sep=";", index=True, encoding="utf-8", decimal=".")
    except PermissionError:
        print("log file for shift_object is open - I skipped saving and executed succeeding code")


# read input data
# added objects to read whole csv file
def build_shift_objects(df: pd.DataFrame) -> list:
    shift_objects = []
    for _, row in df.iterrows():
        s = Shift.Shift(
            shift_id=row['shift_ID'],
            description=row['shift_details'],
            weekdays=[d.strip() for d in row['shift_weekdays'].split(',')],
            start=dt.time(*map(int, row['shift_start_time'].split(':'))),
            end=dt.time(*map(int, row['shift_end_time'].replace('24','0').split(':'))),
            required_staff=0 if row['shift_required_staff'] == 'none' else int(row['shift_required_staff']),
            shift_class=int(row['shift_class']),
            shift_work_time_assignment=(None if str(row['shift_work_time_assignment']).strip().lower() in ('none', 'nan', '')
                                        else float(row['shift_work_time_assignment'])),
            is_work_shift=bool(row['isWorkShift']),
            required_qualification=row['[shift_required_qualification]']
        )
        shift_objects.append(s)
    return shift_objects


# reserve clones (team decision 2026-07-08, replaces the old hard-coded reserveShift):
# every shift definition gets a stand-by copy so absences in ANY shift can be covered.
# Clone count per shift: ratio of the required staff, floored, but at least 1.
# The clone keeps all attributes (times, weekdays, work time, ...) except the class,
# which is one step less attractive (original + 1), capped at 10 because the
# Beliebtheit scale ends there (team decision 2026-07-09). Works on the RAW shift set
# BEFORE the explode into per-worker slots, so clones run through the same pipeline
# as any shift and nothing downstream needs special cases.
def add_reserve_clones(input_data: pd.DataFrame, ratio: float=0.2) -> pd.DataFrame:
    staff = pd.to_numeric(input_data["shift_required_staff"], errors="coerce").fillna(0)
    clones = input_data[staff > 0].copy()
    clone_staff = (staff[staff > 0] * ratio).astype(int).clip(lower=1)
    clones["shift_required_staff"] = clone_staff.astype(str)
    clones["shift_class"] = (pd.to_numeric(clones["shift_class"]).astype(int) + 1).clip(upper=10).astype(str)
    clones["shift_ID"] = clones["shift_ID"].str.replace("]", "#res]", regex=False)
    clones["shift_details"] = "reserve clone of " + clones["shift_details"].astype(str)
    return pd.concat([input_data, clones], ignore_index=True)


# shift set
def readShiftSet(filename, mySep: str=";", clone_ratio: float=None) -> pd.DataFrame:
    input_data = pd.read_csv(filename, sep=mySep, dtype=str) # import all values as string as first step
    # adjust data types for columns not (supposed to be) reflecting strings
    input_data["shift_required_staff"].astype(int)
    input_data["shift_class"].astype(int)
    input_data["shift_work_time_assignment"].astype(float)
    input_data["isWorkShift"] = input_data["isWorkShift"].astype(int).astype(bool)
    # append dynamic reserve clones before the explode (None/0 = feature off)
    if clone_ratio:
        input_data = add_reserve_clones(input_data, clone_ratio)
    # multiply rows by the number of required workers (.explode())
    #input_data = input_data.assign(shift_required_staff=input_data["shift_required_staff"].apply(lambda n: list(range(1, n+1)))).explode("shift_required_staff")

    #multiply rows by number of required staff
    input_data = input_data[input_data["shift_required_staff"].notna() 
                            & (input_data["shift_required_staff"] != 0)].loc[lambda x: x.index.repeat(x["shift_required_staff"])].assign(shift_ID=lambda x: x.groupby(level=0).cumcount().add(1)
                                   .astype(str)
                                   .radd("%_%") # use a clear - unlikely used otherwise - delimiter for later removal (relevant for output)
                                   .radd(x["shift_ID"]))    
    return input_data
    # potentially add further data cleaning steps

