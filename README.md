# Palette

<p align="center">
  <img src="assets/graphic.png" alt="palette" width="720">
</p>

`palette` is a Blender add-on that applies terminal color schemes as Blender UI themes.

Have access to over 600 themes!!!

It loads ANSI-style palettes from existing terminal theme repositories, maps them to Blender’s theme system, and applies them immediately for preview or export.

---

## Features

- Load terminal color schemes from public repositories
- Support for iTerm2 (`.itermcolors`) and Gogh (`.yml`, `.yaml`) formats
- Live theme preview
- Theme search and filtering
- Palette editing (ANSI colors + UI colors)
- Swap palette entries
- Reset to original palette
- Export Blender theme XML files
- Local folder support for custom themes

---

## Installation

1. Download the add-on zip.
2. In Blender: **Edit → Preferences → Add-ons → Install**
3. Select the zip and enable `palette`.

---

## Location

Open: **Edit → Preferences → Themes**

The `palette` panel appears inside the Themes preferences.

---

## Usage

1. Click **Download / Refresh** to fetch theme repositories.
2. Select a theme to preview it immediately.
3. Use search to filter themes.
4. Click **Keep Theme** to apply the theme permanently.

---

## Palette Editor

The palette editor allows modifying theme colors before applying them.

- Load the theme’s source palette
- Edit individual colors
- Swap two palette slots
- Apply a custom palette
- Reset back to the original theme palette

Changes are applied live.

---

## Export

Themes can be exported as Blender XML files.

- Click **Export XML**
- The resulting file can be installed using Blender’s theme installer

---

## Configuration

Add-on preferences allow configuring:

- Theme source mode
  - Remote repositories
  - Local folder
- Enabled repositories
- Local theme directory
- Live preview behavior
- Auto-save preferences
- Auto-export on apply

---

## How It Works

1. Theme files are loaded from repositories or a local folder
2. Color data is parsed into an ANSI-style palette
3. Blender theme values are derived from the palette
4. The generated theme is applied to the active Blender session

---

## Cache

Downloaded themes are cached in Blender’s config directory under:


