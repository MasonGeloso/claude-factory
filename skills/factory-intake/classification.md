# Factory — Classification Framework

The standard scheme is a **2D grid**: a **T** (priority / urgency) and an **E** (complexity / autonomy) for each item. They are independent — a T-level says *when it matters*, an E-level says *how hard and how hands-on it is*. **T does not imply size.**

A project may **opt out** entirely and declare a simpler scheme in its `factory/intake.md` (e.g. a simple automation that just creates every issue with a flat priority). When it does, follow that — this grid is the default, not a mandate.

## T — Priority / urgency

Frame it as a product launch:

- **T1** — Absolute blockers. Paper-cuts, bug fixes, things immediately blocking. *Must* be done before launch.
- **T2** — Imminent and important, but not a hard blocker. Could land around the launch, during it, or slightly after. The bucket for normal initiatives.
- **T3** — Amorphous or lower priority. Future / "big someday" initiatives, nice-to-haves.

## E — Complexity & autonomy

How much human involvement the work realistically needs if an engineer hands it to an AI agent (Claude Code, Cursor, an agent factory, etc.):

- **E1** — Most complex, most hands-on. Needs a very well-defined spec with tight requirements. An agent might build the whole thing, but it must be heavily reviewed, double-checked, and QA-tested. A human has to be in the loop.
- **E2** — The middle. A semi-well-defined spec is enough; hand it to an agent, then give the QA video a watch, scan the diff, confirm nothing was introduced. Medium effort, somewhat hands-off.
- **E3** — Fully hands-off. A straightforward paper-cut you already know is trivial. Submit to an agent, barely review, probably auto-mergeable.

## Using it

- Every item gets one T and one E, e.g. `T1/E3` (a blocking but trivial fix) or `T2/E1` (an important, gnarly, spec-heavy initiative).
- Determine T from the dump's urgency cues; determine E from the lightweight research pass (poke the code/services to gauge how hard and how reviewable it is).
- Reclassify freely during research — first guesses from the transcript are cheap.
- **Map T/E to the tracker's reality** using `factory/intake.md`: which labels/fields encode T and E, and which combos become epics vs. issues vs. spikes. For example, low-priority + fully-autonomous combos (e.g. `T2 or lower` + `E3`) might be wired to an automation that lets an agent pick them up and self-merge.
