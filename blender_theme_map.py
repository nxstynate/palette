"""
Map an iTerm color palette into a Blender theme palette.

Design philosophy for derived colors:
  - Surfaces get a subtle tint from the ANSI palette (not pure gray shifts)
  - Child colors have WIDE steps between them for clear visual distinction
  - Widget states (normal/hover/active/selected) use distinct ANSI-derived hues
  - Text always passes contrast checks against its immediate background
  - Checkmarks, cursors, selection highlights use BRIGHT contrasting colors
"""

from . import color_math as cm


def build_palette(iterm_theme):
    ansi = iterm_theme["ansi"]
    bg = iterm_theme["bg"]
    fg = iterm_theme["fg"]
    selection = iterm_theme.get("selection")
    cursor = iterm_theme.get("cursor")

    dark = cm.is_dark(bg)

    # --- Semantic role assignments ---
    accent_primary = ansi[4]   # blue
    accent_bright = ansi[12]   # bright blue
    accent_secondary = ansi[6] # cyan
    warning = ansi[3]          # yellow
    danger = ansi[1]           # red
    danger_bright = ansi[9]    # bright red
    success = ansi[2]          # green
    success_bright = ansi[10]  # bright green
    magenta = ansi[5]
    bright_magenta = ansi[13]
    bright_yellow = ansi[11]
    bright_cyan = ansi[14]
    black = ansi[0]
    white = ansi[15]
    bright_black = ansi[8]     # gray

    # =====================================================================
    # SURFACES — tinted from palette, not just gray shifts
    # =====================================================================
    # We tint surfaces slightly toward the accent to give the theme character.
    # The tint amount is small (0.05-0.08) so it's subtle but perceptible.

    if dark:
        # Tint bg very slightly toward the accent hue
        _tint_ref = cm.desaturate(accent_primary, 0.6)
        ui_bg = bg
        # Bigger steps between surfaces for clear visual hierarchy
        ui_panel = cm.tint_from(cm.lighten(bg, 0.05), _tint_ref, 0.06)
        ui_card = cm.tint_from(cm.lighten(bg, 0.10), _tint_ref, 0.06)
        ui_popup = cm.tint_from(cm.lighten(bg, 0.12), _tint_ref, 0.04)
        ui_border = cm.desaturate(cm.mix(fg, bg, 0.65), 0.1)
        ui_separator = cm.mix(fg, bg, 0.80)

        # Panel surfaces — distinct from general bg
        ui_panel_header = cm.tint_from(cm.lighten(bg, 0.03), _tint_ref, 0.08)
        ui_panel_sub = cm.tint_from(cm.lighten(bg, 0.02), _tint_ref, 0.04)
    else:
        _tint_ref = cm.desaturate(accent_primary, 0.6)
        ui_bg = bg
        ui_panel = cm.tint_from(cm.darken(bg, 0.04), _tint_ref, 0.06)
        ui_card = cm.tint_from(cm.darken(bg, 0.08), _tint_ref, 0.06)
        ui_popup = cm.tint_from(cm.darken(bg, 0.03), _tint_ref, 0.04)
        ui_border = cm.desaturate(cm.mix(fg, bg, 0.65), 0.1)
        ui_separator = cm.mix(fg, bg, 0.80)

        ui_panel_header = cm.tint_from(cm.darken(bg, 0.05), _tint_ref, 0.08)
        ui_panel_sub = cm.tint_from(cm.darken(bg, 0.02), _tint_ref, 0.04)

    ui_panel_outline = cm.mix(ui_border, ui_bg, 0.3)

    # =====================================================================
    # VIEWPORT GRADIENT — tinted with theme character
    # =====================================================================
    if dark:
        viewport_gradient_low = cm.tint_from(bg, _tint_ref, 0.05)
        viewport_gradient_high = cm.tint_from(cm.lighten(bg, 0.05), _tint_ref, 0.05)
    else:
        viewport_gradient_low = cm.tint_from(cm.darken(bg, 0.04), _tint_ref, 0.05)
        viewport_gradient_high = cm.tint_from(bg, _tint_ref, 0.05)

    # =====================================================================
    # TEXT — high contrast, multiple distinct levels
    # =====================================================================
    ui_text = cm.ensure_contrast(fg, ui_bg, 5.0)
    ui_text_muted = cm.ensure_contrast(cm.mix(ui_text, ui_bg, 0.35), ui_bg, 3.0)
    ui_text_disabled = cm.mix(ui_text, ui_bg, 0.60)
    ui_text_highlight = cm.ensure_contrast(
        cm.lighten(fg, 0.15) if dark else cm.darken(fg, 0.15),
        ui_bg, 6.0
    )

    panel_text = cm.ensure_contrast(fg, ui_panel, 4.5)
    panel_title = cm.ensure_contrast(
        cm.lighten(fg, 0.1) if dark else cm.darken(fg, 0.1),
        ui_panel_header, 5.0
    )

    # =====================================================================
    # ACCENT — the primary interactive color
    # =====================================================================
    ui_accent = accent_primary
    if dark:
        ui_accent_hover = cm.lighten(ui_accent, 0.12)
        ui_accent_active = cm.lighten(ui_accent, 0.20)
    else:
        ui_accent_hover = cm.darken(ui_accent, 0.08)
        ui_accent_active = cm.darken(ui_accent, 0.16)

    # Accent text must POP against the accent bg — force white or black
    ui_accent_text = cm.ensure_contrast((1.0, 1.0, 1.0), ui_accent, 3.5)
    if cm.contrast_ratio(ui_accent_text, ui_accent) < 3.5:
        ui_accent_text = cm.ensure_contrast((0.0, 0.0, 0.0), ui_accent, 3.5)

    # =====================================================================
    # SELECTION — must be clearly visible
    # =====================================================================
    if selection:
        ui_selection = selection
    else:
        # Use accent but make it distinctly different from widget_bg
        ui_selection = cm.mix(ui_accent, ui_bg, 0.50)

    # Selection text MUST contrast against selection bg
    ui_selection_text = cm.ensure_contrast(ui_text, ui_selection, 5.0)
    if cm.contrast_ratio(ui_selection_text, ui_selection) < 4.5:
        # Force to white or black
        ui_selection_text = cm.ensure_contrast((1.0, 1.0, 1.0), ui_selection, 4.5)
        if cm.contrast_ratio(ui_selection_text, ui_selection) < 4.5:
            ui_selection_text = cm.ensure_contrast((0.0, 0.0, 0.0), ui_selection, 4.5)

    # =====================================================================
    # CHECKMARK / OPTION ITEM — bright, unmissable against widget bg
    # =====================================================================
    # The "item" color on wcol_option is the checkmark. It needs to
    # contrast against both inner (unchecked bg) and inner_sel (checked bg).
    option_check = cm.ensure_contrast(accent_bright, ui_bg, 4.0)
    if cm.contrast_ratio(option_check, ui_accent) < 3.0:
        # If check color is too close to accent (selected bg), use white/fg
        option_check = cm.ensure_contrast(white, ui_accent, 4.0)

    # =====================================================================
    # WIDGETS — bigger contrast steps, tinted with palette colors
    # =====================================================================
    if dark:
        widget_bg = cm.tint_from(cm.lighten(ui_bg, 0.10), bright_black, 0.08)
        widget_hover = cm.tint_from(cm.lighten(ui_bg, 0.16), accent_secondary, 0.06)
        widget_active = cm.tint_from(cm.lighten(ui_bg, 0.22), accent_primary, 0.08)
        widget_outline = cm.lighten(ui_bg, 0.20)
    else:
        widget_bg = cm.tint_from(cm.darken(ui_bg, 0.08), bright_black, 0.08)
        widget_hover = cm.tint_from(cm.darken(ui_bg, 0.14), accent_secondary, 0.06)
        widget_active = cm.tint_from(cm.darken(ui_bg, 0.20), accent_primary, 0.08)
        widget_outline = cm.darken(ui_bg, 0.18)

    # Widget text must contrast against widget_bg
    widget_text = cm.ensure_contrast(ui_text, widget_bg, 4.5)

    # =====================================================================
    # BUTTONS — Properties panel buttons, T-panel tools, sidebar buttons
    # These need to be CLEARLY distinct from the panel/card backgrounds.
    # We tint them with the accent hue at a noticeable level.
    # =====================================================================
    if dark:
        button_bg = cm.tint_from(cm.lighten(ui_bg, 0.12), accent_primary, 0.10)
        button_hover = cm.tint_from(cm.lighten(ui_bg, 0.18), accent_primary, 0.14)
    else:
        button_bg = cm.tint_from(cm.darken(ui_bg, 0.10), accent_primary, 0.10)
        button_hover = cm.tint_from(cm.darken(ui_bg, 0.15), accent_primary, 0.14)

    button_text = cm.ensure_contrast(ui_text, button_bg, 4.5)
    button_text_hi = cm.ensure_contrast(ui_text_highlight, button_hover, 5.0)

    # Toolbar items (T-panel) — slightly different from regular buttons
    if dark:
        toolbar_bg = cm.tint_from(cm.lighten(ui_bg, 0.09), accent_secondary, 0.07)
        toolbar_sel = cm.tint_from(cm.lighten(ui_bg, 0.15), accent_primary, 0.15)
    else:
        toolbar_bg = cm.tint_from(cm.darken(ui_bg, 0.07), accent_secondary, 0.07)
        toolbar_sel = cm.tint_from(cm.darken(ui_bg, 0.12), accent_primary, 0.15)

    toolbar_text = cm.ensure_contrast(ui_text, toolbar_bg, 4.5)

    # =====================================================================
    # INPUT FIELDS — distinct from widgets, darker/lighter for depth
    # =====================================================================
    if dark:
        input_bg = cm.darken(ui_bg, 0.04)
        input_border = cm.lighten(ui_bg, 0.15)
    else:
        input_bg = cm.lighten(ui_bg, 0.04)
        input_border = cm.darken(ui_bg, 0.15)

    # Input text
    input_text = cm.ensure_contrast(ui_text, input_bg, 5.0)

    # =====================================================================
    # SCROLL — uses muted palette colors
    # =====================================================================
    scroll_bg = ui_panel
    scroll_handle = cm.desaturate(cm.mix(fg, bg, 0.60), 0.2)
    scroll_handle_hover = cm.mix(accent_primary, cm.mix(fg, bg, 0.45), 0.15)

    # =====================================================================
    # HEADER — tinted with palette
    # =====================================================================
    if dark:
        header_bg = cm.tint_from(cm.darken(ui_bg, 0.03), _tint_ref, 0.06)
    else:
        header_bg = cm.tint_from(cm.darken(ui_bg, 0.05), _tint_ref, 0.06)
    header_text = cm.ensure_contrast(ui_text, header_bg, 5.0)

    # =====================================================================
    # TABS — distinct active vs inactive
    # =====================================================================
    tab_active_bg = ui_bg
    tab_inactive_bg = cm.mix(ui_panel, ui_card, 0.5)
    tab_outline = ui_border

    # =====================================================================
    # CURSOR — bright and visible
    # =====================================================================
    ui_cursor = cursor if cursor else accent_bright

    # =====================================================================
    # 3D VIEWPORT ELEMENTS
    # =====================================================================
    grid_line = cm.mix(ui_border, ui_bg, 0.55)
    grid_axis_x = cm.desaturate(danger, 0.1)
    grid_axis_y = cm.desaturate(success, 0.1)
    grid_axis_z = cm.desaturate(accent_secondary, 0.1)

    obj_selected = accent_bright
    obj_active = cm.lighten(accent_bright, 0.12) if dark else cm.darken(accent_bright, 0.08)
    wire_color = cm.mix(fg, bg, 0.35)
    wire_edit = cm.mix(accent_primary, fg, 0.25)

    vertex_color = cm.lighten(accent_bright, 0.12) if dark else accent_bright
    edge_select = cm.lighten(accent_primary, 0.18) if dark else accent_primary
    face_select = cm.alpha(cm.mix(ui_accent, ui_bg, 0.45), 0.35)

    before_frame = cm.desaturate(danger, 0.1)
    after_frame = cm.desaturate(accent_secondary, 0.1)

    # Gizmo
    gizmo_x = danger
    gizmo_y = success
    gizmo_z = accent_primary

    # State colors
    info_color = accent_secondary
    warning_color = warning
    error_color = danger
    success_color = success

    # =====================================================================
    # NODE EDITOR — distinct node type colors from ANSI
    # =====================================================================
    node_bg = ui_card
    node_selected = cm.mix(ui_accent, ui_bg, 0.4)
    node_frame = cm.mix(ui_card, ui_bg, 0.3)

    # Use more saturated tints for node types — these should be colorful
    def _node_tint(ansi_color, t=0.55):
        return cm.mix(ansi_color, ui_card, t)

    node_converter = _node_tint(accent_secondary, 0.55)
    node_color = _node_tint(bright_yellow, 0.55)
    node_group = _node_tint(success, 0.50)
    node_interface = _node_tint(bright_cyan, 0.50)
    node_input = _node_tint(danger, 0.55)
    node_output = _node_tint(danger_bright, 0.55)
    node_matte = _node_tint(magenta, 0.55)
    node_distort = _node_tint(bright_magenta, 0.55)
    node_filter = _node_tint(accent_primary, 0.55)
    node_pattern = _node_tint(warning, 0.55)
    node_script = _node_tint(bright_black, 0.60)
    node_shader = _node_tint(accent_secondary, 0.45)
    node_texture = _node_tint(warning, 0.45)
    node_vector = _node_tint(magenta, 0.45)
    node_layout = _node_tint(bright_black, 0.70)

    # =====================================================================
    # NLA STRIPS — distinct from each other
    # =====================================================================
    nla_strip = cm.mix(accent_primary, ui_card, 0.40)
    nla_strip_selected = cm.mix(accent_bright, ui_card, 0.30)
    nla_transition = cm.mix(accent_secondary, ui_card, 0.40)
    nla_meta = cm.mix(magenta, ui_card, 0.40)
    nla_sound = cm.mix(success, ui_card, 0.40)
    nla_tweak = cm.mix(danger, ui_bg, 0.50)
    nla_tweak_dup = cm.mix(danger_bright, ui_bg, 0.40)

    # =====================================================================
    # TEXT EDITOR
    # =====================================================================
    text_bg = ui_bg
    text_fg = ui_text
    text_cursor = ui_cursor
    text_selection = ui_selection
    text_line_highlight = cm.lighten(ui_bg, 0.04) if dark else cm.darken(ui_bg, 0.03)
    text_line_numbers = ui_text_muted

    # =====================================================================
    # COLLECTION COLORS — vivid, from ANSI
    # =====================================================================
    collection_colors = [
        cm.desaturate(danger, 0.05),
        cm.desaturate(warning, 0.05),
        cm.desaturate(bright_yellow, 0.05),
        cm.desaturate(success, 0.05),
        cm.desaturate(accent_secondary, 0.05),
        cm.desaturate(accent_primary, 0.05),
        cm.desaturate(magenta, 0.05),
        cm.desaturate(bright_black, 0.05),
    ]

    # =====================================================================
    # ICON COLORS — themed tints from ANSI palette
    # =====================================================================
    icon_scene = cm.desaturate(warning, 0.1)            # yellow-ish for scenes
    icon_collection = cm.desaturate(warning, 0.15)       # warm amber for collections
    icon_object = cm.desaturate(accent_secondary, 0.1)   # cyan-ish for objects
    icon_object_data = cm.desaturate(success, 0.1)       # green for mesh/data
    icon_modifier = cm.desaturate(accent_primary, 0.1)   # blue for modifiers
    icon_shading = cm.desaturate(magenta, 0.1)           # magenta for shading
    icon_folder = cm.desaturate(warning, 0.05)           # warm yellow for folders
    icon_autokey = cm.desaturate(danger, 0.1)            # red for auto-key indicator

    # =====================================================================
    # BUILD PALETTE
    # =====================================================================
    palette = {
        "dark": dark,
        "ansi": ansi,
        # Surfaces
        "ui_bg": ui_bg,
        "ui_panel": ui_panel,
        "ui_card": ui_card,
        "ui_popup": ui_popup,
        "ui_border": ui_border,
        "ui_separator": ui_separator,
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
        # Accent
        "ui_accent": ui_accent,
        "ui_accent_hover": ui_accent_hover,
        "ui_accent_active": ui_accent_active,
        "ui_accent_text": ui_accent_text,
        # Selection
        "ui_selection": ui_selection,
        "ui_selection_text": ui_selection_text,
        # Widgets
        "widget_bg": widget_bg,
        "widget_hover": widget_hover,
        "widget_active": widget_active,
        "widget_outline": widget_outline,
        "widget_text": widget_text,
        # Buttons (properties panel, etc)
        "button_bg": button_bg,
        "button_hover": button_hover,
        "button_text": button_text,
        "button_text_hi": button_text_hi,
        # Toolbar (T-panel)
        "toolbar_bg": toolbar_bg,
        "toolbar_sel": toolbar_sel,
        "toolbar_text": toolbar_text,
        # Option / checkbox
        "option_check": option_check,
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
        # 3D Viewport
        "grid_line": grid_line,
        "grid_axis_x": grid_axis_x,
        "grid_axis_y": grid_axis_y,
        "grid_axis_z": grid_axis_z,
        "obj_selected": obj_selected,
        "obj_active": obj_active,
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
        # Semantic originals
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
                lines.append(f"  {key:25s} = {hexc}")
            elif len(val) == 4:
                r, g, b, a = val
                hexc = "#{:02x}{:02x}{:02x} a={:.2f}".format(
                    int(r * 255), int(g * 255), int(b * 255), a
                )
                lines.append(f"  {key:25s} = {hexc}")
    return "\n".join(lines)
