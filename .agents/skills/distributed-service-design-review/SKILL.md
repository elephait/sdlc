---
name: distributed-service-design-review
description: Review or design a distributed service architecture against correctness, consistency, delivery guarantees, reliability, security, performance, cost and recovery requirements. Use for architecture reviews run against a design matrix, API and messaging contract decisions, idempotency and transaction design, failure-mode analysis and incident follow-up; not routine endpoint edits or code-style reviews.
---

# Distributed service design review

Produce evidence-backed decisions from operation flows and failure scenarios. Scale the review to the user's decision and system size. This is a lightweight synthesis of established methods, not a formal ATAM assessment or security certification.

## Frame the decision

Identify whether the request is a proposed design, implementation review, or focused decision. Preserve the chosen stack and scope. Inspect before recommending. For a proposal, distinguish intended guarantees from verified behavior. A review does not itself authorize implementation or production experiments.

Start with the most consequential business operation, its invariant, the authoritative owner of each fact, and the caller's possible observations. One owner answers each question of record: a middleman may sequence and observe, it never invents or overwrites the authoritative result. Distinguish committed success, definitive rejection, pending work, and unknown outcome. A timeout does not prove failure.

Seek raw evidence: handlers, schemas and constraints, transaction boundaries, SDK and broker settings, infrastructure, API contracts, traces, incidents, and tests. Inspect available evidence before asking questions. Ask only for missing facts that materially affect a decision; continue independent analysis and label unknowns.

## Set acceptance criteria

State the business invariants and a few measurable quality scenarios: stimulus, operating condition, affected operation, expected response, and measurable bound. Use the user's SLOs, workload, tenant boundaries, RPO/RTO, and cost constraints. If values are missing, label proposed values as assumptions rather than requirements.

Select relevant sections of [the design matrix](references/design-matrix.md). Briefly explain major exclusions. Naming a product or pattern does not establish that a requirement is met.

## Trace and challenge

1. Trace an important operation from request through durable state and side effects to response. Identify commits, acknowledgments, retries, ownership transfers, and asynchronous boundaries.
2. At relevant boundaries consider crashes before/after commit, lost response/acknowledgment, concurrent duplicates, delayed replay, stale lease holders, out-of-order events, dependency slowdown, partial compensation, and mixed-version deployment. Choose realistic scenarios rather than an exhaustive hypothetical list.
3. For each material risk show the invariant, concrete failure sequence, existing protection, residual gap, and how the outcome is discovered or repaired. Cite file/line or configuration evidence. An uninspected feature is unknown, not absent.
4. Compare the current/simple design with alternatives only where a decision is needed. Explain correctness, availability, latency, cost, and operational tradeoffs, including which assumption would reverse the recommendation. Do not prescribe microservices, Redis, queues, sagas, 2PC, or multi-region deployment merely to satisfy a checklist.
5. For delivery, ordering, deduplication and transaction claims read [guarantee boundaries](references/messaging.md). Verify version-sensitive claims against authoritative documentation for the actual product/client. Use [professional sources](references/sources.md); when offline, identify unverified guarantees. For each guarantee claimed, name the link that provides it and the link that does not.

## Deliver

Lead with the recommendation and highest-impact risks. Scale the output to the request:

- Scope, key invariants, workload assumptions, authoritative owners.
- Operation trace or diagram when boundaries would otherwise be unclear.
- Matrix: `Concern | Requirement | Evidence/status | Failure scenario | Decision/tradeoff | Validation`.
- Prioritized findings: impact, evidence, failure sequence, smallest viable remedy, and confidence. Separate observed defects, design risks, and unanswered questions. Prioritize by business consequence, not by the missing pattern's name.
- Checks performed and remaining acceptance checks. Report tests as passed only if executed. Distinguish tabletop analysis from runtime testing. For unknown outcomes specify status lookup/reconciliation, owner, retry rules, and escalation criteria.
- The accepted decision and the evidence that would reopen it, recorded where the project keeps decisions rather than only in the review.

Use `supported`, `gap`, `unknown`, or `not applicable`, with evidence or rationale. Support by inspection is not proof under failure. Avoid numerical maturity scores without a defined rubric.

Use Markdown for human review; use structured JSON only when automation requires it, with stable finding IDs and separate evidence, assumption, and validation fields. Do not maintain a duplicate JSON checklist.

See [reusable prompts](references/prompts.md). When maintaining this skill, use [regression fixtures](evals/scenarios.md); they are not evidence about the user's system. This skill is self-contained and does not require `/better` to be installed.
