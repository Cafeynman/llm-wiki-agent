"""Mask Markdown code while preserving source offsets."""

from __future__ import annotations

import re


FENCE_OPEN_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")


def mask_inline_code(line: str) -> str:
    chars = list(line)
    index = 0

    while index < len(chars):
        if chars[index] != "`":
            index += 1
            continue

        run_start = index
        while index < len(chars) and chars[index] == "`":
            index += 1
        marker = "`" * (index - run_start)
        closing = line.find(marker, index)
        if closing == -1:
            continue

        for mask_index in range(run_start, closing + len(marker)):
            chars[mask_index] = " "
        index = closing + len(marker)

    return "".join(chars)


def mask_markdown_code(content: str) -> str:
    """Replace fenced and inline code with spaces without changing offsets."""
    masked_lines: list[str] = []
    fence_char: str | None = None
    fence_length = 0

    for line in content.splitlines(keepends=True):
        if fence_char is not None:
            closing = re.match(
                rf"^[ \t]{{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*(?:\r?\n)?$",
                line,
            )
            masked_lines.append(
                "".join(char if char in "\r\n" else " " for char in line)
            )
            if closing:
                fence_char = None
                fence_length = 0
            continue

        opening = FENCE_OPEN_RE.match(line)
        if opening:
            marker = opening.group(1)
            fence_char = marker[0]
            fence_length = len(marker)
            masked_lines.append(
                "".join(char if char in "\r\n" else " " for char in line)
            )
            continue

        masked_lines.append(mask_inline_code(line))

    return "".join(masked_lines)
