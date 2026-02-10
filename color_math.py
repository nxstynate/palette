"""
Color math utilities for HSL/HSV conversions, blending, contrast, and ramp generation.
"""

import colorsys
import math


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def clamp_rgb(rgb):
    return tuple(clamp(c) for c in rgb)


# --- Conversions ---

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


# --- Luminance & Contrast ---

def luminance(r, g, b):
    """Relative luminance per WCAG."""
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(fg, bg):
    """WCAG contrast ratio between two RGB tuples."""
    l1 = luminance(*fg) + 0.05
    l2 = luminance(*bg) + 0.05
    return max(l1, l2) / min(l1, l2)


def is_dark(rgb):
    """Return True if the color is considered dark."""
    return luminance(*rgb) < 0.18


# --- Manipulations ---

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
    """Linear blend: result = a*(1-t) + b*t."""
    return tuple(clamp(a[i] * (1.0 - t) + b[i] * t) for i in range(3))


def set_lightness(rgb, target_l):
    """Set the HSL lightness to a specific value."""
    h, s, _ = rgb_to_hsl(*rgb)
    return hsl_to_rgb(h, s, clamp(target_l))


def set_saturation(rgb, target_s):
    h, _, l = rgb_to_hsl(*rgb)
    return hsl_to_rgb(h, clamp(target_s), l)


def ensure_contrast(fg, bg, min_ratio=4.5):
    """
    Adjust fg luminance until contrast ratio vs bg meets min_ratio.
    Preserves hue and saturation as much as possible.
    """
    if contrast_ratio(fg, bg) >= min_ratio:
        return fg

    h, s, l = rgb_to_hsl(*fg)
    bg_lum = luminance(*bg)

    # decide direction: if bg is dark, push fg lighter; else darker
    if bg_lum < 0.5:
        # go lighter
        for step in range(100):
            l = clamp(l + 0.01)
            candidate = hsl_to_rgb(h, s, l)
            if contrast_ratio(candidate, bg) >= min_ratio:
                return candidate
    else:
        # go darker
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
    """
    Create a ramp of shades from darker to lighter around base.
    Returns list of (steps) colors.
    """
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
