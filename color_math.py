"""
Color math utilities for perceptual color manipulation.

Primary color space: OKLCH (perceptually uniform lightness, chroma, hue).
Legacy HSL/HSV functions retained for backward compatibility.
WCAG contrast and luminance calculations use sRGB linear light.
"""

import colorsys
import math


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def clamp_rgb(rgb):
    return tuple(clamp(c) for c in rgb)


# =========================================================================
# sRGB <-> Linear sRGB
# =========================================================================

def _srgb_to_linear(c):
    """Single sRGB channel (0-1) to linear light."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c):
    """Single linear light channel to sRGB (0-1)."""
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055


# =========================================================================
# Linear sRGB <-> Oklab
# =========================================================================

def _linear_rgb_to_oklab(r, g, b):
    """Convert linear sRGB (0-1) to Oklab (L, a, b)."""
    l_ = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m_ = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2220049874 * g + 0.6696925507 * b

    l_ = math.copysign(abs(l_) ** (1.0 / 3.0), l_) if l_ != 0 else 0.0
    m_ = math.copysign(abs(m_) ** (1.0 / 3.0), m_) if m_ != 0 else 0.0
    s_ = math.copysign(abs(s_) ** (1.0 / 3.0), s_) if s_ != 0 else 0.0

    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b_val = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_

    return (L, a, b_val)


def _oklab_to_linear_rgb(L, a, b):
    """Convert Oklab (L, a, b) to linear sRGB (0-1)."""
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l_ = l_ * l_ * l_
    m_ = m_ * m_ * m_
    s_ = s_ * s_ * s_

    r = +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    g = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    b_val = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_

    return (r, g, b_val)


# =========================================================================
# sRGB <-> OKLCH
# =========================================================================

def rgb_to_oklch(r, g, b):
    """
    Convert sRGB (0-1) to OKLCH.
    Returns (L, C, H) where L is 0-1, C >= 0, H is 0-360 degrees.
    """
    lr = _srgb_to_linear(r)
    lg = _srgb_to_linear(g)
    lb = _srgb_to_linear(b)

    L, a, b_val = _linear_rgb_to_oklab(lr, lg, lb)

    C = math.sqrt(a * a + b_val * b_val)
    H = math.degrees(math.atan2(b_val, a)) % 360.0

    return (L, C, H)


def oklch_to_rgb(L, C, H):
    """
    Convert OKLCH to sRGB (0-1), clamped to gamut.
    L is 0-1, C >= 0, H is 0-360 degrees.
    """
    H_rad = math.radians(H)
    a = C * math.cos(H_rad)
    b = C * math.sin(H_rad)

    lr, lg, lb = _oklab_to_linear_rgb(L, a, b)

    r = clamp(_linear_to_srgb(lr))
    g = clamp(_linear_to_srgb(lg))
    b_out = clamp(_linear_to_srgb(lb))

    return (r, g, b_out)


def oklch_max_chroma(L, H, tolerance=0.001):
    """Find maximum in-gamut chroma for a given L and H in sRGB."""
    lo, hi = 0.0, 0.4
    for _ in range(32):
        mid = (lo + hi) / 2.0
        H_rad = math.radians(H)
        a = mid * math.cos(H_rad)
        b = mid * math.sin(H_rad)
        lr, lg, lb = _oklab_to_linear_rgb(L, a, b)
        if lr >= -tolerance and lr <= 1.0 + tolerance and \
           lg >= -tolerance and lg <= 1.0 + tolerance and \
           lb >= -tolerance and lb <= 1.0 + tolerance:
            lo = mid
        else:
            hi = mid
    return lo


# =========================================================================
# OKLCH-based color manipulation
# =========================================================================

def ok_lighten(rgb, amount):
    """Lighten a color by shifting L in OKLCH. Perceptually uniform."""
    L, C, H = rgb_to_oklch(*rgb)
    L = clamp(L + amount)
    max_c = oklch_max_chroma(L, H)
    C = min(C, max_c)
    return oklch_to_rgb(L, C, H)


def ok_darken(rgb, amount):
    """Darken a color by shifting L in OKLCH. Perceptually uniform."""
    L, C, H = rgb_to_oklch(*rgb)
    L = clamp(L - amount)
    max_c = oklch_max_chroma(L, H)
    C = min(C, max_c)
    return oklch_to_rgb(L, C, H)


def ok_set_lightness(rgb, target_L):
    """Set OKLCH lightness to a specific value, preserving hue and chroma."""
    _, C, H = rgb_to_oklch(*rgb)
    L = clamp(target_L)
    max_c = oklch_max_chroma(L, H)
    C = min(C, max_c)
    return oklch_to_rgb(L, C, H)


def ok_set_chroma(rgb, target_C):
    """Set OKLCH chroma to a specific value, preserving lightness and hue."""
    L, _, H = rgb_to_oklch(*rgb)
    max_c = oklch_max_chroma(L, H)
    C = min(clamp(target_C, 0.0, 0.4), max_c)
    return oklch_to_rgb(L, C, H)


def ok_desaturate(rgb, amount):
    """Reduce chroma by amount in OKLCH."""
    L, C, H = rgb_to_oklch(*rgb)
    C = max(0.0, C - amount)
    return oklch_to_rgb(L, C, H)


def ok_saturate(rgb, amount):
    """Increase chroma by amount in OKLCH, gamut-clipped."""
    L, C, H = rgb_to_oklch(*rgb)
    C = C + amount
    max_c = oklch_max_chroma(L, H)
    C = min(C, max_c)
    return oklch_to_rgb(L, C, H)


def ok_mix(a, b, t):
    """
    Mix two colors in Oklab space (perceptually linear blending).
    t=0 returns a, t=1 returns b.
    """
    La, Ca, Ha = rgb_to_oklch(*a)
    Lb, Cb, Hb = rgb_to_oklch(*b)

    # Mix L and C linearly
    L = La * (1 - t) + Lb * t
    C = Ca * (1 - t) + Cb * t

    # Mix hue on the shortest arc
    diff = Hb - Ha
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360

    # Handle achromatic mixing
    if Ca < 0.001 and Cb < 0.001:
        H = 0
    elif Ca < 0.001:
        H = Hb
    elif Cb < 0.001:
        H = Ha
    else:
        H = (Ha + diff * t) % 360

    max_c = oklch_max_chroma(L, H)
    C = min(C, max_c)
    return oklch_to_rgb(L, C, H)


def ok_ensure_contrast(fg, bg, min_ratio=4.5):
    """
    Adjust fg lightness in OKLCH until contrast ratio vs bg meets min_ratio.
    Preserves hue and chroma as much as possible.
    """
    if contrast_ratio(fg, bg) >= min_ratio:
        return fg

    L, C, H = rgb_to_oklch(*fg)
    bg_L = rgb_to_oklch(*bg)[0]

    direction = 1.0 if bg_L < 0.5 else -1.0

    for step in range(200):
        L = clamp(L + direction * 0.005)
        max_c = oklch_max_chroma(L, H)
        c = min(C, max_c)
        candidate = oklch_to_rgb(L, c, H)
        if contrast_ratio(candidate, bg) >= min_ratio:
            return candidate

    return oklch_to_rgb(L, min(C, oklch_max_chroma(L, H)), H)


# =========================================================================
# Surface ramp generation (OKLCH-based)
# =========================================================================

def generate_surface_ramp(bg, elevated, steps=10):
    """
    Generate a perceptually uniform surface elevation ramp by interpolating
    between two REAL colors from the source theme.

    Professional design systems (Material Design 3, Nord, Solarized) all
    derive surfaces from their palette's own color DNA — they don't
    generate synthetic grays. We follow the same principle:

    - bg anchors the base (ramp[1])
    - elevated anchors the midpoint (~ramp[5])
    - The ramp extrapolates below bg for recessed surfaces (ramp[0])
      and above elevated for interactive states (ramp[6-9])

    Chroma never decreases below bg's own chroma, since professional themes
    (Nord, Solarized, Material) show surfaces gaining tint at elevation.

    Args:
        bg: Background RGB tuple — THE theme identity color
        elevated: A brighter surface color from the theme (typically bright_black
                  for dark themes, or selection/white for light themes)
        steps: Number of ramp stops (default 10)

    Returns:
        List of RGB tuples. ramp[1] ≈ bg, mid-ramp ≈ elevated.
    """
    bg_L, bg_C, bg_H = rgb_to_oklch(*bg)
    el_L, el_C, el_H = rgb_to_oklch(*elevated)
    dark = bg_L < 0.5

    # Cap: the surface ramp should cover a reasonable L range.
    # Too large a gap (Gruvbox bb is L=0.62 vs bg L=0.27) would make
    # high-elevation surfaces too bright for readability.
    L_gap = abs(el_L - bg_L)
    max_gap = 0.16
    if L_gap > max_gap:
        ratio = max_gap / L_gap
        el_L = bg_L + (el_L - bg_L) * ratio
        el_C = bg_C + (el_C - bg_C) * ratio
        h_diff = el_H - bg_H
        if h_diff > 180: h_diff -= 360
        elif h_diff < -180: h_diff += 360
        el_H = (bg_H + h_diff * ratio) % 360

    # Chroma floor: professional themes show surfaces gaining tint at
    # elevation, never losing it. If elevated has less chroma than bg,
    # we keep bg's chroma as the floor and add a gentle boost.
    min_C = bg_C

    ramp = []
    for i in range(steps):
        # Map ramp indices to interpolation parameter:
        # i=0: slightly below bg (recessed)   t ≈ -0.2
        # i=1: bg itself                       t = 0.0
        # i=5: elevated anchor region           t = 1.0
        # i=9: above elevated                  t ≈ 1.6
        if i == 0:
            t = -0.2
        else:
            t = (i - 1) / 4.0

        # Interpolate L
        new_L = clamp(bg_L + (el_L - bg_L) * t, 0.01, 0.99)

        # Interpolate C with chroma floor
        raw_C = bg_C + (el_C - bg_C) * t
        # Gentle chroma boost with elevation (professional systems do this)
        boost = 0.003 * max(0, t)
        new_C = max(min_C, raw_C) + boost

        # Interpolate H on shortest arc
        h_diff = el_H - bg_H
        if h_diff > 180: h_diff -= 360
        elif h_diff < -180: h_diff += 360
        new_H = (bg_H + h_diff * t) % 360

        # Gamut clip
        max_c = oklch_max_chroma(new_L, new_H)
        new_C = min(new_C, max_c)

        ramp.append(oklch_to_rgb(new_L, new_C, new_H))

    return ramp


def generate_categorical(n, target_L, target_C, start_H=30.0):
    """
    Generate n perceptually equidistant colors via OKLCH hue rotation.

    All colors share the same lightness and chroma, guaranteeing they
    are equally prominent and distinguishable.

    Args:
        n: Number of colors to generate
        target_L: OKLCH lightness (0-1) for all colors
        target_C: OKLCH chroma for all colors
        start_H: Starting hue angle (degrees)

    Returns:
        List of n RGB tuples with maximally spaced hues.
    """
    colors = []
    for i in range(n):
        H = (start_H + i * (360.0 / n)) % 360.0
        max_c = oklch_max_chroma(target_L, H)
        C = min(target_C, max_c)
        colors.append(oklch_to_rgb(target_L, C, H))
    return colors


# =========================================================================
# HSL conversions (legacy, retained for backward compat)
# =========================================================================

def rgb_to_hsl(r, g, b):
    """Convert RGB (0-1) to HSL (H 0-1, S 0-1, L 0-1)."""
    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin
    l = (cmax + cmin) / 2.0

    if delta < 1e-7:
        return (0.0, 0.0, l)

    s = delta / (1.0 - abs(2.0 * l - 1.0)) if abs(2.0 * l - 1.0) < 1.0 else 0.0
    s = clamp(s)

    if cmax == r:
        h = ((g - b) / delta) % 6.0
    elif cmax == g:
        h = (b - r) / delta + 2.0
    else:
        h = (r - g) / delta + 4.0

    h = (h / 6.0) % 1.0
    return (h, s, l)


def hsl_to_rgb(h, s, l):
    """Convert HSL (0-1) to RGB (0-1)."""
    if s < 1e-7:
        return (l, l, l)
    q = l * (1.0 + s) if l < 0.5 else l + s - l * s
    p = 2.0 * l - q

    def hue2rgb(t):
        t = t % 1.0
        if t < 1.0 / 6.0:
            return p + (q - p) * 6.0 * t
        if t < 0.5:
            return q
        if t < 2.0 / 3.0:
            return p + (q - p) * (2.0 / 3.0 - t) * 6.0
        return p

    return (
        clamp(hue2rgb(h + 1.0 / 3.0)),
        clamp(hue2rgb(h)),
        clamp(hue2rgb(h - 1.0 / 3.0)),
    )


def rgb_to_hsv(r, g, b):
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_rgb(h, s, v):
    return colorsys.hsv_to_rgb(h, s, v)


# =========================================================================
# Luminance & Contrast (sRGB-based, per WCAG)
# =========================================================================

def luminance(r, g, b):
    """Relative luminance per WCAG."""
    return 0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g) + 0.0722 * _srgb_to_linear(b)


def contrast_ratio(fg, bg):
    """WCAG contrast ratio between two RGB tuples."""
    l1 = luminance(*fg) + 0.05
    l2 = luminance(*bg) + 0.05
    return max(l1, l2) / min(l1, l2)


def is_dark(rgb):
    """Return True if the color is considered dark."""
    return luminance(*rgb) < 0.18


# =========================================================================
# Legacy HSL manipulation functions
# =========================================================================

def lighten(rgb, amount):
    """Lighten a color by shifting L in HSL. amount is 0-1 range."""
    h, s, l = rgb_to_hsl(*rgb)
    l = clamp(l + amount)
    return hsl_to_rgb(h, s, l)


def darken(rgb, amount):
    """Darken a color by shifting L in HSL."""
    h, s, l = rgb_to_hsl(*rgb)
    l = clamp(l - amount)
    return hsl_to_rgb(h, s, l)


def saturate(rgb, amount):
    h, s, l = rgb_to_hsl(*rgb)
    s = clamp(s + amount)
    return hsl_to_rgb(h, s, l)


def desaturate(rgb, amount):
    h, s, l = rgb_to_hsl(*rgb)
    s = clamp(s - amount)
    return hsl_to_rgb(h, s, l)


def mix(a, b, t):
    """Linear blend in sRGB: result = a*(1-t) + b*t."""
    return tuple(clamp(a[i] * (1.0 - t) + b[i] * t) for i in range(3))


def set_lightness(rgb, target_l):
    """Set the HSL lightness to a specific value."""
    h, s, _ = rgb_to_hsl(*rgb)
    return hsl_to_rgb(h, s, clamp(target_l))


def set_saturation(rgb, target_s):
    h, _, l = rgb_to_hsl(*rgb)
    return hsl_to_rgb(h, clamp(target_s), l)


def ensure_contrast(fg, bg, min_ratio=4.5):
    """Adjust fg luminance until contrast ratio vs bg meets min_ratio."""
    if contrast_ratio(fg, bg) >= min_ratio:
        return fg

    h, s, l = rgb_to_hsl(*fg)
    bg_lum = luminance(*bg)

    if bg_lum < 0.5:
        for step in range(100):
            l = clamp(l + 0.01)
            candidate = hsl_to_rgb(h, s, l)
            if contrast_ratio(candidate, bg) >= min_ratio:
                return candidate
    else:
        for step in range(100):
            l = clamp(l - 0.01)
            candidate = hsl_to_rgb(h, s, l)
            if contrast_ratio(candidate, bg) >= min_ratio:
                return candidate

    return hsl_to_rgb(h, s, l)


def tint_from(color, reference, t):
    """Mix color toward reference by factor t."""
    return mix(color, reference, t)


def shade_ramp(base, steps=5, spread=0.15):
    """Create a ramp of shades from darker to lighter around base."""
    ramp = []
    h, s, l = rgb_to_hsl(*base)
    for i in range(steps):
        frac = i / max(steps - 1, 1)
        offset = (frac - 0.5) * 2.0 * spread
        ramp.append(hsl_to_rgb(h, s, clamp(l + offset)))
    return ramp


def alpha(rgb, a):
    """Append alpha to an RGB tuple."""
    return (*rgb, a)


def with_alpha(rgba, a):
    """Replace alpha in an RGBA tuple."""
    return (*rgba[:3], a)
