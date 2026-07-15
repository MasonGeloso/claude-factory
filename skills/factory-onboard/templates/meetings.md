# Meetings & syncs

> How this org runs alignment meetings. Read by `factory-schedule-sync` (to build an
> agenda that fits the attendees and the time) and `factory-sync-recap` (to process the
> transcript afterward). Ties to `ownership.md` for who owns what and `communication.md`
> for where agendas/recaps get posted.

## Recurring syncs

| Sync | Cadence | Usual attendees | Goal | Length |
|------|---------|-----------------|------|--------|
| <e.g. Weekly team sync> | <weekly, Mon> | <names → ownership.md> | <alignment + decisions> | <30m> |

## Agenda

- **Goal of a sync:** <alignment / decision-making / status — usually "make decisions and align">
- **Where the agenda lives:** <a doc, a channel post, an issue — often via communication.md>
- **Format:** <e.g. per-attendee section + a "decisions needed" block + a "priorities" block>
- **Build the agenda to fit the time** — favor items that (a) need a decision, (b) lack context/alignment, or (c) are blocked, over pure status.

## Attendee lens

For each attendee, `factory-schedule-sync` should ask "what do I need from this person?"
based on their ownership. Note any per-person conventions here:
- <e.g. "Igor owns frontend — always pull status on open frontend issues before his syncs">

## Decisions & priorities

- **How decisions are recorded:** <issue comments / a decisions log / updating priority.md>
- **After a sync**, `factory-sync-recap` updates issues and refreshes `priority.md`. Note any
  extra places decisions must be mirrored (a roadmap doc, a channel announcement, etc.).
