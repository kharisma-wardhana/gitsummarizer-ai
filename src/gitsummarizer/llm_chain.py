import json
from datetime import date

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .config import get_settings
from .gitlab_client import CommitData
from .schema import Roadmap


SYSTEM_PROMPT = """You are a senior software engineering analyst.

Your job: turn a list of git commits into a concise, structured engineering roadmap.

Rules:
1. GROUP related commits into single Initiatives. Use commit messages, file paths,
   and authors to identify related work. Multiple small commits that build one
   feature or fix one bug should become ONE initiative — never one initiative per
   commit unless the commit truly stands alone.
2. For each Initiative:
   - "initiative": short business-facing title (the WHY).
   - "description": one or two sentences of technical summary (the WHAT/HOW).
   - "category": pick the single best fit from the allowed list.
   - "weight": Fibonacci 1, 2, 3, 5, or 8. Use changed-file count and breadth as
     the primary signal: trivial single-file = 1, focused multi-file = 3,
     cross-cutting / many areas = 5 or 8.
   - "status": default "Closed" because the work is already in git history.
     Use "In Progress" only if commit messages indicate WIP / partial work.
   - "priority": infer from message language ("hotfix", "urgent" → High;
     "polish", "cleanup" → Low; default Medium).
   - "finish_date": the date of the LATEST commit in the group, ISO format.
   - "output": short tangible artifact, e.g. "New /users API endpoint",
     "Reduced p95 latency", "Migrated to OAuth2".
   - "difficulty": Easy / Medium / Hard, based on file count breadth and
     whether the change touches sensitive areas (auth, db migrations, infra).
3. Output MUST exactly match the schema below. Do not add or remove fields.
4. Set "repository" to the value provided. Set "period_start" and "period_end"
   to the values provided.

{format_instructions}
"""

USER_PROMPT = """Repository: {repository}
Period: {period_start} to {period_end}

Commits ({commit_count} total), newest first:
{commits_json}
"""


_parser = PydanticOutputParser(pydantic_object=Roadmap)


def _build_chain():
    s = get_settings()
    llm = ChatOpenAI(
        model=s.openai_model,
        api_key=s.openai_api_key,
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("user", USER_PROMPT),
        ]
    ).partial(format_instructions=_parser.get_format_instructions())
    return prompt | llm | _parser


async def summarize(
    commits: list[CommitData],
    repository: str,
    period: tuple[date, date],
) -> Roadmap:
    chain = _build_chain()
    commits_json = json.dumps([c.to_prompt_dict() for c in commits], indent=2)
    return await chain.ainvoke(
        {
            "repository": repository,
            "period_start": period[0].isoformat(),
            "period_end": period[1].isoformat(),
            "commit_count": len(commits),
            "commits_json": commits_json,
        }
    )
