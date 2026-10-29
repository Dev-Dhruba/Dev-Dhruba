"""Add extra motion to the 3D contribution skyline SVG.

Runs after yoshi389111/github-profile-3d-contrib in profile-3d.yml and injects
a ripple that sweeps through the city, twinkling and shooting stars, a pulsing
neon radar and a slowly spinning language donut.

Usage: python3 animate_skyline.py <in.svg> [out.svg]
"""
import math
import random
import re
import sys

GROW_END = 3.2        # the generator's own grow-in animation lasts 3s
RIPPLE_PERIOD = 7.0   # seconds between ripples
RIPPLE_SWEEP = 2.6    # seconds for one ripple to cross the whole year
RIPPLE_HEIGHT = 14.0  # px each tile hops
WALL_SCALE = 1.15     # wall rects are drawn with scale(1 1.15)

DEFS = """<defs>
<filter id="neon-glow" x="-50%" y="-50%" width="200%" height="200%">
<feGaussianBlur stdDeviation="5" result="blur"/>
<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<linearGradient id="meteor-tail" gradientUnits="userSpaceOnUse" x1="-110" y1="0" x2="0" y2="0">
<stop offset="0" stop-color="#00d9ff" stop-opacity="0"/>
<stop offset="1" stop-color="#ffffff"/>
</linearGradient>
</defs>"""

CSS = """
.radar { animation: radar-pulse 3s ease-in-out 3s infinite; }
@keyframes radar-pulse { 0%, 100% { fill-opacity: 0.4; } 50% { fill-opacity: 0.85; } }
"""


def ripple(tile_index, tile_count):
    begin = GROW_END + tile_index / max(tile_count - 1, 1) * RIPPLE_SWEEP
    timing = (f'keyTimes="0;{0.3 / RIPPLE_PERIOD:.4f};{0.75 / RIPPLE_PERIOD:.4f};1" '
              f'calcMode="spline" keySplines="0.25 0.8 0.4 1;0.5 0 0.75 0.4;0 0 1 1" '
              f'dur="{RIPPLE_PERIOD}s" begin="{begin:.3f}s" repeatCount="indefinite" additive="sum"')
    lift = (f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 {-RIPPLE_HEIGHT};0 0;0 0" {timing}/>')
    wall = (f'<animate attributeName="height" '
            f'values="0;{RIPPLE_HEIGHT / WALL_SCALE:.2f};0;0" {timing}/>')
    return lift, wall


def add_ripple(svg):
    tile = re.compile(r'(<g transform="translate\([-\d.]+ [-\d.]+\)">)(.*?</g>)', re.S)
    tiles = [m for m in tile.finditer(svg) if 'class="rb-l' in m.group(2)]
    out, pos = [], 0
    for i, m in enumerate(tiles):
        lift, wall = ripple(i, len(tiles))
        body = re.sub(r'(<rect [^>]*class="rb-l\d-(?:left|right)"[^>]*>)', r'\1' + wall, m.group(2))
        out += [svg[pos:m.start()], m.group(1), lift, body]
        pos = m.end()
    out.append(svg[pos:])
    return "".join(out), len(tiles)


def stars(width, height, rng):
    parts = []
    for _ in range(90):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        r = rng.choice([0.7, 0.9, 1.1, 1.4, 1.8])
        color = rng.choice(["#e6edf3"] * 5 + ["#00d9ff", "#bd00ff"])
        dur, begin = rng.uniform(2.0, 5.0), rng.uniform(0, 4)
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" opacity="0.2">'
            f'<animate attributeName="opacity" values="0.15;1;0.15" dur="{dur:.2f}s" '
            f'begin="{begin:.2f}s" repeatCount="indefinite"/></circle>')
    return "".join(parts)


def meteor(start, end, begin, period):
    (sx, sy), (ex, ey) = start, end
    angle = math.degrees(math.atan2(ey - sy, ex - sx))
    return (
        f'<g><animateTransform attributeName="transform" type="translate" '
        f'values="{sx} {sy};{ex} {ey};{ex} {ey}" keyTimes="0;0.1;1" dur="{period}s" '
        f'begin="{begin}s" repeatCount="indefinite"/>'
        f'<g transform="rotate({angle:.1f})" opacity="0">'
        f'<animate attributeName="opacity" values="0;1;0;0" keyTimes="0;0.03;0.1;1" '
        f'dur="{period}s" begin="{begin}s" repeatCount="indefinite"/>'
        f'<line x1="-110" y1="0" x2="0" y2="0" stroke="url(#meteor-tail)" stroke-width="2.5" stroke-linecap="round"/>'
        f'<circle r="2.6" fill="#ffffff" filter="url(#neon-glow)"/></g></g>')


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    svg = open(src, encoding="utf-8").read()
    if 'id="neon-glow"' in svg:
        print("already animated, skipping")
        return

    width, height = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    rng = random.Random(1337)  # fixed seed keeps the starfield stable between runs

    svg = svg.replace("</style>", CSS + "</style>" + DEFS, 1)
    svg, tile_count = add_ripple(svg)

    sky = (stars(width, height, rng)
           + meteor((width * 0.66, 30), (width * 0.48, 150), begin=4, period=9)
           + meteor((width * 0.50, 70), (width * 0.34, 165), begin=8.5, period=11))
    svg = re.sub(r'(<rect [^>]*class="fill-bg"[^>]*>(?:</rect>)?)', lambda m: m.group(1) + sky, svg, count=1)

    # Spin the language donut slowly around its centre.
    svg = re.sub(r'(<g transform="translate\([\d.]+, [\d.]+\)">)(<path d="M0,-)',
                 r'\1<animateTransform attributeName="transform" type="rotate" from="0" to="360" '
                 r'dur="40s" additive="sum" repeatCount="indefinite"/>\2', svg, count=1)

    # Neon glow on the radar and the contribution count.
    svg = re.sub(r'(<polygon class="radar")', r'\1 filter="url(#neon-glow)"', svg)
    svg = re.sub(r'(<text [^>]*class="fill-strong")', r'\1 filter="url(#neon-glow)"', svg)

    with open(dst, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"animated {tile_count} tiles -> {dst} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
