import pytest

from jobfit.llm.json_schema import strict_json_schema
from jobfit.schemas import ExtractionResult, MatchResult


def _schema_nodes(node):
    """Yield every schema object (not the `properties` name->schema maps)."""
    if isinstance(node, list):
        for item in node:
            yield from _schema_nodes(item)
    elif isinstance(node, dict):
        yield node
        for key, value in node.items():
            if key in ("properties", "$defs"):
                for child in value.values():
                    yield from _schema_nodes(child)
            else:
                yield from _schema_nodes(value)


@pytest.mark.parametrize("model", [ExtractionResult, MatchResult])
def test_every_object_is_closed_and_fully_required(model):
    schema = strict_json_schema(model)
    objects = [n for n in _schema_nodes(schema) if n.get("type") == "object"]
    assert objects, "expected at least one object in the schema"
    for obj in objects:
        assert obj["additionalProperties"] is False
        assert sorted(obj["required"]) == sorted(obj["properties"])


@pytest.mark.parametrize("model", [ExtractionResult, MatchResult])
def test_titles_are_removed(model):
    for node in _schema_nodes(strict_json_schema(model)):
        assert not isinstance(node.get("title"), str)


def test_enums_are_kept():
    schema = strict_json_schema(MatchResult)
    status = schema["$defs"]["RequirementMatch"]["properties"]["status"]
    assert status["enum"] == ["met", "partial", "missing"]


def test_original_pydantic_schema_is_not_mutated():
    strict_json_schema(MatchResult)
    assert "title" in MatchResult.model_json_schema()
