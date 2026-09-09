"""RoboReel method overview animation.

Three acts, rendered as one continuous clip for the website:
  1. how the benchmark is built   (capture rig -> videos -> poses -> sim twin)
  2. the learning-from-observation loop, which is the paper's actual mechanism
  3. the four test suites the loop is evaluated under

Everything is drawn as vector diagram except the video panels, where showing
the real footage says more than a drawing would.

Render:  tools/anim/build.sh
Preview a single act:  .venv/bin/manim -qm -s overview.py Act2Still
"""
import os
import sys

from manim import *

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import *  # noqa: E402

FRAMES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames")
config.background_color = BG


def F(name):
    return os.path.join(FRAMES, name)


# --------------------------------------------------------------------------
# shared helpers
# --------------------------------------------------------------------------
def header(eb, title, sub=None, size=39):
    g = VGroup(eyebrow(eb), sg(title, size, INK, weight=BOLD))
    if sub:
        g.add(mono(sub, 18, MUTED))
    g.arrange(DOWN, buff=0.22, aligned_edge=LEFT).to_corner(UL, buff=0.5)
    return g


def chip(label, w=None, h=0.62, color=INK, fill=SURFACE, stroke=LINE_STRONG, size=21, bold=False):
    lab = label if isinstance(label, Mobject) else (
        sg(label, size, color, weight=BOLD) if bold else mono(label, size, color))
    box = RoundedRectangle(width=w or lab.width + 0.55, height=h, corner_radius=0.12,
                           fill_color=fill, fill_opacity=1, stroke_color=stroke, stroke_width=2)
    lab.move_to(box)
    return VGroup(box, lab)


def elbow(pts, color=INK_SOFT, sw=3.2):
    """Right-angled routed connector with an arrowhead on the final segment."""
    path = VMobject(stroke_color=color, stroke_width=sw)
    path.set_points_as_corners([np.array(p, dtype=float) for p in pts])
    a, b = np.array(pts[-2], dtype=float), np.array(pts[-1], dtype=float)
    d = (b - a) / (np.linalg.norm(b - a) or 1)
    head = Triangle(fill_color=color, fill_opacity=1, stroke_width=0).scale(0.115)
    head.rotate(angle_of_vector(d) - PI / 2).move_to(b)
    return VGroup(path, head)


def _path_of(conn):
    """A clean line to animate along. Arrows carry tip geometry that would make
    MoveAlongPath stutter at the head, so rebuild a plain segment for those."""
    if isinstance(conn, VGroup) and len(conn) == 2 and isinstance(conn[0], VMobject) \
            and not isinstance(conn[0], Triangle):
        return conn[0]
    return Line(conn.get_start(), conn.get_end())


def pulse(scene, conns, rt=0.85, r=0.09):
    """Send dots along one or more connectors - the 'data moving through' beat."""
    if not isinstance(conns, (list, tuple)):
        conns = [conns]
    dots, anims = [], []
    for conn, color in conns:
        p = _path_of(conn)
        dot = Dot(radius=r, color=color).move_to(p.get_start())
        dots.append(dot)
        anims.append(MoveAlongPath(dot, p, rate_func=rate_functions.ease_in_out_sine))
    scene.play(*anims, run_time=rt)
    scene.remove(*dots)


def lift(m, color=ACCENT):
    """Halo marking the currently-active element."""
    ring = m.copy().set_stroke(color=color, width=8, opacity=0.4).set_fill(opacity=0)
    return ring


# --------------------------------------------------------------------------
# ACT 1 - how the benchmark is built
# --------------------------------------------------------------------------
def act1_layout():
    W, H = 2.94, 3.35
    stages = []

    a = VGroup()
    tb = table(1.8).move_to(DOWN * 0.5)
    cams = VGroup(*[camera(0.33).move_to(p) for p in
                    (LEFT * 0.9 + UP * 0.5, UP * 0.72, RIGHT * 0.9 + UP * 0.5)])
    sight = VGroup(*[DashedLine(c.get_center(), tb.get_top(), stroke_width=1.6,
                                stroke_color=MUTED, dash_length=0.06).set_opacity(0.5)
                     for c in cams])
    a.add(sight, tb, cams, camera(0.25, ACCENT).move_to(RIGHT * 1.22 + DOWN * 0.02))
    stages.append((a, "Calibrated rig", "3 fixed + 1 egocentric"))

    # real frames inside the film cells
    b = Group(filmstrip(2.5, 1.62))
    for x, f in zip((-0.76, 0.0, 0.76),
                    ("strip_push_cube.jpg", "strip_bowl_in_plate.jpg", "strip_empty_basket.jpg")):
        b.add(ImageMobject(F(f)).set(height=0.95).move_to(b[0].get_center() + RIGHT * x))
    stages.append((b, "Human videos", "2,000 demos - 10 tasks"))

    c = VGroup(hand_skeleton(1.05).shift(LEFT * 0.36 + DOWN * 0.06))
    obj = RoundedRectangle(width=0.52, height=0.52, corner_radius=0.08, stroke_color=SIM,
                           stroke_width=2.6, fill_opacity=0).shift(RIGHT * 0.8 + DOWN * 0.18)
    c.add(obj, VGroup(*[Dot(radius=0.052, color=SIM).move_to(obj.get_center() + p)
                        for p in (UL * 0.26, UR * 0.26, DL * 0.26, DR * 0.26)]))
    stages.append((c, "3D pose labels", "hand + object keypoints"))

    d = VGroup(table(1.75, SIM).move_to(DOWN * 0.62).set_opacity(0.5))
    d.add(robot_arm(0.9).move_to(LEFT * 0.5 + UP * 0.16))
    d.add(RoundedRectangle(width=0.4, height=0.4, corner_radius=0.07, fill_color=ACCENT,
                           fill_opacity=0.9, stroke_width=0).move_to(RIGHT * 0.62 + DOWN * 0.35))
    stages.append((d, "Paired sim twin", "ManiSkill / SAPIEN"))

    cards = Group()
    for i, (art, title, sub) in enumerate(stages):
        box = card(W, H)
        art.scale(0.95).move_to(box.get_center() + UP * 0.5)
        cards.add(Group(
            box,
            mono(f"0{i+1}", 15, ACCENT_INK, weight=BOLD).move_to(box.get_corner(UL) + DR * 0.32),
            art,
            sg(title, 24, INK, weight=BOLD).move_to(box.get_bottom() + UP * 0.78),
            mono(sub.upper(), 14, MUTED).move_to(box.get_bottom() + UP * 0.4),
        ))
    cards.arrange(RIGHT, buff=0.56).move_to(DOWN * 0.95)
    arrows = VGroup(*[arrow(p.get_right(), q.get_left(), LINE_STRONG, 4.0, buff=0.1)
                      for p, q in zip(cards, cards[1:])])
    return cards, arrows


class Act1Still(Scene):
    def construct(self):
        cards, arrows = act1_layout()
        self.add(header("benchmark", "How RoboReel is built",
                        "one calibrated pipeline, real and simulated"), cards, arrows)


# --------------------------------------------------------------------------
# ACT 2 - the learning-from-observation loop
# --------------------------------------------------------------------------
def act2_layout():
    d = {}
    ENV_Y, BOX_Y = 1.28, -1.9
    LX, RX = -6.5, 6.6

    env = card(4.25, 1.5).move_to([1.45, ENV_Y, 0])
    d["env"] = Group(
        env,
        screen(F("robot.jpg"), 1.85, caption="sim rollout").move_to(env.get_center() + LEFT * 1.0),
        sg("Paired sim\nenvironment", 21, SIM, weight=BOLD).move_to(env.get_center() + RIGHT * 1.15),
    )

    pbox = RoundedRectangle(width=11.8, height=3.3, corner_radius=0.22, fill_color=BG_PLANE,
                            fill_opacity=0.5, stroke_color=LINE_STRONG, stroke_width=2)
    pbox.move_to([0.2, BOX_Y, 0])
    d["pbox"] = pbox
    d["tab"] = chip("Policy", w=1.55, h=0.5, color=BG, fill=INK, stroke=INK, size=20).move_to(
        pbox.get_corner(UL) + RIGHT * 1.0)

    hs = screen(F("human.jpg"), 2.45, caption="human demonstration").move_to([-4.05, -1.38, 0])
    d["human"] = hs

    enc = mlp((3, 4, 3), w=1.15, h=1.0, color=ACCENT, dot_r=0.048).move_to([-1.6, -1.38, 0])
    d["enc"] = VGroup(enc, mono("encoder", 17, ACCENT_INK).next_to(enc, DOWN, buff=0.18))

    rep = chip("z", w=0.74, h=0.62, color=ACCENT_INK, fill=ACCENT_SOFT, stroke=ACCENT, size=23)
    rep.move_to([0.05, -1.38, 0])
    d["rep"] = VGroup(rep, mono("representation", 14, MUTED).next_to(rep, UP, buff=0.14))

    obs = chip(subscripted("o", "t", 22, SIM), w=1.5, h=0.66, stroke=SIM).move_to([-4.05, -3.0, 0])
    d["obs"] = VGroup(obs, mono("CURRENT OBSERVATION", 13, MUTED).next_to(obs, UP, buff=0.15))

    pol = mlp((4, 5, 4, 2), w=1.8, h=1.75, color=INK, dot_r=0.05).move_to([2.55, -1.95, 0])
    d["pol"] = VGroup(pol, sg("policy", 22, INK, weight=BOLD).next_to(pol, DOWN, buff=0.18))

    act = chip(subscripted("a", "t", 22, GOOD), w=1.25, h=0.66, stroke=GOOD).move_to([5.0, -1.95, 0])
    d["act"] = VGroup(act, mono("ACTION", 13, MUTED).next_to(act, DOWN, buff=0.16))

    d["c_hs_enc"] = arrow(hs.get_right(), enc.get_left(), MUTED, 3.2, 0.16)
    d["c_enc_rep"] = arrow(enc.get_right(), rep.get_left(), MUTED, 3.2, 0.16)
    d["c_rep_pol"] = arrow(rep.get_right(), pol.get_left() + UP * 0.5, ACCENT, 3.2, 0.2)
    d["c_obs_pol"] = arrow(obs.get_right(), pol.get_left() + DOWN * 0.55, SIM, 3.2, 0.18)
    d["c_pol_act"] = arrow(pol.get_right(), act.get_left(), GOOD, 3.4, 0.16)
    d["c_up"] = elbow([act.get_right() + RIGHT * 0.08, [RX, -1.95, 0], [RX, ENV_Y, 0],
                       env.get_right() + RIGHT * 0.08], GOOD, 3.4)
    d["c_down"] = elbow([env.get_left() + LEFT * 0.08, [LX, ENV_Y, 0], [LX, -3.0, 0],
                         obs.get_left() + LEFT * 0.08], SIM, 3.4)
    d["l_down"] = mono("next observation", 14, SIM).rotate(PI / 2).move_to([LX - 0.32, -0.9, 0])
    d["l_up"] = mono("executed action", 14, GOOD).rotate(-PI / 2).move_to([RX + 0.32, -0.4, 0])
    return d


ACT2_ORDER = ["c_down", "c_up", "c_hs_enc", "c_enc_rep", "c_rep_pol", "c_obs_pol", "c_pol_act",
              "l_down", "l_up", "pbox", "tab", "env", "human", "enc", "rep", "obs", "pol", "act"]


class Act2Still(Scene):
    def construct(self):
        d = act2_layout()
        self.add(header("method", "Learning from observation",
                        "a human video conditions the policy"))
        for k in ACT2_ORDER:
            self.add(d[k])


# --------------------------------------------------------------------------
# ACT 3 - the four test suites
# --------------------------------------------------------------------------
SUITES = [
    ("♠", "ND", "No Distraction", "clean train - clean eval", "clean", "clean"),
    ("♥", "WD", "With Distraction", "clutter in train and eval", "clutter", "clutter"),
    ("♣", "ED", "Evaluation Distraction", "clean train - cluttered eval", "clean", "clutter"),
    ("♦", "PD", "Pose Defined", "3D keypoints, shared action space", "pose", "pose"),
]


def mini_panel(kind, w=1.18, h=0.94):
    """Tiny schematic of a scene: the task objects, plus distractors when the
    suite adds them. Vector rather than a screenshot because the benchmark's
    distraction footage isn't in the repo."""
    g = VGroup(RoundedRectangle(width=w, height=h, corner_radius=0.08, fill_color=SURFACE,
                                fill_opacity=1, stroke_color=LINE_STRONG, stroke_width=1.6))
    ground = Line(LEFT * (w / 2 - 0.12), RIGHT * (w / 2 - 0.12),
                  stroke_width=2, color=LINE_STRONG).shift(DOWN * (h / 2 - 0.22))
    g.add(ground)
    y = ground.get_y() + 0.1
    if kind == "pose":
        pts = [np.array([x, y + dy, 0]) for x, dy in
               ((-0.26, 0.0), (-0.09, 0.17), (0.09, 0.26), (0.27, 0.13))]
        for p, q in zip(pts, pts[1:]):
            g.add(Line(p, q, stroke_width=2, color=ACCENT, stroke_opacity=0.8))
        g.add(*[Dot(radius=0.045, color=ACCENT).move_to(p) for p in pts])
    else:
        g.add(RoundedRectangle(width=0.2, height=0.2, corner_radius=0.04, fill_color=ACCENT,
                               fill_opacity=1, stroke_width=0).move_to([-0.22, y, 0]))
        g.add(Circle(radius=0.11, fill_color=SIM, fill_opacity=1,
                     stroke_width=0).move_to([0.16, y, 0]))
        if kind == "clutter":
            for x, dy, r in ((-0.4, 0.3, 0.06), (0.0, 0.34, 0.05), (0.4, 0.26, 0.07),
                             (0.36, 0.02, 0.05)):
                g.add(Circle(radius=r, fill_color=MUTED, fill_opacity=0.55,
                             stroke_width=0).move_to([x, y + dy, 0]))
    return g


def act3_layout():
    cards = VGroup()
    for gl, code, name, sub, tr, ev in SUITES:
        box = card(3.05, 3.5, fill=ACCENT_SOFT)
        top = VGroup(suit(gl, 30, ACCENT_INK),
                     mono(code, 16, ACCENT_INK, weight=BOLD)).arrange(RIGHT, buff=0.16)
        top.move_to(box.get_top() + DOWN * 0.42)

        panels = VGroup()
        for lbl, kind in (("TRAIN", tr), ("EVAL", ev)):
            p = mini_panel(kind)
            panels.add(VGroup(p, mono(lbl, 11, MUTED).next_to(p, DOWN, buff=0.1)))
        panels.arrange(RIGHT, buff=0.22).move_to(box.get_center() + UP * 0.18)

        t = sg(name, 21, INK, weight=BOLD).move_to(box.get_bottom() + UP * 0.78)
        if t.width > 2.7:
            t.scale(2.7 / t.width)
        u = mono(sub.upper(), 12, INK_SOFT).move_to(box.get_bottom() + UP * 0.42)
        if u.width > 2.72:
            u.scale(2.72 / u.width)
        cards.add(VGroup(box, top, panels, t, u))
    cards.arrange(RIGHT, buff=0.42).move_to(DOWN * 0.85)
    return cards


class Act3Still(Scene):
    def construct(self):
        self.add(header("evaluation", "Four test suites",
                        "every model, every task, three seeds"), act3_layout())


# --------------------------------------------------------------------------
# the full clip
# --------------------------------------------------------------------------
class Overview(Scene):
    """All three acts back to back. Ends on an empty frame so the <video loop>
    restart is seamless."""

    def construct(self):
        self.act1()
        self.act2()
        self.act3()

    # ---- act 1 ----
    def act1(self):
        h = header("benchmark", "How RoboReel is built",
                   "one calibrated pipeline, real and simulated")
        cards, arrows = act1_layout()
        self.play(FadeIn(h, shift=RIGHT * 0.3), run_time=0.9)
        for i, c in enumerate(cards):
            if i:
                self.play(GrowArrow(arrows[i - 1]), run_time=0.32)
            self.play(FadeIn(c, shift=UP * 0.35), run_time=0.62)
        self.wait(2.4)
        self.play(FadeOut(Group(h, cards, arrows)), run_time=0.65)

    # ---- act 2 ----
    def act2(self):
        h = header("method", "Learning from observation", "a human video conditions the policy")
        d = act2_layout()
        self.play(FadeIn(h, shift=RIGHT * 0.3), run_time=0.85)
        self.play(FadeIn(d["pbox"]), FadeIn(d["tab"]), run_time=0.6)
        self.play(FadeIn(d["env"], shift=DOWN * 0.25), run_time=0.65)
        self.play(FadeIn(d["human"], shift=UP * 0.2), run_time=0.6)
        self.play(FadeIn(d["enc"]), FadeIn(d["rep"]), run_time=0.55)
        self.play(FadeIn(d["pol"]), FadeIn(d["act"]), FadeIn(d["obs"]), run_time=0.65)
        self.play(*[Create(d[k]) for k in
                    ("c_hs_enc", "c_enc_rep", "c_rep_pol", "c_obs_pol", "c_pol_act")],
                  run_time=0.9)
        self.play(Create(d["c_up"]), Create(d["c_down"]),
                  FadeIn(d["l_up"]), FadeIn(d["l_down"]), run_time=0.95)
        self.wait(0.4)

        # the demonstration is encoded once, then the control loop spins
        pulse(self, [(d["c_hs_enc"], ACCENT)])
        pulse(self, [(d["c_enc_rep"], ACCENT)])
        pulse(self, [(d["c_rep_pol"], ACCENT)])
        ring = lift(d["rep"][0], ACCENT)
        self.play(FadeIn(ring), run_time=0.3)

        for _ in range(2):
            pulse(self, [(d["c_obs_pol"], SIM)])
            pulse(self, [(d["c_pol_act"], GOOD)])
            pulse(self, [(d["c_up"], GOOD)], rt=1.15)
            pulse(self, [(d["c_down"], SIM)], rt=1.15)

        self.wait(1.0)
        self.play(FadeOut(Group(h, ring, *[d[k] for k in ACT2_ORDER])), run_time=0.65)

    # ---- act 3 ----
    def act3(self):
        h = header("evaluation", "Four test suites", "every model, every task, three seeds")
        cards = act3_layout()
        self.play(FadeIn(h, shift=RIGHT * 0.3), run_time=0.85)
        for c in cards:
            self.play(FadeIn(c, shift=UP * 0.3), run_time=0.5)
        self.wait(2.6)
        self.play(FadeOut(VGroup(h, cards)), run_time=0.8)
        self.wait(0.3)
