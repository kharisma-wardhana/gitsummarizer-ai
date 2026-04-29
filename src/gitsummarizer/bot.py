import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message

from .config import get_settings
from .gitlab_client import fetch_commits, fetch_user_commits
from .llm_chain import summarize
from .markdown_writer import write_roadmap
from .windows import parse_window


logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.reply(
        "GitSummarizer AI ready.\n"
        "Use /report <window> [project|all] — e.g. `/report 1w`, "
        "`/report 1m group/project`, or `/report 1w all` to scan every "
        "project the configured GitLab user touched."
    )


def _resolve_target(arg: Optional[str], s) -> tuple[Optional[str], Optional[str]]:
    """Return (project, error). project=None means user-wide scan."""
    user_wide = arg == "all" or (arg is None and not s.gitlab_default_project)
    if user_wide:
        if not s.gitlab_username:
            return None, (
                "GITLAB_USERNAME is not set — cannot scan all projects. "
                "Either set it in .env or pass a specific `group/project`."
            )
        return None, None
    return arg or s.gitlab_default_project, None


async def _gather_commits(project: Optional[str], since, s):
    if project is None:
        return await asyncio.to_thread(fetch_user_commits, s.gitlab_username, since)
    return await asyncio.to_thread(fetch_commits, project, since)


@router.message(Command("report"))
async def report_handler(message: Message) -> None:
    s = get_settings()
    parts = (message.text or "").split()[1:]

    if not parts:
        await message.reply(
            "Usage: /report <window> [project|all]\n"
            "Examples: /report 1w · /report 1m group/project · /report 1w all"
        )
        return

    try:
        window = parse_window(parts[0])
    except ValueError as e:
        await message.reply(str(e))
        return

    project, err = _resolve_target(parts[1] if len(parts) > 1 else None, s)
    if err:
        await message.reply(err)
        return

    since = datetime.now(timezone.utc) - window
    if project is None:
        target_label = f"@{s.gitlab_username} (all projects)"
        await message.reply(
            f"Scanning every accessible project for commits by "
            f"`{s.gitlab_username}` over the last {parts[0]}… this can take a moment."
        )
    else:
        target_label = project
        await message.reply(f"Fetching commits for `{project}` over the last {parts[0]}…")

    try:
        commits = await _gather_commits(project, since, s)
    except Exception as e:
        logger.exception("GitLab fetch failed")
        await message.reply(f"GitLab fetch failed: {e}")
        return

    if not commits:
        await message.reply("No commits found in this period.")
        return

    await message.reply(f"Got {len(commits)} commits. Summarizing…")

    try:
        roadmap = await summarize(
            commits,
            repository=target_label,
            period=(since.date(), datetime.now(timezone.utc).date()),
        )
    except Exception as e:
        logger.exception("LLM summarization failed")
        await message.reply(f"Summarization failed: {e}")
        return

    md_path = write_roadmap(roadmap, s.output_dir)
    await message.reply_document(FSInputFile(md_path))
