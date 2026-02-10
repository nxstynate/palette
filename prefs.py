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


def register():
    bpy.utils.register_class(ItermThemeImporterPrefs)


def unregister():
    bpy.utils.unregister_class(ItermThemeImporterPrefs)
