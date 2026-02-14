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
Export the current Blender theme to XML in the exact format that
Edit > Preferences > Themes > Install expects.

Uses Blender's own rna_xml.rna2xml to serialize, which guarantees
the output matches what rna_xml.xml_file_run / xml2rna can parse.
"""

import os


def export_current_theme_xml(filepath):
    """
    Serialize the active Blender theme to XML.

    Must be called from inside Blender after the theme colors have been
    applied to bpy.context.preferences.themes[0].

    Returns the filepath written.
    """
    import bpy
    from rna_xml import rna2xml

    theme = bpy.context.preferences.themes[0]

    os.makedirs(os.path.dirname(os.path.abspath(filepath)) or '.', exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        fw = f.write
        fw("<bpy>\n")
        rna2xml(
            fw,
            root_rna=theme,
            method='ATTR',
            root_ident="  ",
            ident_val="  ",
        )
        fw("</bpy>\n")

    return filepath
