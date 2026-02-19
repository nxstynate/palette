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
Repository management for downloading and caching color scheme repos.

Supports multiple sources:
  - iTerm2-Color-Schemes (default)  ~250 .itermcolors
  - Gogh                            ~240 .yml
  - base16                          ~200+ .yaml

All sources are downloaded as zip archives, extracted to separate
subdirectories, then indexed together with deduplication.
"""

import os
import json
import time
import zipfile
import io
from pathlib import Path


# =========================================================================
# Source definitions
# =========================================================================

SOURCES = {
    "iterm": {
        "name": "iTerm2-Color-Schemes",
        "url": "https://github.com/mbadolato/iTerm2-Color-Schemes/archive/refs/heads/master.zip",
        "subdir": "schemes",
        "extensions": {".itermcolors"},
    },
    "gogh": {
        "name": "Gogh",
        "url": "https://github.com/Gogh-Co/Gogh/archive/refs/heads/master.zip",
        "subdir": "themes",
        "extensions": {".yml"},
    },
}


def get_cache_dir():
    """Get the cache directory path. Creates it if needed.

    Uses Blender's extension_path_user which is the only approved
    storage location for extensions platform add-ons.
    """
    import bpy
    try:
        cache = bpy.utils.extension_path_user(__package__, path="cache", create=True)
    except Exception as ex:
        raise RuntimeError(
            f"[Palette] Could not create extension cache directory: {ex}"
        ) from ex
    return cache


def get_index_path():
    """Get the index JSON file path."""
    return os.path.join(get_cache_dir(), "theme_index.json")


def load_index():
    """Load the theme index from disk."""
    index_path = get_index_path()
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return json.load(f)
    return {"themes": [], "last_updated": 0, "sources": []}


def save_index(index_data):
    """Save the theme index to disk."""
    index_path = get_index_path()
    with open(index_path, "w") as f:
        json.dump(index_data, f, indent=2)


def index_local_folder(folder_path):
    """Scan a local folder for supported theme files and build an index."""
    from .iterm_parser import scan_folder

    themes = scan_folder(folder_path)
    index = {
        "themes": [{"name": name, "path": path, "source": "local"} for name, path in themes],
        "last_updated": time.time(),
        "sources": ["local"],
    }
    save_index(index)
    return index


def _download_and_extract(url, cache_subdir, extensions, repo_subdir=None, progress_callback=None):
    """
    Download a zip from url, extract files matching extensions
    into cache_subdir. If repo_subdir is set, only extract files
    from paths containing that directory name.
    Returns count of extracted files.
    """
    import urllib.request
    import ssl

    os.makedirs(cache_subdir, exist_ok=True)

    if progress_callback:
        progress_callback(f"Downloading from {url[:60]}...")

    try:
        context = ssl.create_default_context()
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Blender-iTerm-Theme-Importer/1.1'
        })
        response = urllib.request.urlopen(req, context=context, timeout=120)
        data = response.read()
    except ssl.SSLError:
        context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Blender-iTerm-Theme-Importer/1.1'
        })
        response = urllib.request.urlopen(req, context=context, timeout=120)
        data = response.read()

    if progress_callback:
        progress_callback("Extracting themes...")

    count = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            basename = os.path.basename(info.filename)
            _, ext = os.path.splitext(basename)
            if ext.lower() not in extensions:
                continue
            # Filter by subdir if specified (e.g. only files under "schemes/" or "base16/")
            if repo_subdir:
                # Check that the path contains the subdir segment
                parts = info.filename.replace('\\', '/').split('/')
                if repo_subdir not in parts:
                    continue
            # Skip config/template files
            if basename.lower() in ('config.yaml', 'config.yml', '.yaml', '.yml'):
                continue
            target = os.path.join(cache_subdir, basename)
            with zf.open(info) as src, open(target, 'wb') as dst:
                dst.write(src.read())
            count += 1

    return count


def download_repo(repo_url=None, progress_callback=None):
    """
    Legacy single-source download. Downloads iTerm2-Color-Schemes.
    Returns the index data dict.
    """
    if repo_url is None:
        repo_url = SOURCES["iterm"]["url"]

    cache_dir = get_cache_dir()
    schemes_dir = os.path.join(cache_dir, "schemes")

    count = _download_and_extract(
        repo_url, schemes_dir, {".itermcolors"},
        repo_subdir="schemes",
        progress_callback=progress_callback,
    )

    if progress_callback:
        progress_callback(f"Extracted {count} themes.")

    return index_local_folder(schemes_dir)


def download_sources(enabled_sources, progress_callback=None):
    """
    Download multiple sources and build a unified, deduplicated index.

    Args:
        enabled_sources: list of source keys, e.g. ["iterm", "gogh", "base16"]
        progress_callback: optional function(msg: str)

    Returns the combined index data dict.
    """
    cache_dir = get_cache_dir()
    all_themes = []
    seen_names = set()
    sources_done = []

    for source_key in enabled_sources:
        src = SOURCES.get(source_key)
        if not src:
            continue

        source_dir = os.path.join(cache_dir, source_key)

        try:
            if progress_callback:
                progress_callback(f"Downloading {src['name']}...")

            count = _download_and_extract(
                src["url"], source_dir, src["extensions"],
                repo_subdir=src.get("subdir"),
                progress_callback=progress_callback,
            )

            if progress_callback:
                progress_callback(f"{src['name']}: {count} themes extracted.")

            sources_done.append(source_key)

        except Exception as e:
            if progress_callback:
                progress_callback(f"Warning: {src['name']} failed: {e}")
            # Continue with other sources
            continue

    # Now scan all source dirs and build unified index
    from .iterm_parser import scan_folder

    for source_key in enabled_sources:
        source_dir = os.path.join(cache_dir, source_key)
        if not os.path.isdir(source_dir):
            # Try legacy "schemes" dir for iterm
            if source_key == "iterm":
                source_dir = os.path.join(cache_dir, "schemes")
                if not os.path.isdir(source_dir):
                    continue
            else:
                continue

        themes = scan_folder(source_dir)
        for name, path in themes:
            if name.lower() not in seen_names:
                all_themes.append({
                    "name": name,
                    "path": path,
                    "source": source_key,
                })
                seen_names.add(name.lower())

    all_themes.sort(key=lambda t: t["name"].lower())

    index = {
        "themes": all_themes,
        "last_updated": time.time(),
        "sources": sources_done,
    }
    save_index(index)

    if progress_callback:
        progress_callback(f"Total: {len(all_themes)} unique themes from {len(sources_done)} sources.")

    return index


def get_theme_list():
    """Get the current list of themes from the index."""
    index = load_index()
    return index.get("themes", [])


def search_themes(query, theme_list=None):
    """Filter theme list by search query (fuzzy match — characters must appear in order)."""
    if theme_list is None:
        theme_list = get_theme_list()
    if not query:
        return theme_list
    q = query.lower()

    results = []
    for t in theme_list:
        name_lower = t["name"].lower()
        # Fuzzy: each char in query must appear in order
        qi = 0
        for ch in name_lower:
            if qi < len(q) and ch == q[qi]:
                qi += 1
        if qi == len(q):
            results.append(t)

    return results
