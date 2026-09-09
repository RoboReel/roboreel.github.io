"""Shared palette, type and diagram primitives for the RoboReel animations.

Everything here mirrors the site's design tokens in assets/css/style.css so the
rendered video sits on the page as if it were part of it. Keep the two in sync:
if a colour changes there, change it here.
"""
import glob
import os

import manimpango
from manim import *

_HERE = os.path.dirname(os.path.abspath(__file__))

# Register the site's webfonts with Pango so Text() can use them by family name.
for _f in sorted(glob.glob(os.path.join(_HERE, "fonts", "*.ttf"))):
    manimpango.register_font(_f)

# ---- palette (light theme tokens from style.css) ----
BG           = "#f7f1e4"
BG_PLANE     = "#efe6d3"
SURFACE      = "#fffdf7"
INK          = "#1c1810"
INK_SOFT     = "#5b5647"
MUTED        = "#8a8471"
LINE         = "#e2d8c2"
LINE_STRONG  = "#cfc2a2"
ACCENT       = "#c15a2c"
ACCENT_INK   = "#7a3113"
ACCENT_SOFT  = "#f4ddc4"
FILM         = "#171310"
FILM_INK     = "#f3ead9"
GOOD         = "#2b6b3f"
BAD          = "#a8352a"
SIM          = "#2f6b8f"   # cool blue for the simulation half of the pairing

DISPLAY = "Space Grotesk"
MONO    = "Fira Code"
SUITS   = "DejaVu Sans"    # the only installed family carrying the suit glyphs


# ---- type ----
def sg(t, size=30, color=INK, weight=NORMAL):
    """Display type - headings and box labels."""
    return Text(t, font=DISPLAY, font_size=size, color=color, weight=weight)


def mono(t, size=18, color=MUTED, weight=NORMAL, spacing=0.06):
    """Mono type - the site uses it for eyebrows, tags and small captions."""
    return Text(t, font=MONO, font_size=size, color=color, weight=weight).set_opacity(1)


def eyebrow(t):
    """The site's pill-shaped section label."""
    lab = mono(t.upper(), 19, ACCENT_INK, weight=BOLD)
    pill = RoundedRectangle(
        width=lab.width + 0.5, height=lab.height + 0.34, corner_radius=0.17,
        fill_color=ACCENT_SOFT, fill_opacity=1, stroke_width=0,
    )
    lab.move_to(pill)
    return VGroup(pill, lab)


# ---- containers ----
def card(w, h, fill=SURFACE, stroke=LINE_STRONG, r=0.18, sw=2.0):
    return RoundedRectangle(
        width=w, height=h, corner_radius=r,
        fill_color=fill, fill_opacity=1, stroke_color=stroke, stroke_width=sw,
    )


def titled_card(w, h, title, sub=None, accent=INK):
    """A card with a heading (and optional mono sub-label) pinned to its top."""
    box = card(w, h)
    head = sg(title, 25, accent, weight=BOLD).move_to(box.get_top() + DOWN * 0.36)
    parts = [box, head]
    if sub:
        parts.append(mono(sub.upper(), 15, MUTED).next_to(head, DOWN, buff=0.13))
    return VGroup(*parts)


def filmstrip(w, h, fill=FILM):
    """The site's film-frame motif: dark panel with sprocket holes top and bottom."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                            fill_color=fill, fill_opacity=1, stroke_width=0)
    holes = VGroup()
    step, n = 0.34, max(int(w / 0.34) - 1, 1)
    x0 = -(n - 1) * step / 2
    for i in range(n):
        for s in (1, -1):
            holes.add(RoundedRectangle(
                width=0.14, height=0.095, corner_radius=0.035,
                fill_color=BG, fill_opacity=1, stroke_width=0,
            ).move_to(body.get_center() + RIGHT * (x0 + i * step) + UP * s * (h / 2 - 0.12)))
    return VGroup(body, holes)


# ---- diagram primitives ----
def arrow(a, b, color=INK_SOFT, sw=3.5, buff=0.16):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.16, tip_length=0.2)


def camera(s=0.42, color=INK_SOFT):
    body = RoundedRectangle(width=s * 1.55, height=s, corner_radius=s * 0.2,
                            stroke_color=color, stroke_width=2.6, fill_opacity=0)
    lens = Circle(radius=s * 0.27, stroke_color=color, stroke_width=2.6)
    return VGroup(body, lens)


def mlp(layers=(3, 5, 4, 2), w=1.7, h=1.35, color=ACCENT, dot_r=0.052, edge_op=0.28):
    """Node-and-edge network, the visual shorthand for a learned policy."""
    cols = []
    for i, n in enumerate(layers):
        x = -w / 2 + (i * w / (len(layers) - 1) if len(layers) > 1 else 0)
        cols.append(VGroup(*[
            Dot(radius=dot_r, color=color).move_to(
                [x, (j - (n - 1) / 2) * (h / max(n - 1, 1)), 0])
            for j in range(n)
        ]))
    edges = VGroup()
    for a, b in zip(cols, cols[1:]):
        for p in a:
            for q in b:
                edges.add(Line(p.get_center(), q.get_center(),
                               stroke_width=0.9, stroke_color=color, stroke_opacity=edge_op))
    return VGroup(edges, *cols)


def robot_arm(scale=1.0, color=SIM):
    """A minimal 3-link arm with a parallel gripper.

    Built from explicit joint coordinates rather than chained next_to calls, so
    the links actually meet at the joints.
    """
    P = [np.array(p, dtype=float) for p in (
        (0.00, -0.44, 0), (0.00, 0.00, 0), (0.44, 0.32, 0), (0.90, 0.16, 0))]
    base = RoundedRectangle(width=0.56, height=0.16, corner_radius=0.05,
                            fill_color=color, fill_opacity=1, stroke_width=0).move_to(P[0] + DOWN * 0.06)
    links = VGroup(
        Line(P[0], P[1], stroke_width=9, color=color),
        Line(P[1], P[2], stroke_width=7.5, color=color),
        Line(P[2], P[3], stroke_width=6, color=color),
    )
    joints = VGroup(*[Dot(radius=r, color=color).move_to(p)
                      for p, r in zip(P[1:3], (0.062, 0.055))])
    grip = VGroup(
        Line(UP * 0.1, DOWN * 0.1, stroke_width=5.5, color=color),
        Line(UP * 0.1, UP * 0.1 + RIGHT * 0.16, stroke_width=5.5, color=color),
        Line(DOWN * 0.1, DOWN * 0.1 + RIGHT * 0.16, stroke_width=5.5, color=color),
    ).move_to(P[3] + RIGHT * 0.04)
    return VGroup(base, links, joints, grip).scale(scale)


def hand_skeleton(scale=1.0, color=ACCENT, dot=0.045):
    """Wrist, knuckle line, four fingers and a thumb - the hand-pose annotation.

    Fingers grow from their own knuckles rather than all radiating from one
    point, which is what stops it reading as a starburst.
    """
    g, pts = VGroup(), []
    wrist = np.array([0.0, -0.46, 0.0])

    def chain(start, ang_deg, seg_lens, fan=0.0):
        prev, a = start, np.deg2rad(ang_deg)
        out = [start]
        for L in seg_lens:
            nxt = prev + np.array([np.cos(a), np.sin(a), 0]) * L
            g.add(Line(prev, nxt, stroke_width=2.8, color=color, stroke_opacity=0.9))
            out.append(nxt)
            prev, a = nxt, a + np.deg2rad(fan)
        return out

    # knuckles across the top of the palm
    knuckles = [np.array([x, 0.02, 0.0]) for x in (-0.21, -0.06, 0.09, 0.23)]
    palm = Polygon(wrist + LEFT * 0.13, knuckles[0] + LEFT * 0.05,
                   knuckles[-1] + RIGHT * 0.05, wrist + RIGHT * 0.13,
                   stroke_color=color, stroke_width=2.4, stroke_opacity=0.55,
                   fill_color=color, fill_opacity=0.10)
    g.add(palm)
    for k in knuckles:
        g.add(Line(wrist, k, stroke_width=2.0, color=color, stroke_opacity=0.45))
    pts.append(wrist)

    for k, (ang, lens) in zip(knuckles, (
            (99, (0.20, 0.15, 0.11)), (92, (0.23, 0.17, 0.12)),
            (85, (0.21, 0.16, 0.11)), (76, (0.17, 0.13, 0.09)))):
        pts += chain(k, ang, lens, fan=-4)
    pts += chain(wrist + RIGHT * 0.02 + UP * 0.06, 32, (0.20, 0.15), fan=14)  # thumb

    for p in pts:
        g.add(Dot(radius=dot, color=color).move_to(p))
    return g.scale(scale)


def table(w=1.9, color=INK_SOFT, op=0.16):
    """The tabletop the tasks happen on."""
    top = Rectangle(width=w, height=0.11, fill_color=color, fill_opacity=1, stroke_width=0)
    legs = VGroup(
        Line(ORIGIN, DOWN * 0.34, stroke_width=3.2, color=color).next_to(top, DOWN, buff=0).shift(LEFT * (w / 2 - 0.14)),
        Line(ORIGIN, DOWN * 0.34, stroke_width=3.2, color=color).next_to(top, DOWN, buff=0).shift(RIGHT * (w / 2 - 0.14)),
    )
    return VGroup(top, legs).set_opacity(1)


def screen(path, w, border=LINE_STRONG, sw=2.0, caption=None):
    """A real video frame in a bordered panel - used only where showing actual
    footage says more than a drawing would. An optional caption is overlaid on
    the frame (the site does the same) so it costs no extra height."""
    img = ImageMobject(path).set(width=w)
    parts = [img]
    if caption:
        bar = Rectangle(width=img.width, height=0.32, fill_color=FILM,
                        fill_opacity=0.82, stroke_width=0)
        bar.move_to(img.get_bottom() + UP * 0.16)
        lab = mono(caption.upper(), 13, FILM_INK, weight=BOLD).move_to(bar)
        if lab.width > img.width - 0.22:
            lab.scale((img.width - 0.22) / lab.width)
        parts += [bar, lab]
    parts.append(Rectangle(width=img.width, height=img.height,
                           stroke_color=border, stroke_width=sw, fill_opacity=0))
    return Group(*parts)


def subscripted(base, sub_, size=22, color=INK, font=None):
    """o_t / a_t style labels - Pango has no subscript run, so compose one."""
    font = font or MONO
    mk = (lambda t, s: Text(t, font=font, font_size=s, color=color))
    b = mk(base, size)
    t = mk(sub_, size * 0.62)
    t.next_to(b, RIGHT, buff=0.04).align_to(b, DOWN).shift(DOWN * 0.05)
    return VGroup(b, t)


def suit(ch, size=34, color=ACCENT):
    return Text(ch, font=SUITS, font_size=size, color=color)
