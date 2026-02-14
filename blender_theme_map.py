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
Map an iTerm color palette into a Blender theme palette.

Design philosophy (v3 — VS Code-aligned direct mapping):
  - Surfaces use the theme's ACTUAL palette colors directly (bg, black, bright_black)
  - NOT a generated ramp — we use the real colors the theme author chose
  - VS Code pattern: most UI surfaces = bg. Only recessed/elevated differ.
  - Accent colors from ANSI blue/cyan used ONLY for focus, badges, links
  - Buttons use elevated surface (bright_black), NOT accent colored
  - Selection uses the theme's selection color directly
  - Widget states use subtle lighten/darken of bg — NOT a separate surface
  - Text contrast pre-validated against actual assigned backgrounds
  - The result should look like "this theme in VS Code" applied to Blender
"""

from . import color_math as cm


def build_palette(iterm_theme):
    ansi = iterm_theme["ansi"]
    bg = iterm_theme["bg"]
    fg = iterm_theme["fg"]
    selection = iterm_theme.get("selection")
    cursor = iterm_theme.get("cursor")

    dark = cm.is_dark(bg)

    # --- Semantic role assignments from ANSI palette ---
    # Swapped pairs for optimal Blender UI mapping:
    #   3 <-> 4:  accent_primary=yellow(3), warning=blue(4)
    #   11 <-> 12: accent_bright=bright_yellow(11), bright_yellow=bright_blue(12)
    #   5 <-> 6:  accent_secondary=magenta(5), magenta=cyan(6)
    accent_primary = ansi[3]   # yellow (swapped from 4)
    accent_bright = ansi[11]   # bright yellow (swapped from 12)
    accent_secondary = ansi[5] # magenta (swapped from 6)
    warning = ansi[4]          # blue (swapped from 3)
    danger = ansi[1]           # red
    danger_bright = ansi[9]    # bright red
    success = ansi[2]          # green
    success_bright = ansi[10]  # bright green
    magenta = ansi[6]          # cyan (swapped from 5)
    bright_magenta = ansi[13]
    bright_yellow = ansi[12]   # bright blue (swapped from 11)
    bright_cyan = ansi[14]
    black = ansi[0]
    white = ansi[15]
    bright_black = ansi[8]     # gray / elevated surface

    # =====================================================================
    # ACCENT PREPARATION — desaturate for dark mode to prevent vibration
    # =====================================================================
    if dark:
        accent_primary = cm.ok_desaturate(accent_primary, 0.04)
        accent_secondary = cm.ok_desaturate(accent_secondary, 0.04)
        danger = cm.ok_desaturate(danger, 0.03)
        warning = cm.ok_desaturate(warning, 0.03)
        success = cm.ok_desaturate(success, 0.03)
        magenta = cm.ok_desaturate(magenta, 0.03)

    # =====================================================================
    # SURFACE COLORS — direct from theme palette, VS Code style
    # =====================================================================
    # VS Code pattern: editor/sidebar/panel/activity bar ALL use bg.
    # Recessed elements (inputs, viewport) go slightly darker.
    # Elevated elements (widgets, buttons) use bright_black or subtle lift.
    # We use the theme's own colors, not synthetic ramp stops.
    #
    # The 4 surface anchors from any terminal theme:
    #   bg          = main background (editor, sidebar, panels)
    #   black       = ansi[0], often same as bg or slightly different
    #   bright_black= ansi[8], the "elevated" gray surface
    #   selection   = highlight/selection surface

    bg_L, bg_C, bg_H = cm.rgb_to_oklch(*bg)
    accent_L, accent_C, accent_H = cm.rgb_to_oklch(*accent_primary)
    bb_L, bb_C, bb_H = cm.rgb_to_oklch(*bright_black)

    # Recessed: slightly darker than bg (for inputs, viewport)
    if dark:
        recessed = cm.ok_darken(bg, 0.025)
    else:
        recessed = cm.ok_lighten(bg, 0.015)

    # Subtle lift: barely visible step above bg (for hover states, panels)
    if dark:
        subtle_lift = cm.ok_lighten(bg, 0.02)
        medium_lift = cm.ok_lighten(bg, 0.04)
    else:
        subtle_lift = cm.ok_darken(bg, 0.015)
        medium_lift = cm.ok_darken(bg, 0.03)

    # Widget/button surface: use bright_black if it's close to bg,
    # otherwise interpolate so it's not too far away
    bb_gap = abs(bb_L - bg_L)
    if bb_gap > 0.18:
        # bright_black is too far from bg, cap the distance
        if dark:
            widget_surface = cm.ok_lighten(bg, 0.09)
        else:
            widget_surface = cm.ok_darken(bg, 0.07)
    else:
        widget_surface = bright_black

    # =====================================================================
    # SURFACE ASSIGNMENTS — VS Code flat model
    # =====================================================================
    ui_bg = bg                          # editor, sidebar, activity bar, title bar
    ui_panel = bg                       # panels use bg (VS Code pattern)
    ui_card = medium_lift               # popups/cards: subtle lift
    ui_popup = medium_lift

    # Panel sub-surfaces: very subtle differences
    ui_panel_header = subtle_lift       # panel headers: barely different
    ui_panel_sub = bg                   # sub-panels: same as bg

    # Borders and separators: muted
    ui_border = cm.ok_mix(fg, bg, 0.75)
    ui_separator = cm.ok_mix(fg, bg, 0.82)
    ui_panel_outline = cm.ok_mix(fg, bg, 0.80)

    # Row alternation: subtle but visible stripe for outliner, spreadsheet
    if dark:
        row_alternate = cm.ok_lighten(bg, 0.025)
    else:
        row_alternate = cm.ok_darken(bg, 0.02)

    # =====================================================================
    # VIEWPORT GRADIENT — recessed below bg
    # =====================================================================
    viewport_gradient_low = recessed
    viewport_gradient_high = bg

    # =====================================================================
    # TEXT — OKLCH-based contrast enforcement
    # =====================================================================
    # Primary text: high contrast against base surface
    ui_text = cm.ok_ensure_contrast(fg, ui_bg, 5.0)

    # Muted: blend toward bg, then ensure minimum contrast
    ui_text_muted = cm.ok_ensure_contrast(cm.ok_mix(ui_text, ui_bg, 0.35), ui_bg, 3.0)

    # Disabled: even more blended, no minimum contrast enforced (per WCAG)
    ui_text_disabled = cm.ok_mix(ui_text, ui_bg, 0.60)

    # Highlight: must be CLEARLY brighter/bolder than ui_text.
    # This is used for titles, text_hi, header_text_hi — active/focused text.
    # On dark themes: push to near-white. On light themes: push to near-black.
    if dark:
        ui_text_highlight = cm.ok_ensure_contrast(white, ui_bg, 10.0)
    else:
        ui_text_highlight = cm.ok_ensure_contrast(black, ui_bg, 10.0)

    # Panel-specific text
    panel_text = cm.ok_ensure_contrast(fg, ui_panel, 4.5)
    panel_title = cm.ok_ensure_contrast(
        cm.ok_lighten(fg, 0.06) if dark else cm.ok_darken(fg, 0.06),
        ui_panel_header, 5.0
    )

    # =====================================================================
    # ACCENT — split into decorative (yellow) and functional (blue)
    # =====================================================================
    # ui_accent = yellow (ansi[3]) — used for indicators, items, personality
    # ui_accent_func = blue (ansi[4]) — used for selection bgs where text
    #   must be readable on top. Yellow bg + white text = poor contrast.
    #   Blue bg + white text = excellent contrast.
    ui_accent = accent_primary      # yellow — decorative
    ui_accent_func = warning        # blue (ansi[4] after swap) — functional
    # On dark themes, darken the functional accent enough for white text
    if dark:
        _func_L, _func_C, _func_H = cm.rgb_to_oklch(*ui_accent_func)
        # Target L where white text gets 4.5:1 — roughly L < 0.50
        if _func_L > 0.48:
            ui_accent_func = cm.oklch_to_rgb(0.48, _func_C, _func_H)

    # States: same hue, vary lightness only
    if dark:
        ui_accent_hover = cm.ok_lighten(ui_accent, 0.07)
        ui_accent_active = cm.ok_lighten(ui_accent, 0.12)
        ui_accent_func_hover = cm.ok_lighten(ui_accent_func, 0.07)
    else:
        ui_accent_hover = cm.ok_darken(ui_accent, 0.05)
        ui_accent_active = cm.ok_darken(ui_accent, 0.10)
        ui_accent_func_hover = cm.ok_darken(ui_accent_func, 0.05)

    # Accent text: readable on the YELLOW (decorative) accent
    white_on_accent = cm.contrast_ratio((1.0, 1.0, 1.0), ui_accent)
    black_on_accent = cm.contrast_ratio((0.0, 0.0, 0.0), ui_accent)
    if white_on_accent >= black_on_accent:
        ui_accent_text = cm.ok_ensure_contrast((1.0, 1.0, 1.0), ui_accent, 4.5)
    else:
        ui_accent_text = cm.ok_ensure_contrast((0.0, 0.0, 0.0), ui_accent, 4.5)

    # Functional accent text: must match theme's text direction
    # Dark themes = white text on blue bg, light themes = dark text on blue bg
    if dark:
        ui_accent_func_text = cm.ok_ensure_contrast(white, ui_accent_func, 4.5)
        # If white doesn't work (accent too bright), darken the functional accent
        if cm.contrast_ratio(ui_accent_func_text, ui_accent_func) < 4.5:
            ui_accent_func = cm.ok_darken(ui_accent_func, 0.10)
            ui_accent_func_text = cm.ok_ensure_contrast(white, ui_accent_func, 4.5)
    else:
        ui_accent_func_text = cm.ok_ensure_contrast(black, ui_accent_func, 4.5)

    # =====================================================================
    # SELECTION — from input or accent-derived
    # =====================================================================
    if selection:
        ui_selection = selection
    else:
        ui_selection = cm.ok_mix(ui_accent, ui_bg, 0.50)

    # Selection text: must contrast against selection bg
    # Try the theme's fg first, then fallback to white/black
    ui_selection_text = cm.ok_ensure_contrast(ui_text, ui_selection, 4.5)
    if cm.contrast_ratio(ui_selection_text, ui_selection) < 4.5:
        w_cr = cm.contrast_ratio((1.0, 1.0, 1.0), ui_selection)
        b_cr = cm.contrast_ratio((0.0, 0.0, 0.0), ui_selection)
        if w_cr >= b_cr:
            ui_selection_text = cm.ok_ensure_contrast((1.0, 1.0, 1.0), ui_selection, 4.5)
        else:
            ui_selection_text = cm.ok_ensure_contrast((0.0, 0.0, 0.0), ui_selection, 4.5)

    # =====================================================================
    # MENU & PIE HIGHLIGHTS — where the palette comes alive
    # =====================================================================
    # In VS Code, syntax highlighting shows the palette on screen.
    # In Blender, there's no syntax highlighting — so menus, pies, and
    # hover states need to carry the palette's personality.
    #
    # Each interactive element gets a SPECIFIC ANSI color assignment:
    #   pie menu item   = ansi[2] green  — selected pie slice
    #   menu_item sel   = ansi[14] bright cyan — hovered dropdown item
    #   menu item       = ansi[3] yellow (darker) — menu bar accent
    #   tab selected    = ansi[6] cyan (darker) — active tab accent
    #
    # This spreads the palette across the UI so users see multiple
    # colors during normal interaction, not just one monotone accent.

    def _make_highlight(color_raw, bright=True):
        """Create a vivid highlight from an ANSI color.
        bright=True: push lightness up for dark themes (hover/selection bg)
        bright=False: keep darker, used for accent items/indicators
        """
        hL, hC, hH = cm.rgb_to_oklch(*color_raw)
        if dark:
            if bright:
                tgt_L = max(hL, 0.78)
            else:
                tgt_L = max(hL * 0.65, 0.42)
            tgt_C = min(hC * 1.1, cm.oklch_max_chroma(tgt_L, hH))
        else:
            if bright:
                tgt_L = min(hL, 0.72)
            else:
                tgt_L = min(hL * 0.75, 0.50)
            tgt_C = min(hC * 0.95, cm.oklch_max_chroma(tgt_L, hH))
        tgt_C = max(tgt_C, 0.06)
        return cm.oklch_to_rgb(tgt_L, tgt_C, hH)

    def _text_on(bg_color):
        """Choose black or white text with 5:1 contrast on bg_color."""
        w = cm.contrast_ratio((1.0, 1.0, 1.0), bg_color)
        b = cm.contrast_ratio((0.0, 0.0, 0.0), bg_color)
        if b >= w:
            return cm.ok_ensure_contrast((0.0, 0.0, 0.0), bg_color, 5.0)
        else:
            return cm.ok_ensure_contrast((1.0, 1.0, 1.0), bg_color, 5.0)

    # --- PIE MENU: item = ansi[2] green — the accent/indicator element ---
    pie_item = ansi[2]  # direct from palette, no modification
    # pie inner_sel (selected slice background): brightened green
    pie_highlight = _make_highlight(ansi[2], bright=True)
    pie_highlight_text = _text_on(pie_highlight)

    # --- MENU ITEM selected: text_sel = ansi[14] bright cyan direct ---
    # Dark themes: color shows as highlighted TEXT on subtle dark bg
    # Light themes: color shows as highlighted BG with dark text
    menu_item_sel = ansi[14]
    menu_item_sel_text = _text_on(menu_item_sel)
    if dark:
        menu_item_sel_bg = cm.ok_lighten(ui_popup, 0.03)
        # Ensure the colored text has enough contrast on hover bg
        _sel_cr = cm.contrast_ratio(menu_item_sel, menu_item_sel_bg)
        if _sel_cr < 4.5:
            menu_item_sel_bg = cm.ok_darken(ui_popup, 0.02)
        # For dark themes: text_sel = colored, inner_sel = subtle bg
        menu_text_sel = menu_item_sel
        menu_inner_sel = menu_item_sel_bg
    else:
        # For light themes: inner_sel = colored bg, text_sel = dark text on it
        menu_inner_sel = menu_item_sel
        menu_text_sel = menu_item_sel_text
        menu_item_sel_bg = menu_item_sel  # same as inner_sel for light

    # --- MENU accent (item color): ansi[3] yellow, darker value ---
    menu_accent = _make_highlight(ansi[3], bright=False)

    # --- TAB selected: inner_sel = ansi[6] cyan, darker value ---
    tab_sel_accent = _make_highlight(ansi[6], bright=False)
    tab_sel_text = _text_on(tab_sel_accent)

    # --- Menu highlight (menu bar hover, pulldown): same as menu_item_sel ---
    menu_highlight = menu_item_sel
    menu_highlight_text = menu_item_sel_text

    # List item highlight for outliner, file browser.
    # The highlight bg must be visibly tinted with accent color AND
    # keep text highly readable.
    if dark:
        # Tinted selection bg — mix accent into bg, keep it dark enough
        # for white text to read well (target L < 0.40)
        list_highlight = cm.ok_mix(accent_primary, ui_bg, 0.75)
        _lh_L, _lh_C, _lh_H = cm.rgb_to_oklch(*list_highlight)
        # If too bright for white text, darken it
        if _lh_L > 0.38:
            list_highlight = cm.oklch_to_rgb(0.38, _lh_C, _lh_H)
        # Ensure it's noticeably different from ui_bg
        _bg_L, _, _ = cm.rgb_to_oklch(*ui_bg)
        _lh_L2, _, _ = cm.rgb_to_oklch(*list_highlight)
        if abs(_lh_L2 - _bg_L) < 0.04:
            list_highlight = cm.ok_lighten(list_highlight, 0.05)
        # White text for max readability
        list_highlight_text = cm.ok_ensure_contrast(white, list_highlight, 5.0)
    else:
        list_highlight = cm.ok_mix(accent_primary, ui_bg, 0.75)
        _lh_L, _lh_C, _lh_H = cm.rgb_to_oklch(*list_highlight)
        if _lh_L < 0.70:
            list_highlight = cm.oklch_to_rgb(0.70, _lh_C, _lh_H)
        _bg_L, _, _ = cm.rgb_to_oklch(*ui_bg)
        _lh_L2, _, _ = cm.rgb_to_oklch(*list_highlight)
        if abs(_lh_L2 - _bg_L) < 0.04:
            list_highlight = cm.ok_darken(list_highlight, 0.05)
        list_highlight_text = cm.ok_ensure_contrast(black, list_highlight, 5.0)

    # =====================================================================
    # WIDGETS — VS Code style: widget surfaces close to bg
    # =====================================================================
    # In VS Code, dropdowns/inputs use a slightly different bg.
    # Widget states are subtle: hover = tiny lighten, active = selection-ish
    widget_bg = widget_surface
    if dark:
        widget_hover = cm.ok_lighten(widget_surface, 0.025)
        widget_active = cm.ok_lighten(widget_surface, 0.045)
    else:
        widget_hover = cm.ok_darken(widget_surface, 0.02)
        widget_active = cm.ok_darken(widget_surface, 0.035)
    widget_outline = cm.ok_mix(fg, bg, 0.70)

    # Widget text: must contrast against the LIGHTEST widget state (active)
    widget_text = cm.ok_ensure_contrast(ui_text, widget_active, 4.5)

    # =====================================================================
    # CHECKMARK & WIDGET ITEMS — must be BRIGHT on dark themes
    # =====================================================================
    # These sit ON TOP of dark backgrounds as indicators (ticks, slider
    # fills, radio dots). They must be vivid and high-contrast.

    # Checkmark/tick: bright white on dark themes for max visibility
    if dark:
        option_check = cm.ok_ensure_contrast(white, ui_accent_func, 5.0)
        if cm.contrast_ratio(option_check, widget_bg) < 4.0:
            option_check = cm.ok_ensure_contrast(white, widget_bg, 5.0)
    else:
        option_check = cm.ok_ensure_contrast(black, ui_accent_func, 5.0)
        if cm.contrast_ratio(option_check, widget_bg) < 4.0:
            option_check = cm.ok_ensure_contrast(black, widget_bg, 5.0)

    # Widget item: bright accent for slider fills, indicators
    if dark:
        widget_item = cm.ok_ensure_contrast(accent_bright, widget_bg, 3.5)
        if cm.contrast_ratio(widget_item, widget_bg) < 3.0:
            widget_item = cm.ok_ensure_contrast(white, widget_bg, 4.0)
    else:
        widget_item = cm.ok_ensure_contrast(accent_primary, widget_bg, 3.5)
        if cm.contrast_ratio(widget_item, widget_bg) < 3.0:
            widget_item = cm.ok_ensure_contrast(black, widget_bg, 4.0)

    # =====================================================================
    # BUTTONS — VS Code style: use elevated surface, NOT accent colored
    # =====================================================================
    # VS Code Nord uses nord2/nord3 for buttons, NOT the accent color.
    # Buttons are just slightly more prominent surfaces.
    button_bg = widget_surface
    if dark:
        button_hover = cm.ok_lighten(widget_surface, 0.03)
    else:
        button_hover = cm.ok_darken(widget_surface, 0.025)

    button_text = cm.ok_ensure_contrast(ui_text, button_bg, 4.5)
    button_text_hi = cm.ok_ensure_contrast(ui_text_highlight, button_hover, 5.0)

    # =====================================================================
    # TOOLBAR — between bg and widget surface
    # =====================================================================
    toolbar_bg = medium_lift
    toolbar_sel = cm.ok_mix(widget_active, accent_primary, 0.12)

    toolbar_text = cm.ok_ensure_contrast(ui_text, toolbar_bg, 4.5)

    # =====================================================================
    # INPUT FIELDS — recessed (VS Code: slightly different from bg)
    # =====================================================================
    input_bg = recessed
    input_border = cm.ok_mix(fg, bg, 0.70)

    input_text = cm.ok_ensure_contrast(ui_text, input_bg, 5.0)

    # =====================================================================
    # SCROLL — muted
    # =====================================================================
    scroll_bg = bg
    scroll_handle = cm.ok_mix(fg, bg, 0.65)
    scroll_handle_hover = cm.ok_mix(fg, bg, 0.50)

    # =====================================================================
    # HEADER — same as bg (VS Code pattern: headers = bg)
    # =====================================================================
    header_bg = recessed
    header_text = cm.ok_ensure_contrast(ui_text, header_bg, 5.0)

    # =====================================================================
    # TABS — active = bg, inactive = slightly different
    # =====================================================================
    tab_active_bg = ui_bg
    tab_inactive_bg = recessed
    tab_outline = ui_border

    # =====================================================================
    # CURSOR & TEXT SELECTION
    # =====================================================================
    # The cursor LINE should be visible (bright) against input backgrounds.
    # But Blender also uses the wcol_text 'item' field as the in-field
    # text selection highlight — so it must contrast with the text color.
    # Solution: use the functional accent (blue) for the selection highlight
    # in widget text fields, and a bright color for the actual cursor line.
    ui_cursor_line = cursor if cursor else accent_bright  # visible cursor line
    # For wcol_text item (text selection highlight): use functional blue
    ui_text_sel_highlight = ui_accent_func
    # Widget_text_cursor (the blinking cursor line in preferences): bright
    ui_cursor = ui_cursor_line

    # =====================================================================
    # 3D VIEWPORT ELEMENTS
    # =====================================================================
    grid_line = cm.ok_mix(ui_border, bg, 0.55)

    # Axis colors: desaturated ANSI semantic colors
    grid_axis_x = cm.ok_desaturate(danger, 0.03)
    grid_axis_y = cm.ok_desaturate(success, 0.03)
    grid_axis_z = cm.ok_desaturate(accent_secondary, 0.03)

    obj_selected = accent_bright
    # Active object needs to be CLEARLY distinct from selected.
    # Use a warm color (yellow/orange from ansi[3]) so it's a different HUE,
    # not just a lightness shift of the same blue.
    # Use RAW ansi[3] — bright_yellow can be gray in some themes (Solarized).
    _active_src = ansi[3]  # raw yellow, pre-desaturation
    _as_L, _as_C, _as_H = cm.rgb_to_oklch(*_active_src)
    _sel_L, _sel_C, _sel_H = cm.rgb_to_oklch(*accent_bright)
    # Guarantee at least 60deg hue separation from selected
    hue_gap = abs(_as_H - _sel_H)
    if hue_gap > 180:
        hue_gap = 360 - hue_gap
    if hue_gap < 60:
        # Yellow too close to accent hue — use danger (red) instead
        _active_src = ansi[1]
    if dark:
        obj_active = cm.ok_lighten(_active_src, 0.05)
    else:
        obj_active = _active_src

    # Outliner active object tint: neutral/desaturated version.
    # In the 3D viewport obj_active is vivid (yellow/orange) for visibility,
    # but in the outliner it's a row tint behind text — needs to be muted.
    if dark:
        outliner_active_obj = cm.ok_mix(fg, bg, 0.45)  # neutral mid-gray
    else:
        outliner_active_obj = cm.ok_mix(fg, bg, 0.55)
    wire_color = cm.ok_mix(fg, bg, 0.35)
    wire_edit = cm.ok_mix(accent_primary, fg, 0.25)

    vertex_color = cm.ok_lighten(accent_bright, 0.07) if dark else accent_bright
    edge_select = cm.ok_lighten(accent_primary, 0.10) if dark else accent_primary
    face_select = cm.alpha(cm.ok_mix(ui_accent, ui_bg, 0.45), 0.35)

    before_frame = cm.ok_desaturate(danger, 0.03)
    after_frame = cm.ok_desaturate(accent_secondary, 0.03)

    # Gizmo: direct ANSI semantic
    gizmo_x = danger
    gizmo_y = success
    gizmo_z = accent_primary

    # State colors: direct ANSI semantic
    info_color = accent_secondary
    warning_color = warning
    error_color = danger
    success_color = success

    # =====================================================================
    # NODE EDITOR — categorical colors via OKLCH hue rotation
    # =====================================================================
    node_bg = ui_card
    node_selected = cm.ok_mix(ui_accent, ui_bg, 0.4)
    node_frame = cm.ok_mix(ui_card, ui_bg, 0.3)

    # Determine node color parameters from the palette's character.
    # We extract a lightness and chroma target from the ANSI colors
    # so nodes feel "of the palette" while being equidistant in hue.
    if dark:
        node_L = 0.42   # visible but not glaring on dark surfaces
        node_C = 0.065   # moderate chroma — colorful but not garish
    else:
        node_L = 0.68
        node_C = 0.060

    # Generate 15 equidistant node colors.
    # Start hue at the accent hue so the first node feels related to theme.
    _node_cats = cm.generate_categorical(
        15, target_L=node_L, target_C=node_C, start_H=accent_H
    )

    # Assign to node types in a stable order.
    # The hue rotation guarantees maximum perceptual distance between
    # adjacent assignments. We interleave to maximize contrast between
    # commonly adjacent node types.
    node_converter = _node_cats[0]
    node_shader = _node_cats[1]
    node_input = _node_cats[2]
    node_output = _node_cats[3]
    node_color = _node_cats[4]
    node_filter = _node_cats[5]
    node_vector = _node_cats[6]
    node_texture = _node_cats[7]
    node_group = _node_cats[8]
    node_script = _node_cats[9]
    node_pattern = _node_cats[10]
    node_matte = _node_cats[11]
    node_distort = _node_cats[12]
    node_interface = _node_cats[13]
    node_layout = cm.ok_mix(_node_cats[14], ui_card, 0.4)  # muted for layout

    # =====================================================================
    # NLA STRIPS — ANSI semantic colors mixed with card for context
    # =====================================================================
    _nla_mix_t = 0.40 if dark else 0.50
    nla_strip = cm.ok_mix(accent_primary, medium_lift, _nla_mix_t)
    nla_strip_selected = cm.ok_mix(accent_bright, medium_lift, _nla_mix_t - 0.10)
    nla_transition = cm.ok_mix(accent_secondary, medium_lift, _nla_mix_t)
    nla_meta = cm.ok_mix(magenta, medium_lift, _nla_mix_t)
    nla_sound = cm.ok_mix(success, medium_lift, _nla_mix_t)
    nla_tweak = cm.ok_mix(danger, bg, 0.50)
    nla_tweak_dup = cm.ok_mix(danger_bright, bg, 0.40)

    # =====================================================================
    # TEXT EDITOR
    # =====================================================================
    text_bg = ui_bg
    text_fg = ui_text
    text_cursor = ui_cursor
    text_selection = ui_selection
    text_line_highlight = subtle_lift  # subtle lift from bg
    text_line_numbers = ui_text_muted

    # =====================================================================
    # COLLECTION COLORS — categorical from OKLCH hue rotation
    # =====================================================================
    if dark:
        coll_L = 0.58
        coll_C = 0.12
    else:
        coll_L = 0.60
        coll_C = 0.11

    collection_colors = cm.generate_categorical(
        8, target_L=coll_L, target_C=coll_C, start_H=25.0
    )

    # =====================================================================
    # ICON COLORS — semantic roles with matched perceptual lightness
    # =====================================================================
    # Icons keep their ANSI semantic hue but are normalized to a consistent
    # OKLCH lightness so no icon overwhelms another. We preserve the
    # original chroma rather than flattening it.
    if dark:
        icon_L = 0.68
    else:
        icon_L = 0.48

    def _icon_color(color):
        """Set icon to target lightness, preserve hue, reduce chroma slightly."""
        iL, iC, iH = cm.rgb_to_oklch(*color)
        # Gentle chroma reduction for visual comfort
        target_C = iC * 0.75
        max_c = cm.oklch_max_chroma(icon_L, iH)
        return cm.oklch_to_rgb(icon_L, min(target_C, max_c), iH)

    icon_scene = _icon_color(warning)
    icon_collection = _icon_color(cm.ok_desaturate(warning, 0.02))
    icon_object = _icon_color(accent_secondary)
    icon_object_data = _icon_color(success)
    icon_modifier = _icon_color(accent_primary)
    icon_shading = _icon_color(magenta)
    icon_folder = _icon_color(warning)
    icon_autokey = _icon_color(danger)

    # =====================================================================
    # BUILD PALETTE — same keys as before for apply.py compatibility
    # =====================================================================
    palette = {
        "dark": dark,
        "ansi": iterm_theme["ansi"],  # preserve originals
        # Surfaces
        "ui_bg": ui_bg,
        "ui_panel": ui_panel,
        "ui_card": ui_card,
        "ui_popup": ui_popup,
        "ui_border": ui_border,
        "ui_separator": ui_separator,
        "row_alternate": row_alternate,
        # Panel
        "ui_panel_header": ui_panel_header,
        "ui_panel_sub": ui_panel_sub,
        "ui_panel_outline": ui_panel_outline,
        "panel_text": panel_text,
        "panel_title": panel_title,
        # Viewport
        "viewport_gradient_low": viewport_gradient_low,
        "viewport_gradient_high": viewport_gradient_high,
        # Text
        "ui_text": ui_text,
        "ui_text_muted": ui_text_muted,
        "ui_text_disabled": ui_text_disabled,
        "ui_text_highlight": ui_text_highlight,
        # Accent (decorative — yellow)
        "ui_accent": ui_accent,
        "ui_accent_hover": ui_accent_hover,
        "ui_accent_active": ui_accent_active,
        "ui_accent_text": ui_accent_text,
        # Accent functional (blue — for selection bgs with text)
        "ui_accent_func": ui_accent_func,
        "ui_accent_func_hover": ui_accent_func_hover,
        "ui_accent_func_text": ui_accent_func_text,
        # Selection
        "ui_selection": ui_selection,
        "ui_selection_text": ui_selection_text,
        # Widgets
        "widget_bg": widget_bg,
        "widget_hover": widget_hover,
        "widget_active": widget_active,
        "widget_outline": widget_outline,
        "widget_text": widget_text,
        # Buttons
        "button_bg": button_bg,
        "button_hover": button_hover,
        "button_text": button_text,
        "button_text_hi": button_text_hi,
        # Toolbar
        "toolbar_bg": toolbar_bg,
        "toolbar_sel": toolbar_sel,
        "toolbar_text": toolbar_text,
        # Option / checkbox
        "option_check": option_check,
        "widget_item": widget_item,
        # Menu & pie highlights
        "menu_highlight": menu_highlight,
        "menu_highlight_text": menu_highlight_text,
        "menu_item_sel": menu_item_sel,
        "menu_item_sel_text": menu_item_sel_text,
        "menu_item_sel_bg": menu_item_sel_bg,
        "menu_inner_sel": menu_inner_sel,
        "menu_text_sel": menu_text_sel,
        "menu_accent": menu_accent,
        "pie_item": pie_item,
        "pie_highlight": pie_highlight,
        "pie_highlight_text": pie_highlight_text,
        "tab_sel_accent": tab_sel_accent,
        "tab_sel_text": tab_sel_text,
        "list_highlight": list_highlight,
        "list_highlight_text": list_highlight_text,
        # Input
        "input_bg": input_bg,
        "input_border": input_border,
        "input_text": input_text,
        # Scroll
        "scroll_bg": scroll_bg,
        "scroll_handle": scroll_handle,
        "scroll_handle_hover": scroll_handle_hover,
        # Header
        "header_bg": header_bg,
        "header_text": header_text,
        # Tabs
        "tab_active_bg": tab_active_bg,
        "tab_inactive_bg": tab_inactive_bg,
        "tab_outline": tab_outline,
        # Cursor
        "ui_cursor": ui_cursor,
        "ui_text_sel_highlight": ui_text_sel_highlight,
        # 3D Viewport
        "grid_line": grid_line,
        "grid_axis_x": grid_axis_x,
        "grid_axis_y": grid_axis_y,
        "grid_axis_z": grid_axis_z,
        "obj_selected": obj_selected,
        "obj_active": obj_active,
        "outliner_active_obj": outliner_active_obj,
        "wire_color": wire_color,
        "wire_edit": wire_edit,
        "vertex_color": vertex_color,
        "edge_select": edge_select,
        "face_select": face_select,
        "before_frame": before_frame,
        "after_frame": after_frame,
        "gizmo_x": gizmo_x,
        "gizmo_y": gizmo_y,
        "gizmo_z": gizmo_z,
        # State
        "info_color": info_color,
        "warning_color": warning_color,
        "error_color": error_color,
        "success_color": success_color,
        # Node editor
        "node_bg": node_bg,
        "node_selected": node_selected,
        "node_frame": node_frame,
        "node_converter": node_converter,
        "node_color": node_color,
        "node_group": node_group,
        "node_interface": node_interface,
        "node_input": node_input,
        "node_output": node_output,
        "node_matte": node_matte,
        "node_distort": node_distort,
        "node_filter": node_filter,
        "node_pattern": node_pattern,
        "node_script": node_script,
        "node_shader": node_shader,
        "node_texture": node_texture,
        "node_vector": node_vector,
        "node_layout": node_layout,
        # NLA
        "nla_strip": nla_strip,
        "nla_strip_selected": nla_strip_selected,
        "nla_transition": nla_transition,
        "nla_meta": nla_meta,
        "nla_sound": nla_sound,
        "nla_tweak": nla_tweak,
        "nla_tweak_dup": nla_tweak_dup,
        # Text editor
        "text_bg": text_bg,
        "text_fg": text_fg,
        "text_cursor": text_cursor,
        "text_selection": text_selection,
        "text_line_highlight": text_line_highlight,
        "text_line_numbers": text_line_numbers,
        # Collection colors
        "collection_colors": collection_colors,
        # Icon colors
        "icon_scene": icon_scene,
        "icon_collection": icon_collection,
        "icon_object": icon_object,
        "icon_object_data": icon_object_data,
        "icon_modifier": icon_modifier,
        "icon_shading": icon_shading,
        "icon_folder": icon_folder,
        "icon_autokey": icon_autokey,
        # Semantic originals (from ANSI)
        "accent_primary": accent_primary,
        "accent_secondary": accent_secondary,
        "danger": danger,
        "danger_bright": danger_bright,
        "warning": warning,
        "success": success,
        "success_bright": success_bright,
        "magenta": magenta,
        "bright_magenta": bright_magenta,
        "bright_yellow": bright_yellow,
        "bright_cyan": bright_cyan,
        "bright_black": bright_black,
        "black": black,
        "white": white,
    }

    return palette


def palette_summary(palette):
    """Return a human-readable summary of the palette for debugging."""
    lines = []
    for key, val in palette.items():
        if key in ("dark", "ansi", "collection_colors"):
            continue
        if isinstance(val, tuple):
            if len(val) == 3:
                r, g, b = val
                hexc = "#{:02x}{:02x}{:02x}".format(
                    int(r * 255), int(g * 255), int(b * 255)
                )
                L, C, H = cm.rgb_to_oklch(r, g, b)
                lines.append(f"  {key:25s} = {hexc}  L={L:.3f} C={C:.3f} H={H:.0f}")
            elif len(val) == 4:
                r, g, b, a = val
                hexc = "#{:02x}{:02x}{:02x} a={:.2f}".format(
                    int(r * 255), int(g * 255), int(b * 255), a
                )
                lines.append(f"  {key:25s} = {hexc}")
    return "\n".join(lines)
