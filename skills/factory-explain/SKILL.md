---
name: factory-explain
description: Explain a just-finished run in plain English to someone who has zero context on it — what got built (before → now), which decisions were made without asking, what was deliberately skipped or is still owed, what new work turned up, and where the demo video and screenshots are. Ad-hoc and read-only; normally run by the user right after a run says "here's the PR, it's ready". Use when the user says "factory explain", "explain this run", "what did you actually do", "tldr this", "I have no context on this", or asks what a finished PR/issue actually changed.
user-invocable: true
---

# Factory — Explain

*Somebody who was not watching is about to decide whether to trust this run. Tell them what happened,
in words they already know, in one screen.*

This skill is **read-only**. It reports on a run — it never continues it, never fixes what it finds,
never pushes anything. If you spot a problem while writing, it goes in the report as a finding.

---

## Who you are writing for

The reader has ten other agents running right now. They did not read your messages. They do not
remember the issue title, the plan, or any word you coined while working. They will give this 60
seconds, and they are reading it to answer one question: **did this run do anything stupid?**

So:

- **They have zero context.** Not "some context". Zero. Re-state everything, including the question
  the run was answering.
- **They are interrogating, not admiring.** The valuable part of this report is the decisions you made
  on your own and the things you did not do. Lead with substance, not with a victory lap.
- **They will click things.** File paths, the PR link, the video, the screenshots — give them, in full,
  at the bottom.

---

## Step 1 — Gather the evidence (never write this from memory)

Even when you ran the work yourself in this same session, **your memory of the run is a claim, and the
diff is the fact.** Where they disagree, the diff wins and you say so.

Collect, in this order — skip a source only if it genuinely does not exist:

| Source | How | What it gives you |
|---|---|---|
| The diff | `git log --oneline <base>..HEAD`, `git diff <base>...HEAD --stat`, then read the real diff of the biggest files | what actually changed |
| The task | the tracker CLI in `factory/intake.md` — issue body **and every comment** | what was actually asked |
| The plan | the markdown file in `./tasks/` | what was intended, and what it flagged as undecided |
| The PR | description + any review comments | what was claimed, what reviewers pushed back on |
| The QA report | the QA comment on the issue and its verdict | whether anyone used it |
| Demo artifacts | the demo output dir (`factory/deployment.md` → *Demo output dir*): `.webm`, `.png`, `artifacts.md` | what you can show them |
| Leftovers in the diff | `git diff <base>...HEAD \| grep -nE 'TODO\|FIXME\|XXX\|HACK\|not implemented\|for now\|placeholder'` | skipped work you may have forgotten you skipped |
| New deps & constants | new entries in `package.json` / `pyproject.toml` / lockfiles, new magic numbers, new config keys, new env vars | decisions nobody approved |
| New issues | tracker query for issues created during the run (by you, in this window) | follow-up work you filed |

`<base>` is the branch the PR targets — `gh pr view --json baseRefName` if there is a PR, otherwise
`git merge-base HEAD origin/main`. Getting this wrong is the most common way this report ends up
describing somebody else's commits, so check the commit list looks like this run before you use it.

Run cold (no session context) exactly the same way — pointed at a PR URL, issue id, or branch, every
one of those sources is still reachable. There is no version of this skill that guesses.

**Rule: every bullet in the report traces back to one of those sources.** Anything you believe but
could not confirm gets the word **unverified** on the same line. Do not quietly drop it and do not
quietly assert it.

---

## Step 2 — Write the report

Fixed sections, this order. Write `None.` under a section that is genuinely empty — **never delete a
section**, because a missing section reads as "nothing to report" and the reader can't tell the
difference between that and you forgetting.

### 1. In one line

What is different now for someone using this thing. One sentence, no clause about how you did it.

> The report page now loads for accounts with no data instead of showing a blank screen.

### 2. The question and the answer *(only if the run was an investigation, spike, evaluation, or a "should we X?")*

Required whenever the run concluded something rather than shipped something. Two parts, in this order:

1. **The question, restated in full.** Not "your original question" — the actual question, written out
   as the reader would have asked it.
2. **The answer**, in one sentence, plus the evidence it rests on and how confident you are.

> **Question:** should we use the small open-source translation model instead of paying per call for
> the API one?
> **Answer:** no. On 20 real product sentences, 7 came back with wrong or invented terms. The cost
> saving was real (about 90% cheaper), but the quality is not usable for customer-facing copy.

Never write a conclusion whose subject is a thing the reader has to go look up. Never write "it fails
the bar" — say what the bar was and what the number was.

### 3. What was built

Bullets. Each one is **before → now**, in that shape, plus where it lives:

```
- **<plain-English name for the thing>** — Before: <what happened, or "did not exist">. Now: <what
  happens>. (`path/to/file.ts`)
```

Six bullets maximum. If there were more changes, pick the six that a person would notice and end with
`+N smaller changes (tests, types, config)`. Behavior over structure: "you can now filter by date" is a
change; "extracted a helper" is not, unless the helper is the whole point of the task.

### 4. Decisions I made without asking you

**This is the section the report exists for.** Every place the task was silent or ambiguous and you
picked a direction anyway. Go find them — do not just recall them. They hide in:

- new constants, limits, timeouts, page sizes, thresholds, retry counts
- new dependencies and new config/env keys
- names you invented for anything user-visible (routes, fields, labels, flags)
- error handling: what happens on failure was almost never specified
- data shape choices (a new column vs. a JSON blob, a new table vs. reusing one)
- anything the plan file marked TBD / "decide later" and the code now decides
- scope calls: something in the issue you interpreted narrowly or broadly

Format, one per decision:

```
- **<the choice, in plain words>.** The task didn't say, so I <what I did>. The alternative was <the
  other option>. Reversing it: cheap / medium / expensive.
```

If you write a decision so vaguely that the reader could not disagree with it, it is useless — rewrite
it until disagreeing is possible.

If there were genuinely none, say `None — every choice here was specified in the issue or its comments.`
That is a rare claim; be sure before making it.

### 5. What I did NOT do

Three labeled buckets. Keep them separate — they mean very different things:

- **Still owed** — in the original spec/issue, still not done. This is a promise outstanding. Say why.
- **Deliberately skipped** — I chose not to, and here is the reason.
- **Out of scope** — I decided this belonged to a different task, and here is where it went (issue
  number, or "not filed").

### 6. New work I found

Anything you noticed along the way that isn't part of this task: bugs, dead code, a broken neighbor, a
thing that will bite later. For each: one line on what it is, one clause on why it matters, and whether
you **filed it** (with the issue number) or **did not file it**. If you fixed something that wasn't
asked for, it goes here, not in "What was built" — unrequested changes are exactly what the reader is
scanning for.

### 7. Check it yourself in two minutes

The shortest real path for the reader to see it working themselves:

- the PR link
- the one command that brings it up (from the provisioning docs — the re-provision one-liner if there
  is one)
- the URL/page to open, or the exact command to run
- the one thing to click or type to see the change

### 8. Artifacts

Full file paths, one per line, each with a short caption, so they can be clicked straight out of the
terminal. Videos first, then screenshots, then documents:

```
- Demo video       /abs/path/demos/date-filter/date-filter-demo.webm — full walkthrough, 1m20s
- Screenshot 01    /abs/path/demos/date-filter/01-empty-state.png — the empty state that used to be blank
- Screenshot 02    /abs/path/demos/date-filter/02-filtered.png — filtered to last 7 days
- Screenshot 03    /abs/path/demos/date-filter/03-mobile.png — same page at 390px
- QA report        <issue comment url>
- Plan             /abs/path/tasks/2026-09-08-date-filter.md
```

Read the demo output dir for real (`ls -1` it) rather than reciting what you think you wrote, and if
the demo skill left an `artifacts.md` manifest, use its captions. Include the QA screenshots too, if
QA put them somewhere other than the demo dir. **Paths must be absolute** — a
relative path is not clickable from wherever the reader is sitting. If a file you name does not exist,
remove the line; a dead path costs you the reader's trust in the whole report.

End the section with the one command that opens all of them at once (e.g. `xdg-open <dir>` on Linux,
`open <dir>` on macOS) for a terminal that doesn't linkify paths.

---

## The language rules

This is the actual product. A correct report written in run-jargon is a failed report.

- **No word you invented during the run.** If you named a mode, a phase, a score, a "bar", a "gate", a
  "lane" — use ordinary words instead, or define it inline in five words the first time and never
  again.
- **Never point at a thing the reader has to remember.** "your original question", "the ask", "the
  bar", "the pipeline", "the flow", "as discussed" — all forbidden unless the same sentence restates
  what it was.
- **Gloss every name.** Models, services, repos, internal tools, file names, acronyms: `cat-translate-7b
  (the small open-source translation model)`. Say what the thing is, then its name.
- **Numbers, not adjectives.** "7 of 20 sentences came back wrong" beats "fails the quality bar".
  "Loads in 400ms instead of 4s" beats "much faster".
- **No status theater.** "Successfully implemented a robust solution", "comprehensive coverage",
  "production-ready" — these carry no information. Delete them.
- **No headline that isn't one.** Do not open with "the honest headline" or "TL;DR" and then not give
  the actual summary in that sentence.
- **Plain sentences.** Short. One idea each. If a sentence needs a comma-and-a-clause to survive, it is
  two sentences.
- **Bad news first, plainly.** If the run went badly, if QA failed, if you are not confident it works —
  that is line one, not a footnote. Reporting a shaky run honestly is worth more than a clean-sounding
  one.

**Length ceiling:** sections 1–7 fit in one screen. Roughly 400 words. No section over six bullets. The
artifacts list does not count against it.

---

## Step 3 — Self-check before you print

Do these four passes. They take a minute and they are the difference between this and a wall of text.

1. **Stranger pass.** Read it as someone who has never seen this repo. Every noun that isn't ordinary
   English gets defined or deleted. Every "the X" gets a check: does the reader know what X is?
2. **Diff pass.** Take each "What was built" bullet back to the diff. Is it actually in the committed
   code? Anything you cannot find, mark **unverified** or cut it.
3. **Disagreement pass.** Read section 4 as a hostile reviewer. Could you push back on any of these
   decisions? If not, they're written too vaguely to be useful — sharpen them.
4. **Path pass.** `ls` every file path you printed. Dead paths get removed.

---

## Delivery

Print it in the chat. Do not post it to the tracker, do not comment on the PR, do not commit it —
unless the user asks. This is a briefing for one person, not an artifact of the run.

If the user asks a follow-up on any bullet, answer it from the evidence you already collected. Do not
start fixing things unless they say to.

---

## Worked example (shape, not content)

```
**In one line:** the weekly report email now sends to people who joined mid-week, instead of silently
skipping them.

**What was built**
- **Who gets the email** — Before: only accounts created before Monday were included. Now: anyone
  active during the week is included. (`jobs/weekly_report.py`)
- **A guard against double-sends** — Before: a retry could email the same person twice. Now: each
  send is recorded and skipped on retry. (`jobs/send_log.py`)
- +4 smaller changes (tests, a migration, config)

**Decisions I made without asking you**
- **What "active" means.** The issue didn't say, so I used "logged in at least once during the week".
  The alternative was "any account not cancelled", which would have roughly tripled the send volume.
  Reversing it: cheap, it's one query.
- **Retry window of 24 hours.** Nothing specified this. I picked 24h because the job runs daily.
  Reversing it: cheap, one constant in `jobs/send_log.py`.

**What I did NOT do**
- Still owed: the issue asks for a per-account opt-out; I did not build it. It needs a settings UI
  and that wasn't scoped here.
- Deliberately skipped: backfilling last week's missed emails. Sending old reports seemed worse than
  not sending them, but that's your call.
- Out of scope: the email template itself is unchanged, filed as #482.

**New work I found**
- The send job has no alerting — if it fails at 3am nobody finds out until Monday. Filed as #483.
- `jobs/legacy_report.py` is dead code, nothing calls it. Not filed.

**Check it yourself in two minutes**
- PR: <url>
- `dev up reports`
- Run: `python -m jobs.weekly_report --dry-run --week 2026-09-01`
- It prints the recipient list; the mid-week signups are the new names in it.

**Artifacts**
- Demo video    /home/…/demos/weekly-report/weekly-report-demo.webm — full run, 50s
- Screenshot 01 /home/…/demos/weekly-report/01-recipients.png — dry-run recipient list
- Screenshot 02 /home/…/demos/weekly-report/02-send-log.png — the retry guard in the log
- QA report     <issue comment url>
```
