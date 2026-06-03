# Snake Building – Modellierungsseminar (Feuerwehr)

**Course:** Modellierungsseminar, Uni Siegen  
**Supervisor:** Prof. Erwin Pesch  
**Team:** 3 members  
**Collaborative environment:** [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/poprjaduhhaa/Modellierungsseminar-Firestation/blob/main/snake_building.ipynb)

## Structure

```
docs/                              team documents (specs, templates, definitions)
  TuMuPl-Beschreibung_cleanedUp.docx   original problem statement (cleaned)
  Input-Daten.docx                     what input data the system needs
  definitions.docx                     team definitions
  template_ShiftDataSet.xlsx           shift dataset template (fire station)

claude-modeling/                   Claude-assisted model (step-by-step build)
  problem_definition.md            formal math: sets, parameters, variables, constraints
  data/shifts.py                   synthetic fire station dataset
  model/ILP.py                     full ILP model (Gurobi)
  examples/toy_model.py            simplified model — no solver, pure Python

results/                           solver output goes here
```

## How to read this repo (start here)

1. Read `docs/TuMuPl-Beschreibung_cleanedUp.docx` — understand the problem
2. Read `claude-modeling/problem_definition.md` — formal math definition
3. Run `claude-modeling/examples/toy_model.py` — see a working 4-shift example
4. Run `claude-modeling/model/ILP.py` — full model (needs Gurobi)

## Requirements

- Python 3.10+
- `gurobipy` with a valid Gurobi licence (student licence via Uni Siegen)
- No extra packages needed for `toy_model.py`

## Git workflow

```bash
git pull                   # always before you start
git add <file>
git commit -m "message"
git push
```
