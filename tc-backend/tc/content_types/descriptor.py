"""Type descriptors.

A *descriptor* declares, for one content type, which fields inside the
free-form JSONB content are meaningful for cross-type retrieval and
aggregation. It is the single source of truth shared by:

* the write path (``tc.services.nodes``) which uses ``fields`` to
  populate the ``node_fields`` projection index;
* the API (``/api/types``) which serves descriptors to the frontend;
* the frontend, which maps ``ui.component`` to a registered renderer.

Descriptors never constrain how content is stored: ``nodes.content`` keeps
its original shape. They only *annotate* which JSON paths carry searchable
or aggregatable values, and map them onto canonical, shareable keys so that
values from different types can be compared.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import datetime
from typing import Any, Callable, Iterator

FIELD_KINDS = {"text", "number", "keyword", "date"}

MAX_TEXT_LEN = 4000
SKIP_TEXT_KEYS = {"file_id", "file_ids", "data", "base64"}


@dataclass(frozen=True)
class FieldSpec:
    """Maps a content path onto a canonical, shareable field key."""

    path: str
    key: str
    kind: str
    unit: str | None = None
    label: str | None = None
    comparable: bool | None = None

    def __post_init__(self) -> None:
        if self.kind not in FIELD_KINDS:
            raise ValueError(f"Unknown field kind: {self.kind!r}")
        if self.comparable is None:
            object.__setattr__(
                self, "comparable", self.kind in {"number", "keyword", "date"}
            )


@dataclass
class TypeDescriptor:
    type: str
    display_name: str
    version: int = 0
    schema: dict[str, Any] | None = None
    fields: list[FieldSpec] = dc_field(default_factory=list)
    preview: list[str] = dc_field(default_factory=list)
    ui: dict[str, Any] = dc_field(default_factory=dict)
    upcast: Callable[[Any], Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "display_name": self.display_name,
            "version": self.version,
            "schema": self.schema,
            "preview": self.preview,
            "ui": self.ui,
            "fields": [
                {
                    "path": f.path,
                    "key": f.key,
                    "kind": f.kind,
                    "unit": f.unit,
                    "label": f.label,
                    "comparable": f.comparable,
                }
                for f in self.fields
            ],
        }


def _iter_path(content: Any, path: str) -> Iterator[Any]:
    """Yield every value reachable at ``path``.

    Path tokens are dot separated. A token suffixed with ``[]`` descends
    into a list, yielding once per element, e.g. ``channels[].data[].value``.
    """
    parts = path.split(".")

    def rec(node: Any, i: int) -> Iterator[Any]:
        if i == len(parts):
            yield node
            return
        token = parts[i]
        list_step = token.endswith("[]")
        key = token[:-2] if list_step else token
        if not isinstance(node, dict) or key not in node:
            return
        value = node[key]
        if list_step:
            if isinstance(value, list):
                for item in value:
                    yield from rec(item, i + 1)
        else:
            yield from rec(value, i + 1)

    yield from rec(content, 0)


def _coerce(kind: str, value: Any) -> Any:
    if value is None:
        return None
    if kind == "number":
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None
    if kind == "keyword":
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        return None
    if kind == "text":
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        return None
    if kind == "date":
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
    return None


def _row(key: str, kind: str, unit: str | None, value: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "key": key,
        "kind": kind,
        "unit": unit,
        "num_value": None,
        "text_value": None,
        "ts_value": None,
    }
    if kind == "number":
        row["num_value"] = value
    elif kind == "date":
        row["ts_value"] = value
    else:
        row["text_value"] = value
    return row


def _iter_text_leaves(node: Any) -> Iterator[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in SKIP_TEXT_KEYS:
                continue
            yield from _iter_text_leaves(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_text_leaves(item)
    elif isinstance(node, str):
        if 0 < len(node) <= MAX_TEXT_LEN:
            yield node


def extract_field_rows(
    content: Any, descriptor: TypeDescriptor | None
) -> list[dict[str, Any]]:
    """Project content into index rows according to the descriptor.

    Declared fields become typed rows; additionally every string leaf is
    indexed under the synthetic ``_content`` text key so that plain text
    search also reaches arbitrary content.
    """
    rows: list[dict[str, Any]] = []
    if descriptor is not None:
        for spec in descriptor.fields:
            for raw in _iter_path(content, spec.path):
                value = _coerce(spec.kind, raw)
                if value is None:
                    continue
                rows.append(_row(spec.key, spec.kind, spec.unit, value))
    for text in _iter_text_leaves(content):
        rows.append(_row("_content", "text", None, text))
    return rows
