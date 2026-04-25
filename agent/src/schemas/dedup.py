from typing import TypedDict

from schemas.paper import Paper


class DedupResult(TypedDict):
    deduplicated_papers: list[Paper]
    total_deduplicated: int
    duplicates_removed: int
