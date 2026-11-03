from dataclasses import dataclass
from typing import Callable

Matches = Callable[[str], bool]
Extract = Callable[[str, str], dict]


@dataclass(frozen=True)
class Parser:
    code: str
    matches: Matches
    extract: Extract