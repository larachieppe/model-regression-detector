import os
import time
from typing import Protocol

from src.schemas import ClassificationOutput, LLMClassification, PromptConfig


class ChatClient(Protocol):
    """Minimal shape we need from an OpenAI-compatible client, so tests can
    swap in a fake without touching the network."""

    def parse(
        self, *, model: str, messages: list[dict], temperature: float,
        response_format: type[LLMClassification],
    ) -> tuple[LLMClassification, int, int]:
        """Returns (parsed_result, prompt_tokens, completion_tokens)."""
        ...


def _default_client() -> ChatClient:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export it or pass an explicit `client` "
            "(e.g. a fake) to classify_email for offline/testing use."
        )

    openai_client = OpenAI(api_key=api_key)

    class _Adapter:
        def parse(self, *, model, messages, temperature, response_format):
            completion = openai_client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format=response_format,
            )
            choice = completion.choices[0].message
            usage = completion.usage
            return choice.parsed, usage.prompt_tokens, usage.completion_tokens

    return _Adapter()


def build_messages(prompt_config: PromptConfig, email_text: str) -> list[dict]:
    messages = [{"role": "system", "content": prompt_config.system_prompt}]
    for example in prompt_config.few_shot_examples:
        messages.append({"role": "user", "content": example.email})
        messages.append({
            "role": "assistant",
            "content": LLMClassification(
                category=example.category, summary=example.summary
            ).model_dump_json(),
        })
    messages.append({"role": "user", "content": email_text})
    return messages


def classify_email(
    email_text: str,
    prompt_config: PromptConfig,
    client: ChatClient | None = None,
) -> ClassificationOutput:
    client = client or _default_client()
    messages = build_messages(prompt_config, email_text)

    start = time.perf_counter()
    parsed, prompt_tokens, completion_tokens = client.parse(
        model=prompt_config.model,
        messages=messages,
        temperature=prompt_config.temperature,
        response_format=LLMClassification,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    return ClassificationOutput.from_llm_result(
        parsed,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_version=prompt_config.version,
        model=prompt_config.model,
    )
