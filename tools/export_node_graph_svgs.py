"""Export deterministic, lightweight SVG previews of selected DH Audio node groups."""
from pathlib import Path
import html
import sys

import bpy


GROUPS = {
    "temporal-response": "DH Audio Temporal Response",
    "spectrum-history": "DH Audio Spectrum History",
    "material-reader": "DH Audio Material Reader",
}


def export(tree, path):
    nodes = list(tree.nodes)
    if not nodes:
        return
    min_x = min(node.location.x for node in nodes) - 40
    min_y = min(node.location.y for node in nodes) - 40
    max_x = max(node.location.x + node.width for node in nodes) + 40
    max_y = max(node.location.y + 80 for node in nodes) + 40
    width, height = max_x - min_x, max_y - min_y
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
            '<rect width="100%" height="100%" fill="#202124"/>']
    for node in nodes:
        x, y = node.location.x - min_x, max_y - node.location.y - 70
        w, h = max(node.width, 160), 70 + 18 * min(len(node.inputs), 5)
        label = html.escape(node.label or node.name)
        rows += [f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="6" fill="#3a3d41" stroke="#858b93"/>',
                 f'<text x="{x + 10:.0f}" y="{y + 24:.0f}" fill="white" font-family="sans-serif" font-size="14">{label}</text>']
    rows.append(f'<text x="20" y="{height - 16:.0f}" fill="#b9c0ca" font-family="sans-serif" font-size="12">{html.escape(tree.name)}</text></svg>')
    path.write_text("\n".join(rows), encoding="utf-8")


def main():
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo / "src"))
    import dh_audio_toolkit
    dh_audio_toolkit.main()
    output = repo / "temp" / "node-previews"
    output.mkdir(parents=True, exist_ok=True)
    for slug, name in GROUPS.items():
        tree = bpy.data.node_groups.get(name)
        if tree:
            export(tree, output / f"{slug}.svg")


if __name__ == "__main__":
    main()
