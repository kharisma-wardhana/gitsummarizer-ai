import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile, Message

from .config import get_settings
from .gitlab_client import fetch_commits
from .llm_chain import summarize
from .markdown_writer import write_roadmap
from .windows import parse_window


logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.reply(
        "GitSummarizer AI ready.\n"
        "Use /report <window> [project] — e.g. `/report 1w` or `/report 1m group/project`."
    )


@router.message(Command("report"))
async def report_handler(message: Message) -> None:
    s = get_settings()
    text = message.text or ""
    parts = text.split()[1:]

    if not parts:
        await message.reply("Usage: /report <window> [project]\nExamples: /report 1w · /report 1m group/project")
        return

    try:
        window = parse_window(parts[0])
    except ValueError as e:
        await message.reply(str(e))
        return

    project = parts[1] if len(parts) > 1 else s.gitlab_default_project
    if not project:
        await message.reply("No default project configured. Pass one as the second argument.")
        return

    await message.reply(f"Fetching commits for `{project}` over the last {parts[0]}…")

    since = datetime.now(timezone.utc) - window
    try:
        commits = await asyncio.to_thread(fetch_commits, project, since)
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
            repository=project,
            period=(since.date(), datetime.now(timezone.utc).date()),
        )
    except Exception as e:
        logger.exception("LLM summarization failed")
        await message.reply(f"Summarization failed: {e}")
        return

    md_path = write_roadmap(roadmap, s.output_dir)
    await message.reply_document(FSInputFile(md_path))
