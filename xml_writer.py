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
