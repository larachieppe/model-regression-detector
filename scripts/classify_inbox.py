import argparse

from dotenv import load_dotenv

from src.classifier import classify_email
from src.gmail_client import fetch_recent_emails
from src.prompt_loader import load_prompt_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify recent emails in your inbox.")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent emails to fetch")
    parser.add_argument("--prompt-version", default="v2", help="Prompt version to use, e.g. v1 or v2")
    args = parser.parse_args()

    load_dotenv()
    config = load_prompt_config(args.prompt_version)
    emails = fetch_recent_emails(limit=args.limit)

    for inbox_email in emails:
        result = classify_email(inbox_email.email_text, config)
        print(f"[{result.category.value:>10}] {inbox_email.subject!r} -- {result.summary}")


if __name__ == "__main__":
    main()
