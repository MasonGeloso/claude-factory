# Factory Codebases — <SERVICE NAME>

> The repo(s) this service spans, where they live, and how they relate.
> Read by `/factory-implement` (the driver) before setting up worktrees. Filled during onboarding.

## Repos
| Repo | Role | Local path | Git remote | Primary? |
|------|------|-----------|-----------|----------|
| <e.g. acme-api> | <backend API> | <~/code/acme-api> | <git@…> | yes |
| <e.g. acme-ui>  | <frontend>    | <~/code/acme-ui>  | <git@…> | no |

## Relationships
- <how they talk to each other — e.g. UI calls API at :PORT; shared auth; shared DB>
- <which repos are typically checked out together for one change vs. independently>

## Notes
- `factory/` lives in: <primary repo>
- <anything else an executor must know to not get confused across repos>
