# Skills

Reusable agent skills, one directory per skill, in the flat `skills/<name>/SKILL.md` layout that current skill discovery walks. Every skill is self-contained: references and evals live inside its directory.

## Available

| Skill | Reach for it when |
|---|---|
| [distributed-service-design-review](distributed-service-design-review/SKILL.md) | Reviewing or designing a distributed service or REST API: consistency, delivery and ordering guarantees, idempotency, transactions, resilience, cost, security, observability, deployment. |

## Using a skill

Agents discover a skill from its `SKILL.md` frontmatter when this directory is on their skill path. When it is not, name the path directly, as in the prompts inside each skill's `references/prompts.md`. For this repository:

- Codex: `$distributed-service-design-review`
- Claude Code: `/distributed-service-design-review`

Neither the flat prompt nor the short invocation needs a global install. A project that wants the skill in its own tree can copy the directory or add a junction to it; keep one canonical copy so edits are not forked.

## Adding a skill

1. Create `skills/<kebab-name>/SKILL.md` with `name` matching the directory and a model-facing `description` that carries the phrases a user would actually say.
2. Add `agents/openai.yaml` with `interface.display_name`, `interface.short_description` (25 to 64 characters) and a `default_prompt` that names `$<name>`.
3. Put material only some runs need in `references/`, reached by relative link; put realistic review fixtures in `evals/`.
4. Run `python scripts/validate-skills.py`, then re-read the skill with the writing guidance in mind: one meaning in one place, trigger wording in the description, nothing an agent already does by default.

## Provenance

`distributed-service-design-review` generalises a design matrix from banking delivery work and synthesises SEI ATAM, AWS Well-Architected, Google SRE, Zalando, OWASP, the IETF HTTP RFCs and Chris Richardson's patterns. `references/sources.md` carries the links, the version anchors and the places where the skill deliberately corrects a common shorthand. The prompt method draws on the `/better` gist kept at `C:\dev\common\skills\ideas\better\`; the two are independent, and this skill does not require it.
