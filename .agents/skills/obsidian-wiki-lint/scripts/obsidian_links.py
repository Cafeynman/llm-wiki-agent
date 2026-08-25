"""Shared, span-preserving scanner for Obsidian wikilinks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator


@dataclass(frozen=True)
class WikilinkParts:
    target: str
    fragment: str
    alias: str
    has_alias: bool
    alias_separator_escaped: bool


@dataclass(frozen=True)
class WikilinkMatch:
    source: str
    start_index: int
    end_index: int

    def group(self, index: int = 0) -> str:
        if index == 0:
            return self.source[self.start_index : self.end_index]
        if index == 1:
            return self.source[self.start_index + 2 : self.end_index - 2]
        raise IndexError("wikilink scanner exposes only groups 0 and 1")

    def span(self, group: int = 0) -> tuple[int, int]:
        if group == 0:
            return self.start_index, self.end_index
        if group == 1:
            return self.start_index + 2, self.end_index - 2
        raise IndexError("wikilink scanner exposes only groups 0 and 1")

    def start(self, group: int = 0) -> int:
        return self.span(group)[0]

    def end(self, group: int = 0) -> int:
        return self.span(group)[1]


class WikilinkPattern:
    def finditer(self, text: str) -> Iterator[WikilinkMatch]:
        cursor = 0
        while True:
            start = text.find("[[", cursor)
            if start < 0:
                return
            end = text.find("]]", start + 2)
            nested_start = text.find("[[", start + 2)
            if nested_start >= 0 and (end < 0 or nested_start < end):
                cursor = nested_start
                continue
            if end < 0:
                return
            yield WikilinkMatch(text, start, end + 2)
            cursor = end + 2

    def sub(
        self,
        replacement: str | Callable[[WikilinkMatch], str],
        text: str,
        count: int = 0,
    ) -> str:
        pieces: list[str] = []
        last = 0
        replacements = 0
        for match in self.finditer(text):
            if count and replacements >= count:
                break
            pieces.append(text[last : match.start()])
            pieces.append(replacement(match) if callable(replacement) else replacement)
            last = match.end()
            replacements += 1
        if not replacements:
            return text
        pieces.append(text[last:])
        return "".join(pieces)


WIKILINK_RE = WikilinkPattern()


def parse_wikilink_inner(inner: str) -> WikilinkParts:
    pipe_index = inner.find("|")
    alias = ""
    escaped = False
    target_end = len(inner)
    if pipe_index >= 0:
        escaped = pipe_index > 0 and inner[pipe_index - 1] == "\\"
        target_end = pipe_index - 1 if escaped else pipe_index
        alias = inner[pipe_index + 1 :]
    target_with_fragment = inner[:target_end].strip()
    hash_index = target_with_fragment.find("#")
    if hash_index >= 0:
        target = target_with_fragment[:hash_index].strip()
        fragment = target_with_fragment[hash_index:]
    else:
        target = target_with_fragment
        fragment = ""
    return WikilinkParts(
        target=target,
        fragment=fragment,
        alias=alias,
        has_alias=pipe_index >= 0,
        alias_separator_escaped=escaped,
    )


def split_wikilink(inner: str) -> str:
    return parse_wikilink_inner(inner).target


def build_wikilink_inner(parts: WikilinkParts, *, target: str | None = None) -> str:
    base = (parts.target if target is None else target) + parts.fragment
    if not parts.has_alias:
        return base
    separator = r"\|" if parts.alias_separator_escaped else "|"
    return base + separator + parts.alias
