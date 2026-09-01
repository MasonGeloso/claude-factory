# Factory Marketing — Content Type — <content-type name, e.g. "Daily news post">

> One file per content type, at `factory/marketing/content-types/<content-type-id>.md`. Read by
> `/factory-marketing-post` (for scheduled types, by the id named in `schedule.md`) and invoked
> directly by name (for on-demand types). Filled during onboarding via `factory-marketing-onboard`.
> Listed in `factory/marketing/content-types/README.md`'s index — add a row there when adding this
> file.
>
> Some content types have real, reusable technique and ship as their own skill in this suite
> (`factory-marketing-video`, `factory-marketing-recap`, `factory-marketing-clips`,
> `factory-marketing-dub`) — for those, this file just says which skill to invoke and any
> project-specific parameters on top of it. Other content types (most "read this data source, post
> about it" types) have NO generic skill, because their entire value is project-specific
> data-sourcing logic — for those, write the actual build steps here; nothing to point at externally.

- **What it is:** <one or two sentences>
- **Cadence:** `scheduled` (see the matching row in `schedule.md`) | `on-demand` (invoked by name,
  never fired by the dispatcher)
- **Skill:** <name of a shipped content-type skill to invoke, e.g. `factory-marketing-recap`, OR
  "none — build steps below" if this content type has no generic technique>
- **Build steps:** <if no shipped skill covers this — the actual, concrete, project-specific
  instructions: which data source to read, how to pick/verify a story, how to construct the piece.
  This is where the real value of a bespoke content type lives; be as concrete as the project needs>
- **Platforms + per-platform notes:** <which platform(s) in `platforms.md` this posts to, and
  anything specific to THIS content type on THAT platform — e.g. "on X, self-reply with the source
  link under the main post" — general platform mechanics belong in `platforms.md`, not here>
- **De-slop language:** <en | ja | none — which language to run `factory-humanizer` in, if any,
  specific to this content type (overrides the platform default if different)>
- **Autonomy mode:** `autonomous-publish` (may publish without a human in the loop, once every other
  gate below passes) | `draft-only` (always stops short of publishing and hands back a draft/deliverable
  for a human to send)
- **Dedup / ledger:** <default: the dispatcher's own canonical ledger under `factory/marketing/.state/`
  handles this automatically for scheduled types. Set to "also mirror to an in-repo narrative ledger"
  here if this content type is low-volume/editorial enough to want committed, human-readable history
  (like a running log of long-form articles) rather than just machine bookkeeping>
