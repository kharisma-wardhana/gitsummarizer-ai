import re
from pathlib import Path

from .schema import Roadmap


_TABLE_HEADER = (
    "| Initiative | Description | Category | Weight | Status | Priority | "
    "Finish Date | Output | Difficulty |"
)
_TABLE_SEP = (
    "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
)


def _slug(repo: str) -> str:
    cleaned = repo.replace("/", "_")
    cleaned = re.sub(r"[^A-Za-z0-9_\-]", "", cleaned)
    return cleaned or "repo"


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def filename_for(roadmap: Roadmap) -> str:
    date_part = roadmap.period_end.strftime("%d%m%Y")
    return f"engineer_roadmap_{date_part}_{_slug(roadmap.repository)}.md"


def render_markdown(roadmap: Roadmap) -> str:
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
    lines.append("")
    return "\n".join(lines)


def write_roadmap(roadmap: Roadmap, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename_for(roadmap)
    path.write_text(render_markdown(roadmap), encoding="utf-8")
    return path
