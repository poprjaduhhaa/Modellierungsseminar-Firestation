# AUDIT v2 & TICKETS: cyclePlanning.ipynb (Snake Building)

Date: 2026-07-07 (v2, after Dirk's big cleanup landed in main, HEAD bc8c2b6).
Replaces AUDIT v1 entirely. Audited fresh: all 52 notebook cells, src/functions.py,
src/Shift.py, parameters.csv, both Pesch datasets, outputs, plus the primary spec
(docs/TuMuPl-Beschreibung_cleanedUp.docx) read in v1.

Execution rule: small blocks, the user applies every change himself and runs between
blocks. No from-scratch rewrites. Cell numbers below refer to the CURRENT notebook;
always re-verify by dumping cells before editing (they drift).

---

## 1. Binding facts from the professor's spec (unchanged from v1)

- Snake is CYCLIC: last shift and first shift must observe time constraints (ring).
- MaxW is a HARD per-week cap on work hours, same for all snakes.
- Off-day clustering is a SOFT effect of jump minimization, not a hard rule.
- Pesch2 (class shares between snakes, space) and Pesch8 (class changes along days,
  time) are different objectives; Pesch3 = Pesch8 with shiftID instead of class
  (Dirk confirmed in chat, 2026-07-07).
- Team deviations accepted: work_time_assignment as absolute hours (spec: percent);
  L1 forms instead of min-max; Pesch2 as consecutive-pair balance proxy.

## 2. Decision log (user, unchanged unless noted)

- D1 dataset: Pesch+.csv canonical (STILL NOT APPLIED, notebook reads Pesch.csv).
- D2 ring closure: yes, snake wraps last active week -> week 1.
- D3 c06: hard MaxW = 56 h/week via a new parameter; soft 40h stays Pesch1.
- D4 night-after-night impossible: already holds via c05 + min_rest (9h15 < 11h).
- D5 reserve = 24h work time.
- D6 Pesch3: UNBLOCKED, definition = minimize day-by-day shiftID changes.
- D7 output: WorkHours net; class columns = presence hours + PresenceHours total.
- D8 refactor wanted, was ON HOLD for Dirk's shuffle; the shuffle has now landed,
  remaining refactor items are back on the table (S8), coordinate with Dirk.
- D9 (pending team confirmation) max 2 full free days per active week; conflicts
  with pure night weeks (4 nights need 3 free days), team must confirm.

## 3. What Dirk's update changed (14e3539 -> bc8c2b6, notebook-only + params)

Improvements:
- Notebook restructured 45 -> 52 cells: one constraint per cell, markdown headers
  with LaTeX per constraint. Much more readable. functions.py/Shift.py untouched.
- Free-day collapse ROOT-CAUSED and fixed by Dirk: dict_shifts_by_class now filters
  `sh in WorkShifts` (cell 46), so freeDay has no class variable. Consequences
  (verified): a free-day island costs 1.0 change (0.5 out + 0.5 in), a free block
  costs 1.0 total regardless of length, and inserting free days AT a class boundary
  costs nothing extra (A->free->B == A->B == 1.0). Free days therefore cluster and
  gravitate to class-change points. Spec-compatible, keep this design.
- Duplicated Pesch8 cell neutralized (commented out, cell 47), can be deleted.
- Objective weights all active in parameters.csv: workers 50, pesch1 10, pesch2 30,
  minChangeOfClasses 10. W_WORKERS renamed W_NB_WORKERS. TimeLimit 90;
  MIPFocus/Symmetry commented out.
- reserve/freeDay placeholder times changed to 07:00-07:00 (cosmetic).

Regressions (both in output cell 51, both introduced by the shuffle):
- Split output: the header is written (with "w") to output_cycle_.csv (trailing
  underscore) while all data rows append to output_cycle.csv, which is never
  truncated. Result: one file with only a header, another growing stale data
  across runs.
- Python 3.10 incompatibility: nested double quotes inside a double-quoted f-string
  (`f"...{sh.split("%_%", 1)[0]}...{shift_info[sh]["start"]}..."`). Works on
  Dirk's newer Python, SyntaxError on the user's 3.10 kernel. The notebook will
  not run for the user until fixed.

Current cell map (for anchors): globals=6, shifts=9, DUMMY/pairs=11, hours=12,
model vars=16, linking=20/22/23, ordering=25, c01=27, c02=30, c03=33, c05=35,
c06=37, c07=40, Pesch1=41, Pesch2=42, Pesch8 prep=44, class vars=45, Pesch8
link+diff=46, dead duplicate=47, objective+solve=49, output=51.

## 4. Open findings (renumbered, only what is still real)

R1 (NEW, user-blocking) Output cell 51: filename split-brain + py3.10 SyntaxError.
R2 Dataset still Pesch.csv, D1 wants Pesch+ (the earlier switch was lost).
R3 reserve hours excluded: reserve sits in DUMMY_SHIFTS, so its 24h are invisible
   to Pesch1, c06, output (cells 11-12). Fix via NO_HOURS_SHIFTS.
R4 c06 vacuous: cap = 40*4 = 160 h/week, but a week holds max 7 shifts (<= 98h
   with Pesch+), so it never binds (cell 37). D3: new param max_weekly_work_hours=56.
R5 Pesch8 (cell 46): transition loop `range(1, MAX_CYCLE_WEEKS-1)` misses the last
   two weeks' transitions, so the solver can dump class chaos there for free; and
   class_diff is not gated by active_week, so the drop to an inactive week creates
   one phantom change per cycle. Coordinate with Dirk (his cells).
R6 Class collision: reserveShift shift_class=5 equals [00dayweekend] class 5; they
   merge in Pesch2 and Pesch8 categories. Becomes visible once R3 lands. Give
   reserve its own class (team confirms Beliebtheit value).
R7 Ring closure missing in c03, c05, Pesch8 (D2, spec-mandated). Technique: with
   c04 ordering, last-active-week indicator = active_week[c,w] - active_week[c,w+1]
   (0/1-valued expression, no new binaries; for w=MAX use active_week[c,MAX]).
   Gate wrap constraints with RHS relaxation `+ BigSmall * (1 - indicator)`.
R8 D9 max-2-free-days per active week: sum_d x[c,w,d,freeDay] <= 2*active_week[c,w].
   BLOCKED on team confirmation (kills pure night weeks).
R9 Hygiene: is_work_shift attribute dead (role sets hardcoded by ID); no-op astype
   calls in readShiftSet; Pesch2 BIG_M ~1858 inflates coefficient range; stray
   "\n," artifact in cell 6 comment; cell 47 dead block deletable; unused imports
   in Shift.py; weights parse int() only (int(float()) safer).
R10 Pesch2 category definition fuzzy: Dirk's "day vs late vs night?" vs current
   grouping by Beliebtheit class. Parked until the team defines Schichtkategorie.
R11 reserve-after-night currently allowed (reserve outside min-rest pairs). Open
   team question.

## 5. Tickets, in execution order (S = sprint item)

S0. Fix output cell (R1). Single filename output_cycle.csv everywhere ("w" for the
    header write, "a" afterwards), replace inner double quotes with single quotes
    for 3.10. Acceptance: notebook runs end-to-end on the user's kernel, one output
    file, fresh timestamp, no stale rows.
S1. Switch dataset to Pesch+ (R2/D1): cell 9 readShiftSet path. Acceptance: solver
    log mentions [allDay_shift]; coverage needs >= 14 weeks.
S2. Count reserve hours (R3/D5): cell 11 add NO_HOURS_SHIFTS = {freeDay id};
    cell 12 both dicts filter by NO_HOURS_SHIFTS. DUMMY_SHIFTS remains for
    min-rest pairing only. Acceptance: weeks containing reserve show +24h.
S3. Real c06 (R4/D3): parameters.csv add max_weekly_work_hours=56; cell 6 set
    MAX_WEEKLY_HOURS from it (kill the AVG*REF construction, mark
    avg_reference_weeks reserved); cell 37 unchanged. Acceptance: 4x14=56 feasible,
    24+24+10=58 infeasible in one week.
S4. Pesch8 mechanical fixes (R5), after pinging Dirk: loop over all cycleWeeks with
    d==7 guarded by w < MAX_CYCLE_WEEKS; gate both diff constraints with
    `- (1 - active_week[c, w_next])` on the RHS. Acceptance: baseline unchanged at
    weight 0; at weight 10 no chaos concentration in the last two weeks.
S5. Pesch3 (D6): generalize the Pesch8 builder instead of duplicating: one helper
    building "change variables" for a grouping dict (key: shiftID base name or
    class), used twice with weights obj_w_pesch3 / obj_w_minChangeOfClasses.
    freeDay excluded from groups exactly like Dirk's WorkShifts filter. New param
    obj_w_pesch3 (default 0). Acceptance: pesch3=0 reproduces baseline; small
    weight visibly blocks same shiftIDs together in output.
S6. Ring closure (R7/D2): apply the last-active-indicator technique to c05 (pair
    wrap Sun_last -> Mon_week1), c03 (windows crossing the wrap), Pesch8/Pesch3
    (one wrap transition per cycle). Acceptance: a night on the last active Sunday
    forces a compatible Monday in week 1.
S7. Classes and output polish (R6/D7): unique class for reserve (team value);
    output adds PresenceHours total column, class columns stay presence-based and
    named class_<k>_presence_h, comment updated (columns sum to PresenceHours).
S8. Remaining refactor (D8/R9), coordinate with Dirk: role sets from shift
    attributes (is_work_shift as single source of truth), hours/pairs builders into
    functions.py, named objective terms (term_weeks, term_pesch1, ...) right before
    setObjective, tighten Pesch2 BIG_M, delete cell 47, robust weight parsing.
    Behavior-preserving, verify identical results at fixed weights.
S9. Weight calibration session: matrix of runs (workers/pesch1/pesch2/classes),
    read the objective decomposition from the diagnostic prints, pick team default.
BLOCKED: R8 (max-2-free) on team; R10 (category def) on team; Pesch4/5 on
    "Turnusgruppe" definition; R11 reserve-after-night on team.

Team questions, one message: (1) max 2 free days/week given it kills pure night
weeks? (2) reserve directly after a night shift ok? (3) Schichtkategorie for
Pesch2: Beliebtheit class or day/late/night? (4) Beliebtheit value for reserve?

## 7. STATUS 2026-07-07 late: fix batch applied and verified by a full run

Applied directly by the assistant on user instruction (exception to rule 4 below),
executed end-to-end on the user's Python 3.10 env, all cells green:
- S0 done: output single-file (output_cycle.csv), 3.10-safe quotes.
- S2 done: NO_HOURS_SHIFTS; reserve 24h now counted (verified: a reserve week shows
  WorkHours 56.0 and c06 binds exactly at the cap).
- S3 done: c06 real, MAX_WEEKLY_HOURS from new param max_weekly_work_hours=56.
- S4 done: Pesch8 loop covers all weeks, transitions gated by active_week.
- S6 done: RING CLOSURE cell added (c05 + c03 + Pesch8 across the wrap),
  last-active-week indicator technique, heavily commented.
- NEW c08: max_free_days_per_week=2 per active week (user decision; pure night
  weeks intentionally impossible).
- NEW: night -> reserve forbidden (explicit incompatible pairs; joker argument).
- S7 output part done: PresenceHours column + class_<k>_presence_h columns
  (sum verified). Class value for reserve still pending team (collision remains).
- Knock-on fixed: Pesch2 class map now includes reserve (was KeyError after S2).
- D1 REVERSED by user: dataset stays Pesch.csv. S1 cancelled.
- S5 (Pesch3) NOT implemented yet: next step after this batch is reviewed.
Observed run (weights 50/10/30/10, TimeLimit 90): 27 active weeks, 192h total
deviation, only 1 week exactly on 40h, gap 25.6%. Interpretation: c08 forces >= 5
work days into every active week while W_PESCH1=10 is weak, so overtime is cheap.
This is weight calibration (S9), not a bug. Discuss target weights with the team.

## 6. Skills for the assistant (how to work, distilled from this project)

1. Verify-first: before ANY claim or edit, dump the actual cells
   (python3 json dump, grep markers). Chat history, memory and this file are
   hints; the notebook is the truth. Cell numbers drift after every merge.
2. Delivery format: exact Ctrl+F anchor (an existing unique line) + full
   replacement/insert block + one line of why. No line numbers. English code
   comments, no em-dashes anywhere, dry tone, Russian chat.
3. One block at a time. After each block: user saves (Ctrl+S!), Restart & Run All,
   pastes output; only then the next block. A stale unsaved cell already produced
   a false bug report once.
4. NEVER edit project files yourself except the two docs (AUDIT.md, TODO_ARTY.md).
   The user learns by applying changes himself.
5. Gurobi literacy: Params before optimize(); SolCount>0 guard; TimeLimit ->
   status TIME_LIMIT; big gap = weak bound, not bad schedule; explain trade-offs
   with the printed decomposition (weeks / dev hours / imbalance / changes), not
   adjectives. Weights are ratios; 0 disables.
6. Domain sanity checks before proposing: min-rest arithmetic (night->night 9h15
   forbidden), 40h packings (5x8, 4x10, with Pesch+ 4x10-day), coverage lower
   bounds (slot-days / 7). Run the numbers, do not assume.
7. Git: commit only cyclePlanning.ipynb, input/*.csv, src/*.py, the two docs.
   Never git add -A (junk: .pyc, .vscode, logs, output). Push only on request,
   English commit messages. Generated files (logs/output/pyc) block merges:
   discard with git checkout -- <paths>, in VS Code pick "Discard tracked" not all.
8. Team etiquette: Dirk owns Pesch8 cells and dataset values; propose, flag for
   sync, never silently rewrite. Check git log for his parallel work before edits.
9. Self-correction culture: when the primary source contradicts an earlier idea,
   say so explicitly and update the plan (happened twice: off-day clustering,
   free-day transparency). Never defend a stale position.
10. Every claim of "works" requires: solver log + diagnostic prints + a look at
    output_cycle.csv. No exceptions.
