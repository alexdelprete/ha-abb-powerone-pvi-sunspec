"""SunSpec model registry that loads JSON definitions from disk."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.resources as resources
import json
from typing import Any, Mapping


@dataclass(slots=True)
class PointDef:
    """Definition of a single SunSpec point."""

    name: str
    type: str
    size: int | None = None  # bytes for strings
    sfref: str | None = None
    units: str | None = None
    label: str | None = None


@dataclass(slots=True)
class GroupDef:
    """Definition of a SunSpec group (optionally repeating)."""

    name: str
    points: list[PointDef]
    repeating: bool = False
    count_field: str | None = None


@dataclass(slots=True)
class ModelDef:
    """Top-level model definition."""

    id: int
    name: str
    groups: list[GroupDef]


class ModelRegistry:
    """Loads and indexes SunSpec JSON model definitions packaged with the library."""

    _by_id: dict[int, ModelDef]
    _by_name: dict[str, ModelDef]

    def __init__(self) -> None:
        self._by_id = {}
        self._by_name = {}

    def load(self) -> None:
        """Load model JSON files from the bundled resources directory."""
        pkg = resources.files(__package__)
        models_pkg = pkg.joinpath("models")
        for entry in models_pkg.iterdir():
            if not entry.name.endswith(".json"):
                continue
            data = json.loads(entry.read_text(encoding="utf-8"))
            model = self._parse_model_json(data)
            self._by_id[model.id] = model
            self._by_name[model.name] = model

    def _parse_model_json(self, data: Mapping[str, Any]) -> ModelDef:
        groups: list[GroupDef] = [
            GroupDef(
                name=str(g.get("name", data.get("name", "group"))),
                points=[
                    PointDef(
                        name=str(p["name"]),
                        type=str(p["type"]),
                        size=(int(p["size"]) if "size" in p else None),
                        sfref=(str(p["sf"]) if "sf" in p else None),
                        units=(str(p["units"]) if "units" in p else None),
                        label=(str(p["label"]) if "label" in p else None),
                    )
                    for p in g.get("points", [])
                ],
                repeating=bool(g.get("repeating", False)),
                count_field=(str(g.get("count")) if g.get("count") else None),
            )
            for g in data.get("groups", [])
        ]
        return ModelDef(id=int(data["id"]), name=str(data["name"]), groups=groups)

    def get_by_id(self, model_id: int) -> ModelDef:
        """Return the model definition for the given id or raise KeyError."""
        if model_id not in self._by_id:
            raise KeyError(model_id)
        return self._by_id[model_id]

    def get_by_name(self, name: str) -> ModelDef:
        """Return the model definition looking up by name (case-insensitive)."""
        key = name.lower()
        for n, model in self._by_name.items():
            if n.lower() == key:
                return model
        raise KeyError(name)

    @property
    def ids(self) -> list[int]:
        """Return a sorted list of all available model ids."""
        return sorted(self._by_id)
