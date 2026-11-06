#!/usr/bin/env python3
"""Validate the agent skills under <repo>/skills against the local conventions.

Checks the things this repo actually depends on: frontmatter the harnesses can
read, a name that matches its directory, a bounded description, relative links
that resolve inside the package, Codex UI metadata, and no unfinished-work
markers. Deliberately dependency-free, so it runs on any Python 3.9+ without a
virtualenv, and CRLF-safe, because this repo checks out with core.autocrlf=true.

Usage:
    python scripts/validate-skills.py
    python scripts/validate-skills.py --skill distributed-service-design-review
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"

NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.S)
KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")
UNFINISHED = ("[TODO:", "TODO:", "TBD", "FIXME", "[FIXME:")

MAX_ENTRY_WORDS = 1500
MIN_DESCRIPTION = 40
MAX_DESCRIPTION = 1024
MIN_SHORT_DESCRIPTION = 25
MAX_SHORT_DESCRIPTION = 64


def read_text(path: Path) -> str:
    """Read as UTF-8 and normalise line endings so parsing is checkout-independent."""
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_scalars(block: str) -> dict[str, str]:
    """Parse the flat `key: value` and `key: |` subset of YAML skills use.

    Avoids a PyYAML dependency that the target machines do not have.
    """
    data: dict[str, str] = {}
    key: str | None = None
    collected: list[str] = []

    def flush() -> None:
        nonlocal key, collected
        if key is not None:
            data[key] = " ".join(part.strip() for part in collected).strip()
        key, collected = None, []

    for line in block.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = KEY_RE.match(line) if not line[:1].isspace() else None
        if match:
            flush()
            name, rest = match.group(1), match.group(2).strip()
            if rest in ("|", ">", "|-", ">-", "|+", ">+"):
                key = name
            else:
                data[name] = _unquote(rest)
        elif key is not None:
            collected.append(line)
    flush()
    return data


def parse_nested(block: str) -> dict[str, str]:
    """Parse one level of nesting, enough for `interface:` metadata."""
    data: dict[str, str] = {}
    parent: str | None = None
    for line in block.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^(\s*)([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            continue
        indent, name, rest = len(match.group(1)), match.group(2), _unquote(match.group(3).strip())
        if indent == 0:
            parent = name if not rest else None
            if rest:
                data[name] = rest
        elif parent:
            data[f"{parent}.{name}"] = rest
    return data


def split_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    # Normalise here too: this repo checks out with core.autocrlf=true, and a
    # caller should not have to remember read_text() to parse safely.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    return parse_scalars(match.group(1)), text[match.end():]


def check_links(package: Path, problems: list[str]) -> int:
    checked = 0
    for path in sorted(package.rglob("*.md")):
        for target in LINK_RE.findall(read_text(path)):
            target = target.strip()
            if not target or "://" in target or target.startswith(("#", "mailto:")):
                continue
            relative = target.split("#", 1)[0].replace("\\", "/")
            if not relative:
                continue
            resolved = (path.parent / relative).resolve()
            where = path.relative_to(package)
            if not resolved.is_relative_to(package.resolve()):
                problems.append(f"{where}: link escapes the package: {target}")
            elif not resolved.exists():
                problems.append(f"{where}: broken link: {target}")
            checked += 1
    return checked


def check_skill(package: Path, warnings: list[str]) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    passes: list[str] = []
    entry = package / "SKILL.md"

    if not entry.is_file():
        return [f"{package.name}: missing SKILL.md"], passes

    text = read_text(entry)
    meta, body = split_frontmatter(text)
    if meta is None:
        problems.append(f"{entry.relative_to(REPO)}: no closing frontmatter block")
        meta, body = {}, text
    else:
        passes.append("frontmatter")

    name = meta.get("name", "")
    if name != package.name:
        problems.append(f"name {name!r} does not match directory {package.name!r}")
    elif not NAME_RE.fullmatch(name):
        problems.append(f"name {name!r} is not lower-kebab-case")
    else:
        passes.append("name")

    description = meta.get("description", "")
    if not MIN_DESCRIPTION <= len(description) <= MAX_DESCRIPTION:
        problems.append(
            f"description is {len(description)} chars, expected "
            f"{MIN_DESCRIPTION}-{MAX_DESCRIPTION}"
        )
    elif "\n" in description:
        problems.append("description must stay on one line")
    else:
        passes.append("description")

    for path in sorted(package.rglob("*.md")):
        for marker in UNFINISHED:
            if marker in read_text(path):
                problems.append(f"{path.relative_to(REPO)}: unfinished marker {marker!r}")
                break

    links = check_links(package, problems)
    passes.append(f"{links} links")

    words = len(body.split())
    if words > MAX_ENTRY_WORDS:
        warnings.append(f"SKILL.md body is {words} words; consider disclosing reference")
    passes.append(f"{words} words")

    ui_path = package / "agents" / "openai.yaml"
    if not ui_path.is_file():
        problems.append(f"{package.name}: missing agents/openai.yaml")
    else:
        ui = parse_nested(read_text(ui_path))
        short = ui.get("interface.short_description", "")
        prompt = ui.get("interface.default_prompt", "")
        if not ui.get("interface.display_name"):
            problems.append("agents/openai.yaml: missing interface.display_name")
        if not MIN_SHORT_DESCRIPTION <= len(short) <= MAX_SHORT_DESCRIPTION:
            problems.append(
                f"agents/openai.yaml: short_description is {len(short)} chars, "
                f"expected {MIN_SHORT_DESCRIPTION}-{MAX_SHORT_DESCRIPTION}"
            )
        if f"${name}" not in prompt:
            problems.append(f"agents/openai.yaml: default_prompt does not mention ${name}")
        if not problems or all("agents/openai.yaml" not in p for p in problems):
            passes.append("Codex metadata")

    return problems, passes


def discover(root: Path) -> list[Path]:
    packages = []
    for entry in sorted(root.rglob("SKILL.md")):
        relative = entry.relative_to(root)
        if any(part.startswith(".") or part == "node_modules" for part in relative.parts):
            continue
        packages.append(entry.parent)
    return packages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skill", help="validate one skill by directory name")
    args = parser.parse_args()

    if not SKILLS.is_dir():
        print(f"FAIL: no skills directory at {SKILLS}")
        return 1

    packages = discover(SKILLS)
    if args.skill:
        packages = [p for p in packages if p.name == args.skill]
        if not packages:
            print(f"FAIL: no skill named {args.skill!r} under {SKILLS}")
            return 1

    if not packages:
        print(f"FAIL: no SKILL.md found under {SKILLS}")
        return 1

    errors = 0
    warnings: list[str] = []
    for package in packages:
        problems, passes = check_skill(package, warnings)
        status = "FAIL" if problems else "PASS"
        print(f"{status} {package.name}  ({len(passes)} checks: {', '.join(passes)})")
        for problem in problems:
            print(f"     - {problem}")
        errors += len(problems)

    for warning in warnings:
        print(f"WARN {warning}")

    print(f"\n{len(packages)} skill(s), {errors} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
