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
Parse color scheme files from multiple sources and normalize to a common format.

Supported formats:
  - .itermcolors (Apple plist) — iTerm2-Color-Schemes repo
  - .yml (Gogh YAML)          — Gogh terminal themes
  - .yaml (base16 YAML)       — base16 schemes

All parsers output the same normalized dict:
    name: str
    path: str
    source: str ("iterm", "gogh", "base16")
    ansi: list of 16 RGB tuples (float 0-1)
    bg: RGB tuple
    fg: RGB tuple
    cursor: RGB tuple or None
    cursor_text: RGB tuple or None
    selection: RGB tuple or None
    selected_text: RGB tuple or None
    bold: RGB tuple or None
"""

import plistlib
import os
from pathlib import Path


# =========================================================================
# Hex helpers
# =========================================================================

def _hex_to_rgb(hexstr):
    """Convert '#RRGGBB' or 'RRGGBB' to (r, g, b) floats 0-1."""
    h = hexstr.strip().lstrip('#')
    if len(h) == 6:
        try:
            return (
                int(h[0:2], 16) / 255.0,
                int(h[2:4], 16) / 255.0,
                int(h[4:6], 16) / 255.0,
            )
        except ValueError:
            return None
    return None


# =========================================================================
# iTerm (.itermcolors) parser
# =========================================================================

ANSI_KEYS = [f"Ansi {i} Color" for i in range(16)]


def _extract_rgb(color_dict):
    """Extract RGB floats from an iTerm color dict."""
    r = float(color_dict.get("Red Component", 0.0))
    g = float(color_dict.get("Green Component", 0.0))
    b = float(color_dict.get("Blue Component", 0.0))
    return (
        max(0.0, min(1.0, r)),
        max(0.0, min(1.0, g)),
        max(0.0, min(1.0, b)),
    )


def parse_itermcolors(filepath):
    """Parse an .itermcolors (plist) file."""
    filepath = Path(filepath)
    with open(filepath, "rb") as f:
        plist = plistlib.load(f)

    theme = {
        "name": filepath.stem,
        "path": str(filepath),
        "source": "iterm",
        "ansi": [],
    }

    for key in ANSI_KEYS:
        if key in plist:
            theme["ansi"].append(_extract_rgb(plist[key]))
        else:
            theme["ansi"].append(None)

    _fill_missing_ansi(theme)

    theme["bg"] = _extract_rgb(plist["Background Color"]) if "Background Color" in plist else theme["ansi"][0]
    theme["fg"] = _extract_rgb(plist["Foreground Color"]) if "Foreground Color" in plist else theme["ansi"][7]

    for extra, key in [
        ("cursor", "Cursor Color"),
        ("cursor_text", "Cursor Text Color"),
        ("selection", "Selection Color"),
        ("selected_text", "Selected Text Color"),
        ("bold", "Bold Color"),
    ]:
        theme[extra] = _extract_rgb(plist[key]) if key in plist else None

    return theme


# =========================================================================
# Gogh YAML parser
# =========================================================================

def _parse_yaml_simple(text):
    """
    Minimal YAML parser for flat or single-nested key-value files.
    Handles: key: 'value', key: "value", key: value, and # comments.
    For nested keys like 'palette:', flattens one level deep.
    Returns dict of string key -> string value.
    """
    result = {}
    in_section = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped == '---':
            continue
        if ':' not in stripped:
            continue

        # Check indentation — if indented, treat as nested under current section
        indent = len(line) - len(line.lstrip())

        key, _, val = stripped.partition(':')
        key = key.strip()
        val = val.strip()

        # Strip quotes
        if val and val[0] in ("'", '"'):
            quote = val[0]
            end = val.find(quote, 1)
            if end > 0:
                val = val[1:end]
        else:
            comment_pos = val.find('#')
            if comment_pos > 0:
                val = val[:comment_pos].strip()

        if indent == 0 or (indent <= 2 and not in_section):
            if val == '' or val == '':
                # This is a section header like "palette:"
                in_section = key
            else:
                in_section = None
                result[key] = val
        else:
            # Nested key — store directly (flattened)
            result[key] = val

    return result


def parse_gogh_yaml(filepath):
    """
    Parse a Gogh YAML theme file.

    Gogh format:
        color_01 - color_08: ANSI 0-7 (normal)
        color_09 - color_16: ANSI 8-15 (bright)
        background: bg hex
        foreground: fg hex
        cursor: cursor hex (optional)
    """
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        data = _parse_yaml_simple(f.read())

    theme_name = data.get("name", filepath.stem)

    theme = {
        "name": theme_name,
        "path": str(filepath),
        "source": "gogh",
        "ansi": [],
    }

    for i in range(16):
        key = f"color_{i+1:02d}"
        hexval = data.get(key, "")
        rgb = _hex_to_rgb(hexval)
        theme["ansi"].append(rgb)

    _fill_missing_ansi(theme)

    bg_hex = data.get("background", "")
    fg_hex = data.get("foreground", "")
    cursor_hex = data.get("cursor", "")

    theme["bg"] = _hex_to_rgb(bg_hex) or theme["ansi"][0]
    theme["fg"] = _hex_to_rgb(fg_hex) or theme["ansi"][7]
    theme["cursor"] = _hex_to_rgb(cursor_hex) if cursor_hex else None
    theme["cursor_text"] = None
    theme["selection"] = None
    theme["selected_text"] = None
    theme["bold"] = None

    return theme


# =========================================================================
# base16 YAML parser
# =========================================================================

def parse_base16_yaml(filepath):
    """
    Parse a base16 YAML scheme file.

    base16 mapping to ANSI:
        base00 = bg / ANSI 0       base08 = red / ANSI 1, 9
        base01 = lighter bg        base09 = orange / ANSI 3
        base02 = selection / ANSI 8 base0A = yellow / ANSI 11
        base03 = comments          base0B = green / ANSI 2, 10
        base04 = dark fg           base0C = cyan / ANSI 6, 14
        base05 = fg / ANSI 7       base0D = blue / ANSI 4, 12
        base06 = light fg          base0E = magenta / ANSI 5, 13
        base07 = ANSI 15           base0F = brown
    """
    filepath = Path(filepath)
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        data = _parse_yaml_simple(f.read())

    theme_name = data.get("scheme", data.get("name", filepath.stem))

    bases = {}
    for i in range(16):
        key = f"base{i:02X}"
        hexval = data.get(key, "")
        if hexval and not hexval.startswith('#'):
            hexval = '#' + hexval
        bases[key] = _hex_to_rgb(hexval)

    ansi = [
        bases.get("base00"),  #  0 Black
        bases.get("base08"),  #  1 Red
        bases.get("base0B"),  #  2 Green
        bases.get("base09"),  #  3 Yellow
        bases.get("base0D"),  #  4 Blue
        bases.get("base0E"),  #  5 Magenta
        bases.get("base0C"),  #  6 Cyan
        bases.get("base05"),  #  7 White
        bases.get("base02"),  #  8 Bright Black
        bases.get("base08"),  #  9 Bright Red
        bases.get("base0B"),  # 10 Bright Green
        bases.get("base0A"),  # 11 Bright Yellow
        bases.get("base0D"),  # 12 Bright Blue
        bases.get("base0E"),  # 13 Bright Magenta
        bases.get("base0C"),  # 14 Bright Cyan
        bases.get("base07"),  # 15 Bright White
    ]

    theme = {
        "name": theme_name,
        "path": str(filepath),
        "source": "base16",
        "ansi": ansi,
    }
    _fill_missing_ansi(theme)

    theme["bg"] = bases.get("base00") or theme["ansi"][0]
    theme["fg"] = bases.get("base05") or theme["ansi"][7]
    theme["cursor"] = bases.get("base06")
    theme["cursor_text"] = bases.get("base00")
    theme["selection"] = bases.get("base02")
    theme["selected_text"] = bases.get("base06")
    theme["bold"] = None

    return theme


# =========================================================================
# Unified parser — dispatch by file extension
# =========================================================================

def parse_theme_file(filepath):
    """Auto-detect format and parse any supported theme file."""
    filepath = Path(filepath)
    ext = filepath.suffix.lower()

    if ext == ".itermcolors":
        return parse_itermcolors(filepath)
    elif ext in (".yml", ".yaml"):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(2000)
        if "color_01:" in content or "color_02:" in content:
            return parse_gogh_yaml(filepath)
        elif "base00:" in content or "base00 :" in content:
            return parse_base16_yaml(filepath)
        elif "palette:" in content and ("base0" in content or "base1" in content):
            return parse_base16_yaml(filepath)
        else:
            try:
                return parse_gogh_yaml(filepath)
            except Exception:
                return parse_base16_yaml(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


# =========================================================================
# Defaults and scanning
# =========================================================================

def _fill_missing_ansi(theme):
    """Fill missing ANSI colors with reasonable defaults."""
    defaults = [
        (0.0, 0.0, 0.0),       # 0  black
        (0.8, 0.0, 0.0),       # 1  red
        (0.0, 0.8, 0.0),       # 2  green
        (0.8, 0.8, 0.0),       # 3  yellow
        (0.0, 0.0, 0.8),       # 4  blue
        (0.8, 0.0, 0.8),       # 5  magenta
        (0.0, 0.8, 0.8),       # 6  cyan
        (0.75, 0.75, 0.75),    # 7  white
        (0.5, 0.5, 0.5),       # 8  bright black
        (1.0, 0.0, 0.0),       # 9  bright red
        (0.0, 1.0, 0.0),       # 10 bright green
        (1.0, 1.0, 0.0),       # 11 bright yellow
        (0.0, 0.0, 1.0),       # 12 bright blue
        (1.0, 0.0, 1.0),       # 13 bright magenta
        (0.0, 1.0, 1.0),       # 14 bright cyan
        (1.0, 1.0, 1.0),       # 15 bright white
    ]
    for i in range(16):
        if theme["ansi"][i] is None:
            theme["ansi"][i] = defaults[i]


SUPPORTED_EXTENSIONS = {".itermcolors", ".yml", ".yaml"}


def scan_folder(folder_path):
    """
    Scan a folder for supported theme files and return a list of
    (name, filepath) tuples, sorted by name. Deduplicates by name.
    """
    folder = Path(folder_path)
    themes = []
    if not folder.is_dir():
        return themes

    seen_names = set()

    def _scan_dir(d, depth=0):
        if depth > 2:
            return
        try:
            entries = sorted(d.iterdir(), key=lambda x: x.name.lower())
        except PermissionError:
            return
        for f in entries:
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                name = f.stem
                if name.lower() not in seen_names:
                    themes.append((name, str(f)))
                    seen_names.add(name.lower())
            elif f.is_dir() and depth < 2:
                _scan_dir(f, depth + 1)

    _scan_dir(folder)
    themes.sort(key=lambda x: x[0].lower())
    return themes
