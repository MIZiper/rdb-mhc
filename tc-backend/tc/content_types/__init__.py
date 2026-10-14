"""Type descriptor system for cross-type retrieval and aggregation."""

from tc.content_types.descriptor import (
    FIELD_KINDS,
    FieldSpec,
    TypeDescriptor,
    extract_field_rows,
)
from tc.content_types.registry import (
    DATA_TYPES,
    all_descriptors,
    get_descriptor,
)

__all__ = [
    "FIELD_KINDS",
    "FieldSpec",
    "TypeDescriptor",
    "extract_field_rows",
    "DATA_TYPES",
    "all_descriptors",
    "get_descriptor",
]
