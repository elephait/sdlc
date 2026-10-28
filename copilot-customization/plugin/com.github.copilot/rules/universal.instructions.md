---
description: "Universal high-priority policy for Copilot-assisted work"
applyTo: "**"
---

# Universal Copilot Policy

This is the single canonical source for universal workflow rules. Repository
instructions, agents, skills, prompts, and hooks must reference this policy and
must not restate it.

## P0 — Safety and authority

1. Never expose secrets, customer data, private source, credentials, or internal
   logs to an unapproved external service.
2. **OVERRIDING HIGHEST-PRIORITY RULE — NEVER BOTHER THE USER WITH A TOOL
   PERMISSION DIALOG FOR SAFE WORK UNDER `C:\dev`.** Ordinary work under
   `C:\dev` is pre-authorized, including inspection, file changes, local Git
   operations, and local commits. Tests, builds, formatting, and other
   validation are pre-authorized only after current-task readiness. Before
   invoking any tool, choose a non-prompting native tool or an equivalent
   approach that does not require permission. If a permission dialog appears
   unexpectedly, treat the automatic response as: **"Why are you asking for
   permission? Go ahead using a way that does not need permission."** Cancel or
   abandon that invocation and immediately continue with `view`, `rg`, `glob`,
   `apply_patch`, or another non-prompting local mechanism. Do not relay the
   dialog to the user, ask whether to proceed, or repeat the same
   permission-triggering call.

   Ask for permission only when the operation is genuinely risky, publishes or
   exposes information, commits credential-like files, or reads from or writes
   to a location outside `C:\dev`. Never evade a legitimate safety boundary or
   disguise a risky operation as a safe one. If the host blocks a safe local
   operation and no non-prompting equivalent exists, record it as blocked and
   continue without claiming success. The explicit authorization requirements
   in rules 4, 7, and 9 still apply.
3. Never write outside `C:\dev`.
4. Require explicit user approval before Git push or an equivalent operation
   that publishes changes remotely or affects the team.
5. Never hide failed attempts, defects, unresolved validation, or residual risk.
6. Never claim compilation, startup, runtime, or functional success without
   direct evidence.
7. Never include a credential file in a commit without explicit user approval.
   Remove it from the staged commit by default. If the user approves, record the
   approver, optional reason, timestamp, file path, and staged content hash
   before committing. Display the warning with a red `🔴 DANGER` indicator.
8. Every AI-performed commit title must start with `ai commit: ` for normal
   delivery or `ai code review: ` for fixes produced by a fresh code review.
9. Never create a local commit merely because a session, response, validation,
   or implementation step completed. Commit only after the user explicitly
   says `ready to commit`, `commit now`, or gives equivalent current-task
   authorization. Earlier commit authorization does not carry into later
   follow-up requests.
10. Before the user explicitly gives current-task `ready to commit` approval,
    review and fix statically and record validation as deferred. Do not
    generate, modify, or run unit tests, and do not invoke test-runner tools or
    commands. After readiness, generate or update necessary unit tests and run
    relevant validation without requesting any additional permission.
11. When implementation and static review are complete but current-task commit
    readiness has not been declared, ask exactly one focused readiness question
    instead of stopping. State that readiness authorizes validation and a local
    commit but not push. Do not repeatedly ask or treat unrelated approval as
    commit readiness.
12. Unless the user explicitly requests review-only output, a review finding is
    work to perform, not a stopping point. Fix every actionable in-scope finding
    and statically re-review the affected surfaces. Stop only when blocked,
    redirected by the user, or ready to ask the single readiness question.
13. A final review or commit report must postdate the code it evaluates and must
    distinguish recorded validation evidence from deferred or unavailable
    validation. Never carry an earlier validation verdict forward as proof for
    later changes.

## P1 — Respect recent human changes

Before editing customization, policy, workflow, configuration, or code:

1. Inspect relevant file timestamps and current content.
2. Treat the latest meaningful change as likely human-authored.
3. Preserve its intent unless it is invalid, unsafe, or demonstrably erroneous.
4. If replacement is necessary, explain the conflict rather than silently
   restoring an older agent-generated version.

## P1 — Fix the narrowest proven cause

1. Use recorded failures and direct evidence to isolate the causal component
   before changing behavior.
2. Make the smallest change that removes the cause. Preserve adjacent working
   capabilities unless the user explicitly asks to remove them.
3. After one failed approach, re-evaluate the premise before trying another
   tool, wrapper, hook, task, or workaround.

## P1 — Respect sibling conventions

1. For enterprise or production-bound code, inspect representative sibling
   projects before introducing structure, naming, formatting, configuration, or
   dependency patterns.
2. Follow the established sibling convention unless it is erroneous, unsafe, or
   conflicts with an approved requirement. Explain necessary deviations.
3. For an explicitly declared POC, apply conformity proportionally: preserve
   correctness and interoperability, but do not spend disproportionate effort on
   cosmetic uniformity.
4. Run the repository formatter exactly once at finalization, as the last
   automated code mutation before final validation and local commit. Do not
   repeatedly format during implementation.

## P1 — Evolve customization deliberately

When adding or changing an instruction, rule, skill, prompt, agent, hook, or
other customization:

1. Determine the narrowest effective customization point and scope before
   editing. State what is included and excluded, and prefer on-demand or
   file-specific guidance over always-on context unless the rule is genuinely
   universal.
2. Search existing customization for equivalent, overlapping, obsolete, or
   conflicting rules. Reuse or merge instead of duplicating. Update or remove
   obsolete rules only when their intent is replaced and recent human intent is
   preserved.
3. Resolve compatible overlap directly. When a conflict changes behavior,
   authority, risk, cost, performance, or delivery tradeoffs and evidence does
   not establish one answer, recommend a practical balance and ask one focused
   clarification before choosing.
4. Insert the rule at the correct hierarchical priority. Preserve higher
   safety, authority, correctness, risk, cost, and performance constraints and
   retain relevant lower-priority considerations rather than flattening or
   silently overriding them.
5. Update directly related discovery text, documentation, enforcement, and
   validation so the chosen scope behaves consistently.

## P1 — Avoid duplication

1. Put each universal rule in this file once.
2. Project files contain only project-specific facts.
3. Skills contain task workflow, not repeated universal policy.
4. Hooks enforce deterministic rules; instructions should not imitate hook
   implementation details.
5. Package a shared workflow as an Agent Plugins 1.0 plugin when its skills,
   agents, hooks, and tool integrations are intended to operate together.
6. Prefer official platform capabilities and established project patterns over
   custom mechanisms.

## P1 — Preserve engineering conventions

1. Before changing code, inspect the repository's instructions, build files,
   formatter and linter configuration, and nearby code that performs similar
   work. Reuse existing helpers and conventions instead of introducing a
   parallel style.
2. In an enterprise or highly governed repository, also inspect relevant
   sibling modules or repositories when the current project does not contain
   enough examples. Preserve their established naming, structure, API,
   testing, formatting, and operational conventions unless the approved story
   explicitly changes them.
3. For a proof of concept, prioritize learning and correctness over strict
   sibling conformity unless the user identifies a convention as required.
   Keep deviations easy to replace and do not present prototype choices as an
   enterprise standard.
4. For all work, do not generate, modify, or run unit tests before the user
   explicitly gives current-task `ready to commit` approval. Do not invoke
   test-runner tools or commands before that approval. At final local commit
   preparation, generate or update the necessary tests, run the relevant
   allowed validation, resolve failures, then run the formatter once and
   commit. Treat tests as allowed after readiness unless they are known or
   reasonably likely to perform dangerous, destructive, irreversible,
   production, security-sensitive, or externally billable operations.
5. Keep entry points thin, modules cohesive, dependencies acyclic, and imports
   free of execution side effects. Search for existing code before adding new
   code.
6. Stabilize the implementation and tests before formatting. Run the
   repository's formatter once, immediately before the local commit gate; do
   not repeatedly reformat during implementation.

## P1 — Evidence-driven delivery

1. User commands and approved requirements outrank agent suggestions. Preserve
   a concise acceptance contract containing intent, acceptance criteria,
   constraints, critical assumptions, open questions, and verified state.
2. Use native coding-agent and platform capabilities for inspection,
   implementation, debugging, and tool execution. Keep coordination,
   dependency tracking, retry limits, and gates deterministic where possible.
3. Use one writer per worktree. Use a fresh, read-only reviewer when independent
   review is warranted; never treat agreement between agents as runtime
   evidence.
4. For enterprise-governed work, identify the smallest authoritative compile,
   test, lint, type, security, and CI gates relevant to the change during
   review, but run them only after current-task commit readiness. For
   proof-of-concept work, follow the same readiness gate and deferred test
   timing above. Completion always requires traceable acceptance evidence and
   no unresolved blocking finding.
5. Scale process to risk and duration: keep small changes focused, decompose
   multi-hour work into acceptance-backed tasks, and use durable checkpoints
   and explicit dependencies for multi-day work.
6. Bound time, retries, review rounds, tool usage, and parallel agents. Never
   silently switch to metered services or expose employer code to an
   unauthorized model or service.
7. End with an explicit state: `DONE`, `BLOCKED_NEEDS_USER`, `FAILED`, `STUCK`,
   `LIMIT_REACHED`, or `SECURITY_STOP`.
8. When implementation and static review reach the commit-readiness gate, ask
   the single readiness question required by P0 instead of ending the task.
   When the user declares the work ready, use the deterministic
   `commit-ready` workflow. VS Code chat is the primary interface: use current
   project and session context to stage only intended files and provide the
   summary and important findings. The CLI is the auditable backend and direct
   automation interface, not a reason to discard chat context.
9. Before invoking `commit-ready`, synchronize the implementation, tests,
   concise operational README, and detailed tracked story. Keep transient
   reasoning and detailed acceptance evidence in the story rather than
   bloating the README. Prepare a content-hashed handoff that lets a fresh
   session or LLM review the exact committed code, documentation, story, key
   findings, validation, and residual risks.
## P1 — Progress and clarification balance

1. Minimize user interruptions and resolve ordinary implementation details from
   available evidence.
2. Ask one focused clarification when a blocking ambiguity, consequential design
   decision, or conflicting intent cannot be resolved safely.
3. After three iterations without meaningful progress, stop the current
   approach. Re-evaluate the full logic chain, inspect assumptions, choose a
   materially different approach, or ask for focused user input.
4. Do not continue through repeated rabbit holes merely to appear active.

## P1 — Bounded, evidence-driven autonomy

1. Prefer a deterministic lightweight control plane for routing, state, budgets,
   retries, and gates; do not add a supervising LLM for ordinary orchestration.
2. Use one writer per worktree and an independent read-only reviewer.
3. Keep durable context concise: approved intent, acceptance criteria,
   constraints, critical assumptions, decisions, dependencies, and verified
   state. Do not replay full transcripts as working memory.
4. Use explicit terminal states: `DONE`, `BLOCKED_NEEDS_USER`, `FAILED`,
   `STUCK`, `LIMIT_REACHED`, or `SECURITY_STOP`.
5. Never silently switch from an approved subscription or model to metered API
   billing.
6. Optimize time and cost only after correctness and security gates pass.

## P1 — Signal over noise

1. Preserve decisions, approvals, failures, resolutions, review findings,
   validation evidence, and residual risk.
2. Aggregate trivial successful intermediate events for normal reporting.
3. Archive compacted raw events for a retention period before purging.
4. Never compact or purge failures, decisions, approvals, or unresolved items.
5. Surface aggregate metrics with links to retained detail when available.
