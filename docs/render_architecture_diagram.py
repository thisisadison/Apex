"""Draw docs/architecture.svg, the system diagram shown in the README.

Positions are set by hand: automatic layout kept routing the self-update
loop around the whole picture. Edit the NODES table or the EDGES list and
re-run:  python docs/render_architecture_diagram.py
The SVG follows the viewer's light/dark setting.
"""

import os
from html import escape

W, H = 1190, 985
SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'

TITLE, BODY, MONO_SIZE, HEADER, LABEL = 21, 17, 16, 27, 16

# Columns: Training on the left, the server's two columns, all sharing rows
# so the loop arrows between them stay straight.
TRAIN_X, TRAIN_W = 45, 250
COL_B, COL_C, COL_W = 545, 865, 280
ROW = {1: 215, 2: 364, 3: 513, 4: 662}

# kind: box | store (cylinder) | external (dashed)
# lines: ("mono", text) for a file path, ("api", text) for an endpoint chip,
#        plain strings for a description.
NODES = {
    "jolpica": dict(kind="external", x=COL_B, y=20, w=COL_W, h=84,
                    title="Jolpica-F1 API", lines=[("mono", "api.jolpi.ca")]),
    "rss": dict(kind="external", x=COL_C, y=20, w=COL_W, h=84,
                title="RSS feeds", lines=["F1 · Motorsport · BBC"]),

    "data": dict(kind="store", x=TRAIN_X, y=ROW[1] - 8, w=TRAIN_W, h=120,
                 title="Race data", lines=[("mono", "data/"), "2008 → today"]),
    "pipeline": dict(kind="box", x=TRAIN_X, y=ROW[2], w=TRAIN_W, h=104,
                     title="Training pipeline",
                     lines=[("mono", "f1/pipeline.py"), "4 models · GridSearchCV"]),
    "model": dict(kind="store", x=TRAIN_X, y=ROW[3] - 8, w=TRAIN_W, h=120,
                  title="Trained model", lines=[("mono", "models/model.pkl")]),

    "live": dict(kind="box", x=COL_B, y=ROW[1], w=COL_W, h=104, title="LiveData",
                 lines=[("mono", "webapp/live_data.py"), ("api", "/api/schedule")]),
    "news": dict(kind="box", x=COL_C, y=ROW[1], w=COL_W, h=104, title="News",
                 lines=[("mono", "webapp/news.py"), ("api", "/api/news")]),
    "scheduler": dict(kind="box", x=COL_B, y=ROW[2], w=COL_W, h=104,
                      title="AutoUpdateScheduler",
                      lines=[("mono", "webapp/scheduler.py"), "checks every 3 h"]),
    "store": dict(kind="box", x=COL_B, y=ROW[3], w=COL_W, h=104, title="ModelStore",
                  lines=[("mono", "webapp/model_store.py"), "hot-reloads the model"]),
    "service": dict(kind="box", x=COL_C, y=ROW[3], w=COL_W, h=104,
                    title="PredictionService",
                    lines=[("mono", "webapp/predictions.py"), ("api", "/api/predictions/*")]),
    "analytics": dict(kind="box", x=COL_B, y=ROW[4], w=COL_W, h=104,
                      title="Season analytics",
                      lines=[("mono", "f1/analytics.py"), ("api", "/api/analytics")]),
    "agent": dict(kind="box", x=COL_C, y=ROW[4], w=COL_W, h=128, title="RaceAnalyst",
                  lines=[("mono", "webapp/agent.py"), "5 read-only tools", ("api", "/api/chat")]),

    "browser": dict(kind="box", x=COL_B, y=861, w=COL_W, h=104, title="Browser",
                    lines=[("mono", "webapp/static/"), "plain HTML · CSS · JS"]),
    "anthropic": dict(kind="external", x=COL_C, y=861, w=COL_W, h=84,
                      title="Anthropic API", lines=["Claude · optional"]),
}

GROUPS = [
    dict(title="Training", x=20, y=150, w=300, h=495),
    dict(title="FastAPI server", x=520, y=150, w=650, h=666),
]


def cx(name):
    n = NODES[name]
    return n["x"] + n["w"] / 2


def cy(name):
    n = NODES[name]
    return n["y"] + n["h"] / 2


def top(name):
    return NODES[name]["y"]


def bottom(name):
    n = NODES[name]
    return n["y"] + n["h"]


def left(name):
    return NODES[name]["x"]


def right(name):
    n = NODES[name]
    return n["x"] + n["w"]


SERVER_BOTTOM = GROUPS[1]["y"] + GROUPS[1]["h"]

# (points, style, label, label position, label anchor)
# style: flow | loop | loop-dashed | both (double-headed flow)
EDGES = [
    ([(cx("data"), bottom("data")), (cx("pipeline"), top("pipeline"))], "flow", None, None, None),
    ([(cx("pipeline"), bottom("pipeline")), (cx("model"), top("model"))], "flow", None, None, None),
    ([(cx("jolpica"), bottom("jolpica")), (cx("live"), top("live"))], "flow", None, None, None),
    ([(cx("rss"), bottom("rss")), (cx("news"), top("news"))], "flow", None, None, None),
    ([(right("model"), cy("model")), (left("store"), cy("store"))], "flow", None, None, None),
    ([(right("store"), cy("store")), (left("service"), cy("service"))], "flow", None, None, None),
    ([(cx("service"), bottom("service")), (cx("agent"), top("agent"))], "flow", None, None, None),
    ([(left("service") + 50, bottom("service")), (left("service") + 50, bottom("service") + 28),
      (cx("analytics"), bottom("service") + 28), (cx("analytics"), top("analytics"))],
     "flow", None, None, None),
    ([(cx("agent"), bottom("agent")), (cx("agent"), top("anthropic"))], "both", None, None, None),
    ([(cx("browser"), SERVER_BOTTOM), (cx("browser"), top("browser"))], "flow",
     "JSON over HTTP", (cx("browser") + 14, (SERVER_BOTTOM + top("browser")) / 2 + 6), "start"),

    # The self-update loop.
    ([(cx("scheduler"), top("scheduler")), (cx("scheduler"), bottom("live"))], "loop",
     "1 · new race?", (cx("scheduler") + 14, (bottom("live") + top("scheduler")) / 2 + 6), "start"),
    ([(left("live"), cy("live") + 2), (right("data"), cy("live") + 2)], "loop",
     "2 · append results", ((right("data") + left("live")) / 2, cy("live") - 12), "middle"),
    ([(left("scheduler"), cy("scheduler")), (right("pipeline"), cy("scheduler"))], "loop-dashed",
     "3 · retrain", ((right("pipeline") + left("scheduler")) / 2, cy("scheduler") - 14), "middle"),
    ([(cx("scheduler"), bottom("scheduler")), (cx("scheduler"), top("store"))], "loop-dashed",
     "4 · hot-swap", (cx("scheduler") + 14, (bottom("scheduler") + top("store")) / 2 + 6), "start"),
]

STYLE = """
  .bg { fill: #ffffff; }
  .group { fill: #eef1fb; stroke: #b9c2e6; }
  .group-title { fill: #1f2547; }
  .node { fill: #ffffff; stroke: #4c5bd4; }
  .node-ext { fill: #f7f8fd; stroke: #4c5bd4; stroke-dasharray: 7 5; }
  .title { fill: #111827; }
  .body { fill: #4b5563; }
  .chip { fill: #eef0f5; }
  .mono { fill: #374151; }
  .api-chip { fill: #e3e7ff; }
  .api { fill: #2f3aa8; }
  .flow { stroke: #5b6478; }
  .flow-head { fill: #5b6478; }
  .flow-label { fill: #5b6478; }
  .loop { stroke: #e11d48; }
  .loop-head { fill: #e11d48; }
  .loop-label { fill: #e11d48; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #161925; }
    .group { fill: #1f2433; stroke: #3b4363; }
    .group-title { fill: #e3e7ff; }
    .node { fill: #272d40; stroke: #8f9ae6; }
    .node-ext { fill: #1d2130; stroke: #8f9ae6; }
    .title { fill: #f3f4f6; }
    .body { fill: #b4bccd; }
    .chip { fill: #343b52; }
    .mono { fill: #d5dae6; }
    .api-chip { fill: #3b4475; }
    .api { fill: #d9ddff; }
    .flow { stroke: #9aa3bd; }
    .flow-head { fill: #9aa3bd; }
    .flow-label { fill: #b4bccd; }
    .loop { stroke: #ff4d6d; }
    .loop-head { fill: #ff4d6d; }
    .loop-label { fill: #ff6b85; }
  }
"""


def text(x, y, value, cls, size, family=SANS, weight="normal", anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" font-family=\'{family}\' '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


def chip(x, y, value, chip_cls, text_cls, weight):
    width = len(value) * MONO_SIZE * 0.61 + 12
    return (f'<rect x="{x:.1f}" y="{y - MONO_SIZE + 2:.1f}" width="{width:.1f}" '
            f'height="{MONO_SIZE + 7}" rx="4" class="{chip_cls}"/>'
            + text(x + 6, y, value, text_cls, MONO_SIZE, MONO, weight))


def node(name):
    n = NODES[name]
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]
    out = []
    pad_top = 0
    if n["kind"] == "store":
        rx, ry = w / 2, 13
        out.append(f'<path class="node" stroke-width="2" d="M{x},{y + ry} '
                   f'a{rx},{ry} 0 0 0 {w},0 v{h - 2 * ry} a{rx},{ry} 0 0 1 {-w},0 z"/>')
        out.append(f'<path class="node" stroke-width="2" d="M{x},{y + ry} '
                   f'a{rx},{ry} 0 0 1 {w},0 a{rx},{ry} 0 0 1 {-w},0 z"/>')
        pad_top = 2 * ry
    else:
        cls = "node-ext" if n["kind"] == "external" else "node"
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" '
                   f'class="{cls}" stroke-width="2"/>')
    tx = x + 18
    ty = y + pad_top + 32
    out.append(text(tx, ty, n["title"], "title", TITLE, weight="bold"))
    for line in n["lines"]:
        ty += 25
        if isinstance(line, tuple) and line[0] == "mono":
            out.append(chip(tx, ty, line[1], "chip", "mono", "normal"))
        elif isinstance(line, tuple) and line[0] == "api":
            out.append(chip(tx, ty, line[1], "api-chip", "api", "bold"))
        else:
            out.append(text(tx, ty, line, "body", BODY))
    return "\n".join(out)


def edge(points, style, label, label_pos, anchor):
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)
    loop = style.startswith("loop")
    stroke_cls = "loop" if loop else "flow"
    head = "url(#head-loop)" if loop else "url(#head-flow)"
    dash = ' stroke-dasharray="9 6"' if style == "loop-dashed" else ""
    start = f' marker-start="{head}"' if style == "both" else ""
    width = 3 if loop else 2
    out = [f'<path d="{path}" class="{stroke_cls}" stroke-width="{width}" fill="none"'
           f'{dash}{start} marker-end="{head}"/>']
    if label:
        cls = "loop-label" if loop else "flow-label"
        weight = "bold" if loop else "normal"
        out.append(text(label_pos[0], label_pos[1], label, cls, LABEL, weight=weight, anchor=anchor))
    return "\n".join(out)


def legend():
    x, y = 30, 700
    items = [
        ("flow", None, "Data and requests"),
        ("loop", None, "Self-update loop, every 3 h"),
        ("loop-dashed", None, "Runs in a subprocess / swaps live"),
    ]
    out = [text(x, y, "Legend", "group-title", 18, weight="bold")]
    for i, (style, _, label) in enumerate(items):
        ly = y + 32 + i * 30
        out.append(edge([(x, ly - 5), (x + 46, ly - 5)], style, None, None, None))
        out.append(text(x + 58, ly, label, "body", 15))
    ly = y + 32 + 3 * 30
    out.append(f'<rect x="{x}" y="{ly - 16}" width="46" height="20" rx="4" '
               f'class="node-ext" stroke-width="2"/>')
    out.append(text(x + 58, ly, "Outside service", "body", 15))
    return "\n".join(out)


def build() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Apex system architecture">',
        f"<style>{STYLE}</style>",
        "<defs>",
        '<marker id="head-flow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="flow-head"/></marker>',
        '<marker id="head-loop" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" '
        'markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="loop-head"/></marker>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="16" class="bg"/>',
    ]
    for g in GROUPS:
        parts.append(f'<rect x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" height="{g["h"]}" rx="14" '
                     f'class="group" stroke-width="2"/>')
        parts.append(text(g["x"] + g["w"] / 2, g["y"] + 40, g["title"], "group-title", HEADER,
                          weight="bold", anchor="middle"))
    for e in EDGES:
        parts.append(edge(*e))
    for name in NODES:
        parts.append(node(name))
    parts.append(legend())
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architecture.svg")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(build())
    print(f"wrote {out}")
