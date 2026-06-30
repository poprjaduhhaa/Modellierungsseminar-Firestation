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
            shift_work_time_assignment=str(row['shift_work_time_assignment']),
            is_work_shift=bool(row['isWorkShift']),
            required_qualification=row['[shift_required_qualification]']
        )
        shift_objects.append(s)
    return shift_objects


# shift set
def readShiftSet(filename, mySep: str=";") -> pd.DataFrame:
    input_data = pd.read_csv(filename, sep=mySep, dtype=str) # import all values as string as first step
    # adjust data types for columns not (supposed to be) reflecting strings
    input_data["shift_required_staff"].astype(int)
    input_data["shift_class"].astype(int)
    input_data["shift_work_time_assignment"].astype(float)
    input_data["isWorkShift"] = input_data["isWorkShift"].astype(int).astype(bool)
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

