---
name: factory-marketing-onboard
description: Interactive, hands-on onboarding for the marketing pillar — sets up `factory/marketing/platforms.md`, `schedule.md`, and one file per content type under `content-types/` (plus its index). Unlike the rest of Factory's onboarding, this is not a batch of upfront questions — after a short setup interview (which platforms, account/brand basics), it walks through building the user's FIRST real piece of content together, step by step, and files what it learns into the right doc as it goes. Ends by offering to add the new content type to the schedule and install the `marketing-post` cron agent. Entirely optional — a repo can say "no marketing here" and nothing about this pillar gets touched. Use when `/factory-onboard` reports the marketing module missing, when the user runs `/factory-marketing-onboard` directly, or says "set up marketing for this repo", "onboard posting", "I want to automate my content".
---

# Factory — Marketing Onboarding (do-it-together, not a form)

*Set up the marketing pillar by actually building something with the user, not by interviewing them
about a system that doesn't exist yet.*

This is the onboarding source for the `marketing/platforms.md`, `marketing/content-types/` (one file
per content type, plus its index), and `marketing/schedule.md` modules in `factory-onboard`'s
registry. If `factory-onboard` routes here because one of those is missing, or the user invokes this
directly, run the whole flow below — it's one contiguous session, not three separate interviews.

> **This is optional, and skippable with zero side effects.** If the user says this repo has no
> marketing/content-posting need, tell `factory-onboard` to mark the module skipped and stop here.
> Nothing gets installed, no cron agent gets scheduled, no `factory/marketing/` directory gets
> created.

---

## Phase 1 — Short setup interview

Ask in one or two small batches (AskUserQuestion where it fits):

1. **Which platforms** does this project post to? For each: account/handle, and — critically — **is
   there more than one account/project on this machine that could be confused with this one?** (If
   yes, the account-switch check in `platforms.md` is not optional decoration — say so plainly and
   make sure it names exactly what to check.)
2. For each platform named, does a **built-in starter** exist in
   `factory-marketing-onboard/starters/` (currently: `x-post.md`, `x-article.md`, `youtube.md`)? If
   so, seed that platform's section in `platforms.md` from the starter. If not, note it as "mechanics
   TBD — will be learned during Phase 2 if we build something for it now, otherwise left for a future
   session."
3. Brand/tone basics: any global tone rules across all platforms before per-platform/per-content-type
   overrides apply? Which language(s) does this project post in — this decides whether
   `factory-humanizer` gets invoked in `en`, `ja`, or both, depending on content.
4. Credentials: env var names only (never values) for anything beyond an already-logged-in Chrome
   session.

Write a first-draft `factory/marketing/platforms.md` from this (from the template + any starters).

## Phase 2 — Build the first piece of content together

Ask: **"What's one real piece of content you want to make right now?"** Get them to describe it in
their own words — the data source, the shape, where it's going. Then **actually do it, together,
step by step**, narrating what you're doing and why.

While doing it, **stop and ask where each new thing you learn belongs**, rather than guessing:

- Something true of *this specific content type, regardless of platform* → a bullet in its own file
  under `content-types/` (the "build steps").
- Something true of *this platform, regardless of content type* → a bullet in its `platforms.md`
  section (or an addendum to the starter, if one exists).
- Something that's really a global rule (tone, a hard "never do X") → the relevant global section.

Work through the real thing end to end: build it, and if the platform/content type has a
`draft-only` default, stop at the draft and don't publish without an explicit go-ahead for this
specific piece — same rule the shipped platform starters already state.

By the end of Phase 2, `content-types/<content-type-id>.md` should exist as one real,
concretely-written file (not a templated stub, and not folded into any other content type's file)
for the content type just built, added as a row in `content-types/README.md`'s index, and
`platforms.md` should be filled in with anything learned live that the starter didn't already cover.

## Phase 3 — Offer the schedule

Ask: **"Do you want this on a recurring schedule, or is this an on-demand thing you'll trigger
yourself?"**

- **On-demand:** mark it `on-demand` in this content type's own file under `content-types/`. Nothing
  more to do — stop here.
- **Scheduled:** add a row to `schedule.md` per the notes in that template (window, cap, min-gap,
  jitter, pacing, gate type — walk the user through each field rather than guessing values; these
  numbers are exactly the kind of thing that's cheap to get wrong and expensive to fix after an
  account has already misbehaved in public). Then ask if they want the cron agent installed now:
  ```
  factory agents install marketing-post /path/to/repo
  ```
  Only run this with explicit confirmation — installing a cron agent is a standing, recurring,
  autonomous action on a real account and should never happen implicitly.

## Recon before writing, always

Use the project's real tools to verify rather than guess: check the account actually exists and is
reachable, check any data source named in Phase 2 actually returns something, read any existing
docs/READMEs the project already has about its own marketing/brand (analogous to a `marketing/`
research directory some projects keep) and fold relevant findings in — but that kind of
audience/brand research stays project-local; it does not belong in `platforms.md`/`content-types/`,
which are mechanics and process, not market research.

## Handing back

Show the resulting `factory/marketing/` files, confirm they match reality, and — if this run was
triggered by `factory-onboard` needing one of these three files — hand control back to it.
