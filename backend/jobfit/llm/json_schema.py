"""Turn a Pydantic model into a schema that structured outputs accept.

Structured outputs require `additionalProperties: false` on every object, and we
want every property listed as required. Pydantic doesn't emit either by default,
so this walks the schema and adds them. Titles are dropped because they only add
noise to the grammar.
"""

from __future__ import annotations

import copy
from typing import Any

from pydantic import BaseModel


def strict_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    schema = copy.deepcopy(model.model_json_schema())
    _strictify(schema)
    return schema


def _strictify(node: Any) -> None:
    if isinstance(node, list):
        for item in node:
            _strictify(item)
        return
    if not isinstance(node, dict):
        return

    if isinstance(node.get("title"), str):
        del node["title"]

    if node.get("type") == "object" or "properties" in node:
        properties = node.get("properties", {})
        node["additionalProperties"] = False
        node["required"] = list(properties)
        for child in properties.values():
            _strictify(child)

    for key, value in node.items():
        if key != "properties":
            _strictify(value)
