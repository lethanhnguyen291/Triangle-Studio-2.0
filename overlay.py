"""A reusable floating window. Native color-key transparency on Windows."""
import sys
import tkinter as tk
from triangle_logic import bounded_vertices, MIN_SIZE, MAX_SIZE


class TriangleOverlay:
    def __init__(self, root, get_state, on_resize, on_move, on_hide):
        self.root, self.get_state = root, get_state
        self.on_resize, self.on_move, self.on_hide = on_resize, on_move, on_hide
        self.window = None
        self.canvas = None
        self.anchor = [100, 650]
        self.visible = False
        self.color_key_supported = False
        self._drag = None

    def _create(self):
        if self.window is not None and self.window.winfo_exists():
            return
        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.window.title("Triangle Studio · Tam giác nổi")
        self.window.overrideredirect(True)
        self.canvas = tk.Canvas(self.window, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<ButtonRelease-1>", self.finish_move)
        self.canvas.bind("<ButtonPress-3>", self.start_resize)
        self.canvas.bind("<B3-Motion>", self.resize)
        self.canvas.bind("<ButtonRelease-3>", self.finish_resize)
        self.canvas.bind("<MouseWheel>", self.wheel)
        self.canvas.bind("<Button-4>", lambda e: self.wheel(e, 1))
        self.canvas.bind("<Button-5>", lambda e: self.wheel(e, -1))
        self.window.bind("<Escape>", lambda e: self.hide())
        self.window.bind("<F2>", lambda e: self.hide())
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

    def show(self):
        self._create()
        self.visible = True
        self.render()
        self.recover_if_offscreen()
        self.window.deiconify()
        self.window.lift()
        self.canvas.focus_set()

    def hide(self):
        if self.window is not None:
            self.window.withdraw()
        self.visible = False
        self._drag = None
        if hasattr(self, "_resize"):
            del self._resize
        self.on_hide()

    def render(self):
        if not self.visible or self.window is None:
            return
        state = self.get_state()
        pts, w, h = bounded_vertices(state)
        key = next(c for c in ("#010203", "#020304", "#030405")
                   if c.lower() not in (state.color.lower(), state.outline.lower()))
        self.color_key_supported = False
        if sys.platform == "win32":
            try:
                self.window.attributes("-transparentcolor", key)
                self.color_key_supported = True
            except tk.TclError:
                pass
        bg = key if self.color_key_supported else "#15232D"
        self.window.configure(bg=bg)
        self.canvas.configure(bg=bg, cursor="arrow" if state.locked else "fleur")
        self.window.attributes("-topmost", state.topmost)
        try:
            self.window.attributes("-alpha", state.opacity)
        except tk.TclError:
            pass
        x, bottom = self.anchor
        # Keep a reachable top-left corner; negative Tk offsets mean right/bottom alignment.
        x, y = max(0, int(x)), max(0, int(bottom-h))
        self.anchor = [x, y+h]
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas.delete("all")
        self.canvas.create_polygon(*[v for p in pts for v in p], fill=state.color if state.filled else "",
                                   outline=state.outline, width=state.line_width, joinstyle="round")

    def recover_if_offscreen(self):
        _, w, h = bounded_vertices(self.get_state())
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x, y = self.anchor[0], self.anchor[1] - h
        x = max(0, min(x, max(0, sw - min(w, sw))))
        y = max(0, min(y, max(0, sh - min(h, sh))))
        self.anchor = [int(x), int(y + h)]
        self.render()

    def center(self):
        _, w, h = bounded_vertices(self.get_state())
        self.anchor = [max(0, (self.root.winfo_screenwidth()-w)//2),
                       max(0, (self.root.winfo_screenheight()-h)//2)+h]
        if self.visible:
            self.render()
        self.on_move(self.anchor)

    def start_move(self, event):
        if not self.get_state().locked:
            self._drag = (event.x_root, event.y_root, *self.anchor)

    def move(self, event):
        if self._drag is None or self.get_state().locked:
            return
        ex, ey, x, y = self._drag
        self.anchor = [x + event.x_root-ex, y + event.y_root-ey]
        self.render()

    def finish_move(self, _event=None):
        if self._drag is not None:
            self.on_move(self.anchor)
        self._drag = None

    def start_resize(self, event):
        if not self.get_state().locked:
            state = self.get_state()
            self._resize = (event.x_root, event.y_root, state.width, state.height)

    def resize(self, event):
        if not hasattr(self, "_resize") or self.get_state().locked:
            return
        x, y, w, h = self._resize
        dx, dy = event.x_root-x, y-event.y_root
        nw, nh = w + dx, h + dy
        if self.get_state().sync:
            nw = nh = w + (dx if abs(dx) >= abs(dy) else dy)
        self.on_resize(max(MIN_SIZE, min(MAX_SIZE, nw)), max(MIN_SIZE, min(MAX_SIZE, nh)), False)

    def finish_resize(self, _event=None):
        if hasattr(self, "_resize"):
            del self._resize
            state = self.get_state()
            self.on_resize(state.width, state.height, True)

    def wheel(self, event, direction=None):
        if self.get_state().locked:
            return
        direction = direction if direction is not None else (1 if event.delta > 0 else -1)
        state = self.get_state()
        factor = 1.05 if direction > 0 else 1/1.05
        self.on_resize(max(MIN_SIZE, min(MAX_SIZE, round(state.width*factor))),
                       max(MIN_SIZE, min(MAX_SIZE, round(state.height*factor))), True)

    def destroy(self):
        if self.window is not None:
            self.window.destroy()
        self.window = None
        self.visible = False
