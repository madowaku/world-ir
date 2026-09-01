from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from .compiler import validate_document


def certainty_band(value: float) -> str:
    """Map v0.1 certainty to the default semantic-comparison band."""
    if not 0.0 <= value <= 1.0:
        raise ValueError("certainty must be between 0.0 and 1.0")
    if value < 0.20:
        return "very_unlikely"
    if value < 0.40:
        return "unlikely"
    if value < 0.60:
        return "unresolved"
    if value < 0.80:
        return "probable"
    if value < 0.95:
        return "highly_probable"
    return "asserted"


def _stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _entity_payload(entity: dict[str, Any]) -> dict[str, Any]:
    """Return meaning-bearing entity fields, excluding local/provenance data."""
    return {
        key: deepcopy(value)
        for key, value in entity.items()
        if key not in {"id", "names"}
    }


def _frame_base_payload(frame: dict[str, Any]) -> dict[str, Any]:
    """Return frame-local semantics without graph-local references."""
    payload = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in {"id", "roles", "certainty", "source_spans"}
    }
    payload["certainty_band"] = certainty_band(float(frame["certainty"]))
    payload["role_labels"] = sorted(role["role"] for role in frame.get("roles", []))
    return payload


def _reference_signature(
    value: dict[str, Any],
    entity_base: dict[str, str],
    frame_base: dict[str, str],
) -> Any:
    if "entity_ref" in value:
        ref = value["entity_ref"]
        if ref.startswith("ctx:"):
            return {"context_ref": ref}
        return {"entity": entity_base[ref]}
    if "frame_ref" in value:
        return {"frame": frame_base[value["frame_ref"]]}
    return deepcopy(value)


def _entity_sort_keys(
    entities: list[dict[str, Any]],
    frames: list[dict[str, Any]],
    entity_base: dict[str, str],
    frame_base: dict[str, str],
) -> dict[str, str]:
    usages: dict[str, list[Any]] = {entity["id"]: [] for entity in entities}
    for frame in frames:
        frame_sig = frame_base[frame["id"]]
        for role in frame.get("roles", []):
            ref = role["value"].get("entity_ref")
            if ref in usages:
                usages[ref].append({"role": role["role"], "frame": frame_sig})

    return {
        entity["id"]: _stable(
            {
                "entity": _entity_payload(entity),
                "usages": sorted(usages[entity["id"]], key=_stable),
            }
        )
        for entity in entities
    }


def _frame_sort_key(
    frame: dict[str, Any],
    entity_keys: dict[str, str],
    entity_base: dict[str, str],
    frame_base: dict[str, str],
) -> str:
    roles = []
    for role in frame.get("roles", []):
        value = role["value"]
        if "entity_ref" in value and value["entity_ref"] in entity_keys:
            ref_sig: Any = {"entity": entity_keys[value["entity_ref"]]}
        else:
            ref_sig = _reference_signature(value, entity_base, frame_base)
        roles.append({"role": role["role"], "value": ref_sig})
    return _stable(
        {
            "frame": _frame_base_payload(frame),
            "roles": sorted(roles, key=_stable),
        }
    )


def _canonical_value(
    value: dict[str, Any], entity_map: dict[str, str], frame_map: dict[str, str]
) -> dict[str, Any]:
    if "entity_ref" in value:
        ref = value["entity_ref"]
        return {"entity_ref": entity_map.get(ref, ref)}
    if "frame_ref" in value:
        return {"frame_ref": frame_map[value["frame_ref"]]}
    return deepcopy(value)


def canonicalize(document: dict[str, Any], *, validate: bool = True) -> dict[str, Any]:
    """Return the deterministic v0.1 E0 semantic comparison form.

    Provenance and compiler-specific metadata are intentionally excluded. Local
    entity/frame IDs are regenerated after semantic sorting.
    """
    if validate:
        validate_document(document)

    entities = document.get("entities", [])
    frames = document.get("frames", [])
    entity_base = {e["id"]: _stable(_entity_payload(e)) for e in entities}
    frame_base = {f["id"]: _stable(_frame_base_payload(f)) for f in frames}
    entity_keys = _entity_sort_keys(entities, frames, entity_base, frame_base)

    sorted_entities = sorted(
        entities, key=lambda entity: (entity_keys[entity["id"]], entity_base[entity["id"]])
    )
    entity_map = {entity["id"]: f"e{index}" for index, entity in enumerate(sorted_entities, 1)}

    frame_keys = {
        frame["id"]: _frame_sort_key(frame, entity_keys, entity_base, frame_base)
        for frame in frames
    }
    sorted_frames = sorted(frames, key=lambda frame: (frame_keys[frame["id"]], frame_base[frame["id"]]))
    frame_map = {frame["id"]: f"f{index}" for index, frame in enumerate(sorted_frames, 1)}

    canonical_entities = []
    for entity in sorted_entities:
        item = _entity_payload(entity)
        item["id"] = entity_map[entity["id"]]
        canonical_entities.append(item)

    canonical_frames = []
    for frame in sorted_frames:
        item = {
            key: deepcopy(value)
            for key, value in frame.items()
            if key not in {"id", "roles", "certainty", "source_spans"}
        }
        item["id"] = frame_map[frame["id"]]
        item["certainty_band"] = certainty_band(float(frame["certainty"]))
        item["roles"] = sorted(
            [
                {
                    "role": role["role"],
                    "value": _canonical_value(role["value"], entity_map, frame_map),
                }
                for role in frame.get("roles", [])
            ],
            key=_stable,
        )
        canonical_frames.append(item)

    canonical_links = []
    for link in document.get("links", []):
        item = deepcopy(link)
        item["from"] = entity_map.get(item["from"], frame_map.get(item["from"], item["from"]))
        item["to"] = entity_map.get(item["to"], frame_map.get(item["to"], item["to"]))
        canonical_links.append(item)
    canonical_links.sort(key=_stable)

    fidelity = document.get("fidelity", {})
    canonical_fidelity = {
        "status": fidelity.get("status"),
        "lost_features": sorted(fidelity.get("lost_features", [])),
    }

    result: dict[str, Any] = {
        "world_ir_version": document["world_ir_version"],
        "utterance": deepcopy(document["utterance"]),
        "entities": canonical_entities,
        "frames": canonical_frames,
        "links": canonical_links,
        "fidelity": canonical_fidelity,
    }
    if "context" in document:
        result["context"] = deepcopy(document["context"])
    return result


def canonical_json(document: dict[str, Any], *, validate: bool = True) -> str:
    """Serialize canonical semantic JSON deterministically."""
    return _stable(canonicalize(document, validate=validate))


def canonical_bytes(document: dict[str, Any], *, validate: bool = True) -> bytes:
    """Return deterministic UTF-8 bytes for hashing or byte-level E0 checks."""
    return canonical_json(document, validate=validate).encode("utf-8")


def e0_equivalent(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Return True when two documents have byte-identical canonical semantics."""
    return canonical_bytes(left) == canonical_bytes(right)
