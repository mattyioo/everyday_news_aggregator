"""Word matching shared by muted words (filters) and followed topics.

Keywords of PREFIX_MIN+ letters match the start of a word, so a stem covers inflected
forms ("ukrain" → Ukraina, Ukrainy, Ukrainian); shorter keywords must be a whole word.
"""

import re

PREFIX_MIN = 4
WORD = re.compile(r"\w+")


def is_single_word(keyword: str) -> bool:
    return bool(WORD.fullmatch(keyword))


def find_keyword(text: str, keywords: tuple[str, ...]) -> str | None:
    """The first keyword (casefolded) that matches a word of `text`, or None."""
    for word in WORD.findall(text.casefold()):
        for k in keywords:
            if word.startswith(k) if len(k) >= PREFIX_MIN else word == k:
                return k
    return None
