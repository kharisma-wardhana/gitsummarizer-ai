import re
from pathlib import Path
from typing import Optional

from .gitlab_client import CommitData
from .schema import Roadmap


_TABLE_HEADER = (
    "| Initiative | Description | Category | Weight | Status | Priority | "
    "Finish Date | Output | Difficulty |"
)
_TABLE_SEP = (
    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
)

_BULLET_MAX_LEN = 200


def _slug(repo: str) -> str:
    cleaned = repo.replace("/", "_")
    cleaned = re.sub(r"[^A-Za-z0-9_\-]", "", cleaned)
    return cleaned or "repo"


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _escape_bullet(text: str) -> str:
    first_line = text.split("\n", 1)[0].strip()
    cleaned = first_line.replace("`", "'").replace("|", "\\|")
    if len(cleaned) > _BULLET_MAX_LEN:
        cleaned = cleaned[: _BULLET_MAX_LEN - 1].rstrip() + "…"
    return cleaned


def filename_for(roadmap: Roadmap) -> str:
    date_part = roadmap.period_end.strftime("%d%m%Y")
    return f"engineer_roadmap_{date_part}_{_slug(roadmap.repository)}.md"


def render_markdown(
    roadmap: Roadmap, commits: Optional[list[CommitData]] = None
) -> str:
    lines = [
        f"# Engineering Roadmap: {roadmap.repository}",
        f"**Period:** {roadmap.period_start.strftime('%d/%m/%Y')} - "
        f"{roadmap.period_end.strftime('%d/%m/%Y')}",
        "",
        _TABLE_HEADER,
        _TABLE_SEP,
    ]
    for it in roadmap.initiatives:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"**{_escape_cell(it.initiative)}**",
                    _escape_cell(it.description),
                    it.category.value,
                    str(it.weight),
                    it.status.value,
                    it.priority.value,
                    it.finish_date.strftime("%d/%m/%Y"),
                    _escape_cell(it.output),
                    it.difficulty.value,
                ]
            )
            + " |"
        )

    if commits:
        by_sha = {c.sha[:8]: c for c in commits}
        section_lines: list[str] = []
        for it in roadmap.initiatives:
            resolved = [by_sha[s] for s in it.commit_shas if s in by_sha]
            if not resolved:
                continue
            resolved.sort(key=lambda c: c.committed_at, reverse=True)
            section_lines.append("")
            section_lines.append(f"### {_escape_cell(it.initiative)}")
            for c in resolved:
                bullet = (
                    f"- `{c.sha[:8]}` — {_escape_bullet(c.message)} "
                    f"*({c.author}, {c.committed_at.strftime('%d/%m/%Y')})*"
                )
                if c.web_url:
                    bullet += f" [link]({c.web_url})"
                section_lines.append(bullet)
        if section_lines:
            lines.append("")
            lines.append("## Commit Log")
            lines.extend(section_lines)

    lines.append("")
    return "\n".join(lines)


def write_roadmap(
    roadmap: Roadmap,
    output_dir: Path,
    commits: Optional[list[CommitData]] = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename_for(roadmap)
    path.write_text(render_markdown(roadmap, commits), encoding="utf-8")
    return path
