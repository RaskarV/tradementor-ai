from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Retrieved:
    title: str
    source_url: Optional[str]
    content: str
    similarity: float
