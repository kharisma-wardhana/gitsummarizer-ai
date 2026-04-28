# PRD: GitSummarizer AI (Telegram-GitLab Integration)

## 1. Project Overview

The goal is to build a Python-based AI assistant that retrieves commit logs from GitLab, processes them using LLMs to infer intent and impact, and delivers a structured Markdown roadmap directly to a user via Telegram.

## 2. Technical Stack

* **Language:** Python 3.10+
* **Orchestration:** [LangChain](https://python.langchain.com/) (for prompt management and LLM chains)
* **LLM:** OpenAI **GPT-4o mini** (chosen for its high reasoning-to-cost ratio)
* **APIs:**
  * `python-telegram-bot` or `aiogram` (Telegram Bot API)
  * `python-gitlab` (GitLab REST API)
* **Environment:** Dockerized deployment (recommended)

---

## 3. Functional Requirements

### 3.1 Telegram Interaction

The bot must support commands or natural language triggers to initiate the report.

* **Input:** User sends a message like `/report 1w` (1 week) or `/report 1m` (1 month).
* **Context:** The bot should identify the repository context (either via a default config or a parameter in the message).

### 3.2 GitLab Data Retrieval

* **Scope:** Fetch all commits within the specified timeframe ($T \in \{7 \text{ days}, 30 \text{ days}\}$).
* **Metadata:** Capture commit message, author, date, and changed files (to provide the LLM with context for "difficulty" and "scope" estimation).

### 3.3 AI Processing & Summarization

Using LangChain, the system will pass the raw commit data to GPT-4o mini with a strictly defined system prompt.

**The Output Fields for each "Initiative":**

| Field | Description |
| :--- | :--- |
| **Initiative** | The business reason or high-level purpose of the change. |
| **Description** | A technical but readable summary of the implementation. |
| **Category** | OKR, Improve Soft Skill, Improve Hard Skill, System Performance, Efficiency, Operational, System Design, Security, Database, AI, Standardization, Others |
| **Weight** | Estimated relative effort (e.g., 1, 2, 3, 5, 8). |
| **Status** | Open, In Progress, Closed, Canceled, or On Hold. |
| **Priority** | Low, Medium, High. |
| **Finish Date** | The date of the latest commit in that logic group. |
| **Output** | The tangible result (e.g., "New API endpoint", "Improved UI"). |

### 3.4 Markdown Generation

The AI's structured response (preferably parsed via Pydantic using LangChain’s `output_parsers`) must be written to a file.

* **Filename Format:** `engineer_roadmap_ddmmyyyy_<repo_name>.md`

### 3.5 File Delivery

* The generated `.md` file is sent back to the user as a document attachment in the same Telegram chat thread.

---

## 4. Implementation Roadmap

### Phase 1: Infrastructure (Days 1-2)

* Register Telegram Bot via `@BotFather`.
* Generate GitLab Personal Access Token (PAT).
* Set up Python environment with `langchain`, `langchain-openai`, and `python-gitlab`.

### Phase 2: GitLab & Parser Logic (Days 3-4)

* Implement the GitLab client to fetch commits.
* **Key Challenge:** Grouping multiple commits that belong to the same feature.
    > *Note: We will feed the list of commits to GPT-4o mini and ask it to "group related commits into single initiatives."*

### Phase 3: LangChain & LLM Integration (Days 5-6)

* Create a `ChatPromptTemplate` that defines the Markdown table format.
* Implement a `PydanticOutputParser` to ensure the AI doesn't hallucinate the format.
* Test with GPT-4o mini to verify it correctly identifies "Difficulty" and "Weight" based on file change volume.

### Phase 4: Telegram Interface (Day 7)

* Connect the bot's "Document Send" method to the output of the AI chain.
* Add error handling for "No commits found in this period."

---

## 5. Sample Markdown Format

The bot will output the following structure inside the `.md` file:

```markdown
# Engineering Roadmap: [Repository Name]
**Period:** 01/04/2026 - 08/04/2026

| Initiative | Description | Category | Weight | Status | Priority | Finish Date | Output | Difficulty |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Auth Refactor** | Migrated JWT logic to OAuth2 | Security | 5 | Closed | High | 05/04/2026 | Enhanced Security | Hard |
| **UI Polish** | Fixed CSS grid issues on mobile | UI/UX | 2 | Closed | Medium | 06/04/2026 | Responsive Dashboard | Easy |
```

---

## 6. Success Metrics

* **Accuracy:** The AI correctly identifies the "Purpose" (Initiative) even if the commit message is vague (e.g., "fixed stuff").
* **Latency:** The report should be generated and sent within 15 seconds of the Telegram request.
* **Reliability:** Zero failures in Markdown formatting.
