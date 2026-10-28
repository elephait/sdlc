# Reusable prompts

When the skill is not discovered automatically, name its path. This avoids global installation and works across projects when the agent has read access to the common directory.

## Existing service: Codex or Claude Code

Read C:/dev/common/denistek/skills/distributed-service-design-review/SKILL.md and apply it to this service. Start with the most consequential mutating operation. Inspect its contract, schemas, transactions, dependency calls, client/broker settings and deployment configuration. Trace duplicate requests, lost responses, crashes around commits and acknowledgments, and recovery. Return evidence-backed findings, failure sequences, minimal remedies, tradeoffs and validation performed versus still needed. Distinguish unknowns from observed defects. Keep the review within the requested scope.

## New service

Read C:/dev/common/denistek/skills/distributed-service-design-review/SKILL.md. Design for the attached requirements, stack and constraints. Establish authoritative ownership, operation states and measurable acceptance scenarios. Compare the simplest viable architecture with alternatives only where a requirement warrants them. Specify API contracts, idempotency, transaction boundaries, uncertain-outcome recovery and safe evolution. Label assumptions and propose tests that could falsify the design. Do not assume queues or microservices are necessary.

## Focused decision

Read C:/dev/common/denistek/skills/distributed-service-design-review/SKILL.md. Review [decision] against [invariant] under [constraints], using [paths/evidence]. Trace the key failure boundary, compare viable options including retaining the current design, and recommend one with tradeoffs and a falsifiable acceptance test. Identify the unknown most likely to change your recommendation.

## Incident follow-up

Read C:/dev/common/denistek/skills/distributed-service-design-review/SKILL.md. Reconstruct [incident] from traces, logs and the affected operation, and separate the trigger from the latent defect that let it become a loss or duplicate. State which guarantee failed, whether the lost or duplicated effect is reconciled or only retried, and the smallest change that makes the next occurrence detectable and repairable. Do not propose a redesign unless the current design cannot meet the invariant.

## Use the existing /better without installing globally

Read C:/dev/common/skills/ideas/better/a1443d30fa1b7c577e74882895cea61b/SKILL.md and apply it to the previous review. Use raw evidence and concrete acceptance criteria while preserving the original scope.

For prompt improvement rather than execution, replace the last sentence with: Improve the following prompt without carrying it out: [prompt].

If separately registered with an agent, the short invocations are `$distributed-service-design-review` for Codex and `/distributed-service-design-review` for Claude Code. Registration is not performed by this package.
