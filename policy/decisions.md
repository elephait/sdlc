# DenisTek AI-Native SDLC — Active Decisions

**Status:** Pilot decisions, not production certification. Updated 2026-10-25.

This file records the strategic decisions and the pilot plan. Operating rules for agents live in [universal.md](universal.md) and [research.md](research.md); update those rather than restating them here. Implementation: [core/README.md](../core/README.md), [copilot-customization](../copilot-customization/README.md), [claude-customization](../claude-customization/README.md).

## Goal

Deliver maintainable software with minimal human intervention and efficient use of native coding-agent subscriptions. Preserve user instructions, original requirements and verified assumptions. Do not substitute agents' agreement for evidence that the software works.

## Decisions

1. **Native harnesses own coding.** Use Codex CLI/App Server or Claude Code for repository inspection, implementation, debugging and tool execution. Do not recreate coding agents in an LLM orchestration layer.
2. **Control plane stays deterministic and lightweight.** It schedules work, isolates branches/worktrees, tracks state, checks CI, routes review findings, enforces retry/time/budget limits and stops or escalates. No supervising LLM for ordinary routing.
3. **Existing tool before custom code.** **Pilot Agent Orchestrator first** for Codex writer + Claude read-only reviewer on Windows. It documents multi-vendor agents, PR review and feedback routing, but the exact end-to-end configuration remains **unverified**. **Symphony is the alternative** for Codex-first issue-driven execution and a clean controller specification; its reference implementation does **not** natively provide a separate Claude reviewer loop. Spec Kit/OpenSpec are optional specification tools, **not** substitutes for the controller.
4. **Operating rules.** One writer and an independent read-only reviewer, authority and durable context, quality gates before LLM review, bounded autonomy with explicit terminal states, time tiers, cost and security limits, and DAG priority are specified in the policy. Pilot values: 1 writer, 1 reviewer, max 3 review rounds, explicit elapsed-time and usage caps, adjusted from measured evidence. Two days of uninterrupted work is **not** guaranteed on $20 plans.

## Next decision: pilot, then choose

On an authorized small repo, run the same feature, refactor and unresolved-requirement tasks with (A) native Codex alone and (B) Agent Orchestrator: Codex writes, Claude reviews. Measure requirement pass rate, tests/CI, human-confirmed review defects, human intervention, usage/credits, time and correct BLOCKED behavior. Test restart, repeated failure and quota exhaustion. If B fails on reliability or overhead, trial Symphony for Codex-only scheduling; add Claude integration **only if its measured benefit justifies the work**. No tool is approved as enterprise-proven without controlled results and security/legal review.

## References (verify versions before rollout)

- [Agent Orchestrator](https://github.com/OrchestratorInc/agent-orchestrator)
- [OpenAI Symphony](https://github.com/openai/symphony) · [specification](https://github.com/openai/symphony/blob/main/SPEC.md) · [Elixir reference implementation](https://github.com/openai/symphony/blob/main/elixir/README.md)
- [Anthropic long-running agent harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
