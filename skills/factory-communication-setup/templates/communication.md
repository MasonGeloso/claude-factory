# Communication — how this org talks

> Read by Factory's communication-driven agents (starting with `factory-ai-pm`).
> Companion to `factory/intake.md` (the tracker). Fill every section concretely.
> **Never** put the actual token/secret in this file — only the name of the env var that holds it.

## Medium

- **Primary medium:** <Slack | Discord | Teams | email | other>
- **Other media (if any):** <…>

## Access & authentication

- **How to connect:** <official API | bot/app | CLI | webhooks>
- **Credential env var:** `<E.G. DISCORD_BOT_TOKEN>` — lives in the repo `.env`. (Name only. Never the value.)
- **IDs / endpoints:** workspace/guild/team ID `<…>`, base URL `<…>`, API version `<…>`
- **Required scopes/permissions:** <e.g. channels:history, chat:write / Discord Read Message History>
- **Auth check:** <one command or call that verifies the credential works>

## Channels to read

Read **every** channel listed here on each run — do not sample.

| Channel | ID | Work-group / area | Notes |
|---------|----|-------------------|-------|
| #<name> | <id> | <team / owner from ownership.md> | <…> |

- **Never read:** <private/HR/leadership channels to stay out of>

## Read protocol

- **Fetch-since-timestamp:** <endpoint/call + pagination, e.g. `conversations.history?oldest=<ts>` / Discord `GET /channels/{id}/messages?after=<snowflake>`>
- **Threads:** <how to include thread replies>
- **Timestamp format:** <ISO 8601 | Slack `ts` float | Discord snowflake> — and how it maps to the watermark stored in `factory/.state/ai-pm.json`
- **First-run look-back window:** <default 24h> — how far back to read before a watermark exists

## Reply / write policy

- **May the agent post messages back?** <NO — read-only, only updates the tracker | YES>
- **If yes — where:** <specific channel / thread reply / DM to owner>
- **If yes — when:** <e.g. only to ask a clarifying question; only to confirm an action it took>
- **Tone / format:** <…>
- **Never do:** <@-here/@-everyone, public announcements, DMs, …>

## Scheduled posts (recurring reports)

Where the scheduled agents publish. The **reply policy above governs ad-hoc
messages**; these are the standing, expected posts, and they're allowed even when
the agent is otherwise read-only — the org asked for them.

One row per recurring post. If a row has no destination, that agent must **not**
post: it renders/writes its artifact locally and logs that it had nowhere to send
it. Silence is correct; guessing a channel is not.

| Report | Agent | Cadence | Destination | Format |
|--------|-------|---------|-------------|--------|
| Daily activity digest | `daily-digest` | <daily, ~09:00> | <#channel + ID> | <bullet TLDR, in-channel> |
| Tech-tree board | `weekly-report` | <daily 09:00 \| Mondays 09:00> | <#channel + ID> | <PNG attachment + 2-line summary> |

- **Cadence is set at install time** (`factory agents install <agent> <repo> --interval <minutes>`; 1440 = daily, 10080 = weekly). The times above are documentation of what's actually scheduled — keep them in step.
- The tech-tree board always reports a **rolling 7-day window** regardless of how often it posts; cadence and window are independent. Posting it daily republishes a refreshed board, it doesn't narrow it to one day.
- **Image/file uploads:** <the exact API call or CLI to attach a file — e.g. Slack `files.upload_v2` with `channels=<id>`, Discord `POST /channels/{id}/messages` multipart `files[0]`. Name it concretely; posting an image is not the same call as posting text.>
- **Threading:** <new top-level message each week | reply into a standing thread | pin and replace the previous one>
- **If the artifact fails to build:** post nothing, log the reason. A silently wrong report is worse than a missed one.

## Restrictions

- **Rate limits / quiet hours:** <…>
- **Privacy / compliance:** <…>

## Conversation → tracker mapping

- How conversations map to work items and owners (defer to `ownership.md` for people, `intake.md` for classification and issue types).
- Any org-specific cues: e.g. "a message starting with `TODO:` is always a new issue", "the #releases channel closing a thread means ship it".
