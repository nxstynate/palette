"""
Add-on preferences for the Palette.
"""

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty


class ItermThemeImporterPrefs(bpy.types.AddonPreferences):
    bl_idname = "palette"

    source_mode: EnumProperty(
        name="Source Mode",
        description="Where to load themes from",
        items=[
            ('REMOTE', "Remote Repositories", "Download from public Git repositories"),
            ('LOCAL', "Local Folder", "Load from a local folder of theme files"),
        ],
        default='REMOTE',
    )

    # Source toggles
    source_iterm: BoolProperty(
        name="iTerm2-Color-Schemes",
        description="~250 schemes from the iTerm2-Color-Schemes repository",
        default=True,
    )
    source_gogh: BoolProperty(
        name="Gogh",
        description="~240 schemes from the Gogh terminal themes repository",
        default=True,
    )

    local_folder: StringProperty(
        name="Local Folder",
        description="Path to a folder containing theme files (.itermcolors, .yml, .yaml)",
        default="",
        subtype='DIR_PATH',
    )

    save_on_apply: BoolProperty(
        name="Save Preferences on Apply",
        description="Automatically save user preferences when applying a theme",
        default=False,
    )

    export_xml: BoolProperty(
        name="Export XML on Apply",
        description="Also export a Blender theme XML file when applying",
        default=False,
    )

    live_preview: BoolProperty(
        name="Live Preview",
        description="Preview themes instantly when clicking in the list (no disk writes)",
        default=True,
    )

    def get_enabled_sources(self):
        """Return list of enabled source keys."""
        sources = []
        if self.source_iterm:
            sources.append("iterm")
        if self.source_gogh:
            sources.append("gogh")
        return sources

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        layout.prop(self, "source_mode")

        if self.source_mode == 'REMOTE':
            box = layout.box()
            box.label(text="Scheme Sources:", icon='WORLD')
            box.prop(self, "source_iterm")
            box.prop(self, "source_gogh")
            layout.operator("iterm_theme.refresh_repo", text="Download / Refresh All", icon='IMPORT')
        else:
            layout.prop(self, "local_folder")
            layout.operator("iterm_theme.refresh_repo", text="Scan Local Folder", icon='FILE_REFRESH')

        layout.separator()
        layout.prop(self, "live_preview")
        layout.prop(self, "save_on_apply")
        layout.prop(self, "export_xml")

        # --- Theme Browser ---
        layout.separator()
        box = layout.box()
        box.label(text="Theme Browser", icon='COLOR')

        # Search
        row = box.row(align=True)
        row.prop(wm, "iterm_theme_search", text="", icon='VIEWZOOM')
        row.operator("iterm_theme.search", text="", icon='VIEWZOOM')

        # Theme list
        row = box.row()
        row.template_list(
            "ITERM_UL_theme_list", "",
            wm, "iterm_themes",
            wm, "iterm_theme_active",
            rows=12,
        )

        # Theme count
        if wm.iterm_themes:
            box.label(text=f"{len(wm.iterm_themes)} themes available")

        # Primary actions
        col = box.column(align=True)
        col.scale_y = 1.3
        col.operator("iterm_theme.apply_theme", text="Keep Theme", icon='CHECKMARK')
        col.operator("iterm_theme.reset_theme", text="Reset to Initial Theme", icon='LOOP_BACK')

        row = box.row(align=True)
        row.operator("iterm_theme.load_palette", text="Edit Colors", icon='BRUSHES_ALL')
        row.operator("iterm_theme.export_xml", text="Export XML", icon='EXPORT')

        box.operator("iterm_theme.refresh_repo", text="Refresh List", icon='FILE_REFRESH')

        # --- Palette Editor ---
        if wm.iterm_palette_loaded:
            layout.separator()
            pbox = layout.box()
            pbox.label(text=f"Palette Editor — {wm.iterm_palette_theme_name}", icon='BRUSHES_ALL')

            for i, item in enumerate(wm.iterm_palette):
                row = pbox.row(align=True)
                row.label(text=item.label)
                row.prop(item, "color", text="")
                row.prop(item, "hex_value", text="")

            pbox.separator()

            # Swap
            sbox = pbox.box()
            sbox.label(text="Swap Colors", icon='UV_SYNC_SELECT')
            row = sbox.row(align=True)
            row.prop(wm, "iterm_palette_swap_a", text="Slot A")
            row.prop(wm, "iterm_palette_swap_b", text="Slot B")
            sbox.operator("iterm_theme.swap_colors", text="Swap", icon='UV_SYNC_SELECT')

            pbox.separator()

            col = pbox.column(align=True)
            col.scale_y = 1.4
            col.operator("iterm_theme.apply_custom", text="Apply Custom Palette", icon='CHECKMARK')

            pbox.operator("iterm_theme.reset_palette", text="Reset to Original", icon='LOOP_BACK')


def register():
    bpy.utils.register_class(ItermThemeImporterPrefs)


def unregister():
    bpy.utils.unregister_class(ItermThemeImporterPrefs)
