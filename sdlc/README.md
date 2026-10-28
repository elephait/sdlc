# DenisTek AI-Native SDLC — Active Decisions

**Status:** Pilot decisions, not production certification. Updated 2026-10-25.

This file is the **single source of truth** for AI coding assistants. Follow the decisions below. Do not reconstruct debate or treat untested capabilities as proven. If a decision must change, update this file rather than append a discussion history.

## Goal

Deliver maintainable software with minimal human intervention and efficient use of native coding-agent subscriptions. Preserve user instructions, original requirements and verified assumptions. Do not substitute agents' agreement for evidence that the software works.

## Decisions

1. **Native harnesses own coding.** Use Codex CLI/App Server or Claude Code for repository inspection, implementation, debugging and tool execution. Do not recreate coding agents in an LLM orchestration layer.
2. **Control plane stays deterministic and lightweight.** It schedules work, isolates branches/worktrees, tracks state, checks CI, routes review findings, enforces retry/time/budget limits and stops or escalates. No supervising LLM for ordinary routing.
3. **Existing tool before custom code.** **Pilot Agent Orchestrator first** for Codex writer + Claude read-only reviewer on Windows. It documents multi-vendor agents, PR review and feedback routing, but the exact end-to-end configuration remains **unverified**. **Symphony is the alternative** for Codex-first issue-driven execution and a clean controller specification; its reference implementation does **not** natively provide a separate Claude reviewer loop. Spec Kit/OpenSpec are optional specification tools, **not** substitutes for the controller.
4. **One writer, independent reviewer.** Begin with one Codex coding worker and at most one Claude reviewer, using their **native harnesses**. Reviewer is read-only, inspects approved requirements and diff, and returns actionable findings. Fix only material findings, then rerun gates and, if needed, review. Never allow two writers to alter the same worktree simultaneously.
5. **Authority and durable context.** User commands and approved requirements outrank agent suggestions. Keep only a small versioned acceptance contract: goals, acceptance criteria, constraints, critical assumptions/questions, and current verified state. Do not replay full transcripts or allow workers to silently change requirements or acceptance tests.
6. **Quality gates.** Compilation, tests, lint/type checks, relevant security checks and CI come **before** costly LLM review. Completion requires traceable acceptance evidence, critical assumptions resolved, green required checks and no blocking review findings. Agent self-assessment alone cannot mark success. Human approval for merging high-risk or employer code.
7. **Bounded autonomy.** Resume from concise state and Git history. Stop with explicit `DONE`, `BLOCKED_NEEDS_USER`, `FAILED`, `STUCK`, `LIMIT_REACHED` or `SECURITY_STOP`. No endless loops, blind retries or premature success. For initial pilot: 1 writer, 1 reviewer, max 3 review rounds, and explicit elapsed-time/usage caps; adjust from measured evidence.
8. **Time tiers.** Small task (~2 minutes): native agent and focused tests, no heavyweight process. Multi-hour task: task breakdown, acceptance contract, bounded fix/review iterations. Multi-day task: checkpointed task dependencies, persistent state and human decision gates. Two days of uninterrupted work is **not** guaranteed on $20 plans.
9. **Costs and security.** Minimize context injection, redundant reads, parallel agents, repeated reviews and retries. Measure native-only vs orchestrated runs by *accepted functionality and human time per unit of usage*. Subscription caps and API charges differ; never silently switch to metered API billing. Isolate workspaces, protect secrets, require authorization for employer code.
10. **Priority structure.** Plan with initiative → task tree and explicit blocking dependencies (DAG); execute highest-value eligible task. Correctness/security are hard gates; optimize speed and cost only after those pass.

## Next decision: pilot, then choose

On an authorized small repo, run the same feature, refactor and unresolved-requirement tasks with (A) native Codex alone and (B) Agent Orchestrator: Codex writes, Claude reviews. Measure requirement pass rate, tests/CI, human-confirmed review defects, human intervention, usage/credits, time and correct BLOCKED behavior. Test restart, repeated failure and quota exhaustion. If B fails on reliability or overhead, trial Symphony for Codex-only scheduling; add Claude integration **only if its measured benefit justifies the work**. No tool is approved as enterprise-proven without controlled results and security/legal review.

## References (verify versions before rollout)

- [Agent Orchestrator](https://github.com/OrchestratorInc/agent-orchestrator)
- [OpenAI Symphony](https://github.com/openai/symphony) · [specification](https://github.com/openai/symphony/blob/main/SPEC.md) · [Elixir reference implementation](https://github.com/openai/symphony/blob/main/elixir/README.md)
- [Anthropic long-running agent harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
