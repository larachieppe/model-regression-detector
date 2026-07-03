from src.classifier import classify_email
from src.prompt_loader import load_prompt_config
from src.schemas import Category, LLMClassification


class FakeChatClient:
    """Stands in for the OpenAI client so tests run offline."""

    def __init__(self, response: LLMClassification):
        self.response = response

    def parse(self, *, model, messages, temperature, response_format):
        return self.response, 42, 7


def test_load_prompt_config_v1():
    config = load_prompt_config("v1")
    assert config.version == "v1"
    assert config.model == "gpt-4o-mini"
    assert len(config.few_shot_examples) == 4
    assert "billing" in config.system_prompt.lower()


def test_classify_email_uses_injected_client():
    config = load_prompt_config("v1")
    fake = FakeChatClient(
        LLMClassification(
            category=Category.BILLING,
            summary="Customer wants a refund for a duplicate charge.",
        )
    )

    result = classify_email(
        "I was double charged, please refund me.", config, client=fake
    )

    assert result.category == Category.BILLING
    assert result.prompt_tokens == 42
    assert result.completion_tokens == 7
    assert result.prompt_version == "v1"
    assert result.latency_ms >= 0


def test_classify_email_raises_without_key_or_client(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = load_prompt_config("v1")
    try:
        classify_email("test", config)
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "OPENAI_API_KEY" in str(e)
