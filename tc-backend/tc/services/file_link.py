"""Extract referenced file UUIDs from arbitrary node content.

Convention: any ``file_id`` (string) or ``file_ids`` (list of strings)
field, at any depth, is treated as a stored file reference. This keeps
module content schemas decoupled from the file storage layer.
"""

import re
from typing import Iterator
from uuid import UUID

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _iter_ids(value) -> Iterator[UUID]:
    if isinstance(value, str):
        if _UUID_RE.match(value):
            try:
                yield UUID(value)
            except ValueError:
                return
    elif isinstance(value, list):
        for item in value:
            yield from _iter_ids(item)


def extract_file_ids(content) -> list[UUID]:
    found: list[UUID] = []
    seen: set[UUID] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("file_id", "file_ids"):
                    for fid in _iter_ids(value):
                        if fid not in seen:
                            seen.add(fid)
                            found.append(fid)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(content)
    return found
