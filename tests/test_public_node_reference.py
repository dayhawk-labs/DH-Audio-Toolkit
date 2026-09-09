"""Tests for the generated public-node knowledge base tooling."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    path = ROOT / "tools" / "build_public_node_reference.py"
    spec = importlib.util.spec_from_file_location("node_reference_builder", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_manifest_and_agent_guidance_cover_exactly_25_public_groups():
    builder = load_builder()
    manifest = json.loads((ROOT / "tools" / "public_node_previews.json").read_text())
    assert set(manifest["groups"]) == set(manifest["files"])
    assert len(manifest["groups"]) == 25
    assert set(manifest["groups"].values()) == set(builder.GUIDANCE)
    assert len(set(manifest["files"].values())) == 25
    assert all("/" not in name and not name.startswith(".") for name in manifest["files"].values())


def test_generated_page_uses_verified_interface_fields_and_preview():
    builder = load_builder()
    node = {
        "name": "DH Audio Temporal Response",
        "tree_type": "GeometryNodeTree",
        "default_width": 310,
        "description": "Stateful response.",
        "items": [
            {
                "kind": "panel",
                "name": "Timing",
                "description": "Response time.",
                "default_closed": False,
            },
            {
                "kind": "socket",
                "name": "Attack",
                "panel": "Timing",
                "direction": "INPUT",
                "socket_type": "NodeSocketFloat",
                "default": 0.05,
                "description": "Rise time.",
            },
            {
                "kind": "socket",
                "name": "Peak",
                "panel": "Outputs",
                "direction": "OUTPUT",
                "socket_type": "NodeSocketFloat",
                "default": 0.0,
                "description": "Held peak.",
            },
        ],
    }
    page = builder.build_page(
        node, "temporal_response", "dh-audio-temporal-response.png"
    )
    assert "../images/node-previews/dh-audio-temporal-response.png" in page
    assert "**Attack**" in page
    assert "**Peak**" in page
    assert "Peak Hold is enabled by default" in page
    assert "## Key choices" in page
    assert "Peak Hold Time" in page


def test_key_choices_document_source_verified_menu_options():
    builder = load_builder()
    choices = "\n".join(builder.KEY_CHOICES["DH Audio Spectrum Curve"])
    assert "Raw, Smooth, or Smooth + Resample" in choices
    assert "Custom Geometry" in "\n".join(
        builder.KEY_CHOICES["DH Audio Spectrum Bars"]
    )


def test_checked_in_reference_covers_every_allowlisted_public_node():
    manifest = json.loads((ROOT / "tools" / "public_node_previews.json").read_text())
    for slug, filename in manifest["files"].items():
        page = (ROOT / "docs" / "nodes" / f"{slug}.md").read_text(encoding="utf-8")
        assert f"../images/node-previews/{filename}" in page
        assert "## Agent notes" in page
        assert "## Inputs" in page
        assert "## Outputs" in page
        assert (ROOT / "docs" / "images" / "node-previews" / filename).is_file()
