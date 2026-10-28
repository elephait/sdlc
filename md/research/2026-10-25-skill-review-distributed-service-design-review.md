# Skill review: `distributed-service-design-review` (ChatGPT handover)

Reviewed 2026-10-25. Subject: the skill ChatGPT built from the banking architecture design matrix and left in `C:\dev\common\skills\.staging-distributed-review\`.

## Verdict

The content is good and the delivery is unfinished. The guarantee analysis survived independent fact-checking with no wrong claims. What failed is everything around the content: the skill was never installed, the usage instructions pointed at a path that did not exist, and the validator that was supposed to prove it correct could not start on this machine. Content quality was never the problem; the package was never finished or exercised.

## What held up

- **Sources and version-sensitive claims.** All 16 cited URLs were fetched, and all eight claims were checked against primary documentation. Every claim is correct: Kafka producer idempotence requires `retries > 0`, `acks=all` and `max.in.flight.requests.per.connection <= 5`; `isolation.level` defaults to `read_uncommitted`; SQS FIFO send deduplication lasts five minutes; RFC 9110/9457, OWASP API 2023, Zalando, SEI ATAM, the SRE workbook and the two microservices.io pattern pages all resolve to the described content. The gist revision `5d2b31e5…` is the current one. Only the two AWS Builders Library URLs had moved to `builder.aws.com`.
- **Corrections to the matrix are technically right.** The matrix says "disable retry", "2PC ~ store onto the same table" and implies `read_committed` gives exactly-once. The skill contradicts all three, correctly, with sources.
- **Shape.** Failure-first framing, the six-column deliverable matrix, the `supported / gap / unknown / not applicable` verdicts, self-containment (no dependency on `/better`), and reference disclosure all follow the local conventions well.
- **Writing.** No em-dashes, no filler, prohibitions paired with positive targets. It reads like the maintained skills in `skills/codebase-design/mattpocock-skills`.

## Defects

| # | Severity | Defect | Evidence |
|---|---|---|---|
| 1 | High | Never installed. Every prompt in the package pointed at `C:/dev/common/denistek/skills/distributed-service-design-review/SKILL.md`, which did not exist; `denistek/skills` was empty. | `USAGE.md`, `references/prompts.md`; empty target directory |
| 2 | High | Staged in a directory that is not a discovery location. The documented containers are `skills/`, `skills/.curated/`, `skills/.experimental/`, `skills/.system/` and the per-agent folders; `.staging-distributed-review` is none of them. | `skills/find/vercel-labs-skills/docs/creating-skills.md` |
| 3 | High | Validator could not run. `import yaml` fails (no PyYAML in the bundled runtime), the frontmatter regex accepts LF only while this repo checks out with `core.autocrlf=true`, and the repo root was hardcoded. | `ModuleNotFoundError: No module named 'yaml'`; LF-only regex confirmed failing on CRLF input |
| 4 | Medium | Two cited URLs had rotted (AWS Builders Library moved to `builder.aws.com`); nothing checked external links. | Fact-check run, 14/16 OK |
| 5 | Medium | Matrix coverage gaps: no consolidated treatment of acknowledgement vs completion, in-sequence scope, eventual consistency, durability (acknowledged write vs replication vs backup), or an identity known only after the fact (sequence/version). | `references/messaging.md`, `references/design-matrix.md` before the fix |
| 6 | Medium | Reconciliation, the matrix's most banking-specific habit, had no regression fixture. | `evals/scenarios.md` had five fixtures, none about settlement or reconciliation |
| 7 | Medium | Corrected the matrix silently. A reader of `SKILL.md` would think the skill agrees with "disable retry" and with 2PC-as-one-table. | `references/messaging.md` contradicted the matrix; nothing said so |
| 8 | Low | `USAGE.md` talks to the wrong reader: it explains what a gist is and whether a hosted fork is needed. That is handover commentary, not usage. | `USAGE.md` paragraphs 2 and 3 |
| 9 | Low | Description missed the user's own vocabulary. "Architecture design matrix" and "distributed" are the words the request will arrive in; the old description led with "REST APIs". | `SKILL.md` frontmatter before the fix |
| 10 | Low | Validator checks were partly invented (`short_description` 25 to 64 characters) and several `assert`s carried no message and disappear under `python -O`. | `validate.py` |

## What I changed

| File | Change |
|---|---|
| `skills/distributed-service-design-review/` | Installed from staging. Staging archived at `.archive/chatgpt-staging-2026-10-25/` (9 files, nothing deleted). |
| `SKILL.md` | Description now leads with architecture, design matrix and distributed systems while keeping the exclusions. Added the "one owner answers each question of record" rule for middlemen, "name the link that provides each guarantee", and recording the accepted decision with the evidence that would reopen it. |
| `references/design-matrix.md` | New `Delivery, ordering and consistency` section (acknowledgement, in-sequence scope, eventual consistency, durability). Ownership now separates request/trace, event and business transaction IDs, and asks for double-entry, value date, cut-off and scheme-report reconciliation for money movement. Removed the duplicated ordering sentence from the messaging section. |
| `references/messaging.md` | New `Delivery and consistency` section: exactly-once is an effect, not a hop; ack is not completion; replication is not backup. Added sequence/version identity for intents known only after the fact, removed the "TTL proves once" implication, scoped Kafka producer idempotence to the producer session, and added the Kafka-as-work-queue boundary. |
| `references/sources.md` | Fixed both AWS Builders Library URLs. Recorded the matrix's provenance and its deliberate corrections in one place. Marked the Kafka anchors as pinned to 4.1. |
| `references/prompts.md` | Added an incident follow-up prompt. Paths unchanged and now real. |
| `evals/scenarios.md` | Added a compensated-transfer fixture and a replication-is-not-durability fixture. Added how to run a fixture. |
| `agents/openai.yaml` | `short_description` now carries "architecture" within the 64-character limit; `default_prompt` unchanged in shape. |
| `scripts/validate-skills.py` | Replaced the staged validator: no third-party imports, CRLF normalisation, repo root derived from the script, messages on every failure, non-zero exit, checks every skill under `skills/`, and reports words/links/metadata per skill. |
| `skills/README.md` | New index: what the skill is for, how to invoke it, how to add a skill, provenance. |
| `README.md` | Was empty; now indexes `md/`, `skills/` and the validator. |
| `C:\dev\common\skills\denistek` | Directory junction to `denistek\skills`, so the skill is visible from the common skills folder without a second copy. |

## Verification performed

- `python scripts/validate-skills.py`: PASS, 1 skill, 0 errors, 6 checks, 8 internal links, 663-word entrypoint.
- CRLF regression: the rewritten parser reads CRLF frontmatter and metadata; the LF-only regex it replaced fails on the same bytes, confirming the bug was real and is fixed.
- Live fixture run: a fresh agent was given only `SKILL.md` and the compensated-transfer description. It identified the refund-plus-settlement double-spend, required settlement-file reconciliation with owner, cadence, safe repair and escalation, rejected retry-only, and stated that compensation does not prove the rail did nothing. All expected points present.
- External sources: 16 URLs fetched, 8 claims checked against primary text, 2 corrections applied.
- Not run: no runtime tests against a real service, and no check that `npx skills` follows the junction. Both are outside what a prose skill claims.

## Left to you

1. Nothing is committed. The work is in the working tree: `git add skills scripts README.md md/research` then commit when you have reviewed it. `md/CLAUDE.md` and `md/sdlc-automation-research-prompt.md` were already dirty before this work and were not touched.
2. No global registration. The skill is reachable by path, and by `$distributed-service-design-review` or `/distributed-service-design-review` only if a harness is pointed at `denistek/skills`. Say the word and I will link it into the harness skill directories.
3. The junction at `C:\dev\common\skills\denistek` is a convenience, not a second copy. Remove it with `Remove-Item C:\dev\common\skills\denistek` if you prefer one canonical path only.

## Feedback to send ChatGPT

```text
You built distributed-service-design-review and left it in C:\dev\common\skills\.staging-distributed-review. I reviewed it, fact-checked it, installed it, and closed the gaps. Apply this to your next handover.

WHAT HELD UP
Every external claim was independently checked against primary docs and all were correct: Kafka producer idempotence (retries > 0, acks=all, max.in.flight <= 5), the read_uncommitted default, the five-minute SQS FIFO dedup window, RFC 9110/9457, OWASP API 2023, Zalando, SEI ATAM, the SRE workbook and the microservices.io patterns. Your corrections to the source matrix (do not disable retries; one table is not 2PC; read_committed is not exactly-once) are right and well argued. Self-containment, the failure-first framing and the six-column deliverable matrix are good.

WHAT TO FIX
1. Install before documenting. All four prompts pointed at C:/dev/common/denistek/skills/... which did not exist, and the package sat in a folder that is not one of the documented discovery containers (skills/, skills/.curated/, skills/.experimental/, skills/.system/, or a per-agent skills folder). A finished skill is placed, discoverable, and proven by running one prompt from its own usage doc. Acceptance: every path named in the package resolves on disk.
2. Make the validator runnable. It failed at import yaml on a machine without PyYAML, and its frontmatter regex accepted LF only while the repo checks out with core.autocrlf=true. Derive the repo root from the script, parse without third-party packages, normalise line endings, print a message for every failure, exit non-zero. Acceptance: it passes on a CRLF checkout and reports a mismatched name as an error.
3. Every URL you cite is a claim. Two AWS Builders Library links had moved to builder.aws.com. Fetch what you cite, or mark it unverified.
4. Cover the whole matrix. Acknowledgement vs completion, in-sequence scope, eventual consistency and durability were absent, and an identity that only exists after the fact (sequence or version) had no treatment. Reconciliation, the most banking-specific habit in the matrix, had no regression fixture. I added a Delivery, ordering and consistency section plus settlement-reconciliation and replication-is-not-durability fixtures.
5. Say where you disagree with the source. You contradicted "disable retry" and "2PC ~ same table" inside messaging.md and told nobody, so the skill and the matrix looked aligned when they were not. Put every deliberate divergence in one maintainer-visible place and mention it in the handover.
6. Write each doc for its reader. USAGE.md explained what a gist is; that belongs in the handover, not in usage. Usage goes in the skills index, provenance in sources.md.
7. Trigger wording is the product. The description led with "REST APIs" and omitted "architecture design matrix" and "distributed", which is how the request will actually arrive.

RULES FOR NEXT TIME
Finish means placed, discoverable, and exercised, not just written. Every path in a doc is an assertion to test. A bundled validator must run with no third-party packages. Record departures from the supplied source. Keep the package self-contained and the index outside it.
```
