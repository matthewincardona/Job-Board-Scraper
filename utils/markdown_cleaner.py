import re

def clean_markdown(text: str) -> str:
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Fix escaped characters that break markdown
    text = (
        text
        .replace("\\-", "-")
        .replace("\\*", "*")
        .replace("\\+", "+")
        .replace("\\_", "_")
    )

    # Remove leading indentation that blocks markdown parsing
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.lstrip()

        # Keep real blank lines
        if stripped == "":
            cleaned_lines.append("")
            continue

        # List item fix: auto-insert spacing before lists
        if stripped.startswith(("* ", "- ", "1. ")):
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")

        cleaned_lines.append(stripped)

    cleaned = "\n".join(cleaned_lines)

    # Remove excessive blank lines (3+ becomes 2)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()
