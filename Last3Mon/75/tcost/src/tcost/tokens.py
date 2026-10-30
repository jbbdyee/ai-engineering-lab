"""Count tokens on this computer (no API call). o200k_base is the encoding of the gpt-4.1 / gpt-5 family."""
from __future__ import annotations

from functools import lru_cache

import tiktoken

ENCODING = "o200k_base"


@lru_cache(maxsize=1)
def _encoder():
    return tiktoken.get_encoding(ENCODING)


def count(text: str) -> int:
    return len(_encoder().encode(text or ""))
