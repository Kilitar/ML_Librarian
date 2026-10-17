"""Presentation-only normalization of source excerpts for Streamlit Markdown."""
import html
import re


def format_snippet(text: str) -> str:
    # Leave code samples untouched, including their escaping and HTML entities.
    parts = re.split(r"(```[\s\S]*?```|`[^`\n]+`)", text)
    for index in range(0, len(parts), 2):
        part = html.unescape(parts[index])
        # Notebook exports use both single and doubled backslashes at delimiters.
        part = re.sub(r"\\{1,2}\((.*?)\\{1,2}\)", lambda m: "$" + m[1] + "$", part, flags=re.S)
        part = re.sub(r"\\{1,2}\[(.*?)\\{1,2}\]", lambda m: "\n\n$$\n" + m[1] + "\n$$\n\n", part, flags=re.S)
        parts[index] = part
    return "".join(parts)
