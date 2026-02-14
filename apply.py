"""
Apply a generated theme palette to the live Blender session.

Comprehensive mapping covering:
- 3D Viewport gradient background
- Panel colors (back, header, sub, outline, text)
- All widget types
- Node editor node-type colors
- NLA strip colors
- Collection colors
- Bone color sets
- Topbar / Statusbar
- All editor spaces
"""

import traceback as _tb


def _set_color(obj, attr, color):
    """
    Safely set a color property on a Blender theme object.
    Handles RGB(3) vs RGBA(4) mismatches via try/except cascade.
    """
    if not hasattr(obj, attr):
        return

    color = tuple(float(c) for c in color)

    # Strategy 1: try as-is
    try:
        setattr(obj, attr, color)
        return
    except (TypeError, ValueError):
        pass

    # Strategy 2: if we sent 4, try 3
    if len(color) >= 4:
        try:
            setattr(obj, attr, color[:3])
            return
        except (TypeError, ValueError):
            pass

    # Strategy 3: if we sent 3, try 4
    if len(color) == 3:
        try:
            setattr(obj, attr, (*color, 1.0))
            return
        except (TypeError, ValueError):
            pass

    # Strategy 4: introspect
    try:
        current = getattr(obj, attr)
        n = len(current)
        if n == 3:
            setattr(obj, attr, color[:3])
        elif n == 4:
            setattr(obj, attr, (*color[:3], color[3] if len(color) > 3 else 1.0))
        else:
            setattr(obj, attr, color[:n])
    except Exception:
        pass


def _try_set(obj, attr, value):
    """Try to set a non-color attribute, silently skip on failure."""
    try:
        setattr(obj, attr, value)
    except (AttributeError, TypeError, ValueError):
        pass


def apply_theme_to_blender(palette):
    """
    Apply the palette to Blender's active theme via the Python API.
    Returns True on success, error string on failure.
    """
    try:
        import bpy
    except ImportError:
        return "bpy not available - not running inside Blender"

    theme = bpy.context.preferences.themes[0]
    p = palette

    # =====================================================================
    # USER INTERFACE (global widget colors + panel colors)
    # =====================================================================
    ui = theme.user_interface

    def set_wcol(wcol, outline, inner, inner_sel, item, text, text_sel):
        # outline, inner, inner_sel, item are RGBA float[4] in Blender
        _set_color(wcol, 'outline', (*outline[:3], 1.0))
        _set_color(wcol, 'inner', (*inner[:3], 1.0))
        _set_color(wcol, 'inner_sel', (*inner_sel[:3], 1.0))
        _set_color(wcol, 'item', (*item[:3], 1.0))
        _set_color(wcol, 'text', (*text[:3], 1.0))
        _set_color(wcol, 'text_sel', (*text_sel[:3], 1.0))

    set_wcol(ui.wcol_regular,
             p["widget_outline"], p["widget_bg"], p["ui_accent_func"],
             p["ui_accent_func"], p["widget_text"], p["ui_accent_func_text"])

    set_wcol(ui.wcol_tool,
             p["widget_outline"], p["button_bg"], p["ui_accent_func"],
             p["ui_accent_func"], p["button_text"], p["ui_accent_func_text"])

    set_wcol(ui.wcol_toolbar_item,
             p["widget_outline"], p["toolbar_bg"], p["toolbar_sel"],
             p["option_check"], p["toolbar_text"], p["ui_accent_func_text"])

    set_wcol(ui.wcol_radio,
             p["widget_outline"], p["widget_bg"], p["ui_accent_func"],
             p["option_check"], p["widget_text"], p["ui_accent_func_text"])

    set_wcol(ui.wcol_text,
             p["input_border"], p["input_bg"], p["ui_selection"],
             p["ui_text_sel_highlight"], p["input_text"], p["ui_selection_text"])

    # Checkbox/option: item = checkmark color, must pop against both states
    set_wcol(ui.wcol_option,
             p["widget_outline"], p["widget_bg"], p["ui_accent_func"],
             p["option_check"], p["widget_text"], p["ui_accent_func_text"])

    set_wcol(ui.wcol_toggle,
             p["widget_outline"], p["widget_bg"], p["ui_accent_func"],
             p["option_check"], p["widget_text"], p["ui_accent_func_text"])

    set_wcol(ui.wcol_num,
             p["input_border"], p["input_bg"], p["ui_selection"],
             p["ui_accent_func"], p["input_text"], p["ui_selection_text"])

    set_wcol(ui.wcol_numslider,
             p["input_border"], p["input_bg"], p["ui_selection"],
             p["ui_accent_func"], p["input_text"], p["ui_selection_text"])

    set_wcol(ui.wcol_box,
             p["ui_border"], p["ui_card"], p["ui_selection"],
             p["ui_accent_func"], p["widget_text"], p["ui_selection_text"])

    set_wcol(ui.wcol_menu,
             p["ui_border"], p["ui_popup"], p["menu_inner_sel"],
             p["menu_accent"], p["widget_text"], p["menu_text_sel"])

    set_wcol(ui.wcol_pulldown,
             p["ui_border"], p["ui_popup"], p["menu_inner_sel"],
             p["menu_accent"], p["widget_text"], p["menu_text_sel"])

    set_wcol(ui.wcol_menu_back,
             p["ui_border"], p["ui_popup"], p["menu_inner_sel"],
             p["menu_accent"], p["widget_text"], p["menu_text_sel"])

    set_wcol(ui.wcol_menu_item,
             p["ui_border"], p["ui_popup"], p["menu_inner_sel"],
             p["menu_accent"], p["widget_text"], p["menu_text_sel"])

    set_wcol(ui.wcol_tooltip,
             p["ui_border"], p["ui_card"], p["ui_selection"],
             p["ui_accent_func"], p["widget_text"], p["ui_selection_text"])

    set_wcol(ui.wcol_scroll,
             p["ui_border"], p["scroll_bg"], p["scroll_handle_hover"],
             p["scroll_handle"], p["widget_text"], p["widget_text"])

    set_wcol(ui.wcol_progress,
             p["ui_border"], p["widget_bg"], p["ui_accent_func"],
             p["ui_accent_func"], p["widget_text"], p["ui_accent_func_text"])

    set_wcol(ui.wcol_list_item,
             p["ui_border"], p["ui_bg"], p["list_highlight"],
             p["ui_accent_func"], p["widget_text"], p["list_highlight_text"])

    set_wcol(ui.wcol_tab,
             p["tab_outline"], p["tab_inactive_bg"], p["tab_sel_accent"],
             p["ui_accent_func"], p["ui_text_muted"], p["tab_sel_text"])

    # wcol_pie_menu if available
    try:
        set_wcol(ui.wcol_pie_menu,
                 p["ui_border"], p["ui_popup"], p["pie_highlight"],
                 p["pie_item"], p["widget_text"], p["pie_highlight_text"])
    except AttributeError:
        pass

    # --- Panel colors (global) ---
    _set_color(ui, 'panel_back', (*p["ui_panel"], 0.7))
    _set_color(ui, 'panel_header', (*p["ui_panel_header"], 1.0))
    _set_color(ui, 'panel_sub_back', (*p["ui_panel_sub"], 0.5))
    _set_color(ui, 'panel_outline', (*p["ui_panel_outline"], 1.0))
    _set_color(ui, 'panel_text', p["panel_text"])
    _set_color(ui, 'panel_title', p["panel_title"])
    _try_set(ui, 'panel_roundness', 0.4)

    # --- Axis & gizmo ---
    _set_color(ui, 'axis_x', p["gizmo_x"])
    _set_color(ui, 'axis_y', p["gizmo_y"])
    _set_color(ui, 'axis_z', p["gizmo_z"])
    _set_color(ui, 'gizmo_primary', p["ui_accent"])
    _set_color(ui, 'gizmo_secondary', p["accent_secondary"])
    _set_color(ui, 'gizmo_a', p["ui_accent"])
    _set_color(ui, 'gizmo_b', p["accent_secondary"])

    # --- Widget emboss ---
    _set_color(ui, 'widget_emboss', (0.0, 0.0, 0.0, 0.25))
    _set_color(ui, 'widget_text_cursor', p["ui_cursor"])

    # --- Transparent checker ---
    _set_color(ui, 'transparent_checker_primary', p["ui_card"])
    _set_color(ui, 'transparent_checker_secondary', p["ui_panel"])
    _try_set(ui, 'transparent_checker_size', 10)

    # --- Icon alpha/saturation ---
    _try_set(ui, 'icon_alpha', 1.0)
    _try_set(ui, 'icon_saturation', 1.0)
    _try_set(ui, 'icon_border_intensity', 0.0)
    _try_set(ui, 'menu_shadow_fac', 0.3)
    _try_set(ui, 'menu_shadow_width', 12)

    # --- Icon colors ---
    _set_color(ui, 'icon_scene', (*p["icon_scene"][:3], 1.0))
    _set_color(ui, 'icon_collection', (*p["icon_collection"][:3], 1.0))
    _set_color(ui, 'icon_object', (*p["icon_object"][:3], 1.0))
    _set_color(ui, 'icon_object_data', (*p["icon_object_data"][:3], 1.0))
    _set_color(ui, 'icon_modifier', (*p["icon_modifier"][:3], 1.0))
    _set_color(ui, 'icon_shading', (*p["icon_shading"][:3], 1.0))
    _set_color(ui, 'icon_folder', (*p["icon_folder"][:3], 1.0))
    _set_color(ui, 'icon_autokey', (*p["icon_autokey"][:3], 1.0))

    # =====================================================================
    # COLLECTION COLORS
    # =====================================================================
    try:
        ccolors = p.get("collection_colors", [])
        for i, cc in enumerate(ccolors):
            if i < len(theme.collection_color):
                _set_color(theme.collection_color[i], 'color', cc)
    except (AttributeError, IndexError):
        pass

    # =====================================================================
    # BONE COLOR SETS
    # =====================================================================
    try:
        ansi = p["ansi"]
        bone_sets = [
            (p["danger"], p["danger_bright"], p["ui_accent"]),      # set 1
            (p["success"], p["success_bright"], p["ui_accent"]),     # set 2
            (p["accent_primary"], p["bright_cyan"], p["ui_accent"]), # set 3
            (p["magenta"], p["bright_magenta"], p["ui_accent"]),     # set 4
            (p["warning"], p["bright_yellow"], p["ui_accent"]),      # set 5
        ]
        for i, (normal, select, active) in enumerate(bone_sets):
            if i < len(theme.bone_color_sets):
                bcs = theme.bone_color_sets[i]
                _set_color(bcs, 'normal', normal)
                _set_color(bcs, 'select', select)
                _set_color(bcs, 'active', active)
                _try_set(bcs, 'show_colored_constraints', True)
    except (AttributeError, IndexError):
        pass

    # =====================================================================
    # SPACE THEME HELPERS
    # =====================================================================

    def set_space_generic(space):
        """Apply common space properties (ThemeSpaceGeneric)."""
        _set_color(space, 'back', p["ui_bg"])
        _set_color(space, 'title', p["ui_text_highlight"])
        _set_color(space, 'text', p["ui_text"])
        _set_color(space, 'text_hi', p["ui_text_highlight"])
        _set_color(space, 'header', (*p["header_bg"][:3], 1.0))
        _set_color(space, 'header_text', p["header_text"])
        _set_color(space, 'header_text_hi', p["ui_text_highlight"])
        # Button bg — MUST have alpha=1.0 or Blender won't show the tint
        _set_color(space, 'button', (*p["button_bg"][:3], 1.0))
        _set_color(space, 'button_title', p["button_text"])
        _set_color(space, 'button_text', p["button_text"])
        _set_color(space, 'button_text_hi', p["button_text_hi"])
        _set_color(space, 'navigation_bar', (*p["ui_panel"][:3], 1.0))
        _set_color(space, 'execution_buts', (*p["button_bg"][:3], 1.0))
        _set_color(space, 'tab_active', p["tab_active_bg"])
        _set_color(space, 'tab_inactive', p["tab_inactive_bg"])
        _set_color(space, 'tab_back', p["ui_bg"])
        _set_color(space, 'tab_outline', p["tab_outline"])
        # Panel colors per-space
        try:
            pc = space.panelcolors
            _set_color(pc, 'header', (*p["ui_panel_header"], 1.0))
            _set_color(pc, 'back', (*p["ui_panel"], 0.7))
            _set_color(pc, 'sub_back', (*p["ui_panel_sub"], 0.5))
        except AttributeError:
            pass

    def set_space_gradient(space):
        """Apply common space properties for ThemeSpaceGradient (3D viewport)."""
        _set_color(space, 'title', p["ui_text_highlight"])
        _set_color(space, 'text', p["ui_text"])
        _set_color(space, 'text_hi', p["ui_text_highlight"])
        _set_color(space, 'header', (*p["header_bg"][:3], 1.0))
        _set_color(space, 'header_text', p["header_text"])
        _set_color(space, 'header_text_hi', p["ui_text_highlight"])
        _set_color(space, 'button', (*p["button_bg"][:3], 1.0))
        _set_color(space, 'button_title', p["button_text"])
        _set_color(space, 'button_text', p["button_text"])
        _set_color(space, 'button_text_hi', p["button_text_hi"])
        _set_color(space, 'navigation_bar', (*p["ui_panel"][:3], 1.0))
        _set_color(space, 'execution_buts', (*p["button_bg"][:3], 1.0))
        _set_color(space, 'tab_active', p["tab_active_bg"])
        _set_color(space, 'tab_inactive', p["tab_inactive_bg"])
        _set_color(space, 'tab_back', p["ui_bg"])
        _set_color(space, 'tab_outline', p["tab_outline"])
        # Gradients — this controls the 3D viewport canvas background
        try:
            grad = space.gradients
            _set_color(grad, 'gradient', p["viewport_gradient_low"])
            _set_color(grad, 'high_gradient', p["viewport_gradient_high"])
            _try_set(grad, 'background_type', 'SINGLE_COLOR')
        except AttributeError:
            pass
        # Panel colors per-space
        try:
            pc = space.panelcolors
            _set_color(pc, 'header', (*p["ui_panel_header"], 1.0))
            _set_color(pc, 'back', (*p["ui_panel"], 0.7))
            _set_color(pc, 'sub_back', (*p["ui_panel_sub"], 0.5))
        except AttributeError:
            pass

    # =====================================================================
    # 3D VIEWPORT
    # =====================================================================
    v3d = theme.view_3d
    set_space_gradient(v3d.space)

    # Asset shelf
    try:
        ash = v3d.asset_shelf
        _set_color(ash, 'header_back', p["header_bg"])
        _set_color(ash, 'back', p["ui_bg"])
    except AttributeError:
        pass

    _set_color(v3d, 'grid', p["grid_line"])
    _set_color(v3d, 'wire', p["wire_color"])
    _set_color(v3d, 'wire_edit', p["wire_edit"])
    _set_color(v3d, 'object_selected', p["obj_selected"])
    _set_color(v3d, 'object_active', p["obj_active"])
    _set_color(v3d, 'vertex', p["vertex_color"])
    _set_color(v3d, 'vertex_select', p["edge_select"])
    _set_color(v3d, 'vertex_unreferenced', p["danger"])
    _set_color(v3d, 'edge_select', p["edge_select"])
    _set_color(v3d, 'edge_seam', p["danger"])
    _set_color(v3d, 'edge_sharp', p["bright_cyan"])
    _set_color(v3d, 'edge_crease', p["bright_magenta"])
    _set_color(v3d, 'edge_bevel', p["bright_cyan"])
    _set_color(v3d, 'edge_facesel', p["ui_accent"])
    _set_color(v3d, 'face_select', (*p["ui_accent"], 0.25))
    _set_color(v3d, 'face_dot', p["ui_accent"])
    _set_color(v3d, 'freestyle_edge_mark', p["success"])
    _set_color(v3d, 'freestyle_face_mark', (*p["accent_secondary"], 0.4))
    _set_color(v3d, 'empty', p["ui_text_muted"])
    _set_color(v3d, 'camera', p["ui_text_muted"])
    _set_color(v3d, 'lamp', p["warning"])
    _set_color(v3d, 'light', p["warning"])
    _set_color(v3d, 'speaker', p["ui_text_muted"])
    _set_color(v3d, 'text_grease_pencil', p["success"])
    _set_color(v3d, 'gp_vertex', p["success"])
    _set_color(v3d, 'gp_vertex_select', p["success_bright"])
    _try_set(v3d, 'gp_vertex_size', 3)
    _set_color(v3d, 'bone_solid', p["ui_card"])
    _set_color(v3d, 'bone_pose', p["accent_secondary"])
    _set_color(v3d, 'bone_pose_active', p["ui_accent"])
    _set_color(v3d, 'bone_locked_weight', (*p["danger"], 0.4))
    _set_color(v3d, 'frame_current', p["success"])
    _set_color(v3d, 'before_current_frame', p["before_frame"])
    _set_color(v3d, 'after_current_frame', p["after_frame"])
    _set_color(v3d, 'transform', p["ui_accent"])
    _set_color(v3d, 'lastsel_point', p["ui_text_highlight"])
    _set_color(v3d, 'normal', p["accent_secondary"])
    _set_color(v3d, 'vertex_normal', p["ui_accent"])
    _set_color(v3d, 'loop_normal', p["magenta"])
    _set_color(v3d, 'split_normal', p["danger"])
    _set_color(v3d, 'face_back', (*p["ui_accent"], 0.1))
    _set_color(v3d, 'face_front', (*p["ui_accent"], 0.2))
    _set_color(v3d, 'editmesh_active', (*p["ui_accent"], 0.5))
    _set_color(v3d, 'handle_free', p["danger"])
    _set_color(v3d, 'handle_auto', p["success"])
    _set_color(v3d, 'handle_vect', p["accent_secondary"])
    _set_color(v3d, 'handle_align', p["magenta"])
    _set_color(v3d, 'handle_sel_free', p["danger"])
    _set_color(v3d, 'handle_sel_auto', p["success"])
    _set_color(v3d, 'handle_sel_vect', p["accent_secondary"])
    _set_color(v3d, 'handle_sel_align', p["bright_magenta"])
    _set_color(v3d, 'nurb_uline', p["accent_secondary"])
    _set_color(v3d, 'nurb_vline', p["magenta"])
    _set_color(v3d, 'nurb_sel_uline', p["obj_selected"])
    _set_color(v3d, 'nurb_sel_vline', p["bright_magenta"])
    _set_color(v3d, 'act_spline', p["ui_accent"])
    _set_color(v3d, 'clipping_border_3d', (*p["warning"], 0.5))
    _set_color(v3d, 'view_overlay', p["ui_text"])
    _set_color(v3d, 'paint_curve_pivot', p["danger"])
    _set_color(v3d, 'paint_curve_handle', p["success"])
    _set_color(v3d, 'skin_root', p["danger"])
    _set_color(v3d, 'extra_edge_len', p["success"])
    _set_color(v3d, 'extra_edge_angle', p["accent_secondary"])
    _set_color(v3d, 'extra_face_angle', p["ui_accent"])
    _set_color(v3d, 'extra_face_area', p["magenta"])
    _set_color(v3d, 'bundle_solid', p["ui_card"])
    _set_color(v3d, 'object_origin_size', p["ui_text_muted"])
    _try_set(v3d, 'outline_width', 1)
    _try_set(v3d, 'vertex_size', 3)
    _try_set(v3d, 'edge_width', 1)

    # =====================================================================
    # PROPERTIES EDITOR
    # =====================================================================
    set_space_generic(theme.properties.space)

    # =====================================================================
    # OUTLINER
    # =====================================================================
    set_space_generic(theme.outliner.space)
    o = theme.outliner
    _set_color(o, 'match', p["ui_accent"])
    _set_color(o, 'selected_highlight', p["list_highlight"])
    _set_color(o, 'active', (*p["list_highlight"][:3], 0.45))
    _set_color(o, 'selected_object', (*p["obj_selected"][:3], 0.3))
    _set_color(o, 'active_object', (*p["outliner_active_obj"][:3], 0.25))
    _set_color(o, 'edited_object', (*p["success"][:3], 0.3))
    _set_color(o, 'row_alternate', (*p["row_alternate"][:3], 0.5))

    # =====================================================================
    # TEXT EDITOR
    # =====================================================================
    set_space_generic(theme.text_editor.space)
    te = theme.text_editor
    _set_color(te, 'line_numbers', p["text_line_numbers"])
    _set_color(te, 'line_numbers_background', p["ui_panel"])
    _set_color(te, 'selected_text', p["text_selection"])
    _set_color(te, 'cursor', p["text_cursor"])
    _set_color(te, 'syntax_builtin', p["accent_secondary"])
    _set_color(te, 'syntax_symbols', p["ui_text_muted"])
    _set_color(te, 'syntax_special', p["magenta"])
    _set_color(te, 'syntax_comment', p["ui_text_disabled"])
    _set_color(te, 'syntax_preprocessor', p["accent_primary"])
    _set_color(te, 'syntax_reserved', p["danger"])
    _set_color(te, 'syntax_string', p["success"])
    _set_color(te, 'syntax_numbers', p["warning"])

    # =====================================================================
    # GRAPH EDITOR
    # =====================================================================
    set_space_generic(theme.graph_editor.space)
    ge = theme.graph_editor
    _set_color(ge, 'grid', p["grid_line"])
    _set_color(ge, 'frame_current', p["success"])
    _set_color(ge, 'handle_free', p["danger"])
    _set_color(ge, 'handle_auto', p["success"])
    _set_color(ge, 'handle_vect', p["accent_secondary"])
    _set_color(ge, 'handle_align', p["magenta"])
    _set_color(ge, 'handle_sel_free', p["danger"])
    _set_color(ge, 'handle_sel_auto', p["success"])
    _set_color(ge, 'handle_sel_vect', p["accent_secondary"])
    _set_color(ge, 'handle_sel_align', p["bright_magenta"])
    _set_color(ge, 'handle_auto_clamped', p["warning"])
    _set_color(ge, 'handle_sel_auto_clamped', p["warning"])
    _set_color(ge, 'lastsel_point', p["ui_text_highlight"])
    _set_color(ge, 'handle_vertex', p["vertex_color"])
    _set_color(ge, 'handle_vertex_select', p["edge_select"])
    _try_set(ge, 'handle_vertex_size', 4)
    _set_color(ge, 'channel_group', (*p["accent_secondary"], 0.3))
    _set_color(ge, 'active_channels_group', (*p["ui_accent"], 0.3))
    _set_color(ge, 'dopesheet_channel', (*p["ui_panel"], 0.5))
    _set_color(ge, 'dopesheet_subchannel', (*p["ui_card"], 0.5))
    _set_color(ge, 'window_sliders', p["ui_accent"])
    _set_color(ge, 'channels_region', p["ui_panel"])

    # =====================================================================
    # DOPESHEET EDITOR
    # =====================================================================
    set_space_generic(theme.dopesheet_editor.space)
    de = theme.dopesheet_editor
    _set_color(de, 'grid', p["grid_line"])
    _set_color(de, 'frame_current', p["success"])
    _set_color(de, 'value_sliders', (*p["ui_accent"], 0.3))
    _set_color(de, 'view_sliders', (*p["accent_secondary"], 0.3))
    _set_color(de, 'dopesheet_channel', (*p["ui_panel"], 0.5))
    _set_color(de, 'dopesheet_subchannel', (*p["ui_card"], 0.5))
    _set_color(de, 'channel_group', (*p["accent_secondary"], 0.3))
    _set_color(de, 'active_channels_group', (*p["ui_accent"], 0.3))
    _set_color(de, 'long_key', (*p["magenta"], 0.3))
    _set_color(de, 'long_key_selected', (*p["bright_magenta"], 0.3))
    _set_color(de, 'keyframe', p["warning"])
    _set_color(de, 'keyframe_selected', p["ui_accent"])
    _set_color(de, 'keyframe_extreme', p["danger"])
    _set_color(de, 'keyframe_extreme_selected', p["danger"])
    _set_color(de, 'keyframe_breakdown', p["accent_secondary"])
    _set_color(de, 'keyframe_breakdown_selected', p["accent_secondary"])
    _set_color(de, 'keyframe_jitter', p["success"])
    _set_color(de, 'keyframe_jitter_selected', p["success"])
    _set_color(de, 'keyframe_movehold', p["magenta"])
    _set_color(de, 'keyframe_movehold_selected', p["bright_magenta"])
    _set_color(de, 'keyframe_border', p["ui_border"])
    _set_color(de, 'keyframe_border_selected', p["ui_text"])
    _set_color(de, 'summary', (*p["ui_accent"], 0.3))
    _set_color(de, 'channels_region', p["ui_panel"])
    _set_color(de, 'window_sliders', p["ui_accent"])
    _set_color(de, 'time_scrub_background', (*p["ui_panel"], 0.75))
    _set_color(de, 'time_marker_line', (*p["warning"], 0.5))
    _set_color(de, 'time_marker_line_selected', (*p["ui_accent"], 0.8))

    # =====================================================================
    # NODE EDITOR
    # =====================================================================
    set_space_generic(theme.node_editor.space)
    ne = theme.node_editor
    _set_color(ne, 'grid', p["grid_line"])
    _set_color(ne, 'node_selected', p["node_selected"])
    _set_color(ne, 'node_active', p["ui_accent"])
    _set_color(ne, 'wire', p["wire_color"])
    _set_color(ne, 'wire_inner', p["ui_text_muted"])
    _set_color(ne, 'wire_select', p["obj_selected"])
    _set_color(ne, 'selected_text', p["ui_selection"])
    _set_color(ne, 'node_backdrop', (*p["ui_bg"], 0.6))
    _try_set(ne, 'noodle_curving', 5)
    _set_color(ne, 'grid_levels', p["grid_line"])
    _set_color(ne, 'dash_alpha', p["ui_text_muted"])

    # Node type colors
    _set_color(ne, 'converter_node', p["node_converter"])
    _set_color(ne, 'color_node', p["node_color"])
    _set_color(ne, 'group_node', p["node_group"])
    _set_color(ne, 'interface_node', p["node_interface"])
    _set_color(ne, 'input_node', p["node_input"])
    _set_color(ne, 'output_node', p["node_output"])
    _set_color(ne, 'matte_node', p["node_matte"])
    _set_color(ne, 'distor_node', p["node_distort"])
    _set_color(ne, 'filter_node', p["node_filter"])
    _set_color(ne, 'pattern_node', p["node_pattern"])
    _set_color(ne, 'script_node', p["node_script"])
    _set_color(ne, 'shader_node', p["node_shader"])
    _set_color(ne, 'texture_node', p["node_texture"])
    _set_color(ne, 'vector_node', p["node_vector"])
    _set_color(ne, 'layout_node', p["node_layout"])
    _set_color(ne, 'frame_node', (*p["node_frame"], 0.6))
    _set_color(ne, 'group_socket_node', p["node_group"])

    # =====================================================================
    # NLA EDITOR
    # =====================================================================
    set_space_generic(theme.nla_editor.space)
    nla = theme.nla_editor
    _set_color(nla, 'grid', p["grid_line"])
    _set_color(nla, 'frame_current', p["success"])
    _set_color(nla, 'strips', p["nla_strip"])
    _set_color(nla, 'strips_selected', p["nla_strip_selected"])
    _set_color(nla, 'transition_strips', p["nla_transition"])
    _set_color(nla, 'transition_strips_selected', p["nla_strip_selected"])
    _set_color(nla, 'meta_strips', p["nla_meta"])
    _set_color(nla, 'meta_strips_selected', p["nla_strip_selected"])
    _set_color(nla, 'sound_strips', p["nla_sound"])
    _set_color(nla, 'sound_strips_selected', p["nla_strip_selected"])
    _set_color(nla, 'tweak', p["nla_tweak"])
    _set_color(nla, 'tweak_duplicate', p["nla_tweak_dup"])
    _set_color(nla, 'keyframe_border', p["ui_border"])
    _set_color(nla, 'keyframe_border_selected', p["ui_text"])
    _set_color(nla, 'view_sliders', p["ui_accent"])
    _set_color(nla, 'dopesheet_channel', (*p["ui_panel"], 0.5))
    _set_color(nla, 'dopesheet_subchannel', (*p["ui_card"], 0.5))
    _set_color(nla, 'time_scrub_background', (*p["ui_panel"], 0.75))
    _set_color(nla, 'time_marker_line', (*p["warning"], 0.5))
    _set_color(nla, 'time_marker_line_selected', (*p["ui_accent"], 0.8))

    # =====================================================================
    # TIMELINE
    # =====================================================================
    try:
        set_space_generic(theme.timeline.space)
        tl = theme.timeline
        _set_color(tl, 'grid', p["grid_line"])
        _set_color(tl, 'frame_current', p["success"])
        _set_color(tl, 'time_scrub_background', (*p["ui_panel"], 0.75))
        _set_color(tl, 'time_marker_line', (*p["warning"], 0.5))
        _set_color(tl, 'time_marker_line_selected', (*p["ui_accent"], 0.8))
    except AttributeError:
        pass

    # =====================================================================
    # CONSOLE
    # =====================================================================
    set_space_generic(theme.console.space)
    c = theme.console
    _set_color(c, 'line_output', p["ui_text"])
    _set_color(c, 'line_input', p["success"])
    _set_color(c, 'line_info', p["info_color"])
    _set_color(c, 'line_error', p["danger"])
    _set_color(c, 'cursor', p["ui_cursor"])
    _set_color(c, 'select', p["ui_selection"])

    # =====================================================================
    # INFO
    # =====================================================================
    set_space_generic(theme.info.space)
    inf = theme.info
    _set_color(inf, 'info_selected', p["ui_selection"])
    _set_color(inf, 'info_selected_text', p["ui_selection_text"])
    _set_color(inf, 'info_error', (*p["danger"], 0.3))
    _set_color(inf, 'info_error_text', p["danger"])
    _set_color(inf, 'info_warning', (*p["warning"], 0.3))
    _set_color(inf, 'info_warning_text', p["warning"])
    _set_color(inf, 'info_info', (*p["info_color"], 0.3))
    _set_color(inf, 'info_info_text', p["info_color"])
    _set_color(inf, 'info_debug', (*p["accent_secondary"], 0.3))
    _set_color(inf, 'info_debug_text', p["accent_secondary"])
    _set_color(inf, 'info_property', (*p["ui_accent"], 0.3))
    _set_color(inf, 'info_property_text', p["ui_accent"])
    _set_color(inf, 'info_operator', (*p["success"], 0.3))
    _set_color(inf, 'info_operator_text', p["success"])

    # =====================================================================
    # PREFERENCES
    # =====================================================================
    set_space_generic(theme.preferences.space)

    # =====================================================================
    # FILE BROWSER
    # =====================================================================
    set_space_generic(theme.file_browser.space)
    _set_color(theme.file_browser, 'selected_file', p["ui_selection"])
    _set_color(theme.file_browser, 'row_alternate', (*p["row_alternate"][:3], 0.5))

    # =====================================================================
    # TOPBAR
    # =====================================================================
    try:
        set_space_generic(theme.topbar.space)
    except AttributeError:
        pass

    # =====================================================================
    # STATUSBAR
    # =====================================================================
    set_space_generic(theme.statusbar.space)

    # =====================================================================
    # SPREADSHEET
    # =====================================================================
    try:
        set_space_generic(theme.spreadsheet.space)
        _set_color(theme.spreadsheet, 'row_alternate', (*p["row_alternate"][:3], 0.5))
    except AttributeError:
        pass

    # =====================================================================
    # IMAGE EDITOR
    # =====================================================================
    set_space_generic(theme.image_editor.space)
    ie = theme.image_editor
    _set_color(ie, 'grid', p["grid_line"])
    _set_color(ie, 'vertex', p["vertex_color"])
    _set_color(ie, 'vertex_select', p["edge_select"])
    _set_color(ie, 'vertex_unreferenced', p["danger"])
    _try_set(ie, 'vertex_size', 3)
    _set_color(ie, 'face_select', (*p["ui_accent"], 0.25))
    _set_color(ie, 'face_dot', p["ui_accent"])
    _set_color(ie, 'editmesh_active', (*p["ui_accent"], 0.5))
    _set_color(ie, 'wire_edit', p["wire_edit"])
    _set_color(ie, 'frame_current', p["success"])
    _set_color(ie, 'handle_free', p["danger"])
    _set_color(ie, 'handle_auto', p["success"])
    _set_color(ie, 'handle_align', p["magenta"])
    _set_color(ie, 'handle_sel_free', p["danger"])
    _set_color(ie, 'handle_sel_auto', p["success"])
    _set_color(ie, 'handle_sel_align', p["bright_magenta"])
    _set_color(ie, 'paint_curve_pivot', p["danger"])
    _set_color(ie, 'paint_curve_handle', p["success"])
    _set_color(ie, 'uv_shadow', (*p["ui_text_disabled"], 0.3))
    _set_color(ie, 'stitch_indicator_active', p["success"])
    _set_color(ie, 'stitch_indicator_disconnected', p["danger"])

    # =====================================================================
    # SEQUENCE EDITOR
    # =====================================================================
    set_space_generic(theme.sequence_editor.space)
    se = theme.sequence_editor
    _set_color(se, 'grid', p["grid_line"])
    _set_color(se, 'frame_current', p["success"])
    _set_color(se, 'keyframe', p["warning"])
    _set_color(se, 'draw_action', (*p["ui_accent"], 0.5))
    _set_color(se, 'movie_strip', (*p["accent_secondary"], 0.5))
    _set_color(se, 'movieclip_strip', (*p["magenta"], 0.5))
    _set_color(se, 'image_strip', (*p["accent_primary"], 0.5))
    _set_color(se, 'scene_strip', (*p["success"], 0.5))
    _set_color(se, 'audio_strip', (*p["accent_secondary"], 0.5))
    _set_color(se, 'effect_strip', (*p["magenta"], 0.5))
    _set_color(se, 'transition_strip', (*p["bright_magenta"], 0.5))
    _set_color(se, 'color_strip', (*p["warning"], 0.5))
    _set_color(se, 'meta_strip', (*p["ui_card"], 0.5))
    _set_color(se, 'text_strip', (*p["ui_text"], 0.5))
    _set_color(se, 'active_strip', (*p["obj_active"], 0.5))
    _set_color(se, 'selected_strip', (*p["obj_selected"], 0.5))
    _set_color(se, 'time_scrub_background', (*p["ui_panel"], 0.75))
    _set_color(se, 'row_alternate', (*p["row_alternate"][:3], 0.5))
    _set_color(se, 'window_sliders', p["ui_accent"])

    # =====================================================================
    # CLIP EDITOR
    # =====================================================================
    set_space_generic(theme.clip_editor.space)
    ce = theme.clip_editor
    _set_color(ce, 'grid', p["grid_line"])
    _set_color(ce, 'frame_current', p["success"])
    _set_color(ce, 'marker_outline', p["ui_border"])
    _set_color(ce, 'marker', p["ui_accent"])
    _set_color(ce, 'active_marker', p["obj_active"])
    _set_color(ce, 'selected_marker', p["obj_selected"])
    _set_color(ce, 'dis_marker', p["ui_text_disabled"])
    _set_color(ce, 'locked_marker', p["danger"])
    _set_color(ce, 'handle_vertex', p["vertex_color"])
    _set_color(ce, 'handle_vertex_select', p["edge_select"])
    _try_set(ce, 'handle_vertex_size', 5)
    _set_color(ce, 'path_before', p["danger"])
    _set_color(ce, 'path_after', p["accent_secondary"])
    _set_color(ce, 'path_keyframe_before', p["danger"])
    _set_color(ce, 'path_keyframe_after', p["accent_secondary"])
    _set_color(ce, 'strips', p["ui_accent"])
    _set_color(ce, 'strips_selected', p["obj_selected"])
    _set_color(ce, 'time_scrub_background', (*p["ui_panel"], 0.75))

    # =====================================================================
    # FORCE UI REDRAW
    # =====================================================================
    for area in bpy.context.screen.areas:
        area.tag_redraw()

    return True


def save_user_preferences():
    """Save current preferences (including theme) as startup."""
    try:
        import bpy
        bpy.ops.wm.save_userpref()
        return True
    except Exception as e:
        return str(e)
