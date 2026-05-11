from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class Category(str, Enum):
    OKR = "OKR"
    IMPROVE_SOFT_SKILL = "Improve Soft Skill"
    IMPROVE_HARD_SKILL = "Improve Hard Skill"
    SYSTEM_PERFORMANCE = "System Performance"
    EFFICIENCY = "Efficiency"
    OPERATIONAL = "Operational"
    SYSTEM_DESIGN = "System Design"
    SECURITY = "Security"
    DATABASE = "Database"
    AI = "AI"
    STANDARDIZATION = "Standardization"
    OTHERS = "Others"


class Status(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    CLOSED = "Closed"
    CANCELED = "Canceled"
    ON_HOLD = "On Hold"


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


Weight = Literal[1, 2, 3, 5, 8]


class Initiative(BaseModel):
    initiative: str = Field(description="Business reason or high-level purpose of the change.")
    repositories: list[str] = Field(
        default_factory=list,
        description="Distinct repository paths (group/project) the grouped commits came from.",
    )
    description: str = Field(description="Technical but readable summary of the implementation.")
    category: Category
    weight: Weight = Field(description="Relative effort estimate, Fibonacci: 1, 2, 3, 5, or 8.")
    status: Status
    priority: Priority
    start_date: Optional[date] = Field(
        default=None,
        description="Date of the EARLIEST commit in this initiative group. Defaults to finish_date when omitted.",
    )
    finish_date: date = Field(description="Date of the latest commit in this initiative group.")
    output: str = Field(description="Tangible result (e.g. 'New API endpoint').")
    difficulty: Difficulty

    @model_validator(mode="after")
    def _default_start_date(self) -> "Initiative":
        if self.start_date is None:
            self.start_date = self.finish_date
        return self


class Roadmap(BaseModel):
    repository: str
    repositories: list[str] = Field(default_factory=list)
    period_start: date
    period_end: date
    initiatives: list[Initiative]
