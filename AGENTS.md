# EatHub — Repository Working Rules

## Branch policy (mandatory)
- `develop` is the only working branch for all ongoing EatHub development.
- Make implementation changes, refactors, tests, documentation, lint fixes, and ordinary commits directly on `develop`.
- Do not create a feature, fix, chore, test, or other temporary branch for routine work.
- Do not commit directly to `main`, and never push implementation changes to `main`.
- `main` is the release/integration branch. The only intended path into `main` is a reviewed pull request whose source is `develop` and whose target is `main`.
- Before opening that release PR, ensure `develop` is up to date with `main`, run relevant CI/tests, and review the complete diff.
- Never merge an unrelated branch into `main`. Do not merge a PR from a temporary branch to `main`.
- Keep `develop` based on the latest `main`; after a release merge, continue development on `develop`.

## Git hygiene
- Reuse `develop`; do not create one branch per task or PR.
- Do not delete branches or close PRs until their changes have been checked for unique, unmerged work.
- Preserve user changes and never force-push or rewrite shared history unless explicitly authorized.
- Use squash merges for release PRs unless the repository's release policy says otherwise.

## Quality and safety
- Never expose secrets, tokens, credentials, or environment variable values.
- Respect business/tenant isolation and existing architecture.
- Keep changes scoped; avoid unrelated modifications.
- Run relevant tests, lint, type checks, and CI before claiming a change is validated.
- Report failed, skipped, and unverified checks honestly.

## Assistant operating procedure
- For all future EatHub coding tasks, start from and write to `develop`.
- Before any Git write, verify the current refs and ensure the target is `develop`.
- If a task appears to require a temporary branch, do not create one; work on `develop` instead.
- If `develop` is behind `main`, fast-forward it safely before continuing. Never reset it destructively.
