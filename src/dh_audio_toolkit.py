import bpy
import re
import os

# =====================================================================
# DH AUDIO TOOLKIT 3.3.0
# Blender 5.2+
#
# 3.3.0:
# - Public Menu Switch inputs now have explicit defaults (Bars = Box, Curve = Smooth).
# - Spectrum Curve tube audio thickness now drives Curve to Mesh Scale directly in Blender 5.2.
# - Spectrum Fill grid indexing fixed so every spectrum point contributes to the top silhouette.
# - Material Reader Use Instancer and Shader Response Clamp to 1 are true Boolean checkboxes.
# - Per-group default widths replace the previous one-size-fits-all width.
# - Stable asset catalog UUIDs + shareable blender_assets.cats.txt generation added.
# - README expanded with a node-by-node reference before recipes.
#
# 3.2.3:
# - Fixed Set Curve Radius output socket naming and geometry-family output fallback.
#
# 3.2.2:
# - Added runtime menu capitalization fallback; Resample Curve uses exact menu item "Count".
#
# 3.2.1:
# - Blender 5.2 Resample Curve mode compatibility fix.
#
# 3.2.0:
# - Major modularization, visualizer additions, profile presets, and in-file README.
#
# A consolidated reusable audio-reactive toolkit for Geometry Nodes
# and Shader Nodes using Blender 5.2's Sample Sound Frequencies node.
#
# Creates:
#   GEOMETRY NODE GROUPS
#   - DH Audio Response
#   - DH Audio Frequency Map
#   - DH Audio Frequency Selection
#   - DH Audio Analyzer
#   - DH Audio Spectrum Points
#   - DH Audio Band Query
#   - DH Audio Sample Range
#   - DH Audio Bands
#   - DH Audio Spectrum Instances
#   - DH Audio Spectrum Curve
#   - DH Audio Spectrum Fill
#   - DH Audio Spectrum Bars
#
#   SHADER NODE GROUPS
#   - DH Audio Material Reader
#   - DH Audio Shader Response
#
# Standard spectrum attributes:
#   dh_audio_amp
#   dh_audio_norm
#   dh_audio_raw
#   dh_audio_band_index
#   dh_audio_band_pos
#   dh_audio_low_hz
#   dh_audio_center_hz
#   dh_audio_high_hz
#   dh_audio_bandwidth_hz
#
# Standard named-band attributes:
#   dh_audio_total
#   dh_audio_sub
#   dh_audio_bass
#   dh_audio_low_mid
#   dh_audio_mid
#   dh_audio_high_mids
#   dh_audio_presence
#   dh_audio_brilliance
#   dh_audio_air
#
# Notes:
# - Analyzer spectrum values are stored on the carrier point domain.
# - Instance on Points propagates those point attributes to instances.
# - DH Audio Bands includes its own point/instance named-attribute bridge.
# - Material Reader can switch between Geometry and Instancer lookup.
# =====================================================================

TOOLKIT_VERSION = "3.3.0"
BLENDER_MIN_VERSION = (5, 2, 0)

REBUILD_EXISTING = True
MARK_AS_ASSET = True
CREATE_DEMO_HOST = False
CREATE_README = True
README_TEXT_NAME = "DH Audio Toolkit - README"

# These older experiments are intentionally NOT deleted automatically.
# Set True only if you explicitly want to remove them.
REMOVE_LEGACY_GROUPS = False

GROUP_RESPONSE = "DH Audio Response"
GROUP_FREQ_MAP = "DH Audio Frequency Map"
GROUP_FREQ_SELECT = "DH Audio Frequency Selection"
GROUP_ANALYZER = "DH Audio Analyzer"
GROUP_POINTS = "DH Audio Spectrum Points"
GROUP_QUERY = "DH Audio Band Query"
GROUP_RANGE = "DH Audio Sample Range"
GROUP_BANDS = "DH Audio Bands"
GROUP_INSTANCES = "DH Audio Spectrum Instances"
GROUP_CURVE = "DH Audio Spectrum Curve"
GROUP_FILL = "DH Audio Spectrum Fill"
GROUP_BARS = "DH Audio Spectrum Bars"
GROUP_MATERIAL_READER = "DH Audio Material Reader"
GROUP_SHADER_RESPONSE = "DH Audio Shader Response"

# Stable catalog UUIDs. Keep these unchanged in future releases so users can
# replace/update the .blend without losing catalog assignments.
CATALOG_DEFINITIONS = {
    "Geometry Nodes": ("7bf84dff-c105-5fc6-9c5c-701196ef6282", "Geometry Nodes"),
    "Geometry Nodes/DH Audio": ("b0267192-518d-57aa-b6c9-e77dfb7075f3", "DH Audio"),
    "Geometry Nodes/DH Audio/Analysis": ("75e799e2-55ce-553a-8fdf-a74c5cf0de2c", "Analysis"),
    "Geometry Nodes/DH Audio/Mapping": ("bb4cca6c-c5d5-52c9-80fb-754adc068f91", "Mapping"),
    "Geometry Nodes/DH Audio/Query": ("9b46dff4-fa9d-510f-b0ae-a8af6da87e3a", "Query"),
    "Geometry Nodes/DH Audio/Visualizers": ("de47b34b-1184-5bc8-84ac-3c5ada05f601", "Visualizers"),
    "Geometry Nodes/DH Audio/Utilities": ("a4faf3f4-5a13-5f83-ae97-28993f20ac20", "Utilities"),
    "DH Audio": ("943fa2e2-dade-5829-a651-33cce45d37fb", "DH Audio"),
    "DH Audio/Shaders": ("1a181044-5483-5a07-ad44-2025bf0459e4", "Shaders"),
}

ASSET_CATALOG_PATHS = {
    GROUP_ANALYZER: "Geometry Nodes/DH Audio/Analysis",
    GROUP_BANDS: "Geometry Nodes/DH Audio/Analysis",
    GROUP_RANGE: "Geometry Nodes/DH Audio/Analysis",
    GROUP_FREQ_MAP: "Geometry Nodes/DH Audio/Mapping",
    GROUP_POINTS: "Geometry Nodes/DH Audio/Mapping",
    GROUP_QUERY: "Geometry Nodes/DH Audio/Query",
    GROUP_FREQ_SELECT: "Geometry Nodes/DH Audio/Query",
    GROUP_BARS: "Geometry Nodes/DH Audio/Visualizers",
    GROUP_CURVE: "Geometry Nodes/DH Audio/Visualizers",
    GROUP_FILL: "Geometry Nodes/DH Audio/Visualizers",
    GROUP_INSTANCES: "Geometry Nodes/DH Audio/Visualizers",
    GROUP_RESPONSE: "Geometry Nodes/DH Audio/Utilities",
    GROUP_MATERIAL_READER: "DH Audio/Shaders",
    GROUP_SHADER_RESPONSE: "DH Audio/Shaders",
}

# Tuned for the visible interface of each public group. Long analyzer-style
# groups stay comfortable; small utility/reader groups no longer waste space.
PUBLIC_GROUP_WIDTHS = {
    GROUP_ANALYZER: 330,
    GROUP_BANDS: 330,
    GROUP_RANGE: 315,
    GROUP_FREQ_MAP: 300,
    GROUP_POINTS: 285,
    GROUP_QUERY: 285,
    GROUP_FREQ_SELECT: 280,
    GROUP_BARS: 350,
    GROUP_CURVE: 310,
    GROUP_FILL: 290,
    GROUP_INSTANCES: 315,
    GROUP_RESPONSE: 285,
    GROUP_MATERIAL_READER: 300,
    GROUP_SHADER_RESPONSE: 285,
}

# Internal implementation groups are created for readability but are not
# marked as assets. They keep the public groups compact when you Tab inside.
INTERNAL_STORE_SPECTRUM = "DH Internal - Store Spectrum Attributes"
INTERNAL_NAMED_MAP = "DH Internal - Named Band Map"
INTERNAL_STORE_NAMED_META = "DH Internal - Store Named Band Metadata"
INTERNAL_STORE_NAMED = "DH Internal - Store Named Bands"

# Older public helper from V3.0/V3.1. It is removed during rebuild.
GROUP_STORE_BANDS = "DH Audio Store Bands"

CANONICAL_GROUPS = [
    GROUP_BARS,
    GROUP_FILL,
    GROUP_CURVE,
    GROUP_INSTANCES,
    GROUP_BANDS,
    GROUP_POINTS,
    GROUP_RANGE,
    GROUP_QUERY,
    GROUP_ANALYZER,
    GROUP_FREQ_SELECT,
    GROUP_FREQ_MAP,
    GROUP_RESPONSE,
    GROUP_MATERIAL_READER,
    GROUP_SHADER_RESPONSE,
    INTERNAL_STORE_SPECTRUM,
    INTERNAL_NAMED_MAP,
    INTERNAL_STORE_NAMED_META,
    INTERNAL_STORE_NAMED,
    GROUP_STORE_BANDS,
]

LEGACY_GROUPS = [
    "DH Audio Spectrum Core",
    "DH Audio Material Reader - Instance",
    "DH Audio Material Reader - Geometry",
]

HOST_OBJECT_NAME = "DH Audio Toolkit Demo"

# ---------------------------------------------------------------------
# Attribute schema
# ---------------------------------------------------------------------

SPECTRUM_ATTRS = [
    ("Amplitude",        "dh_audio_amp",          "FLOAT"),
    ("Normalized",       "dh_audio_norm",         "FLOAT"),
    ("Raw Amplitude",    "dh_audio_raw",          "FLOAT"),
    ("Band Index",       "dh_audio_band_index",   "INT"),
    ("Band Position",    "dh_audio_band_pos",     "FLOAT"),
    ("Low Frequency",    "dh_audio_low_hz",       "FLOAT"),
    ("Center Frequency", "dh_audio_center_hz",    "FLOAT"),
    ("High Frequency",   "dh_audio_high_hz",      "FLOAT"),
    ("Bandwidth",        "dh_audio_bandwidth_hz", "FLOAT"),
]

NAMED_BAND_ATTRS = [
    ("Total Volume", "dh_audio_total"),
    ("Sub",          "dh_audio_sub"),
    ("Bass",         "dh_audio_bass"),
    ("Low Mid",      "dh_audio_low_mid"),
    ("Mid Range",    "dh_audio_mid"),
    ("High Mids",    "dh_audio_high_mids"),
    ("Presence",     "dh_audio_presence"),
    ("Brilliance",   "dh_audio_brilliance"),
    ("Air",          "dh_audio_air"),
]


# =====================================================================
# General helpers
# =====================================================================

def require_blender_52():
    if bpy.app.version < BLENDER_MIN_VERSION:
        raise RuntimeError(
            f"DH Audio Toolkit requires Blender 5.2 or newer. "
            f"Current version: {bpy.app.version_string}"
        )


def get_socket(sockets, key):
    """Find a socket by index, display name, or identifier."""
    if isinstance(key, int):
        return sockets[key] if 0 <= key < len(sockets) else None

    sock = sockets.get(key)
    if sock is not None:
        return sock

    for candidate in sockets:
        if getattr(candidate, "identifier", None) == key:
            return candidate

    return None


def set_default(node, socket_key, value):
    sock = get_socket(node.inputs, socket_key)
    if sock is None:
        raise RuntimeError(
            f"Node '{node.name}' has no input '{socket_key}'. "
            f"Available: {[(s.name, s.identifier) for s in node.inputs]}"
        )

    try:
        sock.default_value = value
        return
    except TypeError as exc:
        # Blender 5.2 increasingly exposes node options as runtime menu
        # sockets. Their values are often human-readable menu identifiers
        # ("Count") rather than legacy RNA-style constants ("COUNT").
        #
        # When Blender helpfully includes the valid enum items in the error,
        # retry with a case-insensitive exact match. This keeps the generator
        # resilient to menu capitalization without guessing unrelated values.
        if isinstance(value, str):
            msg = str(exc)
            match = re.search(r"not found in \((.*?)\)", msg)
            if match:
                valid = re.findall(r"'([^']+)'", match.group(1))
                wanted = value.casefold()
                for candidate in valid:
                    if candidate.casefold() == wanted:
                        sock.default_value = candidate
                        return

        raise


def link(tree, from_node, from_socket, to_node, to_socket):
    out_sock = get_socket(from_node.outputs, from_socket)
    in_sock = get_socket(to_node.inputs, to_socket)

    if out_sock is None and from_socket in {"Geometry", "Curve", "Mesh", "Instances"}:
        # Geometry Nodes use several different labels for the same broad
        # geometry-family concept. If a node exposes exactly ONE such output,
        # safely use it as a compatibility fallback.
        geometry_output_names = {"Geometry", "Curve", "Mesh", "Instances"}
        candidates = [
            sock for sock in from_node.outputs
            if sock.name in geometry_output_names
        ]
        if len(candidates) == 1:
            out_sock = candidates[0]

    if out_sock is None:
        raise RuntimeError(
            f"Node '{from_node.name}' has no output '{from_socket}'. "
            f"Available: {[(s.name, s.identifier) for s in from_node.outputs]}"
        )

    if in_sock is None:
        raise RuntimeError(
            f"Node '{to_node.name}' has no input '{to_socket}'. "
            f"Available: {[(s.name, s.identifier) for s in to_node.inputs]}"
        )

    tree.links.new(out_sock, in_sock)


def new_socket(
    tree,
    name,
    in_out,
    socket_type,
    *,
    parent=None,
    default=None,
    min_value=None,
    max_value=None,
    description="",
    structure_type=None,
):
    # Blender 5.2 NodeTreeInterface.new_socket() accepts only BASE socket
    # identifiers. Specialized float socket IDs such as
    # "NodeSocketFloatFrequency" exist as RNA subclasses, but are not valid
    # values for the new_socket(socket_type=...) enum.
    #
    # Create a base NodeSocketFloat and assign the matching UI/unit subtype.
    specialized_float_subtypes = {
        "NodeSocketFloatTime": "TIME_ABSOLUTE",
        "NodeSocketFloatTimeAbsolute": "TIME_ABSOLUTE",
        "NodeSocketFloatFrequency": "FREQUENCY",
        "NodeSocketFloatDistance": "DISTANCE",
        "NodeSocketFloatAngle": "ANGLE",
        "NodeSocketFloatFactor": "FACTOR",
        "NodeSocketFloatPercentage": "PERCENTAGE",
        "NodeSocketFloatPixel": "PIXEL",
        "NodeSocketFloatMass": "MASS",
        "NodeSocketFloatWavelength": "WAVELENGTH",
        "NodeSocketFloatColorTemperature": "COLOR_TEMPERATURE",
        "NodeSocketFloatUnsigned": "UNSIGNED",
    }

    subtype = specialized_float_subtypes.get(socket_type)
    base_socket_type = "NodeSocketFloat" if subtype else socket_type

    sock = tree.interface.new_socket(
        name=name,
        description=description,
        in_out=in_out,
        socket_type=base_socket_type,
        parent=parent,
    )

    if subtype is not None and hasattr(sock, "subtype"):
        try:
            sock.subtype = subtype
        except Exception as exc:
            raise RuntimeError(
                f"Could not set subtype '{subtype}' for interface "
                f"socket '{name}': {exc}"
            ) from exc

    if structure_type is not None and hasattr(sock, "structure_type"):
        sock.structure_type = structure_type

    if default is not None and hasattr(sock, "default_value"):
        sock.default_value = default

    if min_value is not None and hasattr(sock, "min_value"):
        sock.min_value = min_value

    if max_value is not None and hasattr(sock, "max_value"):
        sock.max_value = max_value

    return sock


def new_menu_socket_from(
    tree,
    name,
    source_node,
    source_socket_name,
    *,
    parent=None,
    default=None,
    description="",
):
    """
    Copy Blender's runtime-defined menu definition from a real node socket
    into a group interface. Used for FFT Size and Window Function.
    """
    source_socket = get_socket(source_node.inputs, source_socket_name)
    if source_socket is None:
        raise RuntimeError(
            f"Could not find menu socket '{source_socket_name}' "
            f"on node '{source_node.name}'."
        )

    # Blender 5.2 runtime menu definitions are copied from the source socket,
    # including its current selection. Setting the interface default after
    # from_socket() can silently clear custom Menu Switch defaults to "".
    # Set the native/source socket first so the copied interface and every
    # subsequently created group-node instance inherit a valid selection.
    if default is not None:
        set_default(source_node, source_socket_name, default)

    sock = tree.interface.new_socket(
        name=name,
        description=description,
        in_out="INPUT",
        socket_type="NodeSocketMenu",
        parent=parent,
    )

    try:
        sock.from_socket(source_node, source_socket)
    except Exception as exc:
        raise RuntimeError(
            f"Could not copy Blender 5.2 menu metadata for '{name}' "
            f"from node '{source_node.name}': {exc}"
        ) from exc

    # from_socket can copy source presentation metadata.
    sock.name = name
    sock.description = description

    if hasattr(sock, "structure_type"):
        sock.structure_type = "SINGLE"

    return sock


def make_frame(nodes, name, label, location=(0, 0), width=420, label_size=22):
    frame = nodes.new("NodeFrame")
    frame.name = name
    frame.label = label
    frame.location = location
    frame.width = width
    frame.label_size = label_size
    return frame


def math_node(nodes, name, operation, location, parent=None, label=None):
    node = nodes.new("ShaderNodeMath")
    node.name = name
    node.label = label or name
    node.operation = operation
    if parent is not None:
        node.parent = parent
    node.location = location
    return node


def vector_math_node(nodes, name, operation, location, parent=None, label=None):
    node = nodes.new("ShaderNodeVectorMath")
    node.name = name
    node.label = label or name
    node.operation = operation
    if parent is not None:
        node.parent = parent
    node.location = location
    return node


def integer_math_node(nodes, name, operation, location, parent=None, label=None):
    node = nodes.new("FunctionNodeIntegerMath")
    node.name = name
    node.label = label or name
    node.operation = operation
    if parent is not None:
        node.parent = parent
    node.location = location
    return node


def switch_float_node(nodes, name, location, parent=None, label=None):
    node = nodes.new("GeometryNodeSwitch")
    node.name = name
    node.label = label or name
    node.input_type = "FLOAT"
    if parent is not None:
        node.parent = parent
    node.location = location
    return node


def switch_geometry_node(nodes, name, location, parent=None, label=None):
    node = nodes.new("GeometryNodeSwitch")
    node.name = name
    node.label = label or name
    node.input_type = "GEOMETRY"
    if parent is not None:
        node.parent = parent
    node.location = location
    return node


def switch_bool_node(nodes, name, location, parent=None, label=None):
    node = nodes.new("GeometryNodeSwitch")
    node.name = name
    node.label = label or name
    node.input_type = "BOOLEAN"
    if parent is not None:
        node.parent = parent
    node.location = location
    return node


def local_group_input(
    nodes,
    label,
    visible_sockets,
    *,
    parent=None,
    location=(0, 0),
    width=240,
):
    """
    Create a local Group Input node and hide every output except the sockets
    used by the nearby frame. Multiple Group Input nodes are valid and this
    dramatically reduces cable spaghetti in large reusable groups.
    """
    node = nodes.new("NodeGroupInput")
    node.label = label
    node.width = width
    if parent is not None:
        node.parent = parent
    node.location = location

    visible = set(visible_sockets)
    for sock in node.outputs:
        if sock.name:
            sock.hide = sock.name not in visible
    return node


def hide_node_sockets(node, *, inputs=(), outputs=()):
    hidden_inputs = set(inputs)
    hidden_outputs = set(outputs)
    for sock in node.inputs:
        if sock.name in hidden_inputs:
            sock.hide = True
    for sock in node.outputs:
        if sock.name in hidden_outputs:
            sock.hide = True


def index_switch_float(nodes, name, count, *, parent=None, location=(0, 0), label=None):
    node = nodes.new("GeometryNodeIndexSwitch")
    node.name = name
    node.label = label or name
    node.data_type = "FLOAT"
    node.index_switch_items.clear()
    for _ in range(count):
        node.index_switch_items.new()
    node.width = 280
    if parent is not None:
        node.parent = parent
    node.location = location
    return node


def menu_switch_geometry(nodes, name, items, *, parent=None, location=(0, 0), label=None):
    node = nodes.new("GeometryNodeMenuSwitch")
    node.name = name
    node.label = label or name
    node.data_type = "GEOMETRY"
    node.enum_items.clear()
    for item in items:
        node.enum_items.new(item)
    node.active_index = 0
    node.width = 300
    if parent is not None:
        node.parent = parent
    node.location = location
    return node


def assign_catalog_to_asset(tree):
    """Assign a stable catalog UUID to a marked public asset."""
    if not getattr(tree, "asset_data", None):
        return
    catalog_path = ASSET_CATALOG_PATHS.get(tree.name)
    if not catalog_path:
        return
    catalog_id, _simple_name = CATALOG_DEFINITIONS[catalog_path]
    tree.asset_data.catalog_id = catalog_id


def ensure_catalog_definition_file():
    """
    Merge the toolkit's stable catalogs into blender_assets.cats.txt beside
    the current .blend. This sidecar is what makes catalog folders portable
    when the asset-library folder is shared with somebody else.
    """
    blend_path = bpy.data.filepath
    if not blend_path:
        print(
            "DH Audio catalogs: current .blend has not been saved yet. "
            "Save the file and the registered save handler will create "
            "blender_assets.cats.txt beside it."
        )
        return None

    root = os.path.dirname(os.path.abspath(blend_path))
    catalog_path = os.path.join(root, "blender_assets.cats.txt")

    existing_lines = []
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as handle:
                existing_lines = handle.read().splitlines()
        except Exception as exc:
            print(f"Warning: could not read existing asset catalog file: {exc}")
            return None

    toolkit_ids = {catalog_id for catalog_id, _ in CATALOG_DEFINITIONS.values()}
    kept = []
    managed_comments = {
        "# This is an Asset Catalog Definition file for Blender.",
        "# DH Audio Toolkit entries use stable UUIDs for portable sharing.",
        "# Existing catalogs preserved below.",
    }

    for line in existing_lines:
        stripped = line.strip()
        if stripped == "VERSION 1":
            continue
        if stripped in managed_comments:
            # These lines are regenerated below. Keeping them would make each
            # rebuild append another copy beneath "Existing catalogs".
            continue
        if stripped and not stripped.startswith("#") and ":" in stripped:
            possible_id = stripped.split(":", 1)[0]
            if possible_id in toolkit_ids:
                # Replace any previous definition using our canonical UUID.
                continue
        if stripped:
            # Preserve unrelated catalog definitions and comments while
            # normalizing blank-line layout for deterministic rewrites.
            kept.append(line)

    header = [
        "# This is an Asset Catalog Definition file for Blender.",
        "# DH Audio Toolkit entries use stable UUIDs for portable sharing.",
        "VERSION 1",
        "",
    ]

    catalog_lines = [
        f"{catalog_id}:{path}:{simple_name}"
        for path, (catalog_id, simple_name) in CATALOG_DEFINITIONS.items()
    ]

    # Preserve unrelated catalogs while keeping a clean single VERSION line.
    preserved = kept
    output = header + catalog_lines
    if preserved:
        output += ["", "# Existing catalogs preserved below."] + preserved

    try:
        with open(catalog_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(output).rstrip() + "\n")
        print(f"DH Audio catalogs written: {catalog_path}")
        return catalog_path
    except Exception as exc:
        print(f"Warning: could not write asset catalog file: {exc}")
        return None


def _dh_audio_write_catalogs_on_save(_dummy=None):
    ensure_catalog_definition_file()


def register_catalog_save_handler():
    # Avoid stacking handlers across repeated generator runs in one session.
    handlers = bpy.app.handlers.save_post
    for handler in list(handlers):
        if getattr(handler, "__name__", "") == "_dh_audio_write_catalogs_on_save":
            handlers.remove(handler)
    handlers.append(_dh_audio_write_catalogs_on_save)


def mark_internal(tree, description="Internal DH Audio Toolkit helper"):
    tree.use_fake_user = True
    tree["dh_audio_toolkit_version"] = TOOLKIT_VERSION
    tree["dh_internal"] = True
    if hasattr(tree, "description"):
        try:
            tree.description = description
        except Exception:
            pass
    if hasattr(tree, "default_group_node_width"):
        try:
            tree.default_group_node_width = 360
        except Exception:
            pass


def mark_asset(tree, description):
    tree.use_fake_user = True
    tree["dh_audio_toolkit_version"] = TOOLKIT_VERSION

    # Public groups use tuned widths instead of a one-size-fits-all value.
    if hasattr(tree, "default_group_node_width"):
        try:
            tree.default_group_node_width = PUBLIC_GROUP_WIDTHS.get(tree.name, 310)
        except Exception:
            pass

    if hasattr(tree, "description"):
        try:
            tree.description = description
        except Exception:
            pass

    if not MARK_AS_ASSET:
        return

    try:
        tree.asset_mark()
        if tree.asset_data:
            tree.asset_data.description = description
            for tag in ("DH Audio", "Audio", "Blender 5.2"):
                try:
                    tree.asset_data.tags.new(tag)
                except Exception:
                    pass
            assign_catalog_to_asset(tree)
    except Exception as exc:
        print(f"Warning: could not mark '{tree.name}' as asset: {exc}")


def remove_group(name):
    group = bpy.data.node_groups.get(name)
    if group is not None:
        bpy.data.node_groups.remove(group, do_unlink=True)


def cleanup_existing():
    if REBUILD_EXISTING:
        # Remove in dependency-safe order.
        for name in CANONICAL_GROUPS:
            remove_group(name)

    if REMOVE_LEGACY_GROUPS:
        for name in LEGACY_GROUPS:
            remove_group(name)


def named_attribute_node(
    nodes,
    attr_name,
    data_type="FLOAT",
    *,
    parent=None,
    location=(0, 0),
    label=None,
):
    node = nodes.new("GeometryNodeInputNamedAttribute")
    node.name = f"Read {attr_name}"
    node.label = label or attr_name
    node.data_type = data_type
    if parent is not None:
        node.parent = parent
    node.location = location
    set_default(node, "Name", attr_name)
    return node


def store_named_attribute_node(
    nodes,
    attr_name,
    data_type,
    domain,
    *,
    parent=None,
    location=(0, 0),
    label=None,
):
    node = nodes.new("GeometryNodeStoreNamedAttribute")
    node.name = f"Store {attr_name} [{domain}]"
    node.label = label or attr_name
    node.data_type = data_type
    node.domain = domain
    node.width = 240
    if parent is not None:
        node.parent = parent
    node.location = location
    set_default(node, "Name", attr_name)
    return node


# =====================================================================
# Shared interface helpers
# =====================================================================

def add_time_audio_interface(
    tree,
    template_sample_node,
    *,
    fft_default="8192",
    parent=None,
):
    new_socket(
        tree, "Sound", "INPUT", "NodeSocketSound",
        parent=parent,
        description="Sound data-block to analyze",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Use Scene Time", "INPUT", "NodeSocketBool",
        parent=parent,
        default=True,
        description="Use Scene Time. Disable to use the custom Time input",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Time", "INPUT", "NodeSocketFloatTime",
        parent=parent,
        default=0.0,
        min_value=-100000.0,
        max_value=100000.0,
        description="Custom time in seconds when Use Scene Time is disabled",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Time Offset", "INPUT", "NodeSocketFloatTime",
        parent=parent,
        default=0.0,
        min_value=-100000.0,
        max_value=100000.0,
        description="Seconds added to the selected time source",
        structure_type="SINGLE",
    )

    # Match the compact presentation Blender uses on the native node.
    new_menu_socket_from(
        tree, "Window Function", template_sample_node, "Window Function",
        parent=parent,
        default="Hann",
        description="FFT window function",
    )

    new_menu_socket_from(
        tree, "FFT Size", template_sample_node, "FFT Size",
        parent=parent,
        default=fft_default,
        description=(
            "FFT analysis size. Higher values improve frequency resolution "
            "but reduce time resolution"
        ),
    )

    new_socket(
        tree, "All Channels", "INPUT", "NodeSocketBool",
        parent=parent,
        default=True,
        description="Mix all channels before sampling",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Channel", "INPUT", "NodeSocketInt",
        parent=parent,
        default=0,
        min_value=0,
        max_value=32,
        description="Channel used when All Channels is disabled",
        structure_type="SINGLE",
    )


def build_time_source(tree, group_in, parent, location=(0, 0)):
    nodes = tree.nodes
    x, y = location

    scene_time = nodes.new("GeometryNodeInputSceneTime")
    scene_time.name = "Scene Time"
    scene_time.label = "Scene Time"
    scene_time.parent = parent
    scene_time.location = (x, y + 120)

    time_switch = switch_float_node(
        nodes,
        "Time Source",
        (x + 180, y + 100),
        parent,
        "Custom / Scene Time",
    )

    time_add = math_node(
        nodes,
        "Time + Offset",
        "ADD",
        (x + 390, y + 100),
        parent,
        "Selected Time + Offset",
    )

    link(tree, group_in, "Use Scene Time", time_switch, "Switch")
    link(tree, group_in, "Time", time_switch, "False")
    link(tree, scene_time, "Seconds", time_switch, "True")

    link(tree, time_switch, "Output", time_add, 0)
    link(tree, group_in, "Time Offset", time_add, 1)

    return time_add


def connect_audio_settings(tree, group_in, sample_node, time_node):
    link(tree, group_in, "Sound", sample_node, "Sound")
    link(tree, time_node, "Value", sample_node, "Time")
    link(tree, group_in, "All Channels", sample_node, "All Channels")
    link(tree, group_in, "Channel", sample_node, "Channel")
    link(tree, group_in, "FFT Size", sample_node, "FFT Size")
    link(tree, group_in, "Window Function", sample_node, "Window Function")


def add_response_controls(tree, parent):
    new_socket(
        tree, "Gain", "INPUT", "NodeSocketFloat",
        parent=parent,
        default=1.0,
        min_value=0.0,
        max_value=10000.0,
        description="Multiplier applied before normalization",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Floor", "INPUT", "NodeSocketFloat",
        parent=parent,
        default=0.0,
        min_value=0.0,
        max_value=10000.0,
        description="Post-gain amplitude mapped to zero",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Ceiling", "INPUT", "NodeSocketFloat",
        parent=parent,
        default=0.8,
        min_value=0.000001,
        max_value=10000.0,
        description="Post-gain amplitude mapped to one",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Clamp to 1", "INPUT", "NodeSocketBool",
        parent=parent,
        default=True,
        description="Clamp normalized amplitude to a maximum of one",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Response", "INPUT", "NodeSocketFloat",
        parent=parent,
        default=0.7,
        min_value=0.01,
        max_value=10.0,
        description=(
            "Power curve. Below 1 emphasizes quieter values; "
            "above 1 emphasizes peaks"
        ),
        structure_type="SINGLE",
    )


# =====================================================================
# 1. DH Audio Response
# =====================================================================

def create_response_group():
    tree = bpy.data.node_groups.new(GROUP_RESPONSE, "GeometryNodeTree")
    tree["dh_role"] = "response"

    panel = tree.interface.new_panel(
        name="Response",
        description="Reusable amplitude normalization and response shaping",
        default_closed=False,
    )

    new_socket(
        tree, "Value", "INPUT", "NodeSocketFloat",
        parent=panel,
        default=0.0,
        min_value=0.0,
        max_value=1000000.0,
        description="Raw amplitude or any positive value to shape",
        structure_type="FIELD",
    )
    add_response_controls(tree, panel)

    new_socket(
        tree, "Value", "OUTPUT", "NodeSocketFloat",
        description="Processed response after power curve",
        structure_type="FIELD",
    )
    new_socket(
        tree, "Normalized", "OUTPUT", "NodeSocketFloat",
        description="Normalized value before the Response power curve",
        structure_type="FIELD",
    )
    new_socket(
        tree, "Gained", "OUTPUT", "NodeSocketFloat",
        description="Input multiplied by Gain",
        structure_type="FIELD",
    )

    nodes = tree.nodes
    group_in = nodes.new("NodeGroupInput")
    group_in.location = (-850, 120)

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (950, 120)
    group_out.is_active_output = True

    frame = make_frame(nodes, "FRAME_RESPONSE", "AMPLITUDE RESPONSE", (-520, 420), 1160)

    gain = math_node(nodes, "Apply Gain", "MULTIPLY", (20, 220), frame, "Value × Gain")
    subtract_floor = math_node(
        nodes, "Subtract Floor", "SUBTRACT", (200, 220), frame, "Gained - Floor"
    )
    response_range = math_node(
        nodes, "Response Range", "SUBTRACT", (20, 20), frame, "Ceiling - Floor"
    )
    safe_range = math_node(
        nodes, "Safe Range", "MAXIMUM", (200, 20), frame, "Max(range, epsilon)"
    )
    set_default(safe_range, 1, 0.000001)

    normalize = math_node(
        nodes, "Normalize", "DIVIDE", (390, 220), frame, "Normalize"
    )

    clamp_low = math_node(
        nodes, "Clamp Low", "MAXIMUM", (390, 20), frame, "Max(0)"
    )
    set_default(clamp_low, 1, 0.0)

    clamp_high = math_node(
        nodes, "Clamp High", "MINIMUM", (570, 20), frame, "Min(1)"
    )
    set_default(clamp_high, 1, 1.0)

    clamp_switch = switch_float_node(
        nodes, "Clamp High Switch", (590, 220), frame, "Clamp to 1?"
    )

    response = math_node(
        nodes, "Response Curve", "POWER", (790, 220), frame, "Normalized ^ Response"
    )

    link(tree, group_in, "Value", gain, 0)
    link(tree, group_in, "Gain", gain, 1)

    link(tree, gain, "Value", subtract_floor, 0)
    link(tree, group_in, "Floor", subtract_floor, 1)

    link(tree, group_in, "Ceiling", response_range, 0)
    link(tree, group_in, "Floor", response_range, 1)
    link(tree, response_range, "Value", safe_range, 0)

    link(tree, subtract_floor, "Value", normalize, 0)
    link(tree, safe_range, "Value", normalize, 1)

    link(tree, normalize, "Value", clamp_low, 0)
    link(tree, clamp_low, "Value", clamp_high, 0)

    link(tree, group_in, "Clamp to 1", clamp_switch, "Switch")
    link(tree, clamp_low, "Value", clamp_switch, "False")
    link(tree, clamp_high, "Value", clamp_switch, "True")

    link(tree, clamp_switch, "Output", response, 0)
    link(tree, group_in, "Response", response, 1)

    link(tree, response, "Value", group_out, "Value")
    link(tree, clamp_switch, "Output", group_out, "Normalized")
    link(tree, gain, "Value", group_out, "Gained")

    mark_asset(
        tree,
        "Reusable Geometry Nodes response shaper for audio amplitude or any scalar field."
    )
    return tree


# =====================================================================
# 2. DH Audio Shader Response
# =====================================================================

def create_shader_response_group():
    tree = bpy.data.node_groups.new(GROUP_SHADER_RESPONSE, "ShaderNodeTree")
    tree["dh_role"] = "shader_response"

    panel = tree.interface.new_panel(
        name="Response",
        description="Shader-side equivalent of DH Audio Response",
        default_closed=False,
    )

    new_socket(tree, "Value", "INPUT", "NodeSocketFloat", parent=panel, default=0.0)
    new_socket(tree, "Gain", "INPUT", "NodeSocketFloat", parent=panel, default=1.0, min_value=0.0)
    new_socket(tree, "Floor", "INPUT", "NodeSocketFloat", parent=panel, default=0.0, min_value=0.0)
    new_socket(tree, "Ceiling", "INPUT", "NodeSocketFloat", parent=panel, default=0.8, min_value=0.000001)
    new_socket(tree, "Clamp to 1", "INPUT", "NodeSocketBool", parent=panel, default=True, description="Clamp normalized response to a maximum of 1")
    new_socket(tree, "Response", "INPUT", "NodeSocketFloat", parent=panel, default=0.7, min_value=0.01, max_value=10.0)

    new_socket(tree, "Value", "OUTPUT", "NodeSocketFloat")
    new_socket(tree, "Normalized", "OUTPUT", "NodeSocketFloat")
    new_socket(tree, "Gained", "OUTPUT", "NodeSocketFloat")

    nodes = tree.nodes
    group_in = nodes.new("NodeGroupInput")
    group_in.location = (-850, 120)

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (950, 120)
    group_out.is_active_output = True

    frame = make_frame(nodes, "FRAME_RESPONSE", "SHADER RESPONSE", (-520, 420), 1160)

    gain = math_node(nodes, "Apply Gain", "MULTIPLY", (20, 220), frame, "Value × Gain")
    subtract_floor = math_node(nodes, "Subtract Floor", "SUBTRACT", (200, 220), frame, "Gained - Floor")
    response_range = math_node(nodes, "Response Range", "SUBTRACT", (20, 20), frame, "Ceiling - Floor")
    safe_range = math_node(nodes, "Safe Range", "MAXIMUM", (200, 20), frame, "Max(range, epsilon)")
    set_default(safe_range, 1, 0.000001)

    normalize = math_node(nodes, "Normalize", "DIVIDE", (390, 220), frame, "Normalize")
    clamp_low = math_node(nodes, "Clamp Low", "MAXIMUM", (390, 20), frame, "Max(0)")
    set_default(clamp_low, 1, 0.0)

    clamp_high = math_node(nodes, "Clamp High", "MINIMUM", (570, 20), frame, "Min(1)")
    set_default(clamp_high, 1, 1.0)

    # Shader trees do not have GeometryNodeSwitch. Blend mathematically:
    # selected = unclamped + clamp_factor * (clamped - unclamped)
    clamp_diff = math_node(nodes, "Clamp Difference", "SUBTRACT", (570, -160), frame, "Clamped - Unclamped")
    clamp_weight = math_node(nodes, "Clamp Weight", "MULTIPLY", (740, -160), frame, "Difference × Toggle")
    clamp_select = math_node(nodes, "Clamp Select", "ADD", (740, 60), frame, "Selected Normalized")

    response = math_node(nodes, "Response Curve", "POWER", (920, 60), frame, "Normalized ^ Response")

    link(tree, group_in, "Value", gain, 0)
    link(tree, group_in, "Gain", gain, 1)

    link(tree, gain, "Value", subtract_floor, 0)
    link(tree, group_in, "Floor", subtract_floor, 1)

    link(tree, group_in, "Ceiling", response_range, 0)
    link(tree, group_in, "Floor", response_range, 1)
    link(tree, response_range, "Value", safe_range, 0)

    link(tree, subtract_floor, "Value", normalize, 0)
    link(tree, safe_range, "Value", normalize, 1)
    link(tree, normalize, "Value", clamp_low, 0)
    link(tree, clamp_low, "Value", clamp_high, 0)

    link(tree, clamp_high, "Value", clamp_diff, 0)
    link(tree, clamp_low, "Value", clamp_diff, 1)
    link(tree, clamp_diff, "Value", clamp_weight, 0)
    link(tree, group_in, "Clamp to 1", clamp_weight, 1)
    link(tree, clamp_low, "Value", clamp_select, 0)
    link(tree, clamp_weight, "Value", clamp_select, 1)

    link(tree, clamp_select, "Value", response, 0)
    link(tree, group_in, "Response", response, 1)

    link(tree, response, "Value", group_out, "Value")
    link(tree, clamp_select, "Value", group_out, "Normalized")
    link(tree, gain, "Value", group_out, "Gained")

    mark_asset(
        tree,
        "Shader-side audio response shaper matching DH Audio Response."
    )
    return tree



# =====================================================================
# 3. DH Audio Frequency Map
# =====================================================================

def create_frequency_map():
    tree = bpy.data.node_groups.new(GROUP_FREQ_MAP, "GeometryNodeTree")
    tree["dh_role"] = "frequency_map"

    input_panel = tree.interface.new_panel(
        name="Band Mapping",
        description="Convert an indexed band into frequency bounds",
        default_closed=False,
    )
    output_panel = tree.interface.new_panel(
        name="Outputs",
        description="Mapped band position and frequency metadata",
        default_closed=False,
    )

    new_socket(
        tree, "Band Index", "INPUT", "NodeSocketInt",
        parent=input_panel,
        default=0,
        min_value=0,
        max_value=100000,
        description="Zero-based band index",
        structure_type="FIELD",
    )
    new_socket(
        tree, "Bands", "INPUT", "NodeSocketInt",
        parent=input_panel,
        default=32,
        min_value=1,
        max_value=100000,
        description="Total number of bands",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Min Frequency", "INPUT", "NodeSocketFloatFrequency",
        parent=input_panel,
        default=30.0,
        min_value=0.001,
        max_value=96000.0,
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Max Frequency", "INPUT", "NodeSocketFloatFrequency",
        parent=input_panel,
        default=16000.0,
        min_value=0.001,
        max_value=96000.0,
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Logarithmic", "INPUT", "NodeSocketBool",
        parent=input_panel,
        default=True,
        structure_type="SINGLE",
    )

    for name, socket_type in [
        ("Band Position", "NodeSocketFloat"),
        ("Low Frequency", "NodeSocketFloatFrequency"),
        ("Center Frequency", "NodeSocketFloatFrequency"),
        ("High Frequency", "NodeSocketFloatFrequency"),
        ("Bandwidth", "NodeSocketFloatFrequency"),
    ]:
        new_socket(
            tree, name, "OUTPUT", socket_type,
            parent=output_panel,
            structure_type="FIELD",
        )

    nodes = tree.nodes
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1750, 120)
    group_out.width = 240
    group_out.is_active_output = True

    frame_norm = make_frame(nodes, "FRAME_INDEX", "1  INDEX NORMALIZATION", (-900, 460), 760)
    frame_range = make_frame(nodes, "FRAME_RANGE", "2  SAFE FREQUENCY RANGE", (-20, 460), 500)
    frame_map = make_frame(nodes, "FRAME_MAP", "3  LINEAR / LOG MAP", (600, 460), 950)

    idx_in = local_group_input(
        nodes, "Band Mapping",
        ["Band Index", "Bands"],
        parent=frame_norm,
        location=(20, 140),
        width=210,
    )
    range_in = local_group_input(
        nodes, "Frequency Range",
        ["Min Frequency", "Max Frequency", "Logarithmic"],
        parent=frame_range,
        location=(20, 140),
        width=220,
    )
    mode_in = local_group_input(
        nodes, "Mapping Mode",
        ["Logarithmic"],
        parent=frame_map,
        location=(20, -250),
        width=190,
    )

    index_plus_one = math_node(nodes, "Index + 1", "ADD", (250, 220), frame_norm, "Index + 1")
    set_default(index_plus_one, 1, 1.0)

    bands_minus_one = math_node(nodes, "Bands - 1", "SUBTRACT", (250, 20), frame_norm, "Bands - 1")
    set_default(bands_minus_one, 1, 1.0)

    safe_pos_div = math_node(
        nodes, "Safe Position Divisor", "MAXIMUM",
        (430, 20), frame_norm, "Max(Bands - 1, 1)"
    )
    set_default(safe_pos_div, 1, 1.0)

    start_norm = math_node(nodes, "Band Start", "DIVIDE", (430, 220), frame_norm, "Index / Bands")
    end_norm = math_node(nodes, "Band End", "DIVIDE", (610, 220), frame_norm, "(Index + 1) / Bands")
    band_pos = math_node(nodes, "Band Position", "DIVIDE", (610, 20), frame_norm, "Index / safe(Bands - 1)")

    link(tree, idx_in, "Band Index", index_plus_one, 0)
    link(tree, idx_in, "Bands", bands_minus_one, 0)
    link(tree, bands_minus_one, "Value", safe_pos_div, 0)

    link(tree, idx_in, "Band Index", start_norm, 0)
    link(tree, idx_in, "Bands", start_norm, 1)
    link(tree, index_plus_one, "Value", end_norm, 0)
    link(tree, idx_in, "Bands", end_norm, 1)
    link(tree, idx_in, "Band Index", band_pos, 0)
    link(tree, safe_pos_div, "Value", band_pos, 1)

    safe_min = math_node(nodes, "Safe Min", "MAXIMUM", (250, 180), frame_range, "Max(Min, 0.001)")
    set_default(safe_min, 1, 0.001)
    min_plus_eps = math_node(nodes, "Min + Epsilon", "ADD", (250, -20), frame_range, "Min + 0.001")
    set_default(min_plus_eps, 1, 0.001)
    safe_max = math_node(nodes, "Safe Max", "MAXIMUM", (430, 80), frame_range, "Max(Max, Min + epsilon)")

    link(tree, range_in, "Min Frequency", safe_min, 0)
    link(tree, safe_min, "Value", min_plus_eps, 0)
    link(tree, range_in, "Max Frequency", safe_max, 0)
    link(tree, min_plus_eps, "Value", safe_max, 1)

    ratio = math_node(nodes, "Frequency Ratio", "DIVIDE", (250, 300), frame_map, "Max / Min")
    log_low_pow = math_node(nodes, "Log Low Power", "POWER", (430, 300), frame_map, "Ratio ^ Start")
    log_high_pow = math_node(nodes, "Log High Power", "POWER", (430, 130), frame_map, "Ratio ^ End")
    log_low = math_node(nodes, "Log Low", "MULTIPLY", (610, 300), frame_map, "Min × Power")
    log_high = math_node(nodes, "Log High", "MULTIPLY", (610, 130), frame_map, "Min × Power")

    link(tree, safe_max, "Value", ratio, 0)
    link(tree, safe_min, "Value", ratio, 1)
    link(tree, ratio, "Value", log_low_pow, 0)
    link(tree, start_norm, "Value", log_low_pow, 1)
    link(tree, ratio, "Value", log_high_pow, 0)
    link(tree, end_norm, "Value", log_high_pow, 1)
    link(tree, safe_min, "Value", log_low, 0)
    link(tree, log_low_pow, "Value", log_low, 1)
    link(tree, safe_min, "Value", log_high, 0)
    link(tree, log_high_pow, "Value", log_high, 1)

    span = math_node(nodes, "Frequency Span", "SUBTRACT", (250, -40), frame_map, "Max - Min")
    lin_low_delta = math_node(nodes, "Linear Low Delta", "MULTIPLY", (430, -40), frame_map, "Span × Start")
    lin_high_delta = math_node(nodes, "Linear High Delta", "MULTIPLY", (430, -210), frame_map, "Span × End")
    lin_low = math_node(nodes, "Linear Low", "ADD", (610, -40), frame_map, "Min + Delta")
    lin_high = math_node(nodes, "Linear High", "ADD", (610, -210), frame_map, "Min + Delta")

    link(tree, safe_max, "Value", span, 0)
    link(tree, safe_min, "Value", span, 1)
    link(tree, span, "Value", lin_low_delta, 0)
    link(tree, start_norm, "Value", lin_low_delta, 1)
    link(tree, span, "Value", lin_high_delta, 0)
    link(tree, end_norm, "Value", lin_high_delta, 1)
    link(tree, safe_min, "Value", lin_low, 0)
    link(tree, lin_low_delta, "Value", lin_low, 1)
    link(tree, safe_min, "Value", lin_high, 0)
    link(tree, lin_high_delta, "Value", lin_high, 1)

    low_switch = switch_float_node(nodes, "Low Mode", (790, 210), frame_map, "Linear / Log Low")
    high_switch = switch_float_node(nodes, "High Mode", (790, 10), frame_map, "Linear / Log High")

    link(tree, mode_in, "Logarithmic", low_switch, "Switch")
    link(tree, lin_low, "Value", low_switch, "False")
    link(tree, log_low, "Value", low_switch, "True")

    link(tree, mode_in, "Logarithmic", high_switch, "Switch")
    link(tree, lin_high, "Value", high_switch, "False")
    link(tree, log_high, "Value", high_switch, "True")

    low_x_high = math_node(nodes, "Low × High", "MULTIPLY", (790, -170), frame_map, "Low × High")
    geom_center = math_node(nodes, "Geometric Center", "SQRT", (970, -170), frame_map, "sqrt(Low × High)")
    low_plus_high = math_node(nodes, "Low + High", "ADD", (790, -330), frame_map, "Low + High")
    linear_center = math_node(nodes, "Linear Center", "MULTIPLY", (970, -330), frame_map, "(Low + High) / 2")
    set_default(linear_center, 1, 0.5)
    center_switch = switch_float_node(nodes, "Center Mode", (1140, -220), frame_map, "Linear / Log Center")
    bandwidth = math_node(nodes, "Bandwidth", "SUBTRACT", (1140, -30), frame_map, "High - Low")

    link(tree, low_switch, "Output", low_x_high, 0)
    link(tree, high_switch, "Output", low_x_high, 1)
    link(tree, low_x_high, "Value", geom_center, 0)
    link(tree, low_switch, "Output", low_plus_high, 0)
    link(tree, high_switch, "Output", low_plus_high, 1)
    link(tree, low_plus_high, "Value", linear_center, 0)

    link(tree, mode_in, "Logarithmic", center_switch, "Switch")
    link(tree, linear_center, "Value", center_switch, "False")
    link(tree, geom_center, "Value", center_switch, "True")

    link(tree, high_switch, "Output", bandwidth, 0)
    link(tree, low_switch, "Output", bandwidth, 1)

    link(tree, band_pos, "Value", group_out, "Band Position")
    link(tree, low_switch, "Output", group_out, "Low Frequency")
    link(tree, center_switch, "Output", group_out, "Center Frequency")
    link(tree, high_switch, "Output", group_out, "High Frequency")
    link(tree, bandwidth, "Value", group_out, "Bandwidth")

    mark_asset(
        tree,
        "Advanced utility: map a band index to linear or logarithmic frequency bounds."
    )
    return tree



# =====================================================================
# 4. DH Audio Frequency Selection
# =====================================================================

def create_frequency_selection():
    """
    Create a reusable Boolean field that selects analyzer points/instances
    by their actual center frequency rather than by band index.
    """
    tree = bpy.data.node_groups.new(GROUP_FREQ_SELECT, "GeometryNodeTree")
    tree["dh_role"] = "frequency_selection"

    panel = tree.interface.new_panel(
        name="Frequency Selection",
        description="Select spectrum elements by stored center frequency",
        default_closed=False,
    )
    outputs_panel = tree.interface.new_panel(name="Outputs", default_closed=False)

    new_socket(
        tree, "Low Frequency", "INPUT", "NodeSocketFloatFrequency",
        parent=panel,
        default=20.0,
        min_value=0.0,
        max_value=96000.0,
        description="Inclusive lower bound",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "High Frequency", "INPUT", "NodeSocketFloatFrequency",
        parent=panel,
        default=20000.0,
        min_value=0.0,
        max_value=96000.0,
        description="Inclusive upper bound",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Invert", "INPUT", "NodeSocketBool",
        parent=panel,
        default=False,
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Selection", "OUTPUT", "NodeSocketBool",
        parent=outputs_panel,
        description="Boolean field based on dh_audio_center_hz",
        structure_type="FIELD",
    )
    new_socket(
        tree, "Amplitude", "OUTPUT", "NodeSocketFloat",
        parent=outputs_panel,
        description="Convenience pass-through of dh_audio_amp",
        structure_type="FIELD",
    )
    new_socket(
        tree, "Normalized", "OUTPUT", "NodeSocketFloat",
        parent=outputs_panel,
        description="Convenience pass-through of dh_audio_norm",
        structure_type="FIELD",
    )

    nodes = tree.nodes
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1050, 100)
    group_out.is_active_output = True

    frame = make_frame(nodes, "FRAME_SELECTION", "FREQUENCY RANGE SELECTION", (-760, 500), 1450)

    inp = local_group_input(
        nodes, "Frequency Range",
        ["Low Frequency", "High Frequency", "Invert"],
        parent=frame, location=(20, 100), width=220
    )

    center_attr = named_attribute_node(
        nodes, "dh_audio_center_hz", "FLOAT",
        parent=frame, location=(270, 280), label="Center Frequency"
    )
    amp_attr = named_attribute_node(
        nodes, "dh_audio_amp", "FLOAT",
        parent=frame, location=(270, -80), label="Amplitude"
    )
    norm_attr = named_attribute_node(
        nodes, "dh_audio_norm", "FLOAT",
        parent=frame, location=(270, -250), label="Normalized"
    )

    low_cmp = nodes.new("FunctionNodeCompare")
    low_cmp.name = "Above Low"
    low_cmp.label = "Center ≥ Low"
    low_cmp.data_type = "FLOAT"
    low_cmp.operation = "GREATER_EQUAL"
    low_cmp.parent = frame
    low_cmp.location = (500, 260)

    high_cmp = nodes.new("FunctionNodeCompare")
    high_cmp.name = "Below High"
    high_cmp.label = "Center ≤ High"
    high_cmp.data_type = "FLOAT"
    high_cmp.operation = "LESS_EQUAL"
    high_cmp.parent = frame
    high_cmp.location = (500, 80)

    link(tree, center_attr, "Attribute", low_cmp, "A")
    link(tree, inp, "Low Frequency", low_cmp, "B")
    link(tree, center_attr, "Attribute", high_cmp, "A")
    link(tree, inp, "High Frequency", high_cmp, "B")

    both = nodes.new("FunctionNodeBooleanMath")
    both.name = "Inside Range"
    both.label = "Inside Frequency Range"
    both.operation = "AND"
    both.parent = frame
    both.location = (720, 180)
    link(tree, low_cmp, "Result", both, 0)
    link(tree, high_cmp, "Result", both, 1)

    invert = nodes.new("FunctionNodeBooleanMath")
    invert.name = "Invert Selection"
    invert.label = "Not Selection"
    invert.operation = "NOT"
    invert.parent = frame
    invert.location = (720, -20)
    link(tree, both, "Boolean", invert, 0)

    choose = switch_bool_node(
        nodes, "Invert?", (910, 120), frame, "Normal / Inverted"
    )
    link(tree, inp, "Invert", choose, "Switch")
    link(tree, both, "Boolean", choose, "False")
    link(tree, invert, "Boolean", choose, "True")

    link(tree, choose, "Output", group_out, "Selection")
    link(tree, amp_attr, "Attribute", group_out, "Amplitude")
    link(tree, norm_attr, "Attribute", group_out, "Normalized")

    mark_asset(
        tree,
        "Select DH Audio spectrum elements by actual center-frequency range, "
        "with convenient amplitude and normalized pass-through fields."
    )
    return tree


# =====================================================================
# Internal helper: Store Analyzer attributes
# =====================================================================

def create_internal_store_spectrum():
    tree = bpy.data.node_groups.new(INTERNAL_STORE_SPECTRUM, "GeometryNodeTree")
    tree["dh_role"] = "internal_store_spectrum"

    new_socket(tree, "Geometry", "INPUT", "NodeSocketGeometry")
    for name, socket_type in [
        ("Amplitude", "NodeSocketFloat"),
        ("Normalized", "NodeSocketFloat"),
        ("Raw Amplitude", "NodeSocketFloat"),
        ("Band Index", "NodeSocketInt"),
        ("Band Position", "NodeSocketFloat"),
        ("Low Frequency", "NodeSocketFloat"),
        ("Center Frequency", "NodeSocketFloat"),
        ("High Frequency", "NodeSocketFloat"),
        ("Bandwidth", "NodeSocketFloat"),
    ]:
        new_socket(tree, name, "INPUT", socket_type, structure_type="FIELD")
    new_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry")

    nodes = tree.nodes
    gi = nodes.new("NodeGroupInput")
    gi.location = (-700, 100)
    gi.width = 240
    go = nodes.new("NodeGroupOutput")
    go.location = (1450, 100)
    go.is_active_output = True

    specs = [
        ("dh_audio_amp",          "FLOAT", "Amplitude"),
        ("dh_audio_norm",         "FLOAT", "Normalized"),
        ("dh_audio_raw",          "FLOAT", "Raw Amplitude"),
        ("dh_audio_band_index",   "INT",   "Band Index"),
        ("dh_audio_band_pos",     "FLOAT", "Band Position"),
        ("dh_audio_low_hz",       "FLOAT", "Low Frequency"),
        ("dh_audio_center_hz",    "FLOAT", "Center Frequency"),
        ("dh_audio_high_hz",      "FLOAT", "High Frequency"),
        ("dh_audio_bandwidth_hz", "FLOAT", "Bandwidth"),
    ]

    previous = gi
    previous_socket = "Geometry"
    for i, (attr_name, dtype, input_name) in enumerate(specs):
        store = store_named_attribute_node(
            nodes, attr_name, dtype, "POINT",
            location=(-350 + i * 190, 100),
            label=input_name,
        )
        link(tree, previous, previous_socket, store, "Geometry")
        link(tree, gi, input_name, store, "Value")
        previous = store
        previous_socket = "Geometry"

    link(tree, previous, previous_socket, go, "Geometry")
    mark_internal(tree, "Internal writer for DH Audio Analyzer named attributes")
    return tree


# =====================================================================
# Internal helper: Named band range map
# =====================================================================

def create_internal_named_band_map():
    tree = bpy.data.node_groups.new(INTERNAL_NAMED_MAP, "GeometryNodeTree")
    tree["dh_role"] = "internal_named_band_map"

    panel = tree.interface.new_panel(name="Inputs", default_closed=False)

    new_socket(
        tree, "Band Index", "INPUT", "NodeSocketInt",
        parent=panel, default=0, min_value=0, max_value=8,
        structure_type="FIELD",
    )
    for name, default in [
        ("Total Low", 20.0),
        ("Total High", 20000.0),
        ("Low Cut", 20.0),
        ("Sub", 60.0),
        ("Bass", 250.0),
        ("Low Mids", 500.0),
        ("Mid Range", 2000.0),
        ("High Mids", 4000.0),
        ("Presence", 6000.0),
        ("Brilliance", 10000.0),
        ("Air", 20000.0),
    ]:
        new_socket(
            tree, name, "INPUT", "NodeSocketFloatFrequency",
            parent=panel, default=default, min_value=0.0, max_value=96000.0,
            structure_type="SINGLE",
        )

    for name in ("Low Frequency", "Center Frequency", "High Frequency", "Bandwidth"):
        new_socket(
            tree, name, "OUTPUT", "NodeSocketFloatFrequency",
            structure_type="FIELD",
        )

    nodes = tree.nodes
    go = nodes.new("NodeGroupOutput")
    go.location = (1550, 100)
    go.is_active_output = True

    frame_safe = make_frame(nodes, "FRAME_SAFE", "SAFE CONTIGUOUS LIMITS", (-950, 520), 920)
    frame_select = make_frame(nodes, "FRAME_SELECT", "INDEXED RANGE", (100, 520), 1050)

    limits_in = local_group_input(
        nodes, "Named Band Limits",
        ["Band Index", "Total Low", "Total High", "Low Cut", "Sub", "Bass",
         "Low Mids", "Mid Range", "High Mids", "Presence", "Brilliance", "Air"],
        parent=frame_safe, location=(20, 170), width=240
    )

    total_low = math_node(nodes, "Safe Total Low", "MAXIMUM", (280, 300), frame_safe, "Max(Total Low, 0)")
    set_default(total_low, 1, 0.0)
    total_high = math_node(nodes, "Safe Total High", "MAXIMUM", (480, 300), frame_safe, "Max(Total High, Total Low)")
    link(tree, limits_in, "Total Low", total_low, 0)
    link(tree, limits_in, "Total High", total_high, 0)
    link(tree, total_low, "Value", total_high, 1)

    safe = {}
    low_cut = math_node(nodes, "Safe Low Cut", "MAXIMUM", (280, 80), frame_safe, "Max(Low Cut, 0)")
    set_default(low_cut, 1, 0.0)
    link(tree, limits_in, "Low Cut", low_cut, 0)
    safe["Low Cut"] = low_cut

    chain_names = ["Sub", "Bass", "Low Mids", "Mid Range", "High Mids", "Presence", "Brilliance", "Air"]
    prev = low_cut
    for i, name in enumerate(chain_names):
        col = i % 4
        row = i // 4
        node = math_node(
            nodes, f"Safe {name}", "MAXIMUM",
            (480 + col * 200, 80 - row * 180),
            frame_safe, f"Max({name}, previous)"
        )
        link(tree, limits_in, name, node, 0)
        link(tree, prev, "Value", node, 1)
        safe[name] = node
        prev = node

    select_in = local_group_input(
        nodes, "Band Index",
        ["Band Index"],
        parent=frame_select, location=(20, 80), width=180
    )

    low_switch = index_switch_float(nodes, "Low Boundary", 9, parent=frame_select, location=(240, 220), label="Low Boundary by Band")
    high_switch = index_switch_float(nodes, "High Boundary", 9, parent=frame_select, location=(240, -100), label="High Boundary by Band")
    link(tree, select_in, "Band Index", low_switch, "Index")
    link(tree, select_in, "Band Index", high_switch, "Index")

    low_sources = [
        (total_low, "Value"),
        (low_cut, "Value"),
        (safe["Sub"], "Value"),
        (safe["Bass"], "Value"),
        (safe["Low Mids"], "Value"),
        (safe["Mid Range"], "Value"),
        (safe["High Mids"], "Value"),
        (safe["Presence"], "Value"),
        (safe["Brilliance"], "Value"),
    ]
    high_sources = [
        (total_high, "Value"),
        (safe["Sub"], "Value"),
        (safe["Bass"], "Value"),
        (safe["Low Mids"], "Value"),
        (safe["Mid Range"], "Value"),
        (safe["High Mids"], "Value"),
        (safe["Presence"], "Value"),
        (safe["Brilliance"], "Value"),
        (safe["Air"], "Value"),
    ]

    for i, (node, sock) in enumerate(low_sources):
        link(tree, node, sock, low_switch, i + 1)
    for i, (node, sock) in enumerate(high_sources):
        link(tree, node, sock, high_switch, i + 1)

    add = math_node(nodes, "Low + High", "ADD", (620, 170), frame_select, "Low + High")
    center = math_node(nodes, "Center", "MULTIPLY", (800, 170), frame_select, "(Low + High) / 2")
    set_default(center, 1, 0.5)
    bandwidth = math_node(nodes, "Bandwidth", "SUBTRACT", (800, -40), frame_select, "High - Low")

    link(tree, low_switch, "Output", add, 0)
    link(tree, high_switch, "Output", add, 1)
    link(tree, add, "Value", center, 0)
    link(tree, high_switch, "Output", bandwidth, 0)
    link(tree, low_switch, "Output", bandwidth, 1)

    link(tree, low_switch, "Output", go, "Low Frequency")
    link(tree, center, "Value", go, "Center Frequency")
    link(tree, high_switch, "Output", go, "High Frequency")
    link(tree, bandwidth, "Value", go, "Bandwidth")

    mark_internal(tree, "Internal named musical-band range mapper")
    return tree


# =====================================================================
# Internal helper: Store point-specific named-band carrier metadata
# =====================================================================

def create_internal_store_named_metadata():
    tree = bpy.data.node_groups.new(INTERNAL_STORE_NAMED_META, "GeometryNodeTree")
    tree["dh_role"] = "internal_store_named_metadata"

    new_socket(tree, "Geometry", "INPUT", "NodeSocketGeometry")
    for name, socket_type in [
        ("Amplitude", "NodeSocketFloat"),
        ("Band Index", "NodeSocketInt"),
        ("Low Frequency", "NodeSocketFloat"),
        ("Center Frequency", "NodeSocketFloat"),
        ("High Frequency", "NodeSocketFloat"),
        ("Bandwidth", "NodeSocketFloat"),
    ]:
        new_socket(tree, name, "INPUT", socket_type, structure_type="FIELD")
    new_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry")

    nodes = tree.nodes
    gi = nodes.new("NodeGroupInput")
    gi.location = (-600, 100)
    gi.width = 220
    go = nodes.new("NodeGroupOutput")
    go.location = (1000, 100)
    go.is_active_output = True

    specs = [
        ("dh_audio_named_amp", "FLOAT", "Amplitude"),
        ("dh_audio_named_index", "INT", "Band Index"),
        ("dh_audio_named_low_hz", "FLOAT", "Low Frequency"),
        ("dh_audio_named_center_hz", "FLOAT", "Center Frequency"),
        ("dh_audio_named_high_hz", "FLOAT", "High Frequency"),
        ("dh_audio_named_bandwidth_hz", "FLOAT", "Bandwidth"),
    ]

    previous = gi
    previous_socket = "Geometry"
    for i, (attr, dtype, input_name) in enumerate(specs):
        store = store_named_attribute_node(
            nodes, attr, dtype, "POINT",
            location=(-300 + i * 200, 100),
            label=input_name,
        )
        link(tree, previous, previous_socket, store, "Geometry")
        link(tree, gi, input_name, store, "Value")
        previous = store
        previous_socket = "Geometry"

    link(tree, previous, previous_socket, go, "Geometry")
    mark_internal(tree, "Internal writer for per-point named-band carrier metadata")
    return tree


# =====================================================================
# Internal helper: Store named musical-band values
# =====================================================================

def create_internal_store_named_bands():
    tree = bpy.data.node_groups.new(INTERNAL_STORE_NAMED, "GeometryNodeTree")
    tree["dh_role"] = "internal_store_named_bands"

    new_socket(tree, "Geometry", "INPUT", "NodeSocketGeometry")
    new_socket(tree, "Store on Points", "INPUT", "NodeSocketBool", default=True, structure_type="SINGLE")
    new_socket(tree, "Store on Instances", "INPUT", "NodeSocketBool", default=True, structure_type="SINGLE")
    for name, _attr in NAMED_BAND_ATTRS:
        new_socket(tree, name, "INPUT", "NodeSocketFloat", default=0.0, structure_type="FIELD")
    new_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry")

    nodes = tree.nodes
    go = nodes.new("NodeGroupOutput")
    go.location = (2100, 100)
    go.is_active_output = True

    frame_points = make_frame(nodes, "FRAME_POINTS", "POINT DOMAIN", (-1200, 520), 1400)
    frame_instances = make_frame(nodes, "FRAME_INSTANCES", "INSTANCE DOMAIN", (320, 520), 1400)

    point_in = local_group_input(
        nodes, "Point Attributes",
        ["Geometry", "Store on Points"] + [name for name, _ in NAMED_BAND_ATTRS],
        parent=frame_points, location=(20, 150), width=230
    )
    inst_in = local_group_input(
        nodes, "Instance Attributes",
        ["Store on Instances"] + [name for name, _ in NAMED_BAND_ATTRS],
        parent=frame_instances, location=(20, 150), width=230
    )

    previous = point_in
    previous_socket = "Geometry"
    for i, (input_name, attr_name) in enumerate(NAMED_BAND_ATTRS):
        store = store_named_attribute_node(
            nodes, attr_name, "FLOAT", "POINT",
            parent=frame_points,
            location=(300 + (i % 3) * 330, 300 - (i // 3) * 240),
            label=input_name,
        )
        link(tree, previous, previous_socket, store, "Geometry")
        link(tree, point_in, "Store on Points", store, "Selection")
        link(tree, point_in, input_name, store, "Value")
        previous = store
        previous_socket = "Geometry"

    # Geometry enters the instance frame from the final point-domain writer.
    previous_inst = previous
    previous_inst_socket = previous_socket
    for i, (input_name, attr_name) in enumerate(NAMED_BAND_ATTRS):
        store = store_named_attribute_node(
            nodes, attr_name, "FLOAT", "INSTANCE",
            parent=frame_instances,
            location=(300 + (i % 3) * 330, 300 - (i // 3) * 240),
            label=input_name,
        )
        link(tree, previous_inst, previous_inst_socket, store, "Geometry")
        link(tree, inst_in, "Store on Instances", store, "Selection")
        link(tree, inst_in, input_name, store, "Value")
        previous_inst = store
        previous_inst_socket = "Geometry"

    link(tree, previous_inst, previous_inst_socket, go, "Geometry")
    mark_internal(tree, "Internal writer for named musical-band attributes")
    return tree


# =====================================================================
# 3. DH Audio Analyzer
# =====================================================================

def create_analyzer(response_group, frequency_map_group, store_spectrum_group):
    tree = bpy.data.node_groups.new(GROUP_ANALYZER, "GeometryNodeTree")
    tree["dh_role"] = "spectrum_analyzer"

    nodes = tree.nodes

    template = nodes.new("GeometryNodeSampleSoundFrequencies")
    template.name = "MENU TEMPLATE"
    set_default(template, "FFT Size", "8192")
    set_default(template, "Window Function", "Hann")

    audio_panel = tree.interface.new_panel(
        name="Audio",
        description="Sound, time, channel and FFT controls",
        default_closed=False,
    )
    spectrum_panel = tree.interface.new_panel(
        name="Spectrum",
        description="Frequency distribution and band count",
        default_closed=False,
    )
    response_panel = tree.interface.new_panel(
        name="Response",
        description="Normalize and shape sampled amplitudes",
        default_closed=False,
    )
    carrier_panel = tree.interface.new_panel(
        name="Carrier",
        description="Advanced spacing of the internal carrier points",
        default_closed=True,
    )
    primary_output_panel = tree.interface.new_panel(
        name="Primary Outputs",
        description="The outputs used most often for geometry and modulation",
        default_closed=False,
    )
    metadata_output_panel = tree.interface.new_panel(
        name="Frequency Metadata",
        description="Detailed per-band frequency information",
        default_closed=True,
    )

    add_time_audio_interface(tree, template, fft_default="8192", parent=audio_panel)

    new_socket(
        tree, "Bands", "INPUT", "NodeSocketInt",
        parent=spectrum_panel,
        default=32,
        min_value=1,
        max_value=512,
        description="Number of frequency bands",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Min Frequency", "INPUT", "NodeSocketFloatFrequency",
        parent=spectrum_panel,
        default=30.0,
        min_value=0.001,
        max_value=96000.0,
        description="Lowest analyzed frequency",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Max Frequency", "INPUT", "NodeSocketFloatFrequency",
        parent=spectrum_panel,
        default=16000.0,
        min_value=0.001,
        max_value=96000.0,
        description="Highest analyzed frequency",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Logarithmic", "INPUT", "NodeSocketBool",
        parent=spectrum_panel,
        default=True,
        description="Logarithmic frequency spacing when enabled; linear Hz spacing when disabled",
        structure_type="SINGLE",
    )

    add_response_controls(tree, response_panel)

    new_socket(
        tree, "Spacing", "INPUT", "NodeSocketFloatDistance",
        parent=carrier_panel,
        default=1.0,
        min_value=0.0,
        max_value=10000.0,
        description="X spacing between internal carrier points",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Spectrum", "OUTPUT", "NodeSocketGeometry",
        parent=primary_output_panel,
        description="One carrier vertex per frequency band with standardized named attributes",
    )

    for name, socket_type, desc in [
        ("Amplitude",        "NodeSocketFloat",          "Processed response field"),
        ("Normalized",       "NodeSocketFloat",          "Normalized response before power curve"),
        ("Band Index",       "NodeSocketInt",            "Zero-based band index"),
        ("Band Position",    "NodeSocketFloat",          "Normalized 0-1 position across bands"),
        ("Raw Amplitude",    "NodeSocketFloat",          "Native sampled amplitude"),
        ("Low Frequency",    "NodeSocketFloatFrequency", "Lower frequency bound"),
        ("Center Frequency", "NodeSocketFloatFrequency", "Center frequency"),
        ("High Frequency",   "NodeSocketFloatFrequency", "Upper frequency bound"),
        ("Bandwidth",        "NodeSocketFloatFrequency", "Band width in Hz"),
    ]:
        panel = (
            metadata_output_panel
            if name in {"Raw Amplitude", "Low Frequency", "Center Frequency", "High Frequency", "Bandwidth"}
            else primary_output_panel
        )
        new_socket(
            tree, name, "OUTPUT", socket_type,
            parent=panel,
            description=desc,
            structure_type="FIELD",
        )

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (2050, 120)
    group_out.width = 260
    group_out.is_active_output = True

    frame_carrier = make_frame(nodes, "FRAME_CARRIER", "1  CARRIER", (-1400, 500), 520)
    frame_map = make_frame(nodes, "FRAME_MAP", "2  FREQUENCY MAP", (-760, 500), 560)
    frame_audio = make_frame(nodes, "FRAME_AUDIO", "3  AUDIO SAMPLE", (-80, 500), 640)
    frame_response = make_frame(nodes, "FRAME_RESPONSE", "4  RESPONSE", (680, 500), 520)
    frame_attrs = make_frame(nodes, "FRAME_ATTRS", "5  STANDARD ATTRIBUTES", (1320, 500), 560)

    carrier_in = local_group_input(
        nodes, "Carrier",
        ["Bands", "Spacing"],
        parent=frame_carrier,
        location=(20, 100),
        width=190,
    )

    offset = nodes.new("ShaderNodeCombineXYZ")
    offset.name = "Carrier Spacing"
    offset.label = "Spacing → X"
    offset.parent = frame_carrier
    offset.location = (240, 20)

    mesh_line = nodes.new("GeometryNodeMeshLine")
    mesh_line.name = "Spectrum Carrier"
    mesh_line.label = "One Vertex per Band"
    mesh_line.mode = "OFFSET"
    mesh_line.parent = frame_carrier
    mesh_line.location = (240, 180)
    mesh_line.width = 220

    index = nodes.new("GeometryNodeInputIndex")
    index.name = "Band Index"
    index.label = "Band Index"
    index.parent = frame_carrier
    index.location = (430, 20)

    link(tree, carrier_in, "Bands", mesh_line, "Count")
    link(tree, carrier_in, "Spacing", offset, "X")
    link(tree, offset, "Vector", mesh_line, "Offset")

    map_in = local_group_input(
        nodes, "Spectrum Range",
        ["Bands", "Min Frequency", "Max Frequency", "Logarithmic"],
        parent=frame_map,
        location=(20, 100),
        width=220,
    )

    freq_map = nodes.new("GeometryNodeGroup")
    freq_map.name = "Frequency Map"
    freq_map.label = GROUP_FREQ_MAP
    freq_map.node_tree = frequency_map_group
    freq_map.parent = frame_map
    freq_map.location = (270, 80)
    freq_map.width = 260

    link(tree, index, "Index", freq_map, "Band Index")
    for socket_name in ("Bands", "Min Frequency", "Max Frequency", "Logarithmic"):
        link(tree, map_in, socket_name, freq_map, socket_name)

    audio_in = local_group_input(
        nodes, "Audio Settings",
        ["Sound", "Use Scene Time", "Time", "Time Offset", "Window Function",
         "FFT Size", "All Channels", "Channel"],
        parent=frame_audio,
        location=(20, 100),
        width=230,
    )

    time_node = build_time_source(tree, audio_in, frame_audio, (280, 210))

    sample = nodes.new("GeometryNodeSampleSoundFrequencies")
    sample.name = "Sample Sound Frequencies"
    sample.label = "Per-Band FFT Sample"
    sample.width = 300
    sample.parent = frame_audio
    sample.location = (280, -80)
    set_default(sample, "FFT Size", "8192")
    set_default(sample, "Window Function", "Hann")

    connect_audio_settings(tree, audio_in, sample, time_node)
    link(tree, freq_map, "Low Frequency", sample, "Low")
    link(tree, freq_map, "High Frequency", sample, "High")

    response_in = local_group_input(
        nodes, "Response",
        ["Gain", "Floor", "Ceiling", "Clamp to 1", "Response"],
        parent=frame_response,
        location=(20, 80),
        width=190,
    )

    response = nodes.new("GeometryNodeGroup")
    response.name = "Audio Response"
    response.label = GROUP_RESPONSE
    response.node_tree = response_group
    response.parent = frame_response
    response.location = (240, 80)
    response.width = 280
    hide_node_sockets(response, outputs=("Gained",))

    link(tree, sample, "Amplitude", response, "Value")
    for socket_name in ("Gain", "Floor", "Ceiling", "Clamp to 1", "Response"):
        link(tree, response_in, socket_name, response, socket_name)

    store = nodes.new("GeometryNodeGroup")
    store.name = "Store Spectrum Attributes"
    store.label = "Store dh_audio_*"
    store.node_tree = store_spectrum_group
    store.parent = frame_attrs
    store.location = (20, 80)
    store.width = 500

    link(tree, mesh_line, "Mesh", store, "Geometry")
    link(tree, response, "Value", store, "Amplitude")
    link(tree, response, "Normalized", store, "Normalized")
    link(tree, sample, "Amplitude", store, "Raw Amplitude")
    link(tree, index, "Index", store, "Band Index")
    link(tree, freq_map, "Band Position", store, "Band Position")
    link(tree, freq_map, "Low Frequency", store, "Low Frequency")
    link(tree, freq_map, "Center Frequency", store, "Center Frequency")
    link(tree, freq_map, "High Frequency", store, "High Frequency")
    link(tree, freq_map, "Bandwidth", store, "Bandwidth")

    link(tree, store, "Geometry", group_out, "Spectrum")
    link(tree, response, "Value", group_out, "Amplitude")
    link(tree, response, "Normalized", group_out, "Normalized")
    link(tree, sample, "Amplitude", group_out, "Raw Amplitude")
    link(tree, index, "Index", group_out, "Band Index")
    link(tree, freq_map, "Band Position", group_out, "Band Position")
    link(tree, freq_map, "Low Frequency", group_out, "Low Frequency")
    link(tree, freq_map, "Center Frequency", group_out, "Center Frequency")
    link(tree, freq_map, "High Frequency", group_out, "High Frequency")
    link(tree, freq_map, "Bandwidth", group_out, "Bandwidth")

    nodes.remove(template)

    mark_asset(
        tree,
        "General-purpose Blender 5.2 multi-band audio analyzer with FFT/window controls, "
        "linear/log spacing, response shaping, compact internal architecture, and named attributes."
    )
    return tree


# =====================================================================
# 4. DH Audio Band Query
# =====================================================================

# =====================================================================
# 4. DH Audio Band Query
# =====================================================================

def create_band_query():
    tree = bpy.data.node_groups.new(GROUP_QUERY, "GeometryNodeTree")
    tree["dh_role"] = "band_query"

    input_panel = tree.interface.new_panel(
        name="Query",
        description="Retrieve one indexed band from DH Audio Analyzer carrier geometry",
        default_closed=False,
    )
    primary_output_panel = tree.interface.new_panel(
        name="Band Values",
        description="Common scalar values from the selected band",
        default_closed=False,
    )
    metadata_output_panel = tree.interface.new_panel(
        name="Frequency Metadata",
        description="Detailed frequency bounds for the selected band",
        default_closed=True,
    )

    new_socket(
        tree, "Spectrum", "INPUT", "NodeSocketGeometry",
        parent=input_panel,
        description=f"Carrier geometry from {GROUP_ANALYZER}",
    )
    new_socket(
        tree, "Band", "INPUT", "NodeSocketInt",
        parent=input_panel,
        default=0,
        min_value=0,
        max_value=511,
        description="Zero-based band index. Out-of-range values clamp to the nearest valid band",
        structure_type="SINGLE",
    )

    new_socket(tree, "Band Index", "OUTPUT", "NodeSocketInt", parent=primary_output_panel, structure_type="SINGLE")
    for name, socket_type in [
        ("Amplitude",        "NodeSocketFloat"),
        ("Normalized",       "NodeSocketFloat"),
        ("Raw Amplitude",    "NodeSocketFloat"),
        ("Band Position",    "NodeSocketFloat"),
        ("Low Frequency",    "NodeSocketFloatFrequency"),
        ("Center Frequency", "NodeSocketFloatFrequency"),
        ("High Frequency",   "NodeSocketFloatFrequency"),
        ("Bandwidth",        "NodeSocketFloatFrequency"),
    ]:
        panel = (
            metadata_output_panel
            if name in {"Low Frequency", "Center Frequency", "High Frequency", "Bandwidth"}
            else primary_output_panel
        )
        new_socket(
            tree, name, "OUTPUT", socket_type,
            parent=panel,
            structure_type="SINGLE",
        )

    nodes = tree.nodes
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1350, 100)
    group_out.width = 260
    group_out.is_active_output = True

    frame_query = make_frame(nodes, "FRAME_QUERY", "SAMPLE SELECTED BAND", (-650, 560), 1700)
    query_in = local_group_input(
        nodes, "Query",
        ["Spectrum", "Band"],
        parent=frame_query,
        location=(20, 120),
        width=190,
    )

    specs = [
        ("Band Index",       "dh_audio_band_index",   "INT"),
        ("Amplitude",        "dh_audio_amp",          "FLOAT"),
        ("Normalized",       "dh_audio_norm",         "FLOAT"),
        ("Raw Amplitude",    "dh_audio_raw",          "FLOAT"),
        ("Band Position",    "dh_audio_band_pos",     "FLOAT"),
        ("Low Frequency",    "dh_audio_low_hz",       "FLOAT"),
        ("Center Frequency", "dh_audio_center_hz",    "FLOAT"),
        ("High Frequency",   "dh_audio_high_hz",      "FLOAT"),
        ("Bandwidth",        "dh_audio_bandwidth_hz", "FLOAT"),
    ]

    for i, (output_name, attr_name, dtype) in enumerate(specs):
        col = i % 3
        row = i // 3
        x = 250 + col * 480
        y = 300 - row * 250

        attr = named_attribute_node(
            nodes,
            attr_name,
            dtype,
            parent=frame_query,
            location=(x, y),
            label=output_name,
        )
        attr.width = 190

        sample_index = nodes.new("GeometryNodeSampleIndex")
        sample_index.name = f"Sample {output_name}"
        sample_index.label = output_name
        sample_index.data_type = dtype
        sample_index.domain = "POINT"
        sample_index.width = 230
        sample_index.parent = frame_query
        sample_index.location = (x + 210, y)

        sample_index.clamp = True

        link(tree, query_in, "Spectrum", sample_index, "Geometry")
        link(tree, attr, "Attribute", sample_index, "Value")
        link(tree, query_in, "Band", sample_index, "Index")
        link(tree, sample_index, "Value", group_out, output_name)

    mark_asset(
        tree,
        "Retrieve one spectrum band's amplitude and frequency metadata from DH Audio Analyzer."
    )
    return tree


# =====================================================================
# 5. DH Audio Sample Range
# =====================================================================

# =====================================================================
# 5. DH Audio Sample Range
# =====================================================================

def create_sample_range(response_group):
    tree = bpy.data.node_groups.new(GROUP_RANGE, "GeometryNodeTree")
    tree["dh_role"] = "range_sampler"

    nodes = tree.nodes
    template = nodes.new("GeometryNodeSampleSoundFrequencies")
    template.name = "MENU TEMPLATE"
    set_default(template, "FFT Size", "8192")
    set_default(template, "Window Function", "Hann")

    audio_panel = tree.interface.new_panel(
        name="Audio",
        description="Sound, time, channel and FFT controls",
        default_closed=False,
    )
    range_panel = tree.interface.new_panel(
        name="Frequency Range",
        description="Arbitrary custom frequency range",
        default_closed=False,
    )
    response_panel = tree.interface.new_panel(
        name="Response",
        description="Normalize and shape the sampled amplitude",
        default_closed=False,
    )
    primary_output_panel = tree.interface.new_panel(
        name="Outputs",
        description="Sampled and processed scalar values",
        default_closed=False,
    )
    metadata_output_panel = tree.interface.new_panel(
        name="Range Metadata",
        description="Frequency bounds and bandwidth",
        default_closed=True,
    )

    add_time_audio_interface(tree, template, fft_default="8192", parent=audio_panel)

    new_socket(
        tree, "Low Frequency", "INPUT", "NodeSocketFloatFrequency",
        parent=range_panel,
        default=20.0,
        min_value=0.0,
        max_value=96000.0,
        description="Lower bound of the sampled frequency range",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "High Frequency", "INPUT", "NodeSocketFloatFrequency",
        parent=range_panel,
        default=200.0,
        min_value=0.0,
        max_value=96000.0,
        description="Upper bound. Internally clamped to be at least Low Frequency",
        structure_type="SINGLE",
    )

    add_response_controls(tree, response_panel)

    new_socket(tree, "Amplitude", "OUTPUT", "NodeSocketFloat", parent=primary_output_panel, structure_type="SINGLE")
    new_socket(tree, "Normalized", "OUTPUT", "NodeSocketFloat", parent=primary_output_panel, structure_type="SINGLE")
    new_socket(tree, "Raw Amplitude", "OUTPUT", "NodeSocketFloat", parent=primary_output_panel, structure_type="SINGLE")
    new_socket(tree, "Low Frequency", "OUTPUT", "NodeSocketFloatFrequency", parent=metadata_output_panel, structure_type="SINGLE")
    new_socket(tree, "Center Frequency", "OUTPUT", "NodeSocketFloatFrequency", parent=metadata_output_panel, structure_type="SINGLE")
    new_socket(tree, "High Frequency", "OUTPUT", "NodeSocketFloatFrequency", parent=metadata_output_panel, structure_type="SINGLE")
    new_socket(tree, "Bandwidth", "OUTPUT", "NodeSocketFloatFrequency", parent=metadata_output_panel, structure_type="SINGLE")

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1450, 100)
    group_out.width = 250
    group_out.is_active_output = True

    frame_range = make_frame(nodes, "FRAME_RANGE", "1  SAFE RANGE", (-950, 480), 520)
    frame_audio = make_frame(nodes, "FRAME_AUDIO", "2  AUDIO SAMPLE", (-300, 480), 720)
    frame_response = make_frame(nodes, "FRAME_RESPONSE", "3  RESPONSE", (560, 480), 500)
    frame_meta = make_frame(nodes, "FRAME_META", "4  RANGE METADATA", (560, -200), 620)

    range_in = local_group_input(
        nodes, "Range",
        ["Low Frequency", "High Frequency"],
        parent=frame_range,
        location=(20, 100),
        width=210,
    )

    safe_low = math_node(nodes, "Safe Low", "MAXIMUM", (260, 160), frame_range, "Max(Low, 0)")
    set_default(safe_low, 1, 0.0)
    safe_high = math_node(nodes, "Safe High", "MAXIMUM", (260, -40), frame_range, "Max(High, Low)")
    link(tree, range_in, "Low Frequency", safe_low, 0)
    link(tree, range_in, "High Frequency", safe_high, 0)
    link(tree, safe_low, "Value", safe_high, 1)

    audio_in = local_group_input(
        nodes, "Audio",
        ["Sound", "Use Scene Time", "Time", "Time Offset", "Window Function",
         "FFT Size", "All Channels", "Channel"],
        parent=frame_audio,
        location=(20, 100),
        width=230,
    )

    time_node = build_time_source(tree, audio_in, frame_audio, (280, 200))

    sample = nodes.new("GeometryNodeSampleSoundFrequencies")
    sample.name = "Sample Sound Frequencies"
    sample.label = "Custom Range FFT Sample"
    sample.width = 300
    sample.parent = frame_audio
    sample.location = (330, -100)
    set_default(sample, "FFT Size", "8192")
    set_default(sample, "Window Function", "Hann")

    connect_audio_settings(tree, audio_in, sample, time_node)
    link(tree, safe_low, "Value", sample, "Low")
    link(tree, safe_high, "Value", sample, "High")

    response_in = local_group_input(
        nodes, "Response",
        ["Gain", "Floor", "Ceiling", "Clamp to 1", "Response"],
        parent=frame_response,
        location=(20, 80),
        width=190,
    )

    response = nodes.new("GeometryNodeGroup")
    response.name = "Audio Response"
    response.label = GROUP_RESPONSE
    response.node_tree = response_group
    response.parent = frame_response
    response.location = (230, 80)
    response.width = 240

    link(tree, sample, "Amplitude", response, "Value")
    for socket_name in ("Gain", "Floor", "Ceiling", "Clamp to 1", "Response"):
        link(tree, response_in, socket_name, response, socket_name)

    low_plus_high = math_node(nodes, "Low + High", "ADD", (20, 140), frame_meta, "Low + High")
    center = math_node(nodes, "Center Frequency", "MULTIPLY", (210, 140), frame_meta, "(Low + High) / 2")
    set_default(center, 1, 0.5)
    bandwidth = math_node(nodes, "Bandwidth", "SUBTRACT", (210, -40), frame_meta, "High - Low")

    link(tree, safe_low, "Value", low_plus_high, 0)
    link(tree, safe_high, "Value", low_plus_high, 1)
    link(tree, low_plus_high, "Value", center, 0)
    link(tree, safe_high, "Value", bandwidth, 0)
    link(tree, safe_low, "Value", bandwidth, 1)

    link(tree, response, "Value", group_out, "Amplitude")
    link(tree, response, "Normalized", group_out, "Normalized")
    link(tree, sample, "Amplitude", group_out, "Raw Amplitude")
    link(tree, safe_low, "Value", group_out, "Low Frequency")
    link(tree, center, "Value", group_out, "Center Frequency")
    link(tree, safe_high, "Value", group_out, "High Frequency")
    link(tree, bandwidth, "Value", group_out, "Bandwidth")

    nodes.remove(template)

    mark_asset(
        tree,
        "Sample any custom frequency range directly, independent of spectrum band indexing."
    )
    return tree


# =====================================================================
# 6. DH Audio Bands
# =====================================================================

# =====================================================================
# 6. DH Audio Bands
# =====================================================================

def create_named_bands(named_map_group, named_meta_store_group, named_store_group):
    tree = bpy.data.node_groups.new(GROUP_BANDS, "GeometryNodeTree")
    tree["dh_role"] = "named_frequency_bands"

    nodes = tree.nodes
    template = nodes.new("GeometryNodeSampleSoundFrequencies")
    template.name = "MENU TEMPLATE"
    set_default(template, "FFT Size", "8192")
    set_default(template, "Window Function", "Hann")

    audio_panel = tree.interface.new_panel(
        name="Audio",
        description="Sound, time, channel and FFT controls shared by all named bands",
        default_closed=False,
    )
    total_panel = tree.interface.new_panel(
        name="Total Range",
        description="Independent frequency range for Total Volume",
        default_closed=True,
    )
    limits_panel = tree.interface.new_panel(
        name="Band Limits",
        description="Editable contiguous boundaries for named musical bands",
        default_closed=False,
    )
    outputs_panel = tree.interface.new_panel(
        name="Band Outputs",
        description="Direct scalar amplitude values plus the nine-point named-band carrier",
        default_closed=False,
    )
    bridge_panel = tree.interface.new_panel(
        name="Attribute Bridge",
        description="Optionally stamp all named-band values onto arbitrary geometry",
        default_closed=True,
    )

    add_time_audio_interface(tree, template, fft_default="8192", parent=audio_panel)

    new_socket(
        tree, "Total Low", "INPUT", "NodeSocketFloatFrequency",
        parent=total_panel,
        default=20.0,
        min_value=0.0,
        max_value=96000.0,
        description="Lower bound for Total Volume",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Total High", "INPUT", "NodeSocketFloatFrequency",
        parent=total_panel,
        default=20000.0,
        min_value=0.0,
        max_value=96000.0,
        description="Upper bound for Total Volume",
        structure_type="SINGLE",
    )

    boundaries = [
        ("Low Cut",    20.0,    "Lowest frequency included in Sub"),
        ("Sub",        60.0,    "Upper boundary of Sub"),
        ("Bass",       250.0,   "Upper boundary of Bass"),
        ("Low Mids",   500.0,   "Upper boundary of Low Mid"),
        ("Mid Range",  2000.0,  "Upper boundary of Mid Range"),
        ("High Mids",  4000.0,  "Upper boundary of High Mids"),
        ("Presence",   6000.0,  "Upper boundary of Presence"),
        ("Brilliance", 10000.0, "Upper boundary of Brilliance"),
        ("Air",        20000.0, "Upper boundary of Air"),
    ]

    for name, default, description in boundaries:
        new_socket(
            tree, name, "INPUT", "NodeSocketFloatFrequency",
            parent=limits_panel,
            default=default,
            min_value=0.0,
            max_value=96000.0,
            description=description,
            structure_type="SINGLE",
        )

    new_socket(
        tree, "Band Data", "OUTPUT", "NodeSocketGeometry",
        parent=outputs_panel,
        description=(
            "Nine-point carrier, one point per named range. Carries point-specific "
            "dh_audio_named_* metadata plus every global dh_audio_sub/bass/etc. value."
        ),
    )

    for name, _attr in NAMED_BAND_ATTRS:
        new_socket(
            tree, name, "OUTPUT", "NodeSocketFloat",
            parent=outputs_panel,
            description=f"Raw summed amplitude for {name}",
            structure_type="SINGLE",
        )

    new_socket(
        tree, "Geometry", "INPUT", "NodeSocketGeometry",
        parent=bridge_panel,
        description="Optional geometry that should receive all named-band attributes",
    )
    new_socket(
        tree, "Store on Points", "INPUT", "NodeSocketBool",
        parent=bridge_panel,
        default=True,
        description="Write dh_audio_total/sub/bass/etc. on the point domain",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Store on Instances", "INPUT", "NodeSocketBool",
        parent=bridge_panel,
        default=True,
        description="Write dh_audio_total/sub/bass/etc. on the instance domain",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Geometry", "OUTPUT", "NodeSocketGeometry",
        parent=bridge_panel,
        description="Input Geometry with the named-band attribute set attached",
    )

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (2150, 100)
    group_out.width = 270
    group_out.is_active_output = True

    frame_carrier = make_frame(nodes, "FRAME_CARRIER", "1  NINE-BAND CARRIER", (-1350, 560), 500)
    frame_map = make_frame(nodes, "FRAME_MAP", "2  NAMED BAND MAP", (-730, 560), 660)
    frame_audio = make_frame(nodes, "FRAME_AUDIO", "3  AUDIO SAMPLE", (50, 560), 660)
    frame_query = make_frame(nodes, "FRAME_QUERY", "4  SCALAR BAND OUTPUTS", (830, 560), 1040)
    frame_data = make_frame(nodes, "FRAME_DATA", "5  BAND DATA ATTRIBUTES", (830, -500), 1040)
    frame_bridge = make_frame(nodes, "FRAME_BRIDGE", "6  OPTIONAL ATTRIBUTE BRIDGE", (830, -1050), 1040)

    carrier = nodes.new("GeometryNodeMeshLine")
    carrier.name = "Named Band Carrier"
    carrier.label = "9 Named Bands"
    carrier.mode = "OFFSET"
    carrier.parent = frame_carrier
    carrier.location = (20, 180)
    carrier.width = 220
    set_default(carrier, "Count", 9)
    set_default(carrier, "Offset", (1.0, 0.0, 0.0))

    index = nodes.new("GeometryNodeInputIndex")
    index.name = "Named Band Index"
    index.label = "Named Band Index"
    index.parent = frame_carrier
    index.location = (270, 180)

    limits_in = local_group_input(
        nodes, "Band Limits",
        ["Total Low", "Total High", "Low Cut", "Sub", "Bass", "Low Mids",
         "Mid Range", "High Mids", "Presence", "Brilliance", "Air"],
        parent=frame_map,
        location=(20, 80),
        width=220,
    )

    named_map = nodes.new("GeometryNodeGroup")
    named_map.name = "Named Band Map"
    named_map.label = "Safe Named Band Limits"
    named_map.node_tree = named_map_group
    named_map.parent = frame_map
    named_map.location = (280, 80)
    named_map.width = 340

    link(tree, index, "Index", named_map, "Band Index")
    for socket_name in (
        "Total Low", "Total High", "Low Cut", "Sub", "Bass", "Low Mids",
        "Mid Range", "High Mids", "Presence", "Brilliance", "Air"
    ):
        link(tree, limits_in, socket_name, named_map, socket_name)

    audio_in = local_group_input(
        nodes, "Audio",
        ["Sound", "Use Scene Time", "Time", "Time Offset", "Window Function",
         "FFT Size", "All Channels", "Channel"],
        parent=frame_audio,
        location=(20, 100),
        width=230,
    )

    time_node = build_time_source(tree, audio_in, frame_audio, (280, 200))

    sample = nodes.new("GeometryNodeSampleSoundFrequencies")
    sample.name = "Sample Named Audio Bands"
    sample.label = "One Field-Driven Frequency Sampler"
    sample.width = 300
    sample.parent = frame_audio
    sample.location = (320, -100)
    set_default(sample, "FFT Size", "8192")
    set_default(sample, "Window Function", "Hann")

    connect_audio_settings(tree, audio_in, sample, time_node)
    link(tree, named_map, "Low Frequency", sample, "Low")
    link(tree, named_map, "High Frequency", sample, "High")

    # First store point-specific named-band metadata.
    meta_store = nodes.new("GeometryNodeGroup")
    meta_store.name = "Store Named Band Metadata"
    meta_store.label = "Store dh_audio_named_*"
    meta_store.node_tree = named_meta_store_group
    meta_store.parent = frame_data
    meta_store.location = (20, 150)
    meta_store.width = 430

    link(tree, carrier, "Mesh", meta_store, "Geometry")
    link(tree, sample, "Amplitude", meta_store, "Amplitude")
    link(tree, index, "Index", meta_store, "Band Index")
    link(tree, named_map, "Low Frequency", meta_store, "Low Frequency")
    link(tree, named_map, "Center Frequency", meta_store, "Center Frequency")
    link(tree, named_map, "High Frequency", meta_store, "High Frequency")
    link(tree, named_map, "Bandwidth", meta_store, "Bandwidth")

    amp_attr = named_attribute_node(
        nodes, "dh_audio_named_amp", "FLOAT",
        parent=frame_query, location=(20, 250), label="Named Amplitude"
    )
    amp_attr.width = 210

    queried_values = {}
    for i, (output_name, _attr_name) in enumerate(NAMED_BAND_ATTRS):
        col = i % 3
        row = i // 3
        query = nodes.new("GeometryNodeSampleIndex")
        query.name = f"Query {output_name}"
        query.label = output_name
        query.data_type = "FLOAT"
        query.domain = "POINT"
        query.width = 230
        query.parent = frame_query
        query.location = (270 + col * 260, 300 - row * 230)
        query.clamp = True
        set_default(query, "Index", i)

        link(tree, meta_store, "Geometry", query, "Geometry")
        link(tree, amp_attr, "Attribute", query, "Value")
        link(tree, query, "Value", group_out, output_name)
        queried_values[output_name] = query

    # Attach every scalar named band to the Band Data carrier.
    carrier_store = nodes.new("GeometryNodeGroup")
    carrier_store.name = "Store Named Band Globals"
    carrier_store.label = "Store dh_audio_sub / bass / ..."
    carrier_store.node_tree = named_store_group
    carrier_store.parent = frame_data
    carrier_store.location = (520, 150)
    carrier_store.width = 470

    link(tree, meta_store, "Geometry", carrier_store, "Geometry")
    set_default(carrier_store, "Store on Points", True)
    set_default(carrier_store, "Store on Instances", False)
    for output_name, _attr_name in NAMED_BAND_ATTRS:
        link(tree, queried_values[output_name], "Value", carrier_store, output_name)

    link(tree, carrier_store, "Geometry", group_out, "Band Data")

    # Optional integrated attribute bridge.
    bridge_in = local_group_input(
        nodes, "Attribute Bridge",
        ["Geometry", "Store on Points", "Store on Instances"],
        parent=frame_bridge,
        location=(20, 100),
        width=220,
    )

    bridge_store = nodes.new("GeometryNodeGroup")
    bridge_store.name = "Store Named Bands"
    bridge_store.label = "Attach Named Bands"
    bridge_store.node_tree = named_store_group
    bridge_store.parent = frame_bridge
    bridge_store.location = (280, 80)
    bridge_store.width = 520

    link(tree, bridge_in, "Geometry", bridge_store, "Geometry")
    link(tree, bridge_in, "Store on Points", bridge_store, "Store on Points")
    link(tree, bridge_in, "Store on Instances", bridge_store, "Store on Instances")
    for output_name, _attr_name in NAMED_BAND_ATTRS:
        link(tree, queried_values[output_name], "Value", bridge_store, output_name)

    link(tree, bridge_store, "Geometry", group_out, "Geometry")

    nodes.remove(template)

    mark_asset(
        tree,
        "Named musical frequency bands independent of spectrum band count. "
        "Uses one field-driven audio sampler, a compact indexed band mapper, "
        "direct scalar outputs, Band Data carrier geometry, and an integrated attribute bridge."
    )
    return tree


# =====================================================================
# 7. DH Audio Material Reader
# =====================================================================

# =====================================================================
# 7. DH Audio Material Reader
# =====================================================================

def create_material_reader():
    tree = bpy.data.node_groups.new(GROUP_MATERIAL_READER, "ShaderNodeTree")
    tree["dh_role"] = "material_attribute_reader"

    source_panel = tree.interface.new_panel(
        name="Source",
        description="Choose whether attributes are read from geometry or Geometry Nodes instancing",
        default_closed=False,
    )
    spectrum_panel = tree.interface.new_panel(
        name="Spectrum Attributes",
        description="Common per-band values written by DH Audio Analyzer",
        default_closed=False,
    )
    spectrum_meta_panel = tree.interface.new_panel(
        name="Frequency Metadata",
        description="Detailed spectrum frequency metadata",
        default_closed=True,
    )
    named_panel = tree.interface.new_panel(
        name="Named Bands",
        description="Named values written by DH Audio Bands",
        default_closed=False,
    )

    new_socket(
        tree, "Use Instancer", "INPUT", "NodeSocketBool",
        parent=source_panel,
        default=False,
        description="Off = Geometry/realized attributes; On = Geometry Nodes instancer attributes",
    )

    material_outputs = []
    for output_name, attr_name, dtype in SPECTRUM_ATTRS:
        socket_type = "NodeSocketFloat"
        panel = (
            spectrum_meta_panel
            if output_name in {"Low Frequency", "Center Frequency", "High Frequency", "Bandwidth"}
            else spectrum_panel
        )
        new_socket(
            tree, output_name, "OUTPUT", socket_type,
            parent=panel,
            description=f"Reads '{attr_name}'",
        )
        material_outputs.append((output_name, attr_name))

    for output_name, attr_name in NAMED_BAND_ATTRS:
        new_socket(
            tree, output_name, "OUTPUT", "NodeSocketFloat",
            parent=named_panel,
            description=f"Reads '{attr_name}'",
        )
        material_outputs.append((output_name, attr_name))

    nodes = tree.nodes
    group_in = nodes.new("NodeGroupInput")
    group_in.location = (-1150, 100)
    group_in.width = 220

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1650, 100)
    group_out.width = 250
    group_out.is_active_output = True

    frame_spectrum = make_frame(nodes, "FRAME_SPECTRUM", "SPECTRUM ATTRIBUTE READERS", (-850, 700), 1000)
    frame_named = make_frame(nodes, "FRAME_NAMED", "NAMED BAND ATTRIBUTE READERS", (-850, -700), 1000)

    for i, (output_name, attr_name) in enumerate(material_outputs):
        is_named = i >= len(SPECTRUM_ATTRS)
        local_i = i - len(SPECTRUM_ATTRS) if is_named else i
        frame = frame_named if is_named else frame_spectrum

        col = local_i % 3
        row = local_i // 3
        x = 20 + col * 310
        y = 330 - row * 300

        geo = nodes.new("ShaderNodeAttribute")
        geo.name = f"{output_name} Geometry"
        geo.label = f"{output_name} [Geometry]"
        geo.attribute_type = "GEOMETRY"
        geo.attribute_name = attr_name
        geo.width = 200
        geo.parent = frame
        geo.location = (x, y)

        inst = nodes.new("ShaderNodeAttribute")
        inst.name = f"{output_name} Instancer"
        inst.label = f"{output_name} [Instancer]"
        inst.attribute_type = "INSTANCER"
        inst.attribute_name = attr_name
        inst.width = 200
        inst.parent = frame
        inst.location = (x, y - 100)

        # selected = geo + use_instancer * (inst - geo)
        diff = math_node(
            nodes,
            f"{output_name} Difference",
            "SUBTRACT",
            (x + 210, y - 20),
            frame,
            "Instancer - Geometry",
        )
        weight = math_node(
            nodes,
            f"{output_name} Weight",
            "MULTIPLY",
            (x + 210, y - 110),
            frame,
            "Difference × Source",
        )
        select = math_node(
            nodes,
            f"{output_name} Select",
            "ADD",
            (x + 210, y + 70),
            frame,
            output_name,
        )

        link(tree, inst, "Fac", diff, 0)
        link(tree, geo, "Fac", diff, 1)
        link(tree, diff, "Value", weight, 0)
        link(tree, group_in, "Use Instancer", weight, 1)
        link(tree, geo, "Fac", select, 0)
        link(tree, weight, "Value", select, 1)
        link(tree, select, "Value", group_out, output_name)

    mark_asset(
        tree,
        "Single shader reader for all DH Audio spectrum and named-band attributes. "
        "Use Source = 0 for geometry/realized data and Source = 1 for GN instance attributes."
    )
    return tree




# =====================================================================
# 8. DH Audio Spectrum Points
# =====================================================================

def create_spectrum_points():
    """
    Convert the raw carrier from DH Audio Analyzer into actual audio-height
    points. The output is deliberately compatible with Spectrum Bars'
    Spectrum Points output, so Curve and Fill consumers can accept either.
    """
    tree = bpy.data.node_groups.new(GROUP_POINTS, "GeometryNodeTree")
    tree["dh_role"] = "spectrum_points"

    source_panel = tree.interface.new_panel(
        name="Spectrum",
        description="Map analyzer carrier points into visible audio-height points",
        default_closed=False,
    )
    layout_panel = tree.interface.new_panel(
        name="Layout",
        description="Height and horizontal placement",
        default_closed=False,
    )
    output_panel = tree.interface.new_panel(
        name="Outputs",
        default_closed=False,
    )

    new_socket(
        tree, "Spectrum", "INPUT", "NodeSocketGeometry",
        parent=source_panel,
        description=f"Use the Spectrum output from {GROUP_ANALYZER}",
    )
    new_socket(
        tree, "Height", "INPUT", "NodeSocketFloatDistance",
        parent=layout_panel,
        default=3.0,
        min_value=-10000.0,
        max_value=10000.0,
        description="Height added at amplitude 1.0",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Baseline", "INPUT", "NodeSocketFloatDistance",
        parent=layout_panel,
        default=0.0,
        min_value=-10000.0,
        max_value=10000.0,
        description="Z value corresponding to zero amplitude",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Center Spectrum", "INPUT", "NodeSocketBool",
        parent=layout_panel,
        default=True,
        description="Center the source carrier around X=0 before X Scale is applied",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "X Scale", "INPUT", "NodeSocketFloat",
        parent=layout_panel,
        default=1.0,
        min_value=-10000.0,
        max_value=10000.0,
        description="Horizontal scale around the centered spectrum",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "X Offset", "INPUT", "NodeSocketFloatDistance",
        parent=layout_panel,
        default=0.0,
        min_value=-10000.0,
        max_value=10000.0,
        description="Horizontal offset after centering and scaling",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Spectrum Points", "OUTPUT", "NodeSocketGeometry",
        parent=output_panel,
        description=(
            "Audio-height points carrying the original analyzer attributes. "
            "Compatible with DH Audio Spectrum Curve and DH Audio Spectrum Fill."
        ),
    )

    nodes = tree.nodes
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1250, 100)
    group_out.width = 240
    group_out.is_active_output = True

    frame = make_frame(nodes, "FRAME_POINTS", "SPECTRUM HEIGHT MAPPER", (-900, 520), 1760)

    inp = local_group_input(
        nodes,
        "Spectrum + Layout",
        ["Spectrum", "Height", "Baseline", "Center Spectrum", "X Scale", "X Offset"],
        parent=frame,
        location=(20, 100),
        width=250,
    )

    amp = named_attribute_node(
        nodes, "dh_audio_amp", "FLOAT",
        parent=frame, location=(300, 350), label="Amplitude"
    )

    bounds = nodes.new("GeometryNodeBoundBox")
    bounds.name = "Spectrum Bounds"
    bounds.label = "Spectrum Bounds"
    bounds.parent = frame
    bounds.location = (300, 80)
    link(tree, inp, "Spectrum", bounds, "Geometry")

    sep_min = nodes.new("ShaderNodeSeparateXYZ")
    sep_min.parent = frame
    sep_min.location = (510, 120)
    sep_max = nodes.new("ShaderNodeSeparateXYZ")
    sep_max.parent = frame
    sep_max.location = (510, -20)
    link(tree, bounds, "Min", sep_min, "Vector")
    link(tree, bounds, "Max", sep_max, "Vector")

    center_sum = math_node(
        nodes, "Bounds X Sum", "ADD", (700, 80), frame, "Min X + Max X"
    )
    center_offset = math_node(
        nodes, "Center Offset", "MULTIPLY", (890, 80), frame, "Center × -0.5"
    )
    set_default(center_offset, 1, -0.5)
    link(tree, sep_min, "X", center_sum, 0)
    link(tree, sep_max, "X", center_sum, 1)
    link(tree, center_sum, "Value", center_offset, 0)

    center_switch = switch_float_node(
        nodes, "Center Spectrum", (890, -100), frame, "Keep / Center"
    )
    link(tree, inp, "Center Spectrum", center_switch, "Switch")
    set_default(center_switch, "False", 0.0)
    link(tree, center_offset, "Value", center_switch, "True")

    position = nodes.new("GeometryNodeInputPosition")
    position.name = "Source Position"
    position.parent = frame
    position.location = (300, -260)

    separate = nodes.new("ShaderNodeSeparateXYZ")
    separate.parent = frame
    separate.location = (510, -260)
    link(tree, position, "Position", separate, "Vector")

    centered_x = math_node(
        nodes, "Centered X", "ADD", (700, -230), frame, "X + Center Offset"
    )
    scaled_x = math_node(
        nodes, "Scaled X", "MULTIPLY", (890, -230), frame, "Centered X × Scale"
    )
    final_x = math_node(
        nodes, "Final X", "ADD", (1070, -230), frame, "Scaled X + Offset"
    )

    link(tree, separate, "X", centered_x, 0)
    link(tree, center_switch, "Output", centered_x, 1)
    link(tree, centered_x, "Value", scaled_x, 0)
    link(tree, inp, "X Scale", scaled_x, 1)
    link(tree, scaled_x, "Value", final_x, 0)
    link(tree, inp, "X Offset", final_x, 1)

    amp_height = math_node(
        nodes, "Amplitude Height", "MULTIPLY", (700, 330), frame, "Amplitude × Height"
    )
    final_z = math_node(
        nodes, "Final Z", "ADD", (890, 330), frame, "Baseline + Audio Height"
    )
    link(tree, amp, "Attribute", amp_height, 0)
    link(tree, inp, "Height", amp_height, 1)
    link(tree, inp, "Baseline", final_z, 0)
    link(tree, amp_height, "Value", final_z, 1)

    combine = nodes.new("ShaderNodeCombineXYZ")
    combine.name = "Mapped Position"
    combine.parent = frame
    combine.location = (1070, 100)
    link(tree, final_x, "Value", combine, "X")
    link(tree, separate, "Y", combine, "Y")
    link(tree, final_z, "Value", combine, "Z")

    set_pos = nodes.new("GeometryNodeSetPosition")
    set_pos.name = "Spectrum Height Points"
    set_pos.label = "Spectrum Height Points"
    set_pos.parent = frame
    set_pos.location = (1260, 100)
    set_pos.width = 250
    link(tree, inp, "Spectrum", set_pos, "Geometry")
    link(tree, combine, "Vector", set_pos, "Position")

    link(tree, set_pos, "Geometry", group_out, "Spectrum Points")

    mark_asset(
        tree,
        "Map DH Audio Analyzer carrier geometry into visible audio-height points. "
        "The output is compatible with Spectrum Bars' Spectrum Points, Spectrum Curve, and Spectrum Fill."
    )
    return tree


# =====================================================================
# 8. DH Audio Spectrum Instances
# =====================================================================

def create_spectrum_instances():
    tree = bpy.data.node_groups.new(GROUP_INSTANCES, "GeometryNodeTree")
    tree["dh_role"] = "spectrum_instances"

    source_panel = tree.interface.new_panel(
        name="Source",
        description="Spectrum carrier and geometry to instance",
        default_closed=False,
    )
    transform_panel = tree.interface.new_panel(
        name="Audio Transform",
        description="Use amplitude to add scale and position changes",
        default_closed=False,
    )
    advanced_panel = tree.interface.new_panel(
        name="Advanced",
        description="Layout and realization controls",
        default_closed=True,
    )
    outputs_panel = tree.interface.new_panel(
        name="Outputs",
        default_closed=False,
    )

    new_socket(
        tree, "Spectrum", "INPUT", "NodeSocketGeometry",
        parent=source_panel,
        description=f"Use the Spectrum output from {GROUP_ANALYZER}",
    )
    new_socket(
        tree, "Instance", "INPUT", "NodeSocketGeometry",
        parent=source_panel,
        description="Any mesh, curve, or other geometry to instance once per spectrum band",
    )
    new_socket(
        tree, "Selection", "INPUT", "NodeSocketBool",
        parent=source_panel,
        default=True,
        description="Field selecting which spectrum points receive instances",
        structure_type="FIELD",
    )
    new_socket(
        tree, "Material", "INPUT", "NodeSocketMaterial",
        parent=source_panel,
        description="Optional material applied to the instance geometry",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Base Scale", "INPUT", "NodeSocketVector",
        parent=transform_panel,
        default=(1.0, 1.0, 1.0),
        description="Scale before audio is added",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Amplitude Scale", "INPUT", "NodeSocketVector",
        parent=transform_panel,
        default=(0.0, 0.0, 1.0),
        description="Additional scale at amplitude 1.0",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Base Offset", "INPUT", "NodeSocketVector",
        parent=transform_panel,
        default=(0.0, 0.0, 0.0),
        description="Constant point offset",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Amplitude Offset", "INPUT", "NodeSocketVector",
        parent=transform_panel,
        default=(0.0, 0.0, 0.0),
        description="Additional point offset at amplitude 1.0",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Center Spectrum", "INPUT", "NodeSocketBool",
        parent=advanced_panel,
        default=True,
        description="Center the spectrum horizontally around X=0",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Realize Instances", "INPUT", "NodeSocketBool",
        parent=advanced_panel,
        default=False,
        description="Realize the output when downstream mesh operations require it",
        structure_type="SINGLE",
    )

    new_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry", parent=outputs_panel)
    new_socket(tree, "Points", "OUTPUT", "NodeSocketGeometry", parent=outputs_panel)

    nodes = tree.nodes
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1500, 100)
    group_out.is_active_output = True

    frame_layout = make_frame(nodes, "FRAME_LAYOUT", "1  AUDIO POINT TRANSFORM", (-950, 520), 980)
    frame_instance = make_frame(nodes, "FRAME_INSTANCE", "2  INSTANCE GEOMETRY", (160, 520), 720)

    inp = local_group_input(
        nodes, "Spectrum Instances",
        ["Spectrum", "Instance", "Selection", "Material", "Base Scale", "Amplitude Scale",
         "Base Offset", "Amplitude Offset", "Center Spectrum", "Realize Instances"],
        parent=frame_layout, location=(20, 100), width=240
    )

    amp = named_attribute_node(
        nodes, "dh_audio_amp", "FLOAT",
        parent=frame_layout, location=(290, 300), label="Amplitude"
    )

    bounds = nodes.new("GeometryNodeBoundBox")
    bounds.name = "Spectrum Bounds"
    bounds.label = "Spectrum Bounds"
    bounds.parent = frame_layout
    bounds.location = (290, 80)
    link(tree, inp, "Spectrum", bounds, "Geometry")

    sep_min = nodes.new("ShaderNodeSeparateXYZ")
    sep_min.parent = frame_layout
    sep_min.location = (500, 150)
    sep_max = nodes.new("ShaderNodeSeparateXYZ")
    sep_max.parent = frame_layout
    sep_max.location = (500, 20)
    link(tree, bounds, "Min", sep_min, "Vector")
    link(tree, bounds, "Max", sep_max, "Vector")

    center_sum = math_node(nodes, "Min X + Max X", "ADD", (680, 100), frame_layout, "Min X + Max X")
    center_neg_half = math_node(nodes, "Center Offset", "MULTIPLY", (850, 100), frame_layout, "Center × -0.5")
    set_default(center_neg_half, 1, -0.5)
    link(tree, sep_min, "X", center_sum, 0)
    link(tree, sep_max, "X", center_sum, 1)
    link(tree, center_sum, "Value", center_neg_half, 0)

    center_switch = switch_float_node(nodes, "Center Spectrum", (850, -70), frame_layout, "Keep / Center")
    link(tree, inp, "Center Spectrum", center_switch, "Switch")
    set_default(center_switch, "False", 0.0)
    link(tree, center_neg_half, "Value", center_switch, "True")

    center_vec = nodes.new("ShaderNodeCombineXYZ")
    center_vec.parent = frame_layout
    center_vec.location = (1020, -70)
    link(tree, center_switch, "Output", center_vec, "X")

    amp_offset = vector_math_node(nodes, "Amplitude Offset", "SCALE", (500, 330), frame_layout, "Offset × Amplitude")
    link(tree, inp, "Amplitude Offset", amp_offset, 0)
    link(tree, amp, "Attribute", amp_offset, "Scale")

    offset_add = vector_math_node(nodes, "Base + Audio Offset", "ADD", (700, 330), frame_layout, "Base + Audio Offset")
    link(tree, inp, "Base Offset", offset_add, 0)
    link(tree, amp_offset, "Vector", offset_add, 1)

    final_offset = vector_math_node(nodes, "Add Center Offset", "ADD", (1040, 280), frame_layout, "Audio Offset + Center")
    link(tree, offset_add, "Vector", final_offset, 0)
    link(tree, center_vec, "Vector", final_offset, 1)

    set_pos = nodes.new("GeometryNodeSetPosition")
    set_pos.name = "Position Spectrum Points"
    set_pos.label = "Position Spectrum Points"
    set_pos.parent = frame_layout
    set_pos.location = (1190, 80)
    link(tree, inp, "Spectrum", set_pos, "Geometry")
    link(tree, final_offset, "Vector", set_pos, "Offset")

    amp_scale = vector_math_node(nodes, "Amplitude Scale", "SCALE", (20, 270), frame_instance, "Scale × Amplitude")
    link(tree, inp, "Amplitude Scale", amp_scale, 0)
    link(tree, amp, "Attribute", amp_scale, "Scale")

    scale_add = vector_math_node(nodes, "Final Scale", "ADD", (220, 270), frame_instance, "Base + Audio Scale")
    link(tree, inp, "Base Scale", scale_add, 0)
    link(tree, amp_scale, "Vector", scale_add, 1)

    set_mat = nodes.new("GeometryNodeSetMaterial")
    set_mat.name = "Instance Material"
    set_mat.label = "Apply Material"
    set_mat.parent = frame_instance
    set_mat.location = (20, 20)
    link(tree, inp, "Instance", set_mat, "Geometry")
    link(tree, inp, "Material", set_mat, "Material")

    instance = nodes.new("GeometryNodeInstanceOnPoints")
    instance.name = "Instance on Spectrum"
    instance.label = "Instance on Spectrum"
    instance.parent = frame_instance
    instance.location = (430, 120)
    instance.width = 240
    link(tree, set_pos, "Geometry", instance, "Points")
    link(tree, inp, "Selection", instance, "Selection")
    link(tree, set_mat, "Geometry", instance, "Instance")
    link(tree, scale_add, "Vector", instance, "Scale")

    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.name = "Realize Instances"
    realize.parent = frame_instance
    realize.location = (690, 120)
    link(tree, instance, "Instances", realize, "Geometry")

    realize_switch = switch_geometry_node(nodes, "Realize?", (900, 120), frame_instance, "Instances / Realized")
    link(tree, inp, "Realize Instances", realize_switch, "Switch")
    link(tree, instance, "Instances", realize_switch, "False")
    link(tree, realize, "Geometry", realize_switch, "True")

    link(tree, realize_switch, "Output", group_out, "Geometry")
    link(tree, set_pos, "Geometry", group_out, "Points")

    mark_asset(
        tree,
        "Generic spectrum consumer: instance any geometry on analyzer bands and drive scale/position with amplitude."
    )
    return tree


# =====================================================================
# 9. DH Audio Spectrum Curve
# =====================================================================

def create_spectrum_curve():
    """
    Convert already-positioned spectrum points into a reusable curve.
    Compatible sources:
      - DH Audio Spectrum Points -> Spectrum Points
      - DH Audio Spectrum Bars   -> Spectrum Points
      - any connected mesh line carrying ordered spectrum vertices
    """
    tree = bpy.data.node_groups.new(GROUP_CURVE, "GeometryNodeTree")
    tree["dh_role"] = "spectrum_curve"
    nodes = tree.nodes

    style_switch = menu_switch_geometry(
        nodes,
        "Curve Style",
        ["Raw", "Smooth", "Smooth + Resample"],
        location=(0, 0),
        label="Curve Style",
    )

    source_panel = tree.interface.new_panel(
        name="Source",
        description="Already-positioned spectrum points",
        default_closed=False,
    )
    curve_panel = tree.interface.new_panel(
        name="Curve",
        description="Smoothing and resampling",
        default_closed=False,
    )
    tube_panel = tree.interface.new_panel(
        name="Tube",
        description="Optional mesh generated around the curve",
        default_closed=True,
    )
    outputs_panel = tree.interface.new_panel(name="Outputs", default_closed=False)

    new_socket(
        tree, "Spectrum Points", "INPUT", "NodeSocketGeometry",
        parent=source_panel,
        description=(
            f"Use {GROUP_POINTS} -> Spectrum Points or "
            f"{GROUP_BARS} -> Spectrum Points"
        ),
    )

    new_menu_socket_from(
        tree, "Curve Style", style_switch, "Menu",
        parent=curve_panel,
        default="Smooth",
        description="Raw polyline, Catmull-Rom smoothing, or smooth resampled output",
    )
    new_socket(
        tree, "Resample Count", "INPUT", "NodeSocketInt",
        parent=curve_panel,
        default=128,
        min_value=2,
        max_value=4096,
        description="Point count used by Smooth + Resample",
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Tube Radius", "INPUT", "NodeSocketFloatDistance",
        parent=tube_panel,
        default=0.02,
        min_value=0.0,
        max_value=1000.0,
        description="Base tube profile radius",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Audio Radius", "INPUT", "NodeSocketFloat",
        parent=tube_panel,
        default=0.0,
        min_value=-10.0,
        max_value=100.0,
        description=(
            "Audio-reactive multiplier for the Tube output only. "
            "0 = constant thickness; 1 = up to 2x thickness at amplitude 1."
        ),
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Tube Resolution", "INPUT", "NodeSocketInt",
        parent=tube_panel,
        default=8,
        min_value=3,
        max_value=256,
        description="Vertices around the tube profile",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Material", "INPUT", "NodeSocketMaterial",
        parent=tube_panel,
        structure_type="SINGLE",
    )

    new_socket(tree, "Curve", "OUTPUT", "NodeSocketGeometry", parent=outputs_panel)
    new_socket(tree, "Tube", "OUTPUT", "NodeSocketGeometry", parent=outputs_panel)

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1450, 100)
    group_out.width = 240
    group_out.is_active_output = True

    frame_curve = make_frame(nodes, "FRAME_CURVE", "1  POINTS TO CURVE", (-900, 520), 1220)
    frame_tube = make_frame(nodes, "FRAME_TUBE", "2  OPTIONAL TUBE", (470, 520), 850)

    curve_in = local_group_input(
        nodes, "Spectrum Curve",
        ["Spectrum Points", "Curve Style", "Resample Count"],
        parent=frame_curve,
        location=(20, 120),
        width=235,
    )

    mesh_to_curve = nodes.new("GeometryNodeMeshToCurve")
    mesh_to_curve.name = "Spectrum Mesh to Curve"
    mesh_to_curve.label = "Spectrum Mesh to Curve"
    mesh_to_curve.parent = frame_curve
    mesh_to_curve.location = (290, 220)
    mesh_to_curve.width = 220
    link(tree, curve_in, "Spectrum Points", mesh_to_curve, "Mesh")

    smooth = nodes.new("GeometryNodeCurveSplineType")
    smooth.name = "Smooth Catmull-Rom"
    smooth.label = "Catmull-Rom"
    smooth.spline_type = "CATMULL_ROM"
    smooth.parent = frame_curve
    smooth.location = (530, 220)
    smooth.width = 220
    link(tree, mesh_to_curve, "Curve", smooth, "Curve")

    resample = nodes.new("GeometryNodeResampleCurve")
    resample.name = "Resample Smooth Curve"
    resample.label = "Uniform Resample"
    # Blender 5.2 moved the Resample Curve mode from an RNA property
    # to a native menu input socket ("Mode").
    set_default(resample, "Mode", "Count")
    resample.parent = frame_curve
    resample.location = (760, 220)
    resample.width = 220
    link(tree, smooth, "Curve", resample, "Curve")
    link(tree, curve_in, "Resample Count", resample, "Count")

    style_switch.active_index = 1  # Smooth
    style_switch.parent = frame_curve
    style_switch.location = (1000, 190)
    style_switch.width = 300
    link(tree, curve_in, "Curve Style", style_switch, "Menu")
    link(tree, mesh_to_curve, "Curve", style_switch, "Raw")
    link(tree, smooth, "Curve", style_switch, "Smooth")
    link(tree, resample, "Curve", style_switch, "Smooth + Resample")

    tube_in = local_group_input(
        nodes, "Tube",
        ["Tube Radius", "Audio Radius", "Tube Resolution", "Material"],
        parent=frame_tube,
        location=(20, 100),
        width=225,
    )

    amp = named_attribute_node(
        nodes, "dh_audio_amp", "FLOAT",
        parent=frame_tube, location=(280, 320), label="Amplitude"
    )

    amp_radius = math_node(
        nodes, "Audio Radius Amount", "MULTIPLY",
        (490, 320), frame_tube, "Amplitude × Audio Radius"
    )
    radius_factor = math_node(
        nodes, "Curve Radius Factor", "ADD",
        (680, 320), frame_tube, "1 + Audio Radius"
    )
    set_default(radius_factor, 0, 1.0)
    link(tree, amp, "Attribute", amp_radius, 0)
    link(tree, tube_in, "Audio Radius", amp_radius, 1)
    link(tree, amp_radius, "Value", radius_factor, 1)

    # Blender 5.2 Curve to Mesh has an explicit Scale field. Drive that
    # directly so per-point audio thickness is guaranteed to affect the Tube.
    circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    circle.name = "Tube Profile"
    circle.label = "Tube Profile"
    circle.parent = frame_tube
    circle.location = (520, 80)
    link(tree, tube_in, "Tube Resolution", circle, "Resolution")
    link(tree, tube_in, "Tube Radius", circle, "Radius")

    curve_mesh = nodes.new("GeometryNodeCurveToMesh")
    curve_mesh.name = "Curve to Tube"
    curve_mesh.label = "Curve to Tube"
    curve_mesh.parent = frame_tube
    curve_mesh.location = (720, 80)
    curve_mesh.width = 220
    link(tree, style_switch, "Output", curve_mesh, "Curve")
    link(tree, radius_factor, "Value", curve_mesh, "Scale")
    link(tree, circle, "Curve", curve_mesh, "Profile Curve")
    if get_socket(curve_mesh.inputs, "Fill Caps") is not None:
        set_default(curve_mesh, "Fill Caps", True)

    set_mat = nodes.new("GeometryNodeSetMaterial")
    set_mat.name = "Tube Material"
    set_mat.label = "Apply Material"
    set_mat.parent = frame_tube
    set_mat.location = (720, -130)
    link(tree, curve_mesh, "Mesh", set_mat, "Geometry")
    link(tree, tube_in, "Material", set_mat, "Material")

    link(tree, style_switch, "Output", group_out, "Curve")
    link(tree, set_mat, "Geometry", group_out, "Tube")

    mark_asset(
        tree,
        "Convert positioned spectrum points into a raw, Catmull-Rom smooth, or resampled curve, "
        "with optional audio-reactive tube radius."
    )
    return tree


# =====================================================================
# 10. DH Audio Spectrum Fill
# =====================================================================

def create_spectrum_fill():
    """
    Build a quad strip between positioned spectrum points and a flat baseline.
    Compatible sources:
      - DH Audio Spectrum Points -> Spectrum Points
      - DH Audio Spectrum Bars   -> Spectrum Points
    """
    tree = bpy.data.node_groups.new(GROUP_FILL, "GeometryNodeTree")
    tree["dh_role"] = "spectrum_fill"

    input_panel = tree.interface.new_panel(
        name="Spectrum Fill",
        description="Fill below already-positioned spectrum points",
        default_closed=False,
    )
    outputs_panel = tree.interface.new_panel(name="Outputs", default_closed=False)

    new_socket(
        tree, "Spectrum Points", "INPUT", "NodeSocketGeometry",
        parent=input_panel,
        description=(
            f"Use {GROUP_POINTS} -> Spectrum Points or "
            f"{GROUP_BARS} -> Spectrum Points"
        ),
    )
    new_socket(
        tree, "Baseline", "INPUT", "NodeSocketFloatDistance",
        parent=input_panel,
        default=0.0,
        min_value=-10000.0,
        max_value=10000.0,
        description="Flat Z value used for the bottom edge",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Material", "INPUT", "NodeSocketMaterial",
        parent=input_panel,
        structure_type="SINGLE",
    )

    new_socket(
        tree, "Mesh", "OUTPUT", "NodeSocketGeometry",
        parent=outputs_panel,
        description="Filled quad strip carrying common spectrum attributes",
    )

    nodes = tree.nodes
    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (1500, 100)
    group_out.width = 240
    group_out.is_active_output = True

    frame_source = make_frame(nodes, "FRAME_SOURCE", "1  SOURCE + COUNT", (-900, 520), 650)
    frame_strip = make_frame(nodes, "FRAME_STRIP", "2  BUILD QUAD STRIP", (-100, 520), 1240)
    frame_attrs = make_frame(nodes, "FRAME_ATTRS", "3  ATTRIBUTES + MATERIAL", (1280, 520), 620)

    inp = local_group_input(
        nodes, "Spectrum Fill",
        ["Spectrum Points", "Baseline", "Material"],
        parent=frame_source,
        location=(20, 100),
        width=235,
    )

    domain = nodes.new("GeometryNodeAttributeDomainSize")
    domain.name = "Spectrum Point Count"
    domain.label = "Spectrum Point Count"
    domain.component = "MESH"
    domain.parent = frame_source
    domain.location = (300, 230)
    domain.width = 220
    link(tree, inp, "Spectrum Points", domain, "Geometry")

    grid_count = integer_math_node(
        nodes, "Grid X Count", "MAXIMUM",
        (480, 20), frame_source, "Max(Count, 2)"
    )
    set_default(grid_count, 1, 2)
    link(tree, domain, "Point Count", grid_count, 0)

    strip_in = local_group_input(
        nodes, "Fill Source",
        ["Spectrum Points", "Baseline"],
        parent=frame_strip,
        location=(20, 80),
        width=215,
    )

    grid = nodes.new("GeometryNodeMeshGrid")
    grid.name = "Fill Grid"
    grid.label = "2-Row Quad Strip"
    grid.parent = frame_strip
    grid.location = (260, 280)
    grid.width = 230
    set_default(grid, "Size X", 1.0)
    set_default(grid, "Size Y", 1.0)
    set_default(grid, "Vertices Y", 2)
    link(tree, grid_count, "Value", grid, "Vertices X")

    grid_index = nodes.new("GeometryNodeInputIndex")
    grid_index.name = "Grid Index"
    grid_index.parent = frame_strip
    grid_index.location = (260, 40)

    band_index = integer_math_node(
        nodes, "Source Band Index", "DIVIDE_FLOOR",
        (470, 40), frame_strip, "Grid Index // 2"
    )
    set_default(band_index, 1, 2)
    link(tree, grid_index, "Index", band_index, 0)

    row_index = integer_math_node(
        nodes, "Grid Row Index", "MODULO",
        (470, -70), frame_strip, "Grid Index % 2"
    )
    set_default(row_index, 1, 2)
    link(tree, grid_index, "Index", row_index, 0)

    # Sample original point positions by band index. This lets Fill consume
    # either Spectrum Points generated by this toolkit or Bar top points.
    source_position = nodes.new("GeometryNodeInputPosition")
    source_position.name = "Source Position"
    source_position.parent = frame_strip
    source_position.location = (260, -170)

    sample_position = nodes.new("GeometryNodeSampleIndex")
    sample_position.name = "Sample Spectrum Position"
    sample_position.label = "Sample Spectrum Position"
    sample_position.data_type = "FLOAT_VECTOR"
    sample_position.domain = "POINT"
    sample_position.parent = frame_strip
    sample_position.location = (470, -170)
    sample_position.width = 250
    sample_position.clamp = True
    link(tree, strip_in, "Spectrum Points", sample_position, "Geometry")
    link(tree, source_position, "Position", sample_position, "Value")
    link(tree, band_index, "Value", sample_position, "Index")

    sampled_xyz = nodes.new("ShaderNodeSeparateXYZ")
    sampled_xyz.name = "Sampled XYZ"
    sampled_xyz.parent = frame_strip
    sampled_xyz.location = (740, -170)
    link(tree, sample_position, "Value", sampled_xyz, "Vector")

    # Mesh Grid indices advance in Y first. With two rows, even indices are
    # the lower row and odd indices are the upper row. Using index rather than
    # generated coordinates keeps every top spectrum point in the silhouette.
    top_row = nodes.new("FunctionNodeCompare")
    top_row.name = "Top Row"
    top_row.label = "Row Index = 1"
    top_row.data_type = "INT"
    top_row.operation = "EQUAL"
    top_row.parent = frame_strip
    top_row.location = (930, 270)
    set_default(top_row, "B", 1)
    link(tree, row_index, "Value", top_row, "A")

    z_switch = switch_float_node(
        nodes, "Baseline / Spectrum Z",
        (930, 60), frame_strip, "Bottom / Top"
    )
    link(tree, top_row, "Result", z_switch, "Switch")
    link(tree, strip_in, "Baseline", z_switch, "False")
    link(tree, sampled_xyz, "Z", z_switch, "True")

    final_position = nodes.new("ShaderNodeCombineXYZ")
    final_position.name = "Fill Position"
    final_position.parent = frame_strip
    final_position.location = (1110, 60)
    link(tree, sampled_xyz, "X", final_position, "X")
    link(tree, sampled_xyz, "Y", final_position, "Y")
    link(tree, z_switch, "Output", final_position, "Z")

    set_pos = nodes.new("GeometryNodeSetPosition")
    set_pos.name = "Shape Fill"
    set_pos.label = "Shape Filled Spectrum"
    set_pos.parent = frame_strip
    set_pos.location = (1290, 180)
    set_pos.width = 230
    link(tree, grid, "Mesh", set_pos, "Geometry")
    link(tree, final_position, "Vector", set_pos, "Position")

    # Sample common per-band attributes onto the strip so materials can use
    # the same reader as bars/instances.
    amp_attr = named_attribute_node(
        nodes, "dh_audio_amp", "FLOAT",
        parent=frame_attrs, location=(20, 330), label="Amplitude"
    )
    pos_attr = named_attribute_node(
        nodes, "dh_audio_band_pos", "FLOAT",
        parent=frame_attrs, location=(20, 120), label="Band Position"
    )
    idx_attr = named_attribute_node(
        nodes, "dh_audio_band_index", "INT",
        parent=frame_attrs, location=(20, -90), label="Band Index"
    )

    def sample_source_attr(name, data_type, attr_node, location):
        node = nodes.new("GeometryNodeSampleIndex")
        node.name = f"Sample {name}"
        node.label = f"Sample {name}"
        node.data_type = data_type
        node.domain = "POINT"
        node.parent = frame_attrs
        node.location = location
        node.width = 230
        node.clamp = True
        link(tree, inp, "Spectrum Points", node, "Geometry")
        link(tree, attr_node, "Attribute", node, "Value")
        link(tree, band_index, "Value", node, "Index")
        return node

    sample_amp = sample_source_attr("Amplitude", "FLOAT", amp_attr, (230, 330))
    sample_band_pos = sample_source_attr("Band Position", "FLOAT", pos_attr, (230, 120))
    sample_band_idx = sample_source_attr("Band Index", "INT", idx_attr, (230, -90))

    store_amp = store_named_attribute_node(
        nodes, "dh_audio_amp", "FLOAT", "POINT",
        parent=frame_attrs, location=(480, 330), label="Amplitude"
    )
    store_pos = store_named_attribute_node(
        nodes, "dh_audio_band_pos", "FLOAT", "POINT",
        parent=frame_attrs, location=(480, 120), label="Band Position"
    )
    store_idx = store_named_attribute_node(
        nodes, "dh_audio_band_index", "INT", "POINT",
        parent=frame_attrs, location=(480, -90), label="Band Index"
    )

    link(tree, set_pos, "Geometry", store_amp, "Geometry")
    link(tree, sample_amp, "Value", store_amp, "Value")
    link(tree, store_amp, "Geometry", store_pos, "Geometry")
    link(tree, sample_band_pos, "Value", store_pos, "Value")
    link(tree, store_pos, "Geometry", store_idx, "Geometry")
    link(tree, sample_band_idx, "Value", store_idx, "Value")

    set_mat = nodes.new("GeometryNodeSetMaterial")
    set_mat.name = "Fill Material"
    set_mat.label = "Apply Material"
    set_mat.parent = frame_attrs
    set_mat.location = (480, -300)
    link(tree, store_idx, "Geometry", set_mat, "Geometry")
    link(tree, inp, "Material", set_mat, "Material")

    link(tree, set_mat, "Geometry", group_out, "Mesh")

    mark_asset(
        tree,
        "Build a filled quad strip below positioned spectrum points. "
        "Accepts DH Audio Spectrum Points or Spectrum Bars' Spectrum Points output."
    )
    return tree


# =====================================================================
# 11. DH Audio Spectrum Bars
# =====================================================================

def create_spectrum_bars(analyzer_group):
    tree = bpy.data.node_groups.new(GROUP_BARS, "GeometryNodeTree")
    tree["dh_role"] = "spectrum_bars"
    nodes = tree.nodes

    template = nodes.new("GeometryNodeSampleSoundFrequencies")
    template.name = "MENU TEMPLATE"
    set_default(template, "FFT Size", "8192")
    set_default(template, "Window Function", "Hann")

    profile_switch = menu_switch_geometry(
        nodes,
        "Bar Profile",
        ["Box", "Round", "Cone", "Icosphere", "Custom Profile", "Custom Geometry"],
        location=(0, 0),
        label="Bar Profile",
    )

    audio_panel = tree.interface.new_panel(
        name="Audio",
        description="Sound, time, channel and FFT controls",
        default_closed=False,
    )
    spectrum_panel = tree.interface.new_panel(
        name="Spectrum",
        description="Frequency distribution",
        default_closed=False,
    )
    response_panel = tree.interface.new_panel(
        name="Response",
        description="Audio normalization and response",
        default_closed=False,
    )
    bars_panel = tree.interface.new_panel(
        name="Bars",
        description="Bar geometry and layout",
        default_closed=False,
    )
    profile_panel = tree.interface.new_panel(
        name="Profile",
        description="Built-in or custom bar shape",
        default_closed=False,
    )
    primary_outputs_panel = tree.interface.new_panel(
        name="Outputs",
        description="Geometry and the per-band fields used most often",
        default_closed=False,
    )
    metadata_outputs_panel = tree.interface.new_panel(
        name="Advanced Outputs",
        description="Raw analyzer carrier and detailed frequency metadata",
        default_closed=True,
    )

    add_time_audio_interface(tree, template, fft_default="8192", parent=audio_panel)

    new_socket(tree, "Bands", "INPUT", "NodeSocketInt", parent=spectrum_panel, default=32, min_value=1, max_value=512, structure_type="SINGLE")
    new_socket(tree, "Min Frequency", "INPUT", "NodeSocketFloatFrequency", parent=spectrum_panel, default=30.0, min_value=0.001, max_value=96000.0, structure_type="SINGLE")
    new_socket(tree, "Max Frequency", "INPUT", "NodeSocketFloatFrequency", parent=spectrum_panel, default=16000.0, min_value=0.001, max_value=96000.0, structure_type="SINGLE")
    new_socket(tree, "Logarithmic", "INPUT", "NodeSocketBool", parent=spectrum_panel, default=True, structure_type="SINGLE")

    add_response_controls(tree, response_panel)

    new_socket(tree, "Bar Width", "INPUT", "NodeSocketFloatDistance", parent=bars_panel, default=0.20, min_value=0.001, max_value=10000.0, structure_type="SINGLE")
    new_socket(tree, "Bar Depth", "INPUT", "NodeSocketFloatDistance", parent=bars_panel, default=0.20, min_value=0.001, max_value=10000.0, structure_type="SINGLE")
    new_socket(tree, "Gap", "INPUT", "NodeSocketFloatDistance", parent=bars_panel, default=0.05, min_value=0.0, max_value=10000.0, structure_type="SINGLE")
    new_socket(tree, "Min Height", "INPUT", "NodeSocketFloatDistance", parent=bars_panel, default=0.02, min_value=0.0, max_value=10000.0, structure_type="SINGLE")
    new_socket(tree, "Max Height", "INPUT", "NodeSocketFloatDistance", parent=bars_panel, default=3.0, min_value=0.001, max_value=10000.0, structure_type="SINGLE")
    new_socket(tree, "Baseline", "INPUT", "NodeSocketFloatDistance", parent=bars_panel, default=0.0, min_value=-10000.0, max_value=10000.0, structure_type="SINGLE")
    new_socket(tree, "Center Spectrum", "INPUT", "NodeSocketBool", parent=bars_panel, default=True, structure_type="SINGLE")

    new_menu_socket_from(
        tree, "Bar Profile", profile_switch, "Menu",
        parent=profile_panel,
        default="Box",
        description="Choose a built-in shape or provide a custom profile/geometry",
    )
    new_socket(
        tree, "Profile Resolution", "INPUT", "NodeSocketInt",
        parent=profile_panel,
        default=12,
        min_value=3,
        max_value=256,
        description="Round/Cone radial resolution",
        structure_type="SINGLE",
    )
    new_socket(
        tree, "Custom Profile", "INPUT", "NodeSocketGeometry",
        parent=profile_panel,
        description=(
            "2D curve cross-section used by Custom Profile. "
            "Center it around the origin and size it roughly 1 × 1."
        ),
    )
    new_socket(
        tree, "Custom Geometry", "INPUT", "NodeSocketGeometry",
        parent=profile_panel,
        description=(
            "Full custom bar geometry. For predictable baseline behavior, "
            "make it approximately 1 unit tall and centered on Z=0."
        ),
    )
    new_socket(
        tree, "Material", "INPUT", "NodeSocketMaterial",
        parent=profile_panel,
        description="Material applied to every bar",
        structure_type="SINGLE",
    )

    new_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry", parent=primary_outputs_panel, description="Audio-reactive bar instances")
    new_socket(tree, "Spectrum Points", "OUTPUT", "NodeSocketGeometry", parent=primary_outputs_panel, description="Points positioned at the TOP of each bar")
    for name, socket_type in [
        ("Amplitude", "NodeSocketFloat"),
        ("Normalized", "NodeSocketFloat"),
        ("Band Index", "NodeSocketInt"),
        ("Band Position", "NodeSocketFloat"),
    ]:
        new_socket(tree, name, "OUTPUT", socket_type, parent=primary_outputs_panel, structure_type="FIELD")

    new_socket(tree, "Raw Spectrum", "OUTPUT", "NodeSocketGeometry", parent=metadata_outputs_panel, description="Unpositioned analyzer carrier geometry")
    for name, socket_type in [
        ("Raw Amplitude", "NodeSocketFloat"),
        ("Low Frequency", "NodeSocketFloatFrequency"),
        ("Center Frequency", "NodeSocketFloatFrequency"),
        ("High Frequency", "NodeSocketFloatFrequency"),
        ("Bandwidth", "NodeSocketFloatFrequency"),
    ]:
        new_socket(tree, name, "OUTPUT", socket_type, parent=metadata_outputs_panel, structure_type="FIELD")

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (2100, 100)
    group_out.width = 270
    group_out.is_active_output = True

    frame_analyzer = make_frame(nodes, "FRAME_ANALYZER", "1  AUDIO ANALYZER", (-1450, 560), 700)
    frame_layout = make_frame(nodes, "FRAME_LAYOUT", "2  BAR LAYOUT", (-630, 560), 800)
    frame_profile = make_frame(nodes, "FRAME_PROFILE", "3  BAR PROFILE", (290, 560), 1100)
    frame_build = make_frame(nodes, "FRAME_BUILD", "4  BUILD BARS", (1510, 560), 620)
    frame_fields = make_frame(nodes, "FRAME_FIELDS", "5  OUTPUT FIELDS", (1000, -450), 980)

    analyzer_in = local_group_input(
        nodes, "Analyzer Settings",
        ["Sound", "Use Scene Time", "Time", "Time Offset", "Window Function", "FFT Size",
         "All Channels", "Channel", "Bands", "Min Frequency", "Max Frequency", "Logarithmic",
         "Gain", "Floor", "Ceiling", "Clamp to 1", "Response"],
        parent=frame_analyzer,
        location=(20, 100),
        width=240,
    )

    analyzer = nodes.new("GeometryNodeGroup")
    analyzer.name = "Audio Analyzer"
    analyzer.label = GROUP_ANALYZER
    analyzer.node_tree = analyzer_group
    analyzer.parent = frame_analyzer
    analyzer.location = (290, 100)
    analyzer.width = 390
    hide_node_sockets(
        analyzer,
        outputs=(
            "Normalized", "Band Index", "Band Position",
            "Raw Amplitude", "Low Frequency", "Center Frequency",
            "High Frequency", "Bandwidth",
        ),
    )

    for socket_name in (
        "Sound", "Use Scene Time", "Time", "Time Offset", "Window Function", "FFT Size",
        "All Channels", "Channel", "Bands", "Min Frequency", "Max Frequency", "Logarithmic",
        "Gain", "Floor", "Ceiling", "Clamp to 1", "Response",
    ):
        link(tree, analyzer_in, socket_name, analyzer, socket_name)

    layout_in = local_group_input(
        nodes, "Bar Layout",
        ["Bands", "Bar Width", "Bar Depth", "Gap", "Min Height", "Max Height",
         "Baseline", "Center Spectrum"],
        parent=frame_layout,
        location=(20, 100),
        width=210,
    )

    spacing = math_node(nodes, "Bar Spacing", "ADD", (260, 300), frame_layout, "Width + Gap")
    link(tree, layout_in, "Bar Width", spacing, 0)
    link(tree, layout_in, "Gap", spacing, 1)
    link(tree, spacing, "Value", analyzer, "Spacing")

    bands_minus_one = math_node(nodes, "Bands - 1", "SUBTRACT", (260, 100), frame_layout, "Bands - 1")
    set_default(bands_minus_one, 1, 1.0)
    span = math_node(nodes, "Spectrum Span", "MULTIPLY", (450, 100), frame_layout, "(Bands - 1) × Spacing")
    centered_offset = math_node(nodes, "Centered X", "MULTIPLY", (630, 100), frame_layout, "Span × -0.5")
    set_default(centered_offset, 1, -0.5)
    center_switch = switch_float_node(nodes, "Center Spectrum", (630, -80), frame_layout, "Start / Center")

    link(tree, layout_in, "Bands", bands_minus_one, 0)
    link(tree, bands_minus_one, "Value", span, 0)
    link(tree, spacing, "Value", span, 1)
    link(tree, span, "Value", centered_offset, 0)
    link(tree, layout_in, "Center Spectrum", center_switch, "Switch")
    set_default(center_switch, "False", 0.0)
    link(tree, centered_offset, "Value", center_switch, "True")

    height_range = math_node(nodes, "Height Range", "SUBTRACT", (260, -260), frame_layout, "Max - Min")
    amp_height = math_node(nodes, "Amplitude Height", "MULTIPLY", (450, -260), frame_layout, "Amplitude × Range")
    bar_height = math_node(nodes, "Bar Height", "ADD", (630, -260), frame_layout, "Min + Audio")
    half_height = math_node(nodes, "Half Height", "MULTIPLY", (630, -440), frame_layout, "Height / 2")
    set_default(half_height, 1, 0.5)
    center_z = math_node(nodes, "Bar Center Z", "ADD", (630, -600), frame_layout, "Baseline + Height / 2")
    top_z = math_node(nodes, "Bar Top Z", "ADD", (450, -600), frame_layout, "Baseline + Height")

    link(tree, layout_in, "Max Height", height_range, 0)
    link(tree, layout_in, "Min Height", height_range, 1)
    link(tree, analyzer, "Amplitude", amp_height, 0)
    link(tree, height_range, "Value", amp_height, 1)
    link(tree, layout_in, "Min Height", bar_height, 0)
    link(tree, amp_height, "Value", bar_height, 1)
    link(tree, bar_height, "Value", half_height, 0)
    link(tree, layout_in, "Baseline", center_z, 0)
    link(tree, half_height, "Value", center_z, 1)
    link(tree, layout_in, "Baseline", top_z, 0)
    link(tree, bar_height, "Value", top_z, 1)

    # Two positioned versions of the analyzer carrier:
    # centers for instancing and true top-edge points for downstream curve/fill use.
    center_offset_vec = nodes.new("ShaderNodeCombineXYZ")
    center_offset_vec.parent = frame_build
    center_offset_vec.location = (20, 260)
    link(tree, center_switch, "Output", center_offset_vec, "X")
    link(tree, center_z, "Value", center_offset_vec, "Z")

    center_points = nodes.new("GeometryNodeSetPosition")
    center_points.name = "Bar Center Points"
    center_points.label = "Bar Center Points"
    center_points.parent = frame_build
    center_points.location = (210, 260)
    link(tree, analyzer, "Spectrum", center_points, "Geometry")
    link(tree, center_offset_vec, "Vector", center_points, "Offset")

    top_offset_vec = nodes.new("ShaderNodeCombineXYZ")
    top_offset_vec.parent = frame_build
    top_offset_vec.location = (20, 40)
    link(tree, center_switch, "Output", top_offset_vec, "X")
    link(tree, top_z, "Value", top_offset_vec, "Z")

    top_points = nodes.new("GeometryNodeSetPosition")
    top_points.name = "Spectrum Top Points"
    top_points.label = "Spectrum Top Points"
    top_points.parent = frame_build
    top_points.location = (210, 40)
    link(tree, analyzer, "Spectrum", top_points, "Geometry")
    link(tree, top_offset_vec, "Vector", top_points, "Offset")

    profile_in = local_group_input(
        nodes, "Profile",
        ["Bar Profile", "Profile Resolution", "Custom Profile", "Custom Geometry",
         "Bar Width", "Bar Depth", "Material"],
        parent=frame_profile,
        location=(20, 100),
        width=220,
    )

    cube = nodes.new("GeometryNodeMeshCube")
    cube.name = "Box Profile"
    cube.label = "Box"
    cube.parent = frame_profile
    cube.location = (260, 360)
    set_default(cube, "Size", (1.0, 1.0, 1.0))

    cylinder = nodes.new("GeometryNodeMeshCylinder")
    cylinder.name = "Round Profile"
    cylinder.label = "Round"
    cylinder.parent = frame_profile
    cylinder.location = (260, 170)
    set_default(cylinder, "Side Segments", 1)
    set_default(cylinder, "Fill Segments", 1)
    set_default(cylinder, "Radius", 0.5)
    set_default(cylinder, "Depth", 1.0)
    link(tree, profile_in, "Profile Resolution", cylinder, "Vertices")

    cone = nodes.new("GeometryNodeMeshCone")
    cone.name = "Cone Profile"
    cone.label = "Cone"
    cone.parent = frame_profile
    cone.location = (260, -50)
    set_default(cone, "Side Segments", 1)
    set_default(cone, "Fill Segments", 1)
    set_default(cone, "Radius Top", 0.0)
    set_default(cone, "Radius Bottom", 0.5)
    set_default(cone, "Depth", 1.0)
    link(tree, profile_in, "Profile Resolution", cone, "Vertices")

    ico = nodes.new("GeometryNodeMeshIcoSphere")
    ico.name = "Icosphere Profile"
    ico.label = "Icosphere"
    ico.parent = frame_profile
    ico.location = (260, -270)
    set_default(ico, "Radius", 0.5)
    set_default(ico, "Subdivisions", 2)

    profile_path = nodes.new("GeometryNodeCurvePrimitiveLine")
    profile_path.name = "Unit Z Path"
    profile_path.label = "Unit Z Path"
    profile_path.parent = frame_profile
    profile_path.location = (520, -50)
    profile_path.mode = "POINTS"
    set_default(profile_path, "Start", (0.0, 0.0, -0.5))
    set_default(profile_path, "End", (0.0, 0.0, 0.5))

    custom_profile_mesh = nodes.new("GeometryNodeCurveToMesh")
    custom_profile_mesh.name = "Custom Profile Mesh"
    custom_profile_mesh.label = "Extrude Custom Profile"
    custom_profile_mesh.parent = frame_profile
    custom_profile_mesh.location = (720, -50)
    link(tree, profile_path, "Curve", custom_profile_mesh, "Curve")
    link(tree, profile_in, "Custom Profile", custom_profile_mesh, "Profile Curve")
    if get_socket(custom_profile_mesh.inputs, "Fill Caps") is not None:
        set_default(custom_profile_mesh, "Fill Caps", True)

    profile_switch.active_index = 0  # Box
    profile_switch.parent = frame_profile
    profile_switch.location = (740, 260)
    link(tree, profile_in, "Bar Profile", profile_switch, "Menu")
    link(tree, cube, "Mesh", profile_switch, "Box")
    link(tree, cylinder, "Mesh", profile_switch, "Round")
    link(tree, cone, "Mesh", profile_switch, "Cone")
    link(tree, ico, "Mesh", profile_switch, "Icosphere")
    link(tree, custom_profile_mesh, "Mesh", profile_switch, "Custom Profile")
    link(tree, profile_in, "Custom Geometry", profile_switch, "Custom Geometry")

    set_material = nodes.new("GeometryNodeSetMaterial")
    set_material.name = "Bar Material"
    set_material.label = "Apply Material"
    set_material.parent = frame_profile
    set_material.location = (940, 260)
    link(tree, profile_switch, "Output", set_material, "Geometry")
    link(tree, profile_in, "Material", set_material, "Material")

    scale = nodes.new("ShaderNodeCombineXYZ")
    scale.name = "Bar Dimensions"
    scale.label = "Width / Depth / Height"
    scale.parent = frame_build
    scale.location = (210, -180)
    link(tree, layout_in, "Bar Width", scale, "X")
    link(tree, layout_in, "Bar Depth", scale, "Y")
    link(tree, bar_height, "Value", scale, "Z")

    instance = nodes.new("GeometryNodeInstanceOnPoints")
    instance.name = "Instance Bars"
    instance.label = "Instance Bars"
    instance.parent = frame_build
    instance.location = (420, 180)
    instance.width = 230
    link(tree, center_points, "Geometry", instance, "Points")
    link(tree, set_material, "Geometry", instance, "Instance")
    link(tree, scale, "Vector", instance, "Scale")

    link(tree, instance, "Instances", group_out, "Geometry")
    link(tree, top_points, "Geometry", group_out, "Spectrum Points")
    link(tree, analyzer, "Spectrum", group_out, "Raw Spectrum")

    output_attr_map = [
        ("Amplitude",        "dh_audio_amp",          "FLOAT"),
        ("Normalized",       "dh_audio_norm",         "FLOAT"),
        ("Band Index",       "dh_audio_band_index",   "INT"),
        ("Band Position",    "dh_audio_band_pos",     "FLOAT"),
        ("Raw Amplitude",    "dh_audio_raw",          "FLOAT"),
        ("Low Frequency",    "dh_audio_low_hz",       "FLOAT"),
        ("Center Frequency", "dh_audio_center_hz",    "FLOAT"),
        ("High Frequency",   "dh_audio_high_hz",      "FLOAT"),
        ("Bandwidth",        "dh_audio_bandwidth_hz", "FLOAT"),
    ]

    for i, (output_name, attr_name, dtype) in enumerate(output_attr_map):
        col = i % 3
        row = i // 3
        attr = named_attribute_node(
            nodes, attr_name, dtype,
            parent=frame_fields,
            location=(20 + col * 300, 300 - row * 220),
            label=output_name,
        )
        attr.width = 220
        link(tree, attr, "Attribute", group_out, output_name)

    nodes.remove(template)

    mark_asset(
        tree,
        "Standalone spectrum bar visualizer built on DH Audio Analyzer. "
        "Includes Box/Round/Cone/Icosphere presets, custom curve cross-sections, custom geometry, "
        "top-edge spectrum points, and standardized audio attributes."
    )
    return tree



# =====================================================================
# Blender Text README / Example Recipes
# =====================================================================

def create_readme_text():
    if not CREATE_README:
        return None

    readme = bpy.data.texts.get(README_TEXT_NAME)
    if readme is None:
        readme = bpy.data.texts.new(README_TEXT_NAME)
    else:
        readme.clear()

    readme.write(f"""DH AUDIO TOOLKIT {TOOLKIT_VERSION}
Blender 5.2+

======================================================================
WHAT THIS TOOLKIT IS
======================================================================

A modular audio-reactive Geometry Nodes + Shader Nodes toolkit built around
Blender 5.2's Sample Sound Frequencies node.

The design is intentionally split into:

    ANALYZE     create useful audio data
    MAP         turn analyzer carriers into useful point geometry
    CONSUME     bars / curves / fills / arbitrary instances
    QUERY       retrieve one scalar band
    TRANSPORT   named attributes for geometry and materials
    SHADE       read and reshape those attributes in materials


======================================================================
NODE REFERENCE
======================================================================

DH Audio Analyzer
    Core N-band FFT analyzer. Generates one carrier point per band and stores
    amplitude, normalized amplitude, band index/position, frequency bounds,
    center frequency, and bandwidth as standardized dh_audio_* attributes.

DH Audio Frequency Map
    Advanced mapping utility used by Analyzer. Converts Band Index + band
    count + frequency limits into linear or logarithmic frequency boundaries.
    Most users will not need it directly, but it is useful for custom systems.

DH Audio Spectrum Points
    Turns Analyzer's flat carrier into visible audio-height points while
    preserving all spectrum attributes. This is the standard modular source
    for Spectrum Curve and Spectrum Fill.

DH Audio Spectrum Bars
    Standalone visualizer with Analyzer built in. Creates bars using Box,
    Round, Cone, Icosphere, Custom Profile, or Custom Geometry. Also exposes
    Spectrum Points at the top of the bars for Curve/Fill workflows.

DH Audio Spectrum Curve
    Converts positioned Spectrum Points into Raw, Smooth Catmull-Rom, or
    Smooth + Resampled curves. Can also create a tube mesh whose Scale is
    modulated per point by audio amplitude.

DH Audio Spectrum Fill
    Builds a filled two-row quad strip from positioned Spectrum Points down to
    a flat baseline. Every input spectrum point contributes to the top edge.

DH Audio Spectrum Instances
    Generic visualizer for instancing any geometry once per spectrum band.
    Amplitude can add scale and positional offset, and the spectrum attributes
    remain available on the instance domain for materials.

DH Audio Frequency Selection
    Creates a Boolean Selection field from actual center-frequency bounds,
    so effects can target bass/mids/highs without depending on band indices.

DH Audio Band Query
    Samples one numbered Analyzer band and returns scalar amplitude/normalized
    values plus optional detailed frequency metadata.

DH Audio Sample Range
    Standalone direct sampler for one custom Low Hz -> High Hz range. Use it
    when you want one reaction value and do not need a complete spectrum.

DH Audio Bands
    Standalone named musical ranges: Total, Sub, Bass, Low Mid, Mid Range,
    High Mids, Presence, Brilliance, and Air. Also includes the integrated
    attribute bridge for stamping those values onto arbitrary geometry.

DH Audio Response
    Geometry Nodes response shaper: Gain -> Floor/Ceiling normalization ->
    optional clamp -> response power curve. Useful for any scalar, not just
    the built-in audio nodes.

DH Audio Material Reader
    Shader helper that reads all standardized spectrum and named-band
    attributes. Use Instancer is a checkbox: Off for real/realized geometry,
    On when the material is reading attributes from GN instances.

DH Audio Shader Response
    Shader-side equivalent of DH Audio Response with the same Gain/Floor/
    Ceiling/Clamp/Response workflow. Clamp to 1 is a checkbox.


======================================================================
ASSET CATALOGS / SHARING
======================================================================

The generator assigns stable catalog UUIDs and writes/updates:

    blender_assets.cats.txt

beside the saved .blend. Geometry assets are organized under:

    Geometry Nodes / DH Audio / Analysis
    Geometry Nodes / DH Audio / Mapping
    Geometry Nodes / DH Audio / Query
    Geometry Nodes / DH Audio / Visualizers
    Geometry Nodes / DH Audio / Utilities

Shader groups are under:

    DH Audio / Shaders

For a portable release, share the .blend AND blender_assets.cats.txt together
inside the same asset-library folder. The UUIDs in this toolkit are intended
to remain stable across future versions.


======================================================================
RECIPE 1: STANDALONE BARS
======================================================================

    DH Audio Spectrum Bars -> Group Output

Choose Sound and press Play.

Useful controls:
    Bands
    Min / Max Frequency
    FFT Size
    Window Function
    Ceiling = 0.8 stock
    Bar Profile
    Width / Depth / Gap / Height

Bar Profile defaults to Box. Choices:
    Box
    Round
    Cone
    Icosphere
    Custom Profile
    Custom Geometry

Custom Profile:
    Supply a 2D curve cross-section centered near the origin.
    The group extrudes it along a normalized one-unit Z path.

Custom Geometry:
    Supply anything. Normalize it around Z=0 and about one unit tall
    if you want Width / Depth / Height controls to behave predictably.


======================================================================
RECIPE 2: ANALYZER -> VISIBLE SPECTRUM POINTS
======================================================================

    DH Audio Analyzer [Spectrum]
        -> DH Audio Spectrum Points [Spectrum]

Spectrum Points controls:
    Height
    Baseline
    Center Spectrum
    X Scale
    X Offset

This output is the canonical "audio graph as geometry" representation.

It carries the Analyzer attributes with it, so downstream consumers and
materials still know amplitude, band index, band position, frequency, etc.


======================================================================
RECIPE 3: SMOOTH SPECTRUM CURVE
======================================================================

    DH Audio Analyzer [Spectrum]
        -> DH Audio Spectrum Points [Spectrum]
        -> DH Audio Spectrum Curve [Spectrum Points]

OR:

    DH Audio Spectrum Bars [Spectrum Points]
        -> DH Audio Spectrum Curve [Spectrum Points]

Curve Style defaults to Smooth. For a denser editable curve, try:
    Curve Style    = Smooth + Resample
    Resample Count = 128

Outputs:
    Curve
    Tube

Tube extras:
    Tube Radius
    Audio Radius       modulates Tube Scale from dh_audio_amp (Tube output only)
    Tube Resolution
    Material


======================================================================
RECIPE 4: FILLED SPECTRUM SILHOUETTE
======================================================================

    DH Audio Analyzer [Spectrum]
        -> DH Audio Spectrum Points [Spectrum]
        -> DH Audio Spectrum Fill [Spectrum Points]

OR:

    DH Audio Spectrum Bars [Spectrum Points]
        -> DH Audio Spectrum Fill [Spectrum Points]

The fill follows EVERY input point in order and creates a bottom edge at
Baseline. The two-row grid indexing is explicit, so quiet valleys are not
skipped between louder neighboring points.

Good for:
    emissive spectrum silhouettes
    extrusion / solidification downstream
    masks
    stylized terrain
    spectrum ribbons
    geometry used as a deformation source


======================================================================
RECIPE 5: INSTANCE ANYTHING
======================================================================

    DH Audio Analyzer [Spectrum]
        -> DH Audio Spectrum Instances [Spectrum]

Connect anything to Instance.

Examples:
    Base Scale       = (1, 1, 1)
    Amplitude Scale  = (0, 0, 3)
    Amplitude Offset = (0, 0, 2)

Useful for:
    lights represented by meshes
    logos
    crystals
    particles
    abstract sculptures
    text converted to geometry
    collections converted to geometry upstream

Analyzer point attributes become instance-domain attributes through
Instance on Points, so compatible materials can still react per band.


======================================================================
RECIPE 6: SELECT A FREQUENCY REGION
======================================================================

    DH Audio Frequency Selection

Example:
    Low Frequency  = 60 Hz
    High Frequency = 250 Hz

Connect Selection to:
    DH Audio Spectrum Instances -> Selection
    Set Position -> Selection
    Delete Geometry -> Selection
    Set Material -> Selection

This uses dh_audio_center_hz, so it keeps working even if Analyzer Bands count
changes.

======================================================================
RECIPE 7: QUERY ONE NUMBERED BAND
======================================================================

    DH Audio Analyzer [Spectrum]
        -> DH Audio Band Query [Spectrum]

Set:
    Band = 6

Outputs:
    Band Index
    Amplitude
    Normalized
    Raw Amplitude
    Band Position

Detailed frequency metadata is intentionally collapsed by default.


======================================================================
RECIPE 8: SAMPLE ONE CUSTOM FREQUENCY RANGE
======================================================================

Use:
    DH Audio Sample Range

Example:
    Low Frequency  = 40 Hz
    High Frequency = 120 Hz

Use this when you only want something like:
    kick/sub motion
    a vocal-presence range
    a cymbal shimmer range

and do not need a whole spectrum carrier.


======================================================================
RECIPE 9: NAMED MUSICAL BANDS
======================================================================

Use:
    DH Audio Bands

Outputs:
    Total Volume
    Sub
    Bass
    Low Mid
    Mid Range
    High Mids
    Presence
    Brilliance
    Air

These are independent of Analyzer Bands count.

Internally this uses:
    nine carrier points
    one field-driven Sample Sound Frequencies node
    Index Switch based Low/High range mapping

Band Data contains one point per named range plus:
    dh_audio_named_amp
    dh_audio_named_index
    dh_audio_named_low_hz
    dh_audio_named_center_hz
    dh_audio_named_high_hz
    dh_audio_named_bandwidth_hz

It also carries all global named-band attributes.


======================================================================
RECIPE 10: PUT NAMED BANDS ON YOUR OWN GEOMETRY
======================================================================

Plug your geometry into:

    DH Audio Bands
        Attribute Bridge -> Geometry

Leave:
    Store on Points    = On
    Store on Instances = On

The output now carries:
    dh_audio_total
    dh_audio_sub
    dh_audio_bass
    dh_audio_low_mid
    dh_audio_mid
    dh_audio_high_mids
    dh_audio_presence
    dh_audio_brilliance
    dh_audio_air

No separate Store Bands group and no nine manual cables.


======================================================================
RECIPE 11: MATERIALS
======================================================================

Inside a material add:
    DH Audio Material Reader

Use Instancer = On
    for geometry still living as Geometry Nodes instances.

Use Instancer = Off
    for ordinary / realized geometry.

Common outputs:
    Amplitude
    Normalized
    Band Position
    Sub
    Bass
    Mid Range
    Presence
    Air

Then optionally:
    DH Audio Material Reader [Amplitude]
        -> DH Audio Shader Response
        -> Emission Strength


======================================================================
STANDARD SPECTRUM ATTRIBUTES
======================================================================

dh_audio_amp
dh_audio_norm
dh_audio_raw
dh_audio_band_index
dh_audio_band_pos
dh_audio_low_hz
dh_audio_center_hz
dh_audio_high_hz
dh_audio_bandwidth_hz


======================================================================
WHY THE PUBLIC GROUPS LOOK CLEANER THAN THE INTERNAL ONES
======================================================================

Groups prefixed with:
    DH Internal -

exist only to encapsulate repetitive attribute storage and mapping logic.

Public groups use multiple local Group Input nodes with unrelated sockets
hidden. This intentionally trades one giant cable bundle for localized,
readable frames.

Detailed frequency metadata is kept in collapsed panels because most visual
work only needs:
    geometry
    amplitude
    normalized amplitude
    band index / position


======================================================================
DESIGN NOTES
======================================================================

FFT Size:
    Larger sizes give more frequency precision but respond more slowly
    to short-lived changes.

Ceiling:
    Stock is 0.8 rather than 0.1 because 0.1 visually clipped too many
    bands to full response in normal mastered music.

Curve smoothing:
    Smooth mode uses Catmull-Rom because it passes through the source
    control points.
    Smooth + Resample turns that evaluated shape into an evenly sampled
    curve useful for downstream modeling.

Spectrum interoperability:
    DH Audio Spectrum Points and DH Audio Spectrum Bars intentionally emit
    compatible Spectrum Points. Curve and Fill accept either.


======================================================================
GOOD NEXT ADDITIONS
======================================================================

These fit the current architecture without breaking it:

    Temporal Response
        attack / release
        peak hold
        decay
        temporal averaging

    Spectrum History
        simulation-zone trails
        waterfall plots
        2D / 3D history surfaces

    Radial Spectrum Mapper
        spectrum around a circle
        spiral
        polar displacement

    Frequency Selection Utilities
        band masks
        frequency-to-selection
        select by low/high Hz rather than band number

    Stereo Tools
        left/right channel split
        stereo width visualizations

    Dynamic Normalization
        auto gain
        rolling peak normalization
        per-band normalization

    Events
        rough onset / beat trigger
        threshold crossings
        pulse generation

    Spatial Mapping
        logarithmic X spacing
        frequency-based radius
        frequency-based rotation

    Shader Helpers
        standard audio color-ramp group
        emission helper
        frequency-to-hue helper

    Blender 5.2 Lists / Geometry Bundles
        possible future transport layer for larger procedural systems,
        while named attributes remain the shader-compatible transport.


======================================================================
TIP
======================================================================

Start with one of these three paths:

    EASY:
        DH Audio Spectrum Bars

    MODULAR:
        Analyzer -> Spectrum Points -> Curve / Fill

    CUSTOM:
        Analyzer -> Spectrum Instances / Band Query
""")
    return readme


# =====================================================================
# Optional demo host
# =====================================================================

# =====================================================================
# Optional demo host
# =====================================================================

def create_demo_host(analyzer_group):
    if not CREATE_DEMO_HOST:
        return None

    obj = bpy.data.objects.get(HOST_OBJECT_NAME)
    if obj is None:
        mesh = bpy.data.meshes.new(HOST_OBJECT_NAME + " Mesh")
        obj = bpy.data.objects.new(HOST_OBJECT_NAME, mesh)
        bpy.context.collection.objects.link(obj)

    modifier = obj.modifiers.get(GROUP_ANALYZER)
    if modifier is None:
        modifier = obj.modifiers.new(name=GROUP_ANALYZER, type="NODES")

    modifier.node_group = analyzer_group

    for selected in bpy.context.selected_objects:
        selected.select_set(False)

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


# =====================================================================
# Build all
# =====================================================================

def main():
    require_blender_52()
    cleanup_existing()

    response = create_response_group()
    shader_response = create_shader_response_group()

    frequency_map = create_frequency_map()
    frequency_selection = create_frequency_selection()
    store_spectrum = create_internal_store_spectrum()
    named_map = create_internal_named_band_map()
    named_meta_store = create_internal_store_named_metadata()
    named_store = create_internal_store_named_bands()

    analyzer = create_analyzer(response, frequency_map, store_spectrum)
    spectrum_points = create_spectrum_points()
    query = create_band_query()
    sample_range = create_sample_range(response)
    named_bands = create_named_bands(named_map, named_meta_store, named_store)

    spectrum_instances = create_spectrum_instances()
    spectrum_curve = create_spectrum_curve()
    spectrum_fill = create_spectrum_fill()

    material_reader = create_material_reader()
    bars = create_spectrum_bars(analyzer)

    readme = create_readme_text()
    host = create_demo_host(analyzer)

    register_catalog_save_handler()
    catalog_file = ensure_catalog_definition_file()

    print("\n" + "=" * 82)
    print(f"DH AUDIO TOOLKIT {TOOLKIT_VERSION} CREATED")
    print("=" * 82)
    print("Geometry Node assets:")
    for group in (
        response,
        frequency_map,
        frequency_selection,
        analyzer,
        spectrum_points,
        query,
        sample_range,
        named_bands,
        spectrum_instances,
        spectrum_curve,
        spectrum_fill,
        bars,
    ):
        print(f"  - {group.name}")

    print()
    print("Shader Node assets:")
    print(f"  - {material_reader.name}")
    print(f"  - {shader_response.name}")

    print()
    print("Architecture:")
    print("  Analyzer Spectrum -> Spectrum Points -> Curve / Fill")
    print("  Analyzer Spectrum -> Frequency Selection -> downstream Selection inputs")
    print("  Analyzer Spectrum -> Instances / Band Query")
    print("  Spectrum Bars     -> standalone Analyzer wrapper + compatible Spectrum Points")
    print("  Audio Bands       -> named musical ranges + integrated attribute bridge")

    print()
    print("Spectrum attribute schema:")
    for label, attr_name, _dtype in SPECTRUM_ATTRS:
        print(f"  {label:<18} -> {attr_name}")

    print()
    print("Named-band attribute schema:")
    for label, attr_name in NAMED_BAND_ATTRS:
        print(f"  {label:<18} -> {attr_name}")

    if readme:
        print()
        print(f"Example recipes: open Text Editor -> '{readme.name}'")

    print()
    if catalog_file:
        print(f"Asset catalog sidecar: {catalog_file}")
    else:
        print("Asset catalog UUIDs assigned; save the .blend to write blender_assets.cats.txt")

    if host:
        print()
        print(f"Demo host: {host.name}")

    print("=" * 82 + "\n")


if __name__ == "__main__":
    main()
