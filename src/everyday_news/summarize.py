"""Extractive summaries: the first whole sentences of a lead text, up to a length cap."""

import re

from everyday_news.rank import RankedStory

MAX_CHARS = 280
ELLIPSIS = "…"

# Words that end with a period without ending the sentence (casefolded, no period)
ABBREVIATIONS = {
    # English
    "mr", "mrs", "ms", "dr", "prof", "st", "jr", "sr", "vs", "etc", "inc", "ltd", "co",
    "gen", "gov", "sen", "rep", "no", "approx",
    # Polish
    "ws", "np", "tj", "tzw", "tzn", "m.in", "ok", "ul", "al", "św", "płk", "mjr",
    "r", "w", "tys", "mln", "mld", "nr", "godz", "min", "ub", "br", "pt", "por",
}  # fmt: skip

# A candidate boundary: sentence punctuation, optional closing quote/bracket, whitespace
BOUNDARY = re.compile(r"""[.!?…]["'”»)]?\s+""")
SENTENCE_END = re.compile(r"""[.!?…]["'”»)]?$""")
LAST_WORD = re.compile(r"(\S+)\.$")


def _is_abbreviation(before: str) -> bool:
    """True when the text before a period ends in an abbreviation or an initial."""
    match = LAST_WORD.search(before)
    if not match:
        return False
    word = match.group(1).casefold().lstrip("(\"'„")
    # Initials and dotted abbreviations: "U.S", "J", "m.in"
    return word in ABBREVIATIONS or len(word) == 1 or bool(re.fullmatch(r"(\w\.)+\w", word))


def sentences(text: str) -> list[str]:
    text = " ".join(text.split())
    result, start = [], 0
    for m in BOUNDARY.finditer(text):
        end = m.end()
        candidate = text[start:end].rstrip()
        if candidate.endswith(".") and _is_abbreviation(candidate):
            continue
        result.append(candidate)
        start = end
    if start < len(text):
        result.append(text[start:].strip())
    return [s for s in result if s]


def summarize(text: str, max_chars: int = MAX_CHARS) -> str:
    parts = sentences(text)
    if not parts:
        return ""

    # A feed excerpt cut mid-sentence: drop the fragment if there is a full sentence before it
    if not SENTENCE_END.search(parts[-1]):
        if len(parts) > 1:
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].rstrip(",;:–- ") + ELLIPSIS

    summary = ""
    for s in parts:
        joined = f"{summary} {s}".strip()
        if len(joined) > max_chars:
            break
        summary = joined
    if summary:
        return summary

    # The first sentence alone is too long: cut at a word boundary
    cut = parts[0][: max_chars - 1].rsplit(" ", 1)[0]
    return cut.rstrip(",;:–- ") + ELLIPSIS


def story_summary(story: RankedStory, max_chars: int = MAX_CHARS) -> str:
    """Summary of the first item with text (lead first), or "" when none has text."""
    for item in story.items:
        if item.text:
            return summarize(item.text, max_chars)
    return ""
