from datetime import date
from pathlib import Path

from gitsummarizer.markdown_writer import (
    filename_for,
    render_markdown,
    write_roadmap,
)
from gitsummarizer.schema import (
    Category,
    Difficulty,
    Initiative,
    Priority,
    Roadmap,
    Status,
)


def _sample_roadmap(*, repositories: list[str] | None = None) -> Roadmap:
    return Roadmap(
        repository="group/my-project",
        repositories=repositories if repositories is not None else ["group/my-project", "group/other"],
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 8),
        initiatives=[
            Initiative(
                initiative="Auth Refactor",
                repositories=["group/my-project"],
                description="Migrated JWT logic to OAuth2",
                category=Category.SECURITY,
                weight=5,
                status=Status.CLOSED,
                priority=Priority.HIGH,
                start_date=date(2026, 4, 2),
                finish_date=date(2026, 4, 5),
                output="Enhanced Security",
                difficulty=Difficulty.HARD,
            ),
            Initiative(
                initiative="UI Polish",
                repositories=["group/other"],
                description="Fixed CSS grid issues on mobile",
                category=Category.OTHERS,
                weight=2,
                status=Status.IN_PROGRESS,
                priority=Priority.MEDIUM,
                start_date=date(2026, 4, 4),
                finish_date=date(2026, 4, 6),
                output="Responsive Dashboard",
                difficulty=Difficulty.EASY,
            ),
        ],
    )


def test_filename_format_matches_prd():
    name = filename_for(_sample_roadmap())
    assert name == "engineer_roadmap_08042026_group_my-project.md"


def test_render_contains_header_and_period():
    md = render_markdown(_sample_roadmap())
    assert md.startswith("# Engineering Roadmap: group/my-project")
    assert "**Period:** 01/04/2026 - 08/04/2026" in md


def test_render_uses_display_enum_values():
    md = render_markdown(_sample_roadmap())
    assert "| In Progress |" in md
    assert "| High |" in md
    assert "| Security |" in md


def test_render_includes_all_table_columns():
    md = render_markdown(_sample_roadmap())
    header = (
        "| Initiative | Repositories | Description | Category | Weight | Status | "
        "Priority | Start Date | Finish Date | Output | Difficulty |"
    )
    assert header in md


def test_render_renders_finish_date_in_dmy():
    md = render_markdown(_sample_roadmap())
    assert "05/04/2026" in md
    assert "06/04/2026" in md


def test_render_renders_start_date_in_dmy():
    md = render_markdown(_sample_roadmap())
    assert "02/04/2026" in md
    assert "04/04/2026" in md


def test_render_includes_repositories_line_when_multi_repo():
    md = render_markdown(_sample_roadmap())
    assert "**Repositories:** group/my-project, group/other" in md


def test_render_omits_repositories_line_when_single_repo():
    md = render_markdown(_sample_roadmap(repositories=["group/my-project"]))
    assert "**Repositories:**" not in md


def test_render_omits_repositories_line_when_no_repos():
    md = render_markdown(_sample_roadmap(repositories=[]))
    assert "**Repositories:**" not in md


def test_render_initiative_repositories_cell():
    md = render_markdown(_sample_roadmap())
    # The per-row cell must show the initiative's own repository
    assert "| group/my-project |" in md
    assert "| group/other |" in md


def test_write_roadmap_creates_file(tmp_path: Path):
    rm = _sample_roadmap()
    path = write_roadmap(rm, tmp_path)
    assert path.exists()
    assert path.name == "engineer_roadmap_08042026_group_my-project.md"
    content = path.read_text(encoding="utf-8")
    assert "Auth Refactor" in content
