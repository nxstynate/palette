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
Curated list of popular terminal color schemes.

This list is used to surface well-known themes at the top of the browser.
Update yearly or as needed. Names are matched case-insensitively against
theme names in the loaded list. Partial matching is used — a theme name
only needs to CONTAIN one of these strings to be considered popular.

Last updated: February 2025
"""

# Ordered roughly by community recognition / GitHub stars / usage.
# Each entry is a lowercase substring that will be matched against theme names.
POPULAR_THEMES = [
    # Tier 1 — universally recognized
    "dracula",
    "nord",
    "gruvbox",
    "solarized",
    "monokai",
    "catppuccin",
    "one dark",
    "onedark",
    "tokyo night",
    "tokyonight",

    # Tier 2 — widely used
    "rose pine",
    "rosé pine",
    "material",
    "zenburn",
    "tomorrow night",
    "base16",
    "ayu",
    "everforest",
    "kanagawa",
    "nightfox",
    "night owl",
    "palenight",
    "synthwave",
    "cyberpunk",

    # Tier 3 — well-known classics
    "tango",
    "cobalt",
    "github",
    "atom",
    "vs code",
    "vscode",
    "ubuntu",
    "horizon",
    "spacegray",
    "snazzy",
    "papercolor",
    "iceberg",
    "jellybeans",
    "badwolf",
    "apprentice",
    "afterglow",
    "argonaut",
    "challenger deep",
    "doom one",
    "falcon",
    "flat",
    "homebrew",
    "hybrid",
    "ir black",
    "oceanic",
    "one half",
    "onehalf",
    "pencil",
    "panda",
    "predawn",
    "selenized",
    "tender",
    "terminal basic",
    "wombat",
]


def is_popular(theme_name):
    """Check if a theme name matches any popular theme."""
    name_lower = theme_name.lower()
    return any(pop in name_lower for pop in POPULAR_THEMES)
