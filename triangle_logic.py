"""Geometry and export for Triangle Studio; independent of the desktop UI."""
from dataclasses import dataclass, asdict, fields
import math
import re
from pathlib import Path

MIN_SIZE, MAX_SIZE = 20, 3000


@dataclass
class TriangleState:
    width: int = 420
    height: int = 320
    sync: bool = False
    rotation: float = 0
    flip_x: bool = False
    flip_y: bool = False
    color: str = "#38D9AD"
    outline: str = "#AAFFE7"
    line_width: int = 2
    opacity: float = 0.85
    filled: bool = True
    topmost: bool = True
    locked: bool = False
    grid: bool = True
    labels: bool = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Cấu hình phải là một đối tượng JSON.")
        known = {f.name for f in fields(cls)}
        state = cls(**{k: v for k, v in data.items() if k in known})
        state.validate()
        return state

    def validate(self):
        for key in ("width", "height"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Kích thước phải là số nguyên.")
            if int(value) != value or not MIN_SIZE <= value <= MAX_SIZE:
                raise ValueError(f"Chiều rộng và chiều cao phải từ {MIN_SIZE} đến {MAX_SIZE} px.")
            setattr(self, key, int(value))
        for key in ("rotation", "opacity"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Góc xoay và độ hiển thị phải là số hữu hạn.")
        self.rotation = float(self.rotation) % 360
        if not 0.15 <= self.opacity <= 1:
            raise ValueError("Độ hiển thị phải từ 15% đến 100%.")
        if type(self.line_width) is not int or not 1 <= self.line_width <= 12:
            raise ValueError("Độ dày viền phải từ 1 đến 12 px.")
        for key in ("color", "outline"):
            if not isinstance(getattr(self, key), str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", getattr(self, key)):
                raise ValueError("Màu phải có dạng #RRGGBB.")
        for key in ("sync", "flip_x", "flip_y", "filled", "topmost", "locked", "grid", "labels"):
            if type(getattr(self, key)) is not bool:
                raise ValueError(f"Thiết lập {key} phải là true hoặc false.")
        if self.sync:
            self.height = self.width
        return self


def vertices(state):
    """Positive screen-space rotation is clockwise. Return points A, B, C."""
    state.validate()
    w, h = state.width, state.height
    theta = math.radians(state.rotation)
    co, si = math.cos(theta), math.sin(theta)
    result = []
    for x, y in [(0, 0), (0, h), (w, h)]:
        x, y = x - w / 2, y - h / 2
        if state.flip_x:
            x = -x
        if state.flip_y:
            y = -y
        result.append((x * co - y * si, x * si + y * co))
    return result


def bounded_vertices(state, padding=None):
    padding = state.line_width + 3 if padding is None else padding
    points = vertices(state)
    left, top = min(p[0] for p in points), min(p[1] for p in points)
    right, bottom = max(p[0] for p in points), max(p[1] for p in points)
    return ([(x - left + padding, y - top + padding) for x, y in points],
            math.ceil(right - left + padding * 2), math.ceil(bottom - top + padding * 2))


def measurements(state):
    w, h = state.width, state.height
    hypotenuse = math.hypot(w, h)
    angle_a = math.degrees(math.atan2(w, h))
    return {"area": w * h / 2, "perimeter": w + h + hypotenuse,
            "hypotenuse": hypotenuse, "angle_a": angle_a, "angle_b": 90., "angle_c": 90 - angle_a}


def svg_text(state):
    pts, w, h = bounded_vertices(state)
    coords = " ".join(f"{x:.4f},{y:.4f}" for x, y in pts)
    fill = state.color if state.filled else "none"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            f'  <title>Tam giác vuông — Triangle Studio</title>\n'
            f'  <polygon points="{coords}" fill="{fill}" stroke="{state.outline}" '
            f'stroke-width="{state.line_width}" stroke-linejoin="round" opacity="{state.opacity:.4f}"/>\n</svg>\n')


def export_svg(state, path):
    Path(path).write_text(svg_text(state), encoding="utf-8")


def export_png(state, path):
    from PIL import Image, ImageDraw
    pts, w, h = bounded_vertices(state)
    factor = 3 if max(w, h) < 1600 else 1
    im = Image.new("RGBA", (w * factor, h * factor), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    alpha = round(state.opacity * 255)

    def rgba(color):
        return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) + (alpha,)

    pts = [(round(x * factor), round(y * factor)) for x, y in pts]
    if state.filled:
        draw.polygon(pts, fill=rgba(state.color))
    draw.line(pts + [pts[0]], fill=rgba(state.outline), width=state.line_width * factor, joint="curve")
    if factor > 1:
        im = im.resize((w, h), Image.Resampling.LANCZOS)
    im.save(path, "PNG")
