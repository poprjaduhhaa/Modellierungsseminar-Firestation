# Snake Building – Modellierungsseminar (Feuerwehr)

**Course:** Modellierungsseminar, Uni Siegen  
**Supervisor:** Prof. Erwin Pesch  
**Meeting:** 01.06.2026, 15:00, Room US-D 308  
**Team:** 3 members, collaborative via GitHub

## Problem

Given a set of fire-station shifts (with times, worker requirements and classes),
build a minimum-total-length set of rotating schedules called **snakes** that cover
all shifts while respecting rest-time constraints between consecutive shifts.

Minimising the sum of snake lengths equals minimising the total number of workers needed.

## Repository structure

```
data/     synthetic shift dataset + instance/compatibility helpers
model/    ILP formulation (Gurobi)
docs/     formal problem definition, examples
results/  solver output
```

## Requirements

- Python 3.10+
- `gurobipy` with a valid Gurobi licence (student licence via Uni Siegen)

## Quick start

```bash
git clone https://github.com/poprjaduhhaa/Modellierungsseminar-Firestation
cd Modellierungsseminar-Firestation
python model/ILP.py
```

## Git workflow (for the team)

```bash
git pull                            # always before you start
# … edit files …
git add data/shifts.py              # stage only what you changed
git commit -m "short clear message"
git push
```
