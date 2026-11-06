# Research prompt: SDLC automation stack for AI coding agents (as of 2026-10-24)

## Objective
Find the best COMBINATIONS of tools, harnesses and process for automating the software development lifecycle with AI coding agents, such that the stack:
runs continuously with minimal supervision, stays inside a $20/month consumer-plan budget (and say exactly what changes at the $100 and $200 tiers), runs on a single Windows laptop today, and can later scale to employer-owned projects worth millions. Deliver a decision-ready recommendation, not a survey.

## Requirements (treat as constraints, and test each one)
1. Runs continuously without my intervention. Iteration and recursion should make results better over time.
2. Respects the conversation context and explicit commands, but can also think out of the box now and then, using proven wisdom from top practitioners instead of reinventing the wheel.
3. Does not stop prematurely. Balances a quick answer (seconds), a 2-minute wait, 2 hours, and 2 days of elaboration.
4. Minimizes cost: tokens, number of agents. Uses each vendor's native harness (Claude Code, Codex CLI, etc.) as much as possible.
5. Stays within ChatGPT and Claude $20 plan limits. For the $100/$200 tiers, give the real limits.
6. Results can be judged and cross-checked across Claude, Codex (OpenAI), Grok, DeepSeek and other LLMs.
7. Runs on one laptop now. The end goal is employer-scale projects, so stability and quality must be enterprise-grade.
8. Prioritizes competing perspectives and tasks in the most appropriate structure (list, tree or DAG).

## Hidden assumptions to TEST, not accept
- "Being biased deeply by initial thoughts leads to better solutions." Test whether iteration improves results only when there are external oracles (tests, specs, CI), versus causing anchoring, self-reinforcing errors and drift. Find evidence (papers, benchmarks, postmortems).
- That one stack can serve a laptop, a $20 budget and a million-dollar project. Find where they must diverge.
- That consumer subscriptions may be used for unattended automation. Check each vendor's current terms of service and usage policies.
- That more agents or more loops means better results.

## Evidence rules
- Today is 2026-10-24. Prefer 2026 sources. Mark anything older than 12 months as potentially stale. Prices and plan limits must come from the vendor's current pages, with the retrieval date.
- Source tiers: (A) measured data: benchmarks, raw trajectories, controlled studies, vendor pricing and limits pages, CLI --help output, source code. (B) primary engineering write-ups from vendors and from named production teams. (C) practitioner accounts. (D) marketing. Load-bearing claims must rest on A or B.
- Every load-bearing claim needs two independent sources. List conflicts explicitly. Label each claim VERIFIED (retrieved and read) or TOLD (reported by a source, not retrieved).
- Never invent numbers. Anything unknown goes under Gaps.
- A failed tool is a retrieval limit, not a conclusion. Try another route (docs mirror, GitHub, package registry, web archive) before declaring something unavailable.

## Raw material to start from (not summaries of it)
Vendor docs: Claude Code (headless mode, hooks, subagents, skills, Agent SDK, GitHub Actions, costs and limits), OpenAI Codex (CLI, `codex exec`, cloud, AGENTS.md, limits), Gemini CLI and Jules, xAI Grok, DeepSeek API. Vendor engineering essays on long-running agents and harnesses. Benchmark leaderboards and raw trajectories (SWE-bench variants, Terminal-Bench and similar). Controlled studies (METR, DORA AI reports and similar). Open-source harness source code and issue trackers (OpenHands, Aider, Cline/Roo/Kilo, Goose, OpenCode and similar). Public loop and process implementations (the "Ralph" loop; spec-driven frameworks such as GitHub Spec Kit, Kiro, BMAD, OpenSpec; Matt Pocock's skills flow). Engineering blogs and postmortems from teams running coding agents in production at scale. The actual CLIs from the npm registry, to read their real flags for headless mode, budgets and permissions.

## Workstreams
1. Harness and runtime landscape and each one's native automation features.
2. Continuous-loop orchestration patterns, and evidence on drift versus improvement.
3. Spec and process frameworks, and priority structures (list vs tree vs DAG).
4. Verification and quality gates: tests, CI, review agents, LLM-as-judge reliability, cross-vendor juries, measurement (DORA, cost per merged change).
5. Cost, plan limits and terms of service.
6. Enterprise readiness: security, governance, scale, production case studies.
7. Multi-model portability and routing (Claude, Codex, Grok, DeepSeek and others).
8. Red team: failures, critiques and counter-evidence.

## Methods
Layered-stack decomposition (runtime, orchestration, spec, verification, memory, governance, cost control). Weighted decision matrix with weights taken from the 8 requirements, plus a sensitivity check. Analysis of competing hypotheses for contested claims. A cost model with explicit assumptions and ranges. A pre-mortem on the final recommendation. A pilot design.

## Deliverable
1. BLUF: the recommended combination for each tier ($20 laptop; $100/$200; enterprise), each as a layered stack with named components.
2. A time-tier routing rule: when to answer fast, take 2 minutes, 2 hours or 2 days, and the stop and escalation conditions.
3. The priority structure to use, and why.
4. A limits and cost table with dates and sources, including what a continuous loop would consume against a $20 limit.
5. Anti-drift design: oracles, fresh-context reviewers, stop conditions, checkpoints.
6. A cross-LLM judging protocol that works across Claude, Codex, Grok and DeepSeek.
7. Risks and the pre-mortem, and what humans (legal, security) must review before employer use.
8. A pilot plan to validate on one real repository: arms, metrics, deterministic oracles, sample size, stop rules.
9. Requirement-by-requirement verdict for 1 to 8: met, partly met, or not possible, and why.
10. Appendix: claim ledger (claim, source, date, VERIFIED or TOLD, conflicts) and a short prompt other LLMs can use to try to refute the top claims.

## Do not stop early
Done only when: every workstream has answers backed by A or B sources, all 8 requirements have a verdict, contested claims are resolved or flagged, and the claim ledger is complete.
