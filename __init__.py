"""
Palette for Blender
================================

Import iTerm2 color schemes (.itermcolors) and apply them as Blender themes.
Maps ANSI terminal colors into Blender's UI color surface via HSL/HSV derivation.

Author: NXSTYNATE
License: GPL-3.0
"""

bl_info = {
    "name": "Palette",
    "author": "NXSTYNATE",
    "version": (1, 1, 1),
    "blender": (4, 5, 0),
    "location": "Edit > Preferences > Themes",
    "description": "Import iTerm2 color schemes and apply them as Blender themes",
    "category": "Interface",
}

import bpy
import os
import sys
import importlib
import traceback
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatVectorProperty,
)
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup,
    UIList,
)

# Force-reload submodules on reinstall
_submodules = [
    "color_math",
    "iterm_parser",
    "blender_theme_map",
    "xml_writer",
    "apply",
    "repo",
    "prefs",
]
for _mod_name in _submodules:
    _full = f"{__package__}.{_mod_name}"
    if _full in sys.modules:
        importlib.reload(sys.modules[_full])


# =========================================================================
# Color slot labels — maps index to human-readable role
# =========================================================================

# The palette editor shows these slots in order.
# First 16 are ANSI, then the named extras.
PALETTE_SLOTS = [
    ("ansi_0",  "ANSI 0 — Black"),
    ("ansi_1",  "ANSI 1 — Red"),
    ("ansi_2",  "ANSI 2 — Green"),
    ("ansi_3",  "ANSI 3 — Yellow"),
    ("ansi_4",  "ANSI 4 — Blue / Accent"),
    ("ansi_5",  "ANSI 5 — Magenta"),
    ("ansi_6",  "ANSI 6 — Cyan"),
    ("ansi_7",  "ANSI 7 — White"),
    ("ansi_8",  "ANSI 8 — Bright Black"),
    ("ansi_9",  "ANSI 9 — Bright Red"),
    ("ansi_10", "ANSI 10 — Bright Green"),
    ("ansi_11", "ANSI 11 — Bright Yellow"),
    ("ansi_12", "ANSI 12 — Bright Blue"),
    ("ansi_13", "ANSI 13 — Bright Magenta"),
    ("ansi_14", "ANSI 14 — Bright Cyan"),
    ("ansi_15", "ANSI 15 — Bright White"),
    ("bg",      "Background"),
    ("fg",      "Foreground"),
    ("cursor",  "Cursor"),
    ("selection", "Selection"),
]


def _hex_from_rgb(r, g, b):
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, int(r * 255))),
        max(0, min(255, int(g * 255))),
        max(0, min(255, int(b * 255))),
    )


def _rgb_from_hex(hexstr):
    """Parse hex like '#FF00AA' or 'FF00AA' into (r,g,b) floats."""
    h = hexstr.strip().lstrip('#')
    if len(h) != 6:
        return None
    try:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return (r, g, b)
    except ValueError:
        return None


# =========================================================================
# Property groups
# =========================================================================

class ITERM_ThemeItem(PropertyGroup):
    name: StringProperty(name="Theme Name")
    path: StringProperty(name="File Path")


def _on_palette_hex_update(self, context):
    """When hex field is edited, update the color swatch."""
    rgb = _rgb_from_hex(self.hex_value)
    if rgb:
        # Prevent recursive update
        if (abs(self.color[0] - rgb[0]) > 0.002
                or abs(self.color[1] - rgb[1]) > 0.002
                or abs(self.color[2] - rgb[2]) > 0.002):
            self.color = rgb


def _on_palette_color_update(self, context):
    """When color swatch is edited, update the hex field."""
    new_hex = _hex_from_rgb(*self.color)
    if self.hex_value != new_hex:
        self.hex_value = new_hex


class ITERM_PaletteColor(PropertyGroup):
    """A single editable color in the palette."""
    slot_id: StringProperty(name="Slot ID")
    label: StringProperty(name="Label")
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=3,
        min=0.0, max=1.0,
        default=(0.5, 0.5, 0.5),
        update=_on_palette_color_update,
    )
    hex_value: StringProperty(
        name="Hex",
        default="#808080",
        maxlen=7,
        update=_on_palette_hex_update,
    )
    # Store original color for reset
    orig_r: bpy.props.FloatProperty(default=0.5)
    orig_g: bpy.props.FloatProperty(default=0.5)
    orig_b: bpy.props.FloatProperty(default=0.5)


# =========================================================================
# Helpers
# =========================================================================

def _populate_palette_from_iterm(wm, iterm_theme):
    """Fill the editable palette collection from a parsed iTerm theme."""
    wm.iterm_palette.clear()

    ansi = iterm_theme.get("ansi", [])

    for slot_id, label in PALETTE_SLOTS:
        item = wm.iterm_palette.add()
        item.slot_id = slot_id
        item.label = label

        # Determine the color for this slot
        if slot_id.startswith("ansi_"):
            idx = int(slot_id.split("_")[1])
            if idx < len(ansi) and ansi[idx]:
                c = ansi[idx]
            else:
                c = (0.5, 0.5, 0.5)
        else:
            c = iterm_theme.get(slot_id)
            if c is None:
                # Use sensible defaults for missing extras
                if slot_id == "bg":
                    c = ansi[0] if ansi[0] else (0.1, 0.1, 0.1)
                elif slot_id == "fg":
                    c = ansi[7] if ansi[7] else (0.9, 0.9, 0.9)
                elif slot_id == "cursor":
                    c = ansi[4] if ansi[4] else (0.5, 0.5, 1.0)
                elif slot_id == "selection":
                    c = (0.3, 0.3, 0.5)
                else:
                    c = (0.5, 0.5, 0.5)

        item.color = c[:3]
        item.hex_value = _hex_from_rgb(*c[:3])
        item.orig_r = c[0]
        item.orig_g = c[1]
        item.orig_b = c[2]

    wm.iterm_palette_loaded = True
    wm.iterm_palette_theme_name = iterm_theme.get("name", "Unknown")


def _snapshot_current_theme(wm):
    """Save the current Blender theme to a temp XML file for later restore."""
    import tempfile
    try:
        from rna_xml import rna2xml
        theme = bpy.context.preferences.themes[0]
        fd, path = tempfile.mkstemp(suffix=".xml", prefix="palette_snapshot_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("<bpy>\n")
            rna2xml(
                f.write,
                root_rna=theme,
                method='ATTR',
                root_ident="  ",
                ident_val="  ",
            )
            f.write("</bpy>\n")
        wm["_iterm_theme_snapshot"] = path
    except Exception:
        # If snapshot fails, store empty — reset will fall back to default
        wm["_iterm_theme_snapshot"] = ""


def _build_iterm_theme_from_palette(wm):
    """Reconstruct an iTerm theme dict from the editable palette."""
    theme = {
        "name": wm.iterm_palette_theme_name,
        "ansi": [],
    }

    # Build a lookup
    palette_map = {}
    for item in wm.iterm_palette:
        palette_map[item.slot_id] = tuple(item.color)

    # ANSI 0-15
    for i in range(16):
        key = f"ansi_{i}"
        theme["ansi"].append(palette_map.get(key, (0.5, 0.5, 0.5)))

    # Named
    theme["bg"] = palette_map.get("bg", theme["ansi"][0])
    theme["fg"] = palette_map.get("fg", theme["ansi"][7])
    theme["cursor"] = palette_map.get("cursor")
    theme["selection"] = palette_map.get("selection")

    # Set extras to None that we don't expose
    theme["cursor_text"] = None
    theme["selected_text"] = None
    theme["bold"] = None

    return theme


# =========================================================================
# Operators
# =========================================================================

class ITERM_OT_refresh_repo(Operator):
    """Refresh the theme list from local folder or remote repositories"""
    bl_idname = "iterm_theme.refresh_repo"
    bl_label = "Refresh Theme List"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from . import repo

        addon_prefs = context.preferences.addons[__package__].preferences
        wm = context.window_manager

        try:
            if addon_prefs.source_mode == 'LOCAL':
                folder = bpy.path.abspath(addon_prefs.local_folder)
                if not folder or not os.path.isdir(folder):
                    self.report({'ERROR'}, f"Invalid folder: {folder}")
                    return {'CANCELLED'}
                index = repo.index_local_folder(folder)
            else:
                enabled = addon_prefs.get_enabled_sources()
                if not enabled:
                    self.report({'ERROR'}, "No sources enabled. Check add-on preferences.")
                    return {'CANCELLED'}
                index = repo.download_sources(
                    enabled_sources=enabled,
                    progress_callback=lambda msg: self.report({'INFO'}, msg)
                )

            wm.iterm_themes.clear()
            for t in index.get("themes", []):
                item = wm.iterm_themes.add()
                item.name = t["name"]
                item.path = t["path"]

            wm.iterm_theme_count = len(wm.iterm_themes)
            self.report({'INFO'}, f"Found {len(wm.iterm_themes)} themes")

        except Exception as e:
            self.report({'ERROR'}, f"Failed to refresh: {e}")
            traceback.print_exc()
            return {'CANCELLED'}

        return {'FINISHED'}


class ITERM_OT_apply_theme(Operator):
    """Apply the selected iTerm2 theme to Blender (one-click)"""
    bl_idname = "iterm_theme.apply_theme"
    bl_label = "Apply Theme"
    bl_options = {'REGISTER', 'UNDO'}

    theme_index: IntProperty(default=-1)

    def execute(self, context):
        from . import iterm_parser, blender_theme_map, apply, xml_writer

        wm = context.window_manager
        addon_prefs = context.preferences.addons[__package__].preferences

        # Snapshot original theme before first apply
        if "_iterm_theme_snapshot" not in wm:
            _snapshot_current_theme(wm)

        idx = self.theme_index if self.theme_index >= 0 else wm.iterm_theme_active
        if idx < 0 or idx >= len(wm.iterm_themes):
            self.report({'ERROR'}, "No theme selected")
            return {'CANCELLED'}

        theme_item = wm.iterm_themes[idx]

        try:
            iterm_theme = iterm_parser.parse_theme_file(theme_item.path)
            palette = blender_theme_map.build_palette(iterm_theme)
            result = apply.apply_theme_to_blender(palette)
            if result is not True:
                self.report({'WARNING'}, f"Apply issue: {result}")

            if addon_prefs.export_xml:
                try:
                    xml_dir = os.path.join(bpy.utils.user_resource('CONFIG'), "themes")
                    safe_name = "".join(
                        c if c.isalnum() or c in (' ', '-', '_') else '_'
                        for c in theme_item.name
                    )
                    xml_path = os.path.join(xml_dir, f"{safe_name}.xml")
                    xml_writer.export_current_theme_xml(xml_path)
                except Exception:
                    pass

            if addon_prefs.save_on_apply:
                apply.save_user_preferences()

            # Also populate the palette editor
            _populate_palette_from_iterm(wm, iterm_theme)

            self.report({'INFO'}, f"Applied theme: {theme_item.name}")

        except Exception as e:
            self.report({'ERROR'}, f"Failed to apply theme: {e}")
            traceback.print_exc()
            return {'CANCELLED'}

        return {'FINISHED'}


class ITERM_OT_load_palette(Operator):
    """Load the selected theme into the palette editor for customization"""
    bl_idname = "iterm_theme.load_palette"
    bl_label = "Load into Editor"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from . import iterm_parser

        wm = context.window_manager
        idx = wm.iterm_theme_active
        if idx < 0 or idx >= len(wm.iterm_themes):
            self.report({'ERROR'}, "No theme selected")
            return {'CANCELLED'}

        theme_item = wm.iterm_themes[idx]

        try:
            iterm_theme = iterm_parser.parse_theme_file(theme_item.path)
            _populate_palette_from_iterm(wm, iterm_theme)
            self.report({'INFO'}, f"Loaded palette: {theme_item.name}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load: {e}")
            traceback.print_exc()
            return {'CANCELLED'}

        return {'FINISHED'}


class ITERM_OT_apply_custom_palette(Operator):
    """Apply the customized palette to Blender"""
    bl_idname = "iterm_theme.apply_custom"
    bl_label = "Apply Custom Palette"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from . import blender_theme_map, apply, xml_writer

        wm = context.window_manager
        addon_prefs = context.preferences.addons[__package__].preferences

        if not wm.iterm_palette_loaded or len(wm.iterm_palette) == 0:
            self.report({'ERROR'}, "No palette loaded. Load a theme first.")
            return {'CANCELLED'}

        try:
            iterm_theme = _build_iterm_theme_from_palette(wm)
            palette = blender_theme_map.build_palette(iterm_theme)
            result = apply.apply_theme_to_blender(palette)
            if result is not True:
                self.report({'WARNING'}, f"Apply issue: {result}")

            if addon_prefs.export_xml:
                try:
                    name = wm.iterm_palette_theme_name + " (Custom)"
                    xml_dir = os.path.join(bpy.utils.user_resource('CONFIG'), "themes")
                    safe_name = "".join(
                        c if c.isalnum() or c in (' ', '-', '_') else '_'
                        for c in name
                    )
                    xml_path = os.path.join(xml_dir, f"{safe_name}.xml")
                    xml_writer.export_current_theme_xml(xml_path)
                except Exception:
                    pass

            if addon_prefs.save_on_apply:
                apply.save_user_preferences()

            self.report({'INFO'}, "Applied custom palette")

        except Exception as e:
            self.report({'ERROR'}, f"Failed to apply: {e}")
            traceback.print_exc()
            return {'CANCELLED'}

        return {'FINISHED'}


class ITERM_OT_reset_palette(Operator):
    """Reset all palette colors to the original theme values"""
    bl_idname = "iterm_theme.reset_palette"
    bl_label = "Reset to Original"
    bl_options = {'REGISTER'}

    def execute(self, context):
        wm = context.window_manager
        for item in wm.iterm_palette:
            item.color = (item.orig_r, item.orig_g, item.orig_b)
            item.hex_value = _hex_from_rgb(item.orig_r, item.orig_g, item.orig_b)

        self.report({'INFO'}, "Palette reset to original")
        return {'FINISHED'}


class ITERM_OT_swap_colors(Operator):
    """Swap two selected palette colors"""
    bl_idname = "iterm_theme.swap_colors"
    bl_label = "Swap Colors"
    bl_options = {'REGISTER'}

    def execute(self, context):
        wm = context.window_manager
        a = wm.iterm_palette_swap_a
        b = wm.iterm_palette_swap_b

        if a == b:
            self.report({'WARNING'}, "Select two different slots to swap")
            return {'CANCELLED'}

        pal = wm.iterm_palette
        if a < 0 or a >= len(pal) or b < 0 or b >= len(pal):
            self.report({'ERROR'}, "Invalid slot indices")
            return {'CANCELLED'}

        # Swap color values (not labels/slot_ids)
        ca = tuple(pal[a].color)
        cb = tuple(pal[b].color)
        pal[a].color = cb
        pal[b].color = ca
        pal[a].hex_value = _hex_from_rgb(*cb)
        pal[b].hex_value = _hex_from_rgb(*ca)

        self.report({'INFO'}, f"Swapped {pal[a].label} ↔ {pal[b].label}")
        return {'FINISHED'}


class ITERM_OT_export_theme_xml(Operator):
    """Export the selected theme as a Blender theme XML file"""
    bl_idname = "iterm_theme.export_xml"
    bl_label = "Export Theme XML"
    bl_options = {'REGISTER'}

    filepath: StringProperty(
        name="File Path",
        description="Path to save the theme XML file",
        subtype='FILE_PATH',
    )

    filter_glob: StringProperty(
        default="*.xml",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        wm = context.window_manager
        idx = wm.iterm_theme_active
        if idx < 0 or idx >= len(wm.iterm_themes):
            self.report({'ERROR'}, "No theme selected")
            return {'CANCELLED'}

        # Set default filename
        theme_item = wm.iterm_themes[idx]
        safe_name = "".join(
            c if c.isalnum() or c in (' ', '-', '_') else '_'
            for c in theme_item.name
        )
        self.filepath = safe_name + ".xml"

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        from . import iterm_parser, blender_theme_map, apply, xml_writer

        wm = context.window_manager
        idx = wm.iterm_theme_active
        if idx < 0 or idx >= len(wm.iterm_themes):
            self.report({'ERROR'}, "No theme selected")
            return {'CANCELLED'}

        theme_item = wm.iterm_themes[idx]

        try:
            # Apply theme first so the live data matches what we export
            iterm_theme = iterm_parser.parse_theme_file(theme_item.path)
            palette = blender_theme_map.build_palette(iterm_theme)
            apply.apply_theme_to_blender(palette)

            # Ensure .xml extension
            filepath = self.filepath
            if not filepath.lower().endswith('.xml'):
                filepath += '.xml'

            xml_writer.export_current_theme_xml(filepath)
            self.report({'INFO'}, f"Exported: {filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {e}")
            traceback.print_exc()
            return {'CANCELLED'}

        return {'FINISHED'}


class ITERM_OT_search_themes(Operator):
    """Filter the theme list by search term"""
    bl_idname = "iterm_theme.search"
    bl_label = "Search Themes"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from . import repo

        wm = context.window_manager
        query = wm.iterm_theme_search

        all_themes = repo.get_theme_list()
        filtered = repo.search_themes(query, all_themes)

        wm.iterm_themes.clear()
        for t in filtered:
            item = wm.iterm_themes.add()
            item.name = t["name"]
            item.path = t["path"]

        wm.iterm_theme_count = len(wm.iterm_themes)
        return {'FINISHED'}


class ITERM_OT_preview_swatches(Operator):
    """Show color swatches for the selected theme"""
    bl_idname = "iterm_theme.preview"
    bl_label = "Preview Theme Colors"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from . import iterm_parser, blender_theme_map

        wm = context.window_manager
        idx = wm.iterm_theme_active
        if idx < 0 or idx >= len(wm.iterm_themes):
            self.report({'ERROR'}, "No theme selected")
            return {'CANCELLED'}

        theme_item = wm.iterm_themes[idx]

        try:
            iterm_theme = iterm_parser.parse_theme_file(theme_item.path)
            palette = blender_theme_map.build_palette(iterm_theme)
            summary = blender_theme_map.palette_summary(palette)
            print(f"\n=== Theme: {theme_item.name} ===")
            print(f"  Dark theme: {palette['dark']}")
            print("  ANSI Colors:")
            for i, c in enumerate(palette['ansi']):
                hexc = "#{:02x}{:02x}{:02x}".format(
                    int(c[0]*255), int(c[1]*255), int(c[2]*255)
                )
                print(f"    [{i:2d}] {hexc}")
            print("  Derived palette:")
            print(summary)
            self.report({'INFO'}, f"Preview printed to console for: {theme_item.name}")
        except Exception as e:
            self.report({'ERROR'}, f"Preview failed: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}


class ITERM_OT_reset_theme(Operator):
    """Reset Blender's theme back to what it was before Palette changed it"""
    bl_idname = "iterm_theme.reset_theme"
    bl_label = "Reset to Initial Theme"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = context.window_manager
        snapshot_path = wm.get("_iterm_theme_snapshot", "")

        if not snapshot_path or not os.path.isfile(snapshot_path):
            # No snapshot saved — reset to Blender factory default
            bpy.ops.preferences.reset_default_theme()
            self.report({'INFO'}, "Reset to Blender default theme")
            return {'FINISHED'}

        try:
            bpy.ops.script.execute_preset(
                filepath=snapshot_path,
                menu_idname="USERPREF_MT_interface_theme_presets",
            )
            self.report({'INFO'}, "Restored initial theme")
        except Exception:
            # execute_preset failed — try direct rna_xml approach
            try:
                import rna_xml
                preset_xml_map = (
                    ("bpy.context.preferences.themes[0]", "Theme"),
                )
                rna_xml.xml_file_run(context, snapshot_path, preset_xml_map)
                # Force UI redraw
                for window in context.window_manager.windows:
                    for area in window.screen.areas:
                        area.tag_redraw()
                self.report({'INFO'}, "Restored initial theme")
            except Exception as e:
                bpy.ops.preferences.reset_default_theme()
                self.report({'WARNING'}, f"Snapshot restore failed, reset to default: {e}")

        return {'FINISHED'}
# =========================================================================

class ITERM_UL_theme_list(UIList):
    bl_idname = "ITERM_UL_theme_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon='COLOR')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='COLOR')


# =========================================================================
# Panels
# =========================================================================






# =========================================================================
# Registration
# =========================================================================

classes = (
    ITERM_ThemeItem,
    ITERM_PaletteColor,
    ITERM_OT_refresh_repo,
    ITERM_OT_apply_theme,
    ITERM_OT_load_palette,
    ITERM_OT_apply_custom_palette,
    ITERM_OT_reset_palette,
    ITERM_OT_swap_colors,
    ITERM_OT_export_theme_xml,
    ITERM_OT_search_themes,
    ITERM_OT_preview_swatches,
    ITERM_OT_reset_theme,
    ITERM_UL_theme_list,
)


def _get_palette_items(self, context):
    """Generate enum items for the swap dropdowns from current palette."""
    items = []
    wm = context.window_manager
    for i, item in enumerate(wm.iterm_palette):
        items.append((str(i), item.label, "", i))
    if not items:
        items.append(('0', "None", "", 0))
    return items


def _on_theme_active_update(self, context):
    """Live-preview callback: apply theme when list selection changes."""
    try:
        addon_prefs = context.preferences.addons[__package__].preferences
        if not addon_prefs.live_preview:
            return
    except (KeyError, AttributeError):
        return

    wm = context.window_manager

    # Snapshot the user's original theme on first preview
    if "_iterm_theme_snapshot" not in wm:
        _snapshot_current_theme(wm)

    idx = wm.iterm_theme_active
    if idx < 0 or idx >= len(wm.iterm_themes):
        return

    theme_item = wm.iterm_themes[idx]

    try:
        from . import iterm_parser, blender_theme_map, apply

        iterm_theme = iterm_parser.parse_theme_file(theme_item.path)
        palette = blender_theme_map.build_palette(iterm_theme)
        apply.apply_theme_to_blender(palette)
        # No XML export, no save — just a visual preview
    except Exception:
        pass  # Silently skip broken themes during browsing


def _on_theme_search_update(self, context):
    """Live-filter the theme list as the user types."""
    from . import repo

    wm = context.window_manager
    query = wm.iterm_theme_search

    all_themes = repo.get_theme_list()
    filtered = repo.search_themes(query, all_themes)

    wm.iterm_themes.clear()
    for t in filtered:
        item = wm.iterm_themes.add()
        item.name = t["name"]
        item.path = t["path"]

    wm.iterm_theme_count = len(wm.iterm_themes)


def register():
    from . import prefs

    for cls in classes:
        bpy.utils.register_class(cls)

    prefs.register()

    # Theme list
    bpy.types.WindowManager.iterm_themes = CollectionProperty(type=ITERM_ThemeItem)
    bpy.types.WindowManager.iterm_theme_active = IntProperty(
        default=0,
        update=_on_theme_active_update,
    )
    bpy.types.WindowManager.iterm_theme_search = StringProperty(
        name="Search", default="",
        description="Filter themes by name (fuzzy match)",
        update=_on_theme_search_update,
    )
    bpy.types.WindowManager.iterm_theme_count = IntProperty(default=0)

    # Palette editor
    bpy.types.WindowManager.iterm_palette = CollectionProperty(type=ITERM_PaletteColor)
    bpy.types.WindowManager.iterm_palette_loaded = BoolProperty(default=False)
    bpy.types.WindowManager.iterm_palette_theme_name = StringProperty(default="")
    bpy.types.WindowManager.iterm_palette_swap_a = IntProperty(
        name="Slot A", default=0, min=0, max=19,
        description="First color slot to swap",
    )
    bpy.types.WindowManager.iterm_palette_swap_b = IntProperty(
        name="Slot B", default=1, min=0, max=19,
        description="Second color slot to swap",
    )


def unregister():
    from . import prefs

    del bpy.types.WindowManager.iterm_palette_swap_b
    del bpy.types.WindowManager.iterm_palette_swap_a
    del bpy.types.WindowManager.iterm_palette_theme_name
    del bpy.types.WindowManager.iterm_palette_loaded
    del bpy.types.WindowManager.iterm_palette

    del bpy.types.WindowManager.iterm_theme_count
    del bpy.types.WindowManager.iterm_theme_search
    del bpy.types.WindowManager.iterm_theme_active
    del bpy.types.WindowManager.iterm_themes

    prefs.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
