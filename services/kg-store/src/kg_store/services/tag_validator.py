"""Haystack customTag catalog validator (ADR-021, 7-c).

haystack: prefixed tags must be registered in the bundled haystack-tags.yaml catalog.
bldg: prefixed tags are free-form and always accepted.
"""
from __future__ import annotations

import importlib.resources
from functools import lru_cache

import yaml

_HAYSTACK_PREFIX = "haystack:"
_BLDG_PREFIX = "bldg:"
_VALID_PREFIXES = (_HAYSTACK_PREFIX, _BLDG_PREFIX)


@lru_cache(maxsize=1)
def load_haystack_catalog() -> frozenset[str]:
    """Return the set of valid haystack tag names (without prefix) from the bundled YAML."""
    pkg = importlib.resources.files("kg_store.taxonomies")
    data = yaml.safe_load(pkg.joinpath("haystack-tags.yaml").read_text(encoding="utf-8"))
    return frozenset(entry["tag"] for entry in data.get("tags", []))


def validate_custom_tags(tags: list[str], catalog: frozenset[str]) -> list[str]:
    """Return list of invalid tags (haystack: not in catalog; any unrecognised prefix).

    bldg: tags always pass. Unknown prefixes are rejected.
    """
    invalid: list[str] = []
    for tag in tags:
        if tag.startswith(_BLDG_PREFIX):
            continue
        if tag.startswith(_HAYSTACK_PREFIX):
            name = tag[len(_HAYSTACK_PREFIX):]
            if name not in catalog:
                invalid.append(tag)
        else:
            invalid.append(tag)
    return invalid
