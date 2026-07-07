# AUDIT & TICKETS: cyclePlanning.ipynb (Snake Building)

Date: 2026-07-07. Audited: all 45 notebook cells, src/functions.py, src/Shift.py,
parameters.csv, input_ShiftDataSet_Pesch.csv, input_ShiftDataSet_Pesch+.csv, and the
primary sources in docs/ (TuMuPl-Beschreibung_cleanedUp.docx, definitions.docx,
Input-Daten.docx). This file is the working plan for the assistant and the team.
Execution rule: work in small blocks, the user applies every change himself and runs
the notebook between blocks. No from-scratch rewrite, evolve what exists.

---

## 1. Primary-source facts (professor's spec) that bind our decisions

- A snake is CYCLIC: "the last shift in the snake ... and the shift at the very first
  snake position must also observe their required time constraints". So rest and
  consecutive-day rules must wrap from the last active week back to week 1.
- MaxW is a HARD per-subsequence (per-week) cap on work hours, "the same for all
  snakes and all subsequences".
- Shift-jump minimization "also includes that off days should be in consecutive
  sequence". Off days are supposed to cluster. Therefore freeDay MUST stay a countable
  class/type in jump objectives; do not make it transparent.
- Class jump minimization (Pesch8) and class-share distribution (Pesch2) are two
  different spec objectives: Pesch8 works along the day sequence (time), Pesch2
  compares class mix between snakes (space). Both are legitimate, no duplication.
- Spec's class-share objective compares each snake's class share to the GLOBAL share
  p_i of that class in the whole dataset (min-max form). Our Pesch2 (consecutive-pair
  balance) is an accepted linear proxy; documented deviation.
- Spec's average-work-time objective is per-snake average vs target D (min-max, with
  an allowed "sums" extension). Our Pesch1 is stricter: per-week L1 deviation from D.
  Team-accepted deviation; keep.
- Max consecutive workdays: after the bound, at least one off day. Our c03 sliding
  window (<= 5 work days in any 6-day window) implements exactly this on a global
  timeline; only the ring wrap is missing.
- Jump shifts in the spec are per-shift copies scaled by an absence rate (e.g. 1.2m).
  Our single static reserveShift is a simplification; fine for now.
- Spec defines work_time_assignment as percent per subshift; the team reinterpreted it
  as absolute hours. Accepted team deviation (the dataset is self-invented anyway).

## 2. Decision log (Artjom, 2026-07-07)

- D1: canonical dataset = input_ShiftDataSet_Pesch+.csv (with 24h allDay shift).
- D2: the snake is a closed ring; wrap-around must be enforced (c03, c05, Pesch8).
- D3: c06 becomes a hard cap MaxW = 56 h/week (new parameter). The soft ~40h target
  stays with Pesch1 (obj_w_pesch1).
- D4: night after night must be impossible. Already guaranteed by c05 + min_rest=660
  (night->night rest is 9h15m). The ring extension closes the last gap.
- D5: reserveShift counts as work time (24h). Standby is not free time.
- D6: Pesch3 is ON HOLD (no team answer on its meaning). Do not implement.
- D7: output semantics: WorkHours = net work hours per week; class columns show the
  time spent per shift class that week in PRESENCE hours, plus a PresenceHours total
  column so the class columns visibly sum to it.
- D8: big refactor wanted: group parameters, shift preparation, model, objectives;
  tidy the objective into named terms; delete dead code; the notebook must read like
  carefully written human code. Behavior-preserving.

## 3. Findings (verified against the current code)

F1  (resolved by D1) The notebook currently reads input_ShiftDataSet_Pesch.csv; the
    user's switch to Pesch+ was lost during a force checkout. Must be redone.
F2  c06 is vacuous: cap = AVG_WEEKLY_HOURS * AVG_REFERENCE_WEEKS = 160 h per single
    week, but c02 allows at most 7 shifts/week (max 7x14 = 98 h with Pesch+ data,
    70 h with Pesch), so the constraint can never bind. Fix per D3.
F3  night->night and night->day are already forbidden by c05 (rest 9h15m / -1h vs
    660 min). Consequence: consecutive identical night blocks are IMPOSSIBLE with this
    data; jump minimization mostly shapes day shifts and off-day blocks. Open team
    question: reserveShift is excluded from min-rest pairs, so reserve directly after
    a night shift is currently allowed. Decide if that is acceptable.
F4  Class collision: reserveShift has shift_class 5, same as [00dayweekend] (in both
    datasets). Pesch2 and Pesch8 treat them as one category. Give reserve its own
    class value (suggest an unused one, e.g. 4 or 6; team confirms Beliebtheit).
F5  The model is a LINE, not a RING: c03, c05 and Pesch8 all stop at the last week.
    Spec requires the wrap (see section 1). Fix in Phase C.
F6  Output units are mixed: class columns multiply shift_hours (presence) but iterate
    work_hours keys, and the header comment still claims the columns sum to WorkHours.
    Fix per D7.
F7  Shift.is_work_shift is dead: constraints use three parallel hardcoded ID sets
    (WorkShifts, DUMMY_SHIFTS, hours-dict keys). This caused the reserve-hours bug.
    Make shift attributes the single source of truth (Phase B).
F8  Pesch8 transition loop: `for w in range(1, MAX_CYCLE_WEEKS-1)` covers w = 1..16
    (with 18 weeks). Missing: within-week transitions of weeks 17 and 18, and the
    17->18 boundary. Why it matters: the objective undercounts changes near the cycle
    end, so the solver can dump all its class chaos into the last two weeks for free.
F9  Pesch8 class_diff is not gated by active_week: the transition from the last
    active day into the first inactive week produces one phantom class change per
    cycle (class_assigned drops to all zeros there).
F10 reserveShift hours are excluded from shift_hours/work_hours because reserve sits
    in DUMMY_SHIFTS. Its 24h are invisible to Pesch1, c06 and the output. Fix designed
    (NO_HOURS_SHIFTS), not yet applied.
F11 The free-day collapse Dirk observed (any positive class weight floods the plan
    with free days) must be re-reproduced AFTER F8/F9 are fixed. Per spec, off-day
    clustering is desired, so the cure is weight calibration, not removing freeDay
    from the count. Note: with weeks minimized, the number of free days is nearly
    fixed (7*active_weeks - required work slots); they can only move, not multiply,
    unless weeks grow. If the collapse persists, check the weights ratio first.
F12 Minor hygiene: no-op astype calls in readShiftSet; unused imports (field, pandas)
    in Shift.py; stale comments (cell 9 "created below", cell 13 "no real duration");
    redundant Link_x_activeWeek constraints (c02 already implies the linkage);
    Pesch2 BIG_M ~1858 inflates the coefficient range (tighten to a realistic
    category-hours bound); weight parsing crashes on non-integers (use int(float()));
    unused class_diff variables for d=7 in the last week (harmless);
    definitions.docx describes the old per-week c03 (outdated doc).

## 4. Tickets, in execution order

### Phase A: correctness quickies (small, independent, run after each)

A1. Switch dataset to Pesch+.csv (D1/F1).
    Touch: cell 9, readShiftSet path. Acceptance: solver log shows the allDay shift;
    coverage now needs >= 14 weeks (94 slot-days/week over 7).
A2. Count reserve hours (D5/F10).
    Touch: cell 12 add NO_HOURS_SHIFTS = {freeDay}; cell 13 both dicts filter on
    NO_HOURS_SHIFTS instead of DUMMY_SHIFTS. DUMMY_SHIFTS stays for min-rest pairing
    only. Acceptance: a week containing reserve shows +24h in WorkHours.
A3. Make c06 real: MaxW = 56 (D3/F2).
    Touch: parameters.csv new row max_weekly_work_hours=56; cell 6 read it as
    MAX_WEEKLY_HOURS (drop the AVG*REF construction; mark avg_reference_weeks as
    reserved/unused or remove); cell 32 unchanged otherwise. Acceptance: constraint
    can bind (e.g. 4x14=56 allowed, 24+24+10=58 rejected); objective/weeks may shift.
A4. Pesch8 mechanical fixes (F8/F9), coordinate with Dirk before editing his cells.
    Touch: cell 40. Loop over all cycleWeeks; d<=6 -> (w, d+1); d==7 guarded by
    w < MAX_CYCLE_WEEKS -> (w+1, 1). Gate both diff constraints with
    "- (1 - active_week[c, w_next])" on the RHS to kill phantom boundary changes.
    Keep the 0.5 double-count factor, it is correct.
    Acceptance: with obj_w_minChangeOfClasses=0 results match pre-fix baseline; with
    a small weight (2..10) the schedule must NOT collapse into free days (F11); if it
    still does, capture the log and stop for analysis.

### Phase B: refactor (D8/F7/F12), staged, behavior-preserving

B1. Single source of truth for shift roles: derive WorkShifts, NO_HOURS_SHIFTS and
    the min-rest exclusion set from Shift attributes (is_work_shift, a new
    has_real_times flag or the placeholder-time convention), not from hardcoded ID
    strings. freeDay/reserve construction moves next to the CSV load, clearly marked.
B2. Move reusable pure logic into src/functions.py (e.g. hours-dict builders,
    incompatible-pairs builder, the global-day decoder); notebook keeps only model
    assembly. Kill the no-op astypes, unused imports, stale comments, dead code
    blocks (old cycle-level Pesch1, old c05 wrap, old output block).
C3 (sic, part of B): tidy the objective: build named LinExpr terms
    (term_weeks, term_pesch1, term_pesch2, term_class_changes) right before
    setObjective, then one readable weighted sum. Tighten Pesch2 BIG_M to
    max category hours (e.g. MAX_CYCLE_WEEKS * 7 * max presence) per category or a
    tabulated bound. Robust weight parsing int(float(...)).
    Acceptance for all of B: identical (or explainably equivalent) solver results
    at the same weights, notebook reads top-down: params -> data -> model -> solve
    -> report.

### Phase C: ring closure (D2/F5), after B so it lands on clean code

C1. Technique: with c04 ordering, last-active indicator for week w is the expression
    (active_week[c,w] - active_week[c,w+1]) for w < MAX, and active_week[c,MAX] for
    the last index; it is 0/1-valued and needs no new binaries.
C2. c05 ring: for each incompatible pair (sh1, sh2) and each candidate last week w:
    x[c,w,7,sh1] + x[c,1,1,sh2] <= 2 - active_week[c,w] + active_week[c,w+1]
    (RHS = 1 exactly when w is the last active week). ~8 pairs x 18 weeks x 3 cycles,
    cheap.
C3. c03 ring: extend the sliding window across the wrap: windows that use the last
    k days of the last active week and the first 6-k days of week 1, gated by the
    same last-active expression (add the gate times MAX_CONSEC_DAYS to the RHS).
    More constraints, still linear.
C4. Pesch8 ring: one wrap transition per cycle: class_diff for (last active Sunday)
    vs (week 1, Monday), gated identically. Also covers off-day block continuity
    across the wrap.
    Acceptance: schedules where week-1 Monday conflicts with last-week Sunday
    disappear; night on the last Sunday forces Monday week-1 to be free/compatible.

### Phase D: classes and output polish

D1t. Give reserveShift a unique shift_class (F4), team confirms the Beliebtheit
     value. Touch: cell 9 constructor arg. Acceptance: Pesch2/Pesch8 categories no
     longer merge reserve with the weekend day shift.
D2t. Output per D7/F6: keep WorkHours (net); add PresenceHours total column; class
     columns in presence hours named class_<k>_presence_h; fix the stale comment;
     iterate shift_hours keys for the class sums. Acceptance: class columns sum to
     PresenceHours exactly.

### Phase E: waiting / blocked (do not start)

E1. Pesch3 (type-change minimization): blocked on team definition (D6). When
    unblocked: generalize the Pesch8 machinery (grouping key = shift type or class),
    one constraint builder, two weights. Note F3: night blocks are infeasible, type
    blocks apply to day shifts and off days.
E2. Pesch4/Pesch5: blocked on the undefined "Turnusgruppe" vs "Turnusauswahl".
E3. Pesch6/Pesch7 (weekend / night distribution): straightforward reuse of the
    Pesch2 pattern restricted to weekend or night shifts; wait for priorities.
E4. Optional spec alignment: min-max variants of Pesch1/Pesch2 (spec letter) as an
    alternative to the L1 forms; only if the professor asks.
E5. Team question: should reserve directly after a night shift be allowed
    (currently yes, reserve is outside min-rest pairs)?

## 5. Working rules for the assistant

1. User writes Russian -> answer Russian. Code, comments, commits: English.
   No em-dashes. Dry, concrete, no filler.
2. NEVER edit project files directly. Deliver: exact Ctrl+F anchor (an existing
   line) + replacement/insert block + one line of why. No line numbers. One block
   at a time; wait for the user's run output before the next.
3. The notebook is JSON. Verify actual state by dumping cells with python3/json
   before claiming anything about the code. Check applied fixes by grepping for
   markers (e.g. NO_HOURS_SHIFTS). Chat history and memory are hints, not truth.
4. Remind the user: Ctrl+S the notebook, then Restart & Run All. A stale cell
   already burned us once.
5. Gurobi: set Params BEFORE optimize(); output guard is SolCount > 0; a large MIP
   gap means a weak bound, not a bad schedule; the incumbent usually arrives in
   seconds. TimeLimit 10-60s is the working range here.
6. Weights are ratios (100/100 == 50/50); 0 disables a term. When tuning, show the
   objective decomposition (weeks / dev hours / imbalance / changes) from the
   diagnostic prints.
7. Git: commit only cyclePlanning.ipynb, input/*.csv, src/*.py, this AUDIT.md.
   Never git add -A. Push only when asked. English commit messages.
8. Dirk owns the Pesch8 cells (39-40) and Pesch+ dataset values; propose changes,
   flag them for team sync, do not silently rewrite.
9. No success claims without a run: solver log + diagnostic prints + a peek at
   output_cycle.csv.

---

## UPDATE 2026-07-07 (late), after Dirk's replies. Overrides earlier sections where they conflict.

U1. Pesch3 UNBLOCKED. Dirk's definitions (verbatim): Pesch2 = equal distribution of
    shift categories (day vs late vs night?); Pesch3 = minimize day-by-day changes of
    shift TYPES, i.e. try to keep the same shiftID on consecutive days; Pesch8 = same
    but for shift CLASSES (convenience rating). So Pesch3 is the shiftID-level twin of
    Pesch8: one shared constraint builder, grouping key = shiftID or class, two
    weights. E1 becomes actionable after the code shuffle (U3).

U2. Pesch2 category caveat: Dirk's own "day vs late vs night?" carries a question
    mark. Current implementation groups by shift_class (Beliebtheit). If the team
    later defines categories as day/late/night, grouping needs its own field, not the
    class. Park until the team decides; do not rework now.

U3. Dirk will "shuffle the code", high merge-conflict risk, and asked for a complete
    push by 5pm. Consequences: (a) everything meaningful is pushed now, including this
    file; (b) Phase B (our refactor) is ON HOLD until his shuffle lands, then pull and
    RE-AUDIT anchors (cell numbers in this file will drift); (c) Phase A starts only
    after pulling his shuffled main.

U4. Off-day clustering demoted from "spec-mandated" to SOFT preference: it emerges
    from the Pesch3/Pesch8 objectives (freeDay->freeDay = no change) and is NOT a
    hard rule. The user's actual hard rules: max 5 consecutive work days (c03,
    exists) and max 2 full free days per active week (NEW, see U5). freeDay stays
    countable inside jump objectives per spec.

U5. NEW TICKET A5 (needs team confirmation before implementing): at most 2 freeDay
    assignments per active week: sum_d x[c,w,d,freeDay] <= 2 * active_week[c,w].
    WARNING, structural conflict: pure night weeks (4 nights = 40h) need 3 free days
    because nights cannot be adjacent (min rest 9h15 < 11h). Under a max-2-free rule
    such weeks become infeasible and nights must mix with day/reserve shifts, e.g.
    night-reserve-night patterns; note reserve directly after a night is currently
    allowed (open question E5) and reserve adds 24h toward the 56h cap. Confirm with
    the team that this consequence is intended before adding the constraint.

U6. Priority of open team questions: (1) U5 max-2-free-days consequence for night
    weeks; (2) E5 reserve-after-night allowed or not; (3) U2 category definition for
    Pesch2; (4) reserve Beliebtheit class value (F4).
