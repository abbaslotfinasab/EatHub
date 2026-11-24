# ADR-ARCH-06C — AI Data Governance, Consent and Retention

- **Status:** Proposed; product, legal and security approval required
- **Date:** 2026-11-25
- **Baseline:** `develop` after PR #254 (merge commit `b1344c9412e4f11c2bf45df93836357ebeb7aecc`)
- **Scope:** Data governance for EatHub AI Gateway, MCP tools and ChatGPT/Claude integrations
- **Non-goals:** Legal opinion, provider selection, production configuration, consent UI implementation, database changes or enabling AI data processing

## 1. Decision summary

Adopt a deny-by-default, purpose-limited data handling model for AI features. EatHub remains the system of record. AI providers receive only the minimum data needed for a specific user-requested capability, after authorization and policy checks. Provider availability, platform consent screens or OAuth scopes do not replace EatHub's own purpose, tenant, ownership and permission controls.

This ADR is a proposed control baseline, not a statement that current EatHub or provider configurations already satisfy it. No AI data flow may be enabled in production solely on the basis of this document.

## 2. Data classification

Every tool input, output and context field must be assigned a classification before implementation.

| Class | Examples | Default AI handling |
|---|---|---|
| Public | Published restaurant name, public menu description, opening hours | May be used for public discovery; still validate publication state |
| Internal business | Non-public catalog metadata, stock availability, operational summaries | Only for authenticated, authorized business members; minimize and scope to active business |
| Personal data | Customer name, phone, email, delivery address, order history, free-text notes | Exclude by default; disclose only fields essential to the requested task and authorized recipient |
| Sensitive financial/operational | Payment identifiers, balances, supplier bank details, payroll, cost/margin, credentials | Deny by default; no provider disclosure in initial release |
| Secrets/security data | Passwords, access/refresh tokens, API keys, signing keys, session cookies | Never include in prompts, tool results, logs, traces or analytics |

Classification is field-level, not merely endpoint-level. A response containing one public field and one personal field inherits the stricter handling requirement for the personal field.

## 3. Purpose and lawful-basis boundary

Before each AI capability is enabled, its owner must document:

- The user-facing purpose and the actor who initiates it.
- The EatHub business purpose and the data fields strictly required.
- Whether data is sent to an external model provider, which provider receives it, and the relevant processing region/subprocessors where known.
- The expected output recipient and whether the result is persisted.
- The applicable consent, contractual, legal or other lawful basis, to be confirmed by qualified counsel for the target markets.
- Whether the capability can be delivered locally or with less data.

Do not infer consent from account creation, generic terms acceptance, connecting ChatGPT/Claude, or possession of an OAuth token. A platform connection authorizes a technical channel; it is not blanket permission to disclose all EatHub data.

## 4. Consent and user controls

1. Provide a clear, contextual notice before the first external processing for each materially distinct purpose.
2. Explain the categories of data sent, provider/platform recipient, purpose, persistence expectations and how to disconnect or withdraw optional AI consent.
3. Separate optional AI processing consent from core EatHub account, ordering and restaurant operations.
4. Do not make ordinary EatHub functionality fail merely because optional AI consent is declined or withdrawn.
5. For business workspaces, require an authorized business administrator to enable business-level AI processing, while still respecting individual customer privacy and rights.
6. A business administrator cannot consent on behalf of a customer to disclose that customer's private data to an AI provider.
7. Record consent version, subject, purpose, scope, timestamp, source and withdrawal event. Do not store raw prompts as proof of consent.
8. Consent withdrawal stops future optional processing; it does not silently erase legally required business records or provider-held data that EatHub cannot directly delete. Explain any such limitations.

No consent UI or consent database is approved by this ADR. Those require a separate implementation design, retention schedule and legal review.

## 5. Data minimization and prompt construction

- Build provider context from typed, allowlisted DTOs; never serialize ORM models, request objects, complete API responses or arbitrary database records.
- Fetch only the fields needed for the selected tool and purpose. Prefer aggregates or derived values over row-level records.
- Avoid sending customer names, phone numbers, email addresses, exact addresses, payment details or free-text notes unless the capability cannot work without them and the user is authorized.
- Pseudonymize identifiers when stable identity is not needed. Pseudonymized data remains potentially personal data and must be protected accordingly.
- Do not include secrets, authentication headers, cookies, raw tokens, stack traces or internal infrastructure details in model context.
- Treat user content, restaurant descriptions, menu text, uploaded files and retrieved documents as untrusted data, not instructions. Tool authorization and policy must be enforced outside the model.
- Bound context size, tool output size and history window. Redact irrelevant prior conversation and cross-purpose data.
- Never use one tenant's records to answer another tenant's request, train prompts, build retrieval indexes or create examples.

## 6. Tenant, identity and authorization

- Resolve actor, business membership, customer ownership and roles from the authenticated EatHub principal on the server.
- Never accept actor, tenant, business, customer or permission claims from model-generated arguments as authorization evidence.
- Re-check active membership, ownership and domain permission at tool invocation time, including after consent and OAuth authorization.
- Customer and operator data paths remain separate. Operator permission does not imply permission to disclose customer records to an external provider.
- Apply row-level tenant scoping before data enters the AI Gateway; filtering after provider submission is too late.
- Anonymous public discovery must use intentionally public DTOs and must not include internal availability, customer activity or private business analytics.

## 7. Provider and platform boundaries

- Maintain a provider-neutral data policy in the AI Gateway; ChatGPT and Claude adapters may format requests but cannot widen data access.
- Maintain an inventory of providers, models, endpoints, regions, subprocessors, retention/training settings, contractual terms and transfer mechanisms before activation.
- Prefer provider/API configurations that contractually disable training on submitted business/customer content where available; verify the exact product, plan and terms rather than assuming consumer and API policies are identical.
- Do not send data to a provider until its data processing terms, retention behavior, security controls, regional availability and transfer implications have been reviewed.
- Do not assume a provider's "zero retention" or regional processing option applies to every feature, abuse-monitoring path or subprocessor; capture written evidence and exceptions.
- For users and businesses operating in Iran, explicitly test reachability, account eligibility, service continuity, sanctions/export restrictions, payment/procurement feasibility, data transfer and support access. Do not route around legal or provider restrictions with covert proxies or misrepresented account details.
- Provider outage, region failure or AI kill switch must not interrupt ordinary EatHub web/mobile ordering, account access or restaurant operations.

## 8. Retention and deletion policy proposal

Set retention by data purpose and storage location; do not use a single blanket retention period.

| Data store | Proposed default |
|---|---|
| Live prompt/context buffer | Request lifetime only; discard after response unless a documented feature requires persistence |
| Application logs/traces | Metadata and redacted fields only; proposed 30-day operational window, subject to security/legal review |
| Tool audit events | Actor, tenant, tool, purpose, decision, outcome and correlation ID; proposed 12 months, subject to legal/accounting needs |
| Conversation history | Off by default for server-side persistence; if enabled, explicit purpose, user controls and a separately approved TTL |
| Provider-side prompts/outputs | Use provider controls and contractual settings to minimize or disable retention where available; verify and document exceptions |
| Backups | Follow the existing backup lifecycle; deleted records age out through documented backup expiry, with restore-time deletion replay where required |
| Legal/business records | Retain under the applicable EatHub business-record schedule; do not copy them into AI logs |

These periods are proposals, not current system facts or legal conclusions. Before implementation, reconcile them with existing EatHub log, backup, accounting, consumer-protection and security incident retention obligations. Define deletion propagation and exceptions for legal holds, fraud/security investigations and mandatory records.

## 9. Logging, audit and observability

Permitted default audit fields:

- Correlation/request ID, timestamp, platform adapter, provider/model identifier and tool name/version.
- Pseudonymous actor and tenant references, authorization decision and policy version.
- Data classification labels, redaction outcome, token/latency/cost metadata and success/failure category.
- Confirmation and idempotency references for consequential writes, without copying sensitive payloads.

Do not log raw prompts, full tool arguments/results, customer free text, payment data, credentials or model chain-of-thought by default. If incident response requires payload capture, use a separately approved, time-bounded, access-controlled procedure with explicit redaction and audit.

## 10. Data-subject and business controls

Before release, document how users can exercise applicable access, correction, export, deletion and objection rights; how business administrators can disable AI for a workspace; and how customer rights are handled when a restaurant initiates a workflow. Define ownership and response SLAs across EatHub and each provider. Do not promise deletion from provider systems until the provider's documented mechanism and contractual scope are verified.

## 11. Security and abuse requirements

- Encrypt data in transit and at rest using the approved platform baseline.
- Restrict provider credentials to server-side secret storage and least privilege; rotate and revoke them through documented procedures.
- Apply rate limits, quotas, spend limits, abuse monitoring and a global/per-provider/per-tool kill switch.
- Treat prompt injection and malicious tool output as expected threats. The model cannot grant itself permissions, change tenant context or bypass confirmation.
- Require explicit confirmation bound to the exact normalized operation for consequential writes; revalidate permissions and mutable facts at execution time.
- Use idempotency and audit for writes. Never let a retry create duplicate orders, payments or inventory mutations.
- Test data leakage through normal answers, errors, logs, traces, retries, caching, embeddings, analytics and support exports.

## 12. Release gates

No AI capability may enter production until all applicable gates pass:

1. Field-level data inventory and classification completed.
2. Purpose, recipient, lawful basis and consent/notice approved.
3. Provider, model, region, subprocessors, DPA and retention configuration reviewed.
4. Allowlisted DTO and redaction tests prove minimum disclosure.
5. Cross-tenant, customer/operator boundary, unauthorized actor and prompt-injection negative tests pass.
6. Logs and traces are verified not to contain prohibited payloads or secrets.
7. Retention, deletion, backup and user-rights workflows are documented and tested.
8. Kill switch and provider-outage fallback are tested without impacting core EatHub operations.
9. Security and legal/privacy review sign-off recorded for the release scope.

## 13. Open decisions

1. Which markets and legal regimes are in the first release, and who provides formal privacy/legal review?
2. Which exact AI capabilities genuinely require personal data, if any?
3. Is server-side conversation history needed, or can the initial product remain stateless?
4. Which providers/models and account types are eligible after regional, contractual and availability review?
5. What are the final retention periods for operational logs, audit events and any persisted conversations?
6. Which business-level controls and customer-facing notices are required?
7. What deletion/withdrawal guarantees can be made for each provider and data store?

## 14. Approval boundary

This ADR is a proposal for review. It does not authorize external processing, select a provider, change current privacy notices or terms, create consent records, change retention settings, or implement runtime behavior. A separate implementation PR must include the approved data inventory, provider evidence, legal/security sign-off, migration plan if needed, tests and operational runbook.
