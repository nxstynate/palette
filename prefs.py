# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 NXSTYNATE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Add-on preferences for the Palette.
"""

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty


class ItermThemeImporterPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    # --- Foldable section states ---
    show_browser: BoolProperty(
        name="Theme Browser",
        default=True,
    )
    show_palette_editor: BoolProperty(
        name="Palette Editor",
        default=False,
    )
    show_settings: BoolProperty(
        name="Settings",
        default=False,
    )

    # --- Source config ---
    source_mode: EnumProperty(
        name="Source Mode",
        description="Where to load themes from",
        items=[
            ('REMOTE', "Remote Repositories", "Download from public Git repositories"),
            ('LOCAL', "Local Folder", "Load from a local folder of theme files"),
        ],
        default='REMOTE',
    )

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

    # --- Behavior ---
    save_on_apply: BoolProperty(
        name="Save Preferences on Apply",
        description="Automatically save user preferences when applying a theme",
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

    # ------------------------------------------------------------------
    # Section header helper
    # ------------------------------------------------------------------
    def _draw_section_header(self, layout, prop_name, label, icon):
        """Draw a foldable section header. Returns the box to draw into,
        or None if the section is collapsed."""
        is_open = getattr(self, prop_name)
        box = layout.box()
        row = box.row()
        row.alignment = 'LEFT'
        row.prop(
            self, prop_name,
            icon='TRIA_DOWN' if is_open else 'TRIA_RIGHT',
            text=label,
            emboss=False,
            icon_only=False,
        )
        # Put the section icon on the right side of the header
        sub = row.row()
        sub.alignment = 'RIGHT'
        sub.label(icon=icon)
        if is_open:
            return box
        return None

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # ==============================================================
        # 1. THEME BROWSER
        # ==============================================================
        box = self._draw_section_header(layout, "show_browser", "Theme Browser", 'COLOR')

        if box is not None:
            # Empty state — guide the user
            if not wm.iterm_themes:
                col = box.column(align=True)
                col.scale_y = 1.0
                col.label(text="No themes loaded yet.", icon='INFO')
                col.label(text="Press the button below to get started.")
                col.separator()

            # Load button — first thing the user sees
            box.operator("iterm_theme.refresh_repo", text="Load Themes", icon='IMPORT')

            # Only show browser controls when themes are loaded
            if wm.iterm_themes:
                # Search + Sort on one row
                row = box.row(align=True)
                row.prop(wm, "iterm_theme_search", text="", icon='VIEWZOOM')
                row.prop(wm, "iterm_theme_sort", text="")

                # Theme list
                box.template_list(
                    "ITERM_UL_theme_list", "",
                    wm, "iterm_themes",
                    wm, "iterm_theme_active",
                    rows=12,
                )

                box.label(text=f"{len(wm.iterm_themes)} themes available")

                # Primary actions
                row = box.row(align=True)
                row.scale_y = 1.3
                row.operator("iterm_theme.apply_theme", text="Apply", icon='CHECKMARK')
                row.operator("preferences.reset_default_theme", text="Reset", icon='LOOP_BACK')

                # Save reminder
                box.separator()
                note = box.row()
                note.alignment = 'CENTER'
                note.label(text="Save your preferences to keep the theme after restart.", icon='FILE_TICK')

        # ==============================================================
        # 1.1 PALETTE EDITOR
        # ==============================================================
        box = self._draw_section_header(layout, "show_palette_editor", "Palette Editor", 'BRUSHES_ALL')

        if box is not None:
            if wm.iterm_palette_loaded:
                box.label(text=f"Editing: {wm.iterm_palette_theme_name}")
                box.separator()

                for i, item in enumerate(wm.iterm_palette):
                    row = box.row(align=True)
                    row.label(text=item.label)
                    row.prop(item, "color", text="")
                    row.prop(item, "hex_value", text="")

                box.separator()

                # Swap
                sbox = box.box()
                sbox.label(text="Swap Colors", icon='UV_SYNC_SELECT')
                row = sbox.row(align=True)
                row.prop(wm, "iterm_palette_swap_a", text="Slot A")
                row.prop(wm, "iterm_palette_swap_b", text="Slot B")
                sbox.operator("iterm_theme.swap_colors", text="Swap", icon='UV_SYNC_SELECT')

                box.separator()

                col = box.column(align=True)
                col.scale_y = 1.3
                col.operator("iterm_theme.apply_custom", text="Apply Custom Palette", icon='CHECKMARK')

                box.operator("iterm_theme.reset_palette", text="Reset to Original", icon='LOOP_BACK')
            else:
                box.label(text="Select a theme and load its palette to edit.")
                box.operator("iterm_theme.load_palette", text="Edit Colors", icon='BRUSHES_ALL')

        # ==============================================================
        # 1.2 SETTINGS
        # ==============================================================
        box = self._draw_section_header(layout, "show_settings", "Settings", 'PREFERENCES')

        if box is not None:
            # Preview
            box.prop(self, "live_preview")

            # On-apply behavior
            box.separator()
            box.label(text="On Apply:")
            box.prop(self, "save_on_apply")

            # Export
            box.separator()
            box.operator("iterm_theme.export_xml", text="Export Theme XML", icon='EXPORT')

            # Theme sources
            box.separator()
            box.label(text="Theme Sources:", icon='WORLD')
            box.prop(self, "source_mode", text="")

            if self.source_mode == 'REMOTE':
                row = box.row(align=True)
                row.prop(self, "source_iterm", toggle=True)
                row.prop(self, "source_gogh", toggle=True)
            else:
                box.prop(self, "local_folder", text="")

        # ==============================================================
        # ATTRIBUTION
        # ==============================================================
        layout.separator()
        attrib = layout.row()
        attrib.alignment = 'CENTER'
        attrib.label(
            text="Themes sourced from iTerm2 and Gogh repositories."
                 " Themes are not made by NXSTYNATE"
        )


def register():
    bpy.utils.register_class(ItermThemeImporterPrefs)


def unregister():
    bpy.utils.unregister_class(ItermThemeImporterPrefs)
