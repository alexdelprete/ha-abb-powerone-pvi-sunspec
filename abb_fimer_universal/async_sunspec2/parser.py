"""Generic SunSpec parser that decodes register blocks using JSON model defs."""

from __future__ import annotations

from dataclasses import dataclass

from .model_registry import GroupDef, ModelDef
from .types import apply_scale, decode_value, precision_from_sf


@dataclass(slots=True)
class PointValue:
    """Normalized value for a parsed SunSpec point."""

    raw: int | float | str | None
    cvalue: int | float | str | None
    units: str | None
    desc: str | None
    precision: int | None


@dataclass(slots=True)
class ModelParseResult:
    """Parsed values for a SunSpec model."""

    model_id: int
    model_name: str
    points: dict[str, PointValue]


class SunSpecParser:
    """Decode register streams according to SunSpec JSON model definitions."""

    def parse(self, model: ModelDef, regs: list[int]) -> ModelParseResult:
        """Parse a model register block.

        Args:
            model: Model definition
            regs: Model data registers (starting immediately after the model header)

        """
        pos = 0
        points_out: dict[str, PointValue] = {}
        scale_map: dict[str, int] = {}

        def parse_group(group: GroupDef, *, suffix: str = "") -> None:
            nonlocal pos
            # Determine repeat count if repeating
            repeats = 1
            if group.repeating:
                if group.count_field is None:
                    raise ValueError("repeating group requires count_field")
                # The count field must have been parsed in this result already
                count_val = points_out.get(group.count_field)
                if count_val is None or count_val.raw is None:
                    repeats = 0
                else:
                    assert isinstance(count_val.raw, (int, float))
                    repeats = int(count_val.raw)
            for _i in range(repeats):
                for p in group.points:
                    # Pad type: skip registers but do not record a value
                    if p.type == "pad":
                        # Default pad size is one register
                        pad_regs = 1
                        if p.size is not None:
                            # For pad, size is in registers
                            pad_regs = int(p.size)
                        pos += pad_regs
                        continue

                    if p.type == "string":
                        res = decode_value(p.type, regs[pos:], size_bytes=p.size or 0)
                    else:
                        res = decode_value(p.type, regs[pos:])
                    pos += res.regs_used

                    raw = res.value
                    # If this is a scale factor, store it and continue
                    if p.type == "sunssf":
                        if raw is not None:
                            assert isinstance(raw, int)
                            scale_map[p.name] = int(raw)
                        points_out[p.name] = PointValue(
                            raw=raw,
                            cvalue=raw,
                            units=None,
                            desc=p.label,
                            precision=None,
                        )
                        continue

                    # Compute engineering value if a scale factor is referenced
                    sf = None
                    if p.sfref:
                        sf = scale_map.get(p.sfref)
                    cval = apply_scale(
                        raw if isinstance(raw, (int, float)) else None, sf
                    )
                    prec = precision_from_sf(sf)

                    key = p.name if not suffix else f"{p.name}{suffix}"
                    points_out[key] = PointValue(
                        raw=raw,
                        cvalue=cval if cval is not None else raw,
                        units=p.units,
                        desc=p.label,
                        precision=prec,
                    )

        # Parse all groups in order
        for g in model.groups:
            parse_group(g)

        return ModelParseResult(
            model_id=model.id, model_name=model.name, points=points_out
        )
