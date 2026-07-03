from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    GENERAL = "general"


class FewShotExample(BaseModel):
    email: str
    category: Category
    summary: str


class PromptConfig(BaseModel):
    """The versioned 'code' the eval pipeline runs against."""

    version: str
    created_at: datetime
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    system_prompt: str
    few_shot_examples: list[FewShotExample] = Field(default_factory=list)


class ClassificationInput(BaseModel):
    email_id: str
    email_text: str


class LLMClassification(BaseModel):
    """Exact shape requested from the model via structured outputs."""

    category: Category
    summary: str = Field(..., description="One-sentence summary of the email")


class ClassificationOutput(BaseModel):
    """LLMClassification plus run metadata, for eval/logging."""

    category: Category
    summary: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    prompt_version: str
    model: str

    @classmethod
    def from_llm_result(
        cls,
        result: LLMClassification,
        *,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        prompt_version: str,
        model: str,
    ) -> "ClassificationOutput":
        return cls(
            category=result.category,
            summary=result.summary,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_version=prompt_version,
            model=model,
        )
