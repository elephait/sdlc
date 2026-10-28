# Skills

Reusable agent skills, one directory per skill, in the flat `skills/<name>/SKILL.md` layout that current skill discovery walks. Every skill is self-contained: references and evals live inside its directory.

## Available

| Skill | Reach for it when |
|---|---|
| [distributed-service-design-review](distributed-service-design-review/SKILL.md) | Reviewing or designing a distributed service or REST API: consistency, delivery and ordering guarantees, idempotency, transactions, resilience, cost, security, observability, deployment. |
| [tracked-story](tracked-story/SKILL.md) | Delivering a story with traceable review, a readiness gate and a local commit report (the SDLC workflow). |

## Using a skill

Agents discover a skill from its `SKILL.md` frontmatter when this directory is on their skill path. When it is not, name the path directly, as in the prompts inside each skill's `references/prompts.md`. For this repository:

- Codex: `$distributed-service-design-review`
- Claude Code: `/distributed-service-design-review`, or `/sdlc:distributed-service-design-review` through the plugin
- Copilot: through the plugin in `copilot-customization/plugin`

This directory is the only place to edit a skill. The Copilot and Claude plugins carry generated copies made by `python scripts/sync-customizations.py`; never edit those.

## Adding a skill

1. Create `skills/<kebab-name>/SKILL.md` with `name` matching the directory and a model-facing `description` that carries the phrases a user would actually say.
2. Add `agents/openai.yaml` (Codex only; the sync leaves it out of the plugins) with `interface.display_name`, `interface.short_description` (25 to 64 characters) and a `default_prompt` that names `$<name>`.
3. Put material only some runs need in `references/`, reached by relative link; put realistic review fixtures in `evals/`.
4. Run `python scripts/sync-customizations.py`, then `python scripts/validate-skills.py`, then re-read the skill with the writing guidance in mind: one meaning in one place, trigger wording in the description, nothing an agent already does by default.

## Provenance

`distributed-service-design-review` generalises a design matrix from banking delivery work and synthesises SEI ATAM, AWS Well-Architected, Google SRE, Zalando, OWASP, the IETF HTTP RFCs and Chris Richardson's patterns. `references/sources.md` carries the links, the version anchors and the places where the skill deliberately corrects a common shorthand. The prompt method draws on the `/better` gist kept at `C:\dev\common\skills\ideas\better\`; the two are independent, and this skill does not require it.
