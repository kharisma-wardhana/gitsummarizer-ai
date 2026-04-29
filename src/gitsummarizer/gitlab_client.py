import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import gitlab
from gitlab.exceptions import GitlabError

from .config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class CommitData:
    sha: str
    message: str
    author: str
    committed_at: datetime
    changed_files: list[str] = field(default_factory=list)
    project: Optional[str] = None

    def to_prompt_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "sha": self.sha[:8],
            "message": self.message.strip(),
            "author": self.author,
            "date": self.committed_at.date().isoformat(),
            "changed_files": self.changed_files,
            "files_changed_count": len(self.changed_files),
        }
        if self.project:
            d["project"] = self.project
        return d


def _commit_to_data(c: Any, project_path: Optional[str] = None) -> CommitData:
    diffs = c.diff(get_all=True)
    files = [d.get("new_path") or d.get("old_path") for d in diffs]
    files = [f for f in files if f]
    return CommitData(
        sha=c.id,
        message=c.message,
        author=c.author_name,
        committed_at=datetime.fromisoformat(c.committed_date.replace("Z", "+00:00")),
        changed_files=files,
        project=project_path,
    )


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

    out = [_commit_to_data(c, project_path=project.path_with_namespace) for c in raw_commits]
    out.sort(key=lambda c: c.committed_at, reverse=True)
    return out


def fetch_user_commits(username: str, since: datetime) -> list[CommitData]:
    """Fetch commits authored by ``username`` across every project the token
    can see, regardless of group.

    Strategy: list every project the PAT has membership in, restrict to
    those active in the window via ``last_activity_after`` (huge speedup
    when the user belongs to many dormant projects), then for each project
    query commits filtered by ``author=username`` server-side. Projects
    that error out (archived, permissions, etc.) are logged and skipped
    so a single bad project does not abort the whole report.
    """
    s = get_settings()
    gl = gitlab.Gitlab(s.gitlab_url, private_token=s.gitlab_token)

    projects = gl.projects.list(
        membership=True,
        all=True,
        simple=True,
        last_activity_after=since.isoformat(),
        order_by="last_activity_at",
        sort="desc",
    )

    out: list[CommitData] = []
    for p in projects:
        try:
            project = gl.projects.get(p.id, lazy=True)
            raw_commits = project.commits.list(
                since=since.isoformat(),
                author=username,
                all=True,
            )
        except GitlabError as e:
            logger.warning("Skipping project %s: %s", p.path_with_namespace, e)
            continue

        for c in raw_commits:
            try:
                out.append(_commit_to_data(c, project_path=p.path_with_namespace))
            except GitlabError as e:
                logger.warning(
                    "Skipping commit %s in %s: %s", c.id, p.path_with_namespace, e
                )

    out.sort(key=lambda c: c.committed_at, reverse=True)
    return out
