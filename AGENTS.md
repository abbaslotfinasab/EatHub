# EatHub — Repository Working Rules

## Long-lived branches
- The only long-lived branches are `develop`, `main`, and `production`.
- `develop` is the integration branch for ongoing work.
- `main` is the release/integration branch; `production` is reserved for the production deployment flow.
- Do not commit implementation changes directly to `main` or `production`.

## Task branch and pull request policy
- Create short-lived task branches from the latest `develop` for implementation, fixes, tests, and documentation.
- Merge task branches into `develop` only through pull requests.
- Keep each pull request focused and reasonably small; do not combine unrelated work.
- Use squash merge for task pull requests unless the repository's release policy explicitly requires otherwise.
- Delete a task branch only after its pull request is merged and its changes are verified on `develop`.
- Release changes from `develop` through a reviewed pull request to the appropriate release branch. Never merge an unrelated task branch directly into `main` or `production`.

## Merge requirements
- Before merging, inspect the complete diff and verify the pull request targets `develop` (or the explicitly intended release branch).
- Wait for every applicable CI check to complete successfully. Investigate failures; do not bypass them.
- Review the latest pull request head SHA immediately before merge and use an expected-head check to prevent merging a changed revision.
- Check review status and resolve actionable review feedback before merging.
- After merge, verify that the target branch points to the merge commit.
- Do not claim branch protection or required checks are enabled unless the repository settings have been verified.

## Git hygiene
- Before any Git write, inspect the current branch, target ref, and working-tree state.
- Preserve user changes. Never force-push or rewrite shared history unless explicitly authorized.
- Do not delete branches or close pull requests until their unique, unmerged work has been checked.
- Keep `develop` synchronized with the intended release baseline through reviewed changes; do not reset it destructively.

## Quality and safety
- Never expose secrets, tokens, credentials, or environment variable values.
- Respect business/tenant isolation and existing architecture.
- Keep changes scoped; avoid unrelated modifications.
- Run relevant tests, lint, type checks, migrations checks, and CI before claiming a change is validated.
- Report failed, skipped, and unverified checks honestly.

## Assistant operating procedure
- Start every task by inspecting repository guidance, the current `develop` ref, and the relevant code.
- Create a short-lived task branch from the verified latest `develop`; do not work directly on long-lived branches.
- Open a pull request to `develop`, validate the latest head, and merge only after all applicable checks pass.
- After merging, verify the target ref equals the merge commit before starting dependent work.
- Never deploy to production or perform destructive database/infrastructure operations without explicit authorization.
