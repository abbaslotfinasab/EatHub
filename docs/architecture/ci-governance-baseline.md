# CI and Branch Governance Baseline

Status: Audit snapshot
Last verified: 2026-11-24
Repository: `abbaslotfinasab/EatHub`
Audited integration ref: `develop` at `675821069945a854b1f59b8400686ec91e7455d9`

This document records the repository's observed CI contract and the branch-governance gaps found during ARCH-07. It is an audit baseline, not a claim that GitHub repository settings have been changed.

## 1. Pull request CI contract

The following check-run names were observed on the audited `develop` commit. These are the exact GitHub Check Run contexts, not workflow display names.

| Check run context | Workflow/job source | Purpose |
| --- | --- | --- |
| `Django / PostgreSQL 16` | Backend CI → `django-postgres` | Django checks, staging settings check, migration drift check, disposable PostgreSQL migrations, tenant integrity audit, backend test suite |
| `Frontend / TypeScript and tests` | Frontend CI → `frontend` | Dependency installation/audit, production build, frontend tests |
| `Analyze (python)` | CodeQL Security Analysis → matrix language `python` | Python static security analysis |
| `Analyze (javascript-typescript)` | CodeQL Security Analysis → matrix language `javascript-typescript` | JavaScript/TypeScript static security analysis |

All four checks completed successfully on the audited commit. A future ruleset should use these exact contexts only after confirming that each check is emitted for the intended pull request event and branch.

## 2. Workflow triggers observed

- `.github/workflows/backend-ci.yml`: push to `develop` and `main`; pull requests targeting `develop`, `main`, and `feat/**`.
- `.github/workflows/frontend-ci.yml`: push to `develop` and `main`; pull requests targeting `develop`, `main`, `feature/purchase-frontend-foundation`, and `feat/**`.
- `.github/workflows/codeql.yml`: push to `develop` and `main`; pull requests targeting `develop`, `main`, and `feat/**`; weekly schedule and manual dispatch.
- `.github/workflows/release-branch-policy.yml`: pull requests targeting `main`; rejects any source branch other than `develop`.

The standard task PR flow into `develop` therefore triggers backend CI, frontend CI, and both CodeQL matrix jobs. The release-source policy is intentionally scoped to PRs targeting `main`.

## 3. Governance findings

The following findings were read from the active GitHub Rulesets API on 2026-11-24:

| Target | Observed enforcement | Gap |
| --- | --- | --- |
| `develop` | Deletion and non-fast-forward restrictions | No required pull-request rule and no required status checks were configured in the audited ruleset |
| `main` | Pull-request rule and required status checks | CodeQL contexts were not included in the required-check list |
| `production` | Pull-request rule | No required status checks were configured in the audited ruleset |

The classic branch-protection API reported `protection.enabled=false` for these refs. Active rulesets are separate controls; do not interpret the classic API field as proof that rulesets are disabled.

Ruleset references at audit time:
- [develop ruleset](https://github.com/abbaslotfinasab/EatHub/rules/26770185)
- [main ruleset](https://github.com/abbaslotfinasab/EatHub/rules/26589695)
- [production ruleset](https://github.com/abbaslotfinasab/EatHub/rules/26589783)

## 4. Recommended follow-up configuration

For `develop`, configure an active ruleset that:
1. Requires pull requests before changes are merged.
2. Requires the four exact check-run contexts listed in section 1.
3. Requires all review conversations to be resolved.
4. Disallows force pushes and branch deletion.
5. Uses squash merge for task PRs, consistent with repository working rules.

For `main`, consider adding both CodeQL contexts to the existing required checks after validating their availability on release PRs. Preserve the existing `develop`-as-source policy.

For `production`, decide the required CI contract and approval policy explicitly before changing its ruleset. Do not weaken or modify production protections as part of routine ARCH-07 work.

## 5. Operational safeguards

- Create task branches from the latest verified `develop`.
- Merge task work only through a PR targeting `develop`.
- Inspect the complete diff, review threads, reviews, and the latest PR head SHA before merge.
- Wait for every applicable check to succeed on that exact head.
- After squash merge, verify all post-merge checks on the merge commit SHA.
- Move the corresponding task card to Done only after post-merge checks succeed.
- Never claim that a ruleset is configured based only on this document; re-read the live ruleset before and after any settings change.
- Keep `main` and `production` untouched unless the repository owner explicitly authorizes a release/governance change.

## 6. Scope and limitations

This repository documentation records the state observed on the audit date. GitHub ruleset write operations were not available through the connected repository integration during this task, so no ruleset was modified. The live settings remain authoritative and must be rechecked before relying on the recommendations above.
