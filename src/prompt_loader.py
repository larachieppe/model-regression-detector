from pathlib import Path

import yaml

from src.schemas import PromptConfig

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt_config(version: str) -> PromptConfig:
    """Load prompts/<version>.yaml (or a bare filename) into a PromptConfig."""
    filename = version if version.endswith(".yaml") else f"classifier_{version}.yaml"
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No prompt file found at {path}")

    with path.open() as f:
        raw = yaml.safe_load(f)

    return PromptConfig(**raw)
