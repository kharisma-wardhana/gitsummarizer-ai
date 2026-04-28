from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import gitlab

from .config import get_settings


@dataclass
class CommitData:
    sha: str
    message: str
    author: str
    committed_at: datetime
    changed_files: list[str] = field(default_factory=list)

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "sha": self.sha[:8],
            "message": self.message.strip(),
            "author": self.author,
            "date": self.committed_at.date().isoformat(),
            "changed_files": self.changed_files,
            "files_changed_count": len(self.changed_files),
        }


def fetch_commits(project_id_or_path: str, since: datetime) -> list[CommitData]:
    """Fetch all commits in the window with their changed-file lists.

    The changed-file list is what lets the LLM estimate Weight/Difficulty
    (PRD §3.2), so it must be populated. We pull filenames only (no patches)
    to keep the round-trip fast.
    """
    s = get_settings()
    gl = gitlab.Gitlab(s.gitlab_url, private_token=s.gitlab_token)
    project = gl.projects.get(project_id_or_path)

    raw_commits = project.commits.list(since=since.isoformat(), all=True)

    out: list[CommitData] = []
    for c in raw_commits:
        diffs = c.diff(get_all=True)
        files = [d.get("new_path") or d.get("old_path") for d in diffs]
        files = [f for f in files if f]
        out.append(
            CommitData(
                sha=c.id,
                message=c.message,
                author=c.author_name,
                committed_at=datetime.fromisoformat(c.committed_date.replace("Z", "+00:00")),
                changed_files=files,
            )
        )

    out.sort(key=lambda c: c.committed_at, reverse=True)
    return out
