"""Minimal JSON Schema validator (standard library only).

Supports the subset the flow's schemas use: type (single or list), properties, required,
additionalProperties (bool), items, enum, minLength, minItems, pattern. Unknown keywords are ignored.
Every agent output is validated here even when the backend already enforced the schema, because a
manual backend or a future backend may not.
"""
from __future__ import annotations

import re
from typing import Any

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def validate(instance: Any, schema: dict, path: str = "$") -> list[str]:
    """Return a list of error messages; an empty list means the instance is valid."""
    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None:
        names = expected if isinstance(expected, list) else [expected]
        if not any(_TYPES[n](instance) for n in names):
            return [f"{path}: expected {'/'.join(names)}, got {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than {schema['minLength']} characters")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}")
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors.extend(validate(item, schema["items"], f"{path}[{i}]"))
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property '{key}'")
        for key, value in instance.items():
            if key in props:
                errors.extend(validate(value, props[key], f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected property '{key}'")
    return errors
