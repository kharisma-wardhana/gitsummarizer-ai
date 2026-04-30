from datetime import date, datetime, timezone
from pathlib import Path

from gitsummarizer.gitlab_client import CommitData
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


def _sample_roadmap() -> Roadmap:
    return Roadmap(
        repository="group/my-project",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 8),
        initiatives=[
            Initiative(
                initiative="Auth Refactor",
                description="Migrated JWT logic to OAuth2",
                category=Category.SECURITY,
                weight=5,
                status=Status.CLOSED,
                priority=Priority.HIGH,
                finish_date=date(2026, 4, 5),
                output="Enhanced Security",
                difficulty=Difficulty.HARD,
            ),
            Initiative(
                initiative="UI Polish",
                description="Fixed CSS grid issues on mobile",
                category=Category.OTHERS,
                weight=2,
                status=Status.IN_PROGRESS,
                priority=Priority.MEDIUM,
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
        "| Initiative | Description | Category | Weight | Status | Priority | "
        "Finish Date | Output | Difficulty |"
    )
    assert header in md


def test_render_renders_finish_date_in_dmy():
    md = render_markdown(_sample_roadmap())
    assert "05/04/2026" in md
    assert "06/04/2026" in md


def test_write_roadmap_creates_file(tmp_path: Path):
    rm = _sample_roadmap()
    path = write_roadmap(rm, tmp_path)
    assert path.exists()
    assert path.name == "engineer_roadmap_08042026_group_my-project.md"
    content = path.read_text(encoding="utf-8")
    assert "Auth Refactor" in content


def _sample_commits() -> list[CommitData]:
    return [
        CommitData(
            sha="abc12345abcdef",
            message="Switch JWT verification to OAuth2 introspection\n\nLong body",
            author="Alice",
            committed_at=datetime(2026, 4, 5, 10, 0, tzinfo=timezone.utc),
            web_url="https://gitlab.example.com/group/my-project/-/commit/abc12345",
        ),
        CommitData(
            sha="def67890abcdef",
            message="Drop legacy session cookie path",
            author="Bob",
            committed_at=datetime(2026, 4, 4, 9, 0, tzinfo=timezone.utc),
            web_url="https://gitlab.example.com/group/my-project/-/commit/def67890",
        ),
    ]


def _roadmap_with_commit_shas(shas: list[str]) -> Roadmap:
    rm = _sample_roadmap()
    rm.initiatives[0].commit_shas = shas
    return rm


def test_render_includes_commit_log_when_commits_provided():
    rm = _roadmap_with_commit_shas(["abc12345", "def67890"])
    md = render_markdown(rm, commits=_sample_commits())
    assert "## Commit Log" in md
    assert "### Auth Refactor" in md
    assert "`abc12345` — Switch JWT verification to OAuth2 introspection" in md
    assert "*(Alice, 05/04/2026)*" in md
    assert "[link](https://gitlab.example.com/group/my-project/-/commit/abc12345)" in md
    # newest-first ordering inside the section
    assert md.index("`abc12345`") < md.index("`def67890`")


def test_render_omits_commit_log_when_no_commits_passed():
    rm = _roadmap_with_commit_shas(["abc12345"])
    md = render_markdown(rm)
    assert "## Commit Log" not in md


def test_render_omits_commit_log_when_no_initiative_has_shas():
    md = render_markdown(_sample_roadmap(), commits=_sample_commits())
    assert "## Commit Log" not in md


def test_render_skips_unresolved_shas():
    rm = _roadmap_with_commit_shas(["zzzzzzzz"])
    md = render_markdown(rm, commits=_sample_commits())
    assert "## Commit Log" not in md
    assert "zzzzzzzz" not in md
