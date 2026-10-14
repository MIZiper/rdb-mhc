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

# --- Tabular: channel / time / value series ------------------------------
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


DATA_TYPES: dict[str, TypeDescriptor] = {
    d.type: d for d in (BASE, TABULAR, FORMULA, IMAGE)
}


def get_descriptor(data_type: str | None) -> TypeDescriptor | None:
    if not data_type:
        return None
    return DATA_TYPES.get(data_type)


def all_descriptors() -> list[TypeDescriptor]:
    return list(DATA_TYPES.values())
