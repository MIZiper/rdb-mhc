"""Concrete type descriptors.

This is the single source of truth for the type registry. Descriptors are
defined here in code (so they are versioned with the application) and seeded
into the ``data_types`` table on startup for serving and SQL joins.
"""

from __future__ import annotations

from tc.content_types.descriptor import FieldSpec, TypeDescriptor

# --- Base: arbitrary JSON -------------------------------------------------
BASE = TypeDescriptor(
    type="Base.v00",
    display_name="Base Item",
    version=0,
    schema=None,
    fields=[],
    preview=[],
    ui={"component": "Base"},
)

# --- Source item: unified entry for source-managed resources --------------
# Users create a Source Item in TC, then link it from a source application.
# The source app fills in the concrete type through PUT /api/nodes/{id}/source.
SOURCE_ITEM = TypeDescriptor(
    type="SourceItem.v00",
    display_name="Source Item",
    version=0,
    schema=None,
    fields=[],
    preview=[],
    ui={"component": "SourceItem", "source_item": True},
)

# --- Tabular: channel / time / value series ------------------------------
def _merge_tabular(existing, incoming):
    if isinstance(existing, dict) and isinstance(incoming, dict):
        merged = {**existing, **incoming}
        if isinstance(existing.get("channels"), list) and isinstance(
            incoming.get("channels"), list
        ):
            merged["channels"] = existing["channels"] + incoming["channels"]
        return merged
    return incoming


TABULAR = TypeDescriptor(
    type="Tabular.v00",
    display_name="Tabular Data",
    version=0,
    schema=None,
    fields=[
        FieldSpec(path="channels[].name", key="channel", kind="keyword", label="Channel"),
        FieldSpec(
            path="channels[].id_name", key="channel_id", kind="keyword", label="Channel id"
        ),
        FieldSpec(path="channels[].data[].time", key="time", kind="number", label="Time"),
        FieldSpec(
            path="channels[].data[].value",
            key="value",
            kind="number",
            label="Value",
        ),
    ],
    preview=["channel", "value"],
    ui={"component": "Tabular"},
    merge=_merge_tabular,
)

# --- Formula: named expressions ------------------------------------------
FORMULA = TypeDescriptor(
    type="Formula.v00",
    display_name="Formula Model",
    version=0,
    schema=None,
    fields=[
        FieldSpec(path="formulas[].name", key="formula_name", kind="keyword", label="Name"),
        FieldSpec(
            path="formulas[].expression", key="formula_expr", kind="text", label="Expression"
        ),
        FieldSpec(path="formulas[].note", key="formula_note", kind="text", label="Note"),
        FieldSpec(path="formulas[].xmin", key="xmin", kind="number", label="x-min"),
        FieldSpec(path="formulas[].xmax", key="xmax", kind="number", label="x-max"),
    ],
    preview=["formula_name"],
    ui={"component": "Formula"},
)

# --- Image gallery --------------------------------------------------------
IMAGE = TypeDescriptor(
    type="Image.v00",
    display_name="Image Gallery",
    version=0,
    schema=None,
    fields=[
        FieldSpec(path="images[].caption", key="caption", kind="text", label="Caption"),
        FieldSpec(
            path="images[].original_name", key="file_name", kind="keyword", label="File name"
        ),
        FieldSpec(
            path="images[].mime_type", key="mime_type", kind="keyword", label="MIME type"
        ),
        FieldSpec(path="images[].width", key="width", kind="number", label="Width"),
        FieldSpec(path="images[].height", key="height", kind="number", label="Height"),
    ],
    preview=["caption"],
    ui={"component": "Image"},
)


# --- External catalog entries -------------------------------------------
# These types are metadata-only: the source application keeps the content,
# while TC stores title/description/tags/status and a link back to the source.
DAC_WEB_PROJECT = TypeDescriptor(
    type="dac_web.project",
    display_name="DAC Web Project",
    version=0,
    schema=None,
    fields=[],
    preview=[],
    ui={"component": "Base"},
    creatable=False,
    source_system="dac_web",
)

TPL_PLAN = TypeDescriptor(
    type="tpl.plan",
    display_name="TPL Plan",
    version=0,
    schema=None,
    fields=[],
    preview=[],
    ui={"component": "Base"},
    creatable=False,
    source_system="tpl",
)

TPL_LOG = TypeDescriptor(
    type="tpl.log",
    display_name="TPL Execution Log",
    version=0,
    schema=None,
    fields=[],
    preview=[],
    ui={"component": "Base"},
    creatable=False,
    source_system="tpl",
)


DATA_TYPES: dict[str, TypeDescriptor] = {
    d.type: d
    for d in (
        BASE,
        SOURCE_ITEM,
        TABULAR,
        FORMULA,
        IMAGE,
        DAC_WEB_PROJECT,
        TPL_PLAN,
        TPL_LOG,
    )
}

# Backward-compatible fallback for clients that only send source coordinates.
_SOURCE_PART_TYPES: dict[tuple[str, str], str] = {
    ("dac_web", "project"): DAC_WEB_PROJECT.type,
    ("tpl", "plan"): TPL_PLAN.type,
    ("tpl", "log"): TPL_LOG.type,
}


def get_descriptor(data_type: str | None) -> TypeDescriptor | None:
    if not data_type:
        return None
    return DATA_TYPES.get(data_type)


def all_descriptors() -> list[TypeDescriptor]:
    return list(DATA_TYPES.values())


def is_source_item(data_type: str | None) -> bool:
    descriptor = get_descriptor(data_type)
    return bool(descriptor and descriptor.ui.get("source_item"))


def resolve_source_type(
    source_system: str | None, source_part: str | None
) -> str | None:
    if not source_system or not source_part:
        return None
    return _SOURCE_PART_TYPES.get((source_system, source_part))


def source_types(source_system: str | None) -> list[str]:
    """Types managed by a source application (legacy unlinked candidates)."""
    return [
        d.type
        for d in DATA_TYPES.values()
        if d.source_system and (source_system is None or d.source_system == source_system)
    ]


def is_source_managed(data_type: str | None) -> bool:
    descriptor = get_descriptor(data_type)
    return bool(descriptor and descriptor.source_system)
