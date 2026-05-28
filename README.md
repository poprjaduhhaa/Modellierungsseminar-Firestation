# Modellierungsseminar - Firestation

Gruppenproject zur Modellierung von Schichtrotationsmustern im Rettungsdienst.

## Struktur
- `data/` — Schichtdatensatz
- `model/` — ILP-Modell
- `results/` — Ausgaben des Solvers

## Voraussetzungen
- Python 3.x
- Gurobi

## Ausführen
```bash
python model/ilp.py

## How to use

### First time setup
1. Install Git: https://git-scm.com/downloads
2. Install Python: https://www.python.org/downloads
3. Open terminal (Mac/Linux) or Git Bash (Windows)
4. Clone the repo:
   git clone https://github.com/poprjaduhhaa/Modellierungsseminar-Firestation
5. Go into the folder:
   cd Modellierungsseminar-Firestation

### Every time you work on the project
Before you start — get the latest version:
   git pull

After you make changes — save and upload:
   git add .
   git commit -m "describe what you changed"
   git push

### Rules to avoid conflicts
- Always git pull before you start working
- Don't edit the same file as someone else at the same time
- Write short but clear commit messages (e.g. "added shift dataset" not "changes")
