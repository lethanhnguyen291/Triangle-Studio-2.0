"""Triangle Studio 2.0 — desktop triangle editor, built on the original Tk app."""
import json
import math
from pathlib import Path
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, colorchooser, filedialog, messagebox, simpledialog

from config_manager import ConfigStore, normalize_payload
from triangle_logic import TriangleState, vertices, measurements, export_png, export_svg
from overlay import TriangleOverlay

BG = "#0B111B"
PANEL = "#121D2A"
FIELD = "#1A2838"
BORDER = "#243548"
TEXT = "#E9F2FA"
MUTED = "#91A4B8"
ACCENT = "#52E0B5"
CANVAS = "#0E1925"
FONT = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"


def label(parent, text, size=10, color=TEXT, bold=False, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                    font=(FONT, size, "bold" if bold else "normal"), **kwargs)


def button(parent, text, command, primary=False, **kwargs):
    return tk.Button(parent, text=text, command=command,
                     bg=ACCENT if primary else FIELD, fg=BG if primary else TEXT,
                     activebackground="#7AEDD0" if primary else "#2A3C50",
                     activeforeground=BG if primary else TEXT, disabledforeground=MUTED,
                     font=(FONT, 10, "bold" if primary else "normal"), bd=0,
                     relief="flat", cursor="hand2", padx=13, pady=9,
                     highlightthickness=1, highlightbackground=ACCENT if primary else BORDER,
                     highlightcolor=ACCENT, **kwargs)


class TriangleApp:
    def __init__(self, root, store=None):
        self.root = root
        self.store = store or ConfigStore()
        loaded = self.store.load()
        self.state = TriangleState.from_dict(loaded["state"])
        self.presets = loaded["presets"]
        self.history, self.future = [self.state.to_dict()], []
        self._history_job = self._save_job = self._input_job = None
        self._syncing = False
        self.zoom = 1.0
        self.overlay = TriangleOverlay(root, lambda: self.state, self.overlay_resize,
                                       self.overlay_move, self.overlay_hidden)
        self.overlay.anchor = loaded["anchor"]
        self.root.title("Triangle Studio 2.0 | Mô hình tam giác")
        self.root.configure(bg=BG)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        width, height = min(1220, sw-40), min(850, sh-70)
        self.root.geometry(f"{width}x{height}+20+20")
        self.root.minsize(980, 680)
        self.setup_style()
        self.setup_icon()
        self.build_ui()
        self.refresh()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<F2>", lambda e: self.toggle_overlay())
        root.bind("<Escape>", lambda e: self.overlay.hide())
        root.bind("<Control-s>", lambda e: self.save_now())
        root.bind("<Control-z>", lambda e: self.undo())
        root.bind("<Control-y>", lambda e: self.redo())
        root.bind("<Control-Shift-Z>", lambda e: self.redo())
        root.bind("<Control-e>", lambda e: self.export("png"))
        self.root.after(100, self.draw_preview)
        if self.store.warning:
            self.status(self.store.warning, error=True)
        elif self.store.loaded_legacy:
            self.status("Đã đọc cấu hình v1.10 của bạn. Chọn một mẫu nhanh để thử diện mạo mới.")

    def setup_style(self):
        self.root.option_add("*Font", (FONT, 10))
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TNotebook", background=PANEL, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED, padding=(10, 9), font=(FONT, 9))
        style.map("TNotebook.Tab", background=[("selected", FIELD)], foreground=[("selected", ACCENT)])
        style.configure("Horizontal.TScale", background=PANEL, troughcolor=FIELD,
                        bordercolor=PANEL, lightcolor=ACCENT, darkcolor=ACCENT)
        style.configure("Vertical.TScrollbar", background=FIELD, troughcolor=PANEL,
                        arrowcolor=MUTED, bordercolor=PANEL)
        style.configure("TCheckbutton", background=PANEL, foreground=TEXT, padding=(0, 5), font=(FONT, 10))
        style.map("TCheckbutton", background=[("active", PANEL)], foreground=[("active", ACCENT)])
        style.configure("TCombobox", fieldbackground=FIELD, background=FIELD, foreground=TEXT, arrowcolor=ACCENT)
        self.root.option_add("*TCombobox*Listbox.background", FIELD)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", BORDER)

    def setup_icon(self):
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ThanhNguyen.TriangleStudio.2")
                self.root.iconbitmap(str(base / "eke.ico"))
            except (OSError, tk.TclError, AttributeError):
                pass

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(21, 19))
        mark = tk.Canvas(header, width=44, height=44, bg=BG, highlightthickness=0)
        mark.pack(side="left", padx=(0, 12))
        mark.create_polygon(5, 4, 5, 39, 39, 39, fill="#173F3B", outline=ACCENT, width=2)
        mark.create_line(13, 22, 13, 31, 22, 31, fill=ACCENT, width=2)
        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        label(brand, "TRIANGLE STUDIO", 17, bold=True).pack(anchor="w")
        label(brand, "KHÔNG GIAN SÁNG TẠO HÌNH HỌC  /  2.0", 8, MUTED).pack(anchor="w", pady=(4, 0))
        self.overlay_button = button(header, "Bật tam giác nổi  ↗", self.toggle_overlay, True)
        self.overlay_button.pack(side="right")
        button(header, "Xuất ảnh", self.export_menu).pack(side="right", padx=9)
        button(header, "Hướng dẫn", self.help).pack(side="right")

        footer = tk.Frame(self.root, bg=BG)
        footer.pack(side="bottom", fill="x", padx=24, pady=(10, 13))
        self.status_label = label(footer, "Sẵn sàng · Mọi thay đổi được lưu tự động", 9, MUTED, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        label(footer, "F2  Hiện / ẩn   ·   Ctrl+S  Lưu", 8, MUTED).pack(side="right", padx=(12, 0))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=24)
        sidebar = tk.Frame(body, bg=PANEL, width=316, highlightthickness=1, highlightbackground=BORDER)
        sidebar.pack(side="left", fill="y", padx=(0, 18))
        sidebar.pack_propagate(False)
        label(sidebar, "Bảng điều khiển", 13, bold=True).pack(anchor="w", padx=18, pady=(18, 3))
        label(sidebar, "Điều chỉnh nhỏ. Thay đổi tức thì.", 9, MUTED).pack(anchor="w", padx=18, pady=(0, 15))
        self.notebook = ttk.Notebook(sidebar)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        shape = self.scroll_tab("Hình dạng")
        style = self.scroll_tab("Màu sắc")
        saved = self.scroll_tab("Đã lưu")
        self.vars = {}
        for key, value in self.state.to_dict().items():
            cls = tk.BooleanVar if type(value) is bool else tk.StringVar
            self.vars[key] = cls(master=self.root, value=value)
        self.build_shape_tab(shape)
        self.build_style_tab(style)
        self.build_saved_tab(saved)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        subhead = tk.Frame(right, bg=BG)
        subhead.pack(fill="x", pady=(1, 13))
        title = tk.Frame(subhead, bg=BG)
        title.pack(side="left")
        label(title, "Một hình. Nhiều góc nhìn.", 19, bold=True).pack(anchor="w")
        label(title, "Xem trước trực tiếp trước khi đặt lên màn hình.", 10, MUTED).pack(anchor="w", pady=(5, 0))
        self.redo_btn = button(subhead, "↷", self.redo)
        self.redo_btn.pack(side="right", padx=(5, 0))
        self.undo_btn = button(subhead, "↶", self.undo)
        self.undo_btn.pack(side="right")

        stats = tk.Frame(right, bg=BG)
        stats.pack(side="bottom", fill="x", pady=(14, 0))
        self.stat_labels = {}
        self.stat_boxes = {}
        for i, (key, caption, suffix) in enumerate([
                ("area", "DIỆN TÍCH", "S = rộng × cao / 2"),
                ("perimeter", "CHU VI", "P = rộng + cao + cạnh huyền"),
                ("angle", "GÓC NHỌN A", "Góc B luôn bằng 90°")]):
            box = tk.Frame(stats, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
            self.stat_boxes[key] = box
            box.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            stats.columnconfigure(i, weight=1, uniform="stat")
            label(box, caption, 8, MUTED, True).pack(anchor="w", padx=14, pady=(13, 5))
            self.stat_labels[key] = label(box, "—", 17, ACCENT, True)
            self.stat_labels[key].pack(anchor="w", padx=14)
            detail = label(box, suffix, 8, MUTED, justify="left", anchor="w")
            detail.pack(anchor="w", padx=14, pady=(4, 13))
            def resize_stat(event, d=detail, k=key):
                d.configure(wraplength=max(100, event.width-28))
                self.fit_stat_value(k, event.width)
            box.bind("<Configure>", resize_stat)

        preview_box = tk.Frame(right, bg=CANVAS, highlightthickness=1, highlightbackground=BORDER)
        preview_box.pack(fill="both", expand=True)
        bar = tk.Frame(preview_box, bg=CANVAS)
        bar.pack(fill="x", padx=16, pady=12)
        label(bar, "●  KHUNG XEM TRƯỚC", 9, ACCENT, True).pack(side="left")
        self.type_label = label(bar, "TAM GIÁC VUÔNG", 8, MUTED)
        self.type_label.pack(side="right")
        toolbar = tk.Frame(preview_box, bg=CANVAS)
        toolbar.pack(side="bottom", fill="x", padx=14, pady=(5, 12))
        self.preview_info = label(toolbar, "", 9, MUTED)
        self.preview_info.pack(side="left")
        self.fit_btn = button(toolbar, "Vừa khung", self.fit_preview)
        self.fit_btn.configure(pady=5, font=(FONT, 8))
        self.fit_btn.pack(side="right")
        self.canvas = tk.Canvas(preview_box, bg=CANVAS, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_preview())
        self.canvas.bind("<MouseWheel>", lambda e: self.change_zoom(1.1 if e.delta > 0 else 1/1.1))
        self.canvas.bind("<Button-4>", lambda e: self.change_zoom(1.1))
        self.canvas.bind("<Button-5>", lambda e: self.change_zoom(1/1.1))

    def scroll_tab(self, name):
        shell = tk.Frame(self.notebook, bg=PANEL)
        self.notebook.add(shell, text=name)
        canvas = tk.Canvas(shell, bg=PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        inner = tk.Frame(canvas, bg=PANEL)
        win = canvas.create_window(0, 0, window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
        # Scoped bindings: scrolling a tab never changes the drawing or another tab.
        def wheel(event):
            if canvas.bbox("all")[3] > canvas.winfo_height():
                canvas.yview_scroll(-1 if event.delta > 0 or event.num == 4 else 1, "units")
        def bind_children(widget):
            widget.bind("<MouseWheel>", wheel, add="+")
            widget.bind("<Button-4>", wheel, add="+")
            widget.bind("<Button-5>", wheel, add="+")
            for child in widget.winfo_children():
                if not isinstance(child, ttk.Scale):
                    bind_children(child)
        self.root.after_idle(lambda: bind_children(inner))
        return inner

    def section(self, parent, text):
        label(parent, text, 9, MUTED, True).pack(anchor="w", padx=12, pady=(20, 9))

    def check(self, parent, text, key):
        c = ttk.Checkbutton(parent, text=text, variable=self.vars[key], command=self.controls_changed)
        c.pack(anchor="w", padx=12)
        return c

    def build_shape_tab(self, parent):
        self.section(parent, "01   KÍCH THƯỚC")
        for key, title in [("width", "Chiều rộng"), ("height", "Chiều cao")]:
            row = tk.Frame(parent, bg=PANEL)
            row.pack(fill="x", padx=12, pady=5)
            label(row, title, 10).pack(side="left")
            label(row, "px", 9, MUTED).pack(side="right", padx=(6, 0))
            entry = tk.Spinbox(row, from_=20, to=3000, increment=10, width=7,
                               textvariable=self.vars[key], bg=FIELD, fg=TEXT,
                               buttonbackground=FIELD, insertbackground=ACCENT,
                               relief="flat", highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=ACCENT, font=(FONT, 11), command=self.controls_changed)
            entry.pack(side="right", ipady=7)
            entry.bind("<KeyRelease>", self.queue_input)
            entry.bind("<Return>", lambda e: self.controls_changed())
            entry.bind("<FocusOut>", lambda e: self.controls_changed())
            setattr(self, key+"_entry", entry)
        label(parent, "20 – 3.000 px  ·  Nhập số nguyên", 8, MUTED).pack(anchor="w", padx=12, pady=3)
        self.check(parent, "Vuông cân · đồng bộ hai cạnh", "sync")
        self.section(parent, "02   MẪU NHANH")
        presets = tk.Frame(parent, bg=PANEL)
        presets.pack(fill="x", padx=12)
        for i, (text, w, h, sync) in enumerate([("Vuông cân", 360, 360, True), ("Tỉ lệ 3 : 4", 400, 300, False),
                                                ("Dáng cao", 240, 480, False), ("Dáng rộng", 560, 240, False)]):
            b = button(presets, text, lambda w=w, h=h, sync=sync: self.quick_preset(w, h, sync))
            b.configure(padx=6, pady=8, font=(FONT, 9))
            b.grid(row=i//2, column=i%2, sticky="ew", padx=(0, 5) if i%2 == 0 else (0, 0), pady=3)
        presets.columnconfigure((0, 1), weight=1)
        self.section(parent, "03   XOAY & LẬT")
        self.rotation_caption = label(parent, "Góc xoay  0°", 10)
        self.rotation_caption.pack(anchor="w", padx=12)
        self.rotation_scale = ttk.Scale(parent, from_=0, to=360, variable=self.vars["rotation"], command=self.scale_changed)
        self.rotation_scale.pack(fill="x", padx=12, pady=(9, 6))
        transforms = tk.Frame(parent, bg=PANEL)
        transforms.pack(fill="x", padx=12)
        for i, (text, action) in enumerate([("↻ 90°", self.rotate), ("Lật ↔", lambda: self.flip("flip_x")),
                                          ("Lật ↕", lambda: self.flip("flip_y"))]):
            b = button(transforms, text, action)
            b.configure(padx=5, font=(FONT, 9))
            b.grid(row=0, column=i, sticky="ew", padx=(0, 4))
            transforms.columnconfigure(i, weight=1)
        self.section(parent, "04   TRÊN MÀN HÌNH")
        self.check(parent, "Luôn nổi trên cửa sổ khác", "topmost")
        self.check(parent, "Khóa di chuyển & kích thước", "locked")
        button(parent, "Đưa tam giác về giữa màn hình", self.center_overlay).pack(fill="x", padx=12, pady=(8, 10))
        label(parent, "Chuột trái: kéo · Chuột phải: co giãn\nCon lăn: đổi kích thước · Esc: ẩn", 8, MUTED, justify="left").pack(anchor="w", padx=12, pady=(0, 18))

    def build_style_tab(self, parent):
        self.section(parent, "01   BẢNG MÀU")
        self.color_buttons = []
        palette = tk.Frame(parent, bg=PANEL)
        palette.pack(fill="x", padx=12)
        for i, color in enumerate(["#38D9AD", "#69B9FF", "#B9A0FF", "#FFBC66", "#FF7897", "#FFFFFF"]):
            b = tk.Button(palette, text="", width=1, bg=color, activebackground=color, bd=0,
                          cursor="hand2", command=lambda c=color: self.change_color(c))
            b.grid(row=0, column=i, padx=3, ipady=9, sticky="ew")
            palette.columnconfigure(i, weight=1, uniform="swatch")
            self.color_buttons.append(b)
        self.color_label = label(parent, "", 9, MUTED)
        self.color_label.pack(anchor="w", padx=12, pady=8)
        button(parent, "Chọn màu tùy chỉnh…", lambda: self.pick_color("color")).pack(fill="x", padx=12, pady=4)
        button(parent, "Chọn màu đường viền…", lambda: self.pick_color("outline")).pack(fill="x", padx=12, pady=4)
        self.check(parent, "Tô màu bên trong tam giác", "filled")
        self.section(parent, "02   ĐỘ HIỂN THỊ & VIỀN")
        self.opacity_caption = label(parent, "", 10)
        self.opacity_caption.pack(anchor="w", padx=12)
        ttk.Scale(parent, from_=.15, to=1, variable=self.vars["opacity"], command=self.scale_changed).pack(fill="x", padx=12, pady=10)
        label(parent, "15%: trong hơn  ↔  100%: đậm hoàn toàn", 8, MUTED).pack(anchor="w", padx=12)
        self.line_caption = label(parent, "", 10)
        self.line_caption.pack(anchor="w", padx=12, pady=(18, 0))
        ttk.Scale(parent, from_=1, to=12, variable=self.vars["line_width"], command=self.scale_changed).pack(fill="x", padx=12, pady=10)
        self.section(parent, "03   KHUNG XEM TRƯỚC")
        self.check(parent, "Hiện lưới căn chỉnh", "grid")
        self.check(parent, "Hiện đỉnh & độ dài cạnh", "labels")
        label(parent, "Lưới và nhãn chỉ nằm trong khung xem\ntrước; ảnh xuất có nền trong suốt.", 8, MUTED, justify="left").pack(anchor="w", padx=12, pady=10)
        button(parent, "Áp dụng phong cách Aurora", self.aurora).pack(fill="x", padx=12, pady=(12, 20))

    def build_saved_tab(self, parent):
        self.section(parent, "01   BỘ SƯU TẬP CỦA BẠN")
        label(parent, "Lưu màu sắc, kích thước và góc xoay\nđể dùng lại chỉ bằng một lần chọn.", 9, MUTED, justify="left").pack(anchor="w", padx=12)
        self.preset_list = tk.Listbox(parent, bg=FIELD, fg=TEXT, selectbackground="#225A50", selectforeground=TEXT,
                                     relief="flat", height=7, exportselection=False, highlightthickness=1,
                                     highlightbackground=BORDER, font=(FONT, 10))
        self.preset_list.pack(fill="x", padx=12, pady=12)
        self.preset_list.bind("<Double-Button-1>", lambda e: self.load_preset())
        button(parent, "+ Lưu thành mẫu mới", self.save_preset, True).pack(fill="x", padx=12, pady=4)
        button(parent, "Áp dụng mẫu đã chọn", self.load_preset).pack(fill="x", padx=12, pady=4)
        button(parent, "Xóa mẫu đã chọn", self.delete_preset).pack(fill="x", padx=12, pady=4)
        self.section(parent, "02   CẤU HÌNH")
        button(parent, "Xuất cấu hình JSON", self.export_config).pack(fill="x", padx=12, pady=4)
        button(parent, "Nhập cấu hình JSON", self.import_config).pack(fill="x", padx=12, pady=4)
        button(parent, "Khôi phục hình mặc định", self.reset).pack(fill="x", padx=12, pady=(15, 20))
        self.refresh_presets()

    def read_controls(self):
        data = self.state.to_dict()
        for key in data:
            raw = self.vars[key].get()
            if key in ("width", "height"):
                try:
                    data[key] = int(raw)
                except (ValueError, TypeError):
                    raise ValueError("Hãy nhập số nguyên cho chiều rộng và chiều cao.") from None
            elif key == "line_width":
                data[key] = round(float(raw))
            elif key in ("opacity", "rotation"):
                data[key] = float(raw)
            else:
                data[key] = raw
        return TriangleState.from_dict(data)

    def queue_input(self, _event=None):
        if self._input_job:
            self.root.after_cancel(self._input_job)
        self._input_job = self.root.after(450, self.controls_changed)

    def scale_changed(self, _value=None):
        if not self._syncing:
            self.controls_changed()

    def controls_changed(self):
        if self._syncing:
            return True
        if self._input_job:
            self.root.after_cancel(self._input_job)
            self._input_job = None
        try:
            new = self.read_controls()
        except (ValueError, tk.TclError) as exc:
            self.status(str(exc), error=True)
            return False
        if new.to_dict() != self.state.to_dict():
            self.set_state(new)
        return True

    def set_state(self, state, remember=True):
        self.state = state.validate()
        self.refresh()
        if remember:
            if self._history_job:
                self.root.after_cancel(self._history_job)
            self._history_job = self.root.after(350, self.commit_history)
        self.queue_save()
        self.status("Đã cập nhật · Thiết lập được lưu tự động")

    def refresh(self):
        self._syncing = True
        try:
            for key, value in self.state.to_dict().items():
                self.vars[key].set(value)
            self.height_entry.configure(state="disabled" if self.state.sync else "normal",
                                        disabledbackground=FIELD, disabledforeground=MUTED)
            self.rotation_caption.configure(text=f"Góc xoay   {self.state.rotation:.0f}°")
            self.opacity_caption.configure(text=f"Độ hiển thị   {self.state.opacity:.0%}")
            self.line_caption.configure(text=f"Độ dày viền   {self.state.line_width} px")
            self.color_label.configure(text=f"Màu hình  {self.state.color.upper()}")
            self.type_label.configure(text="TAM GIÁC VUÔNG CÂN" if self.state.width == self.state.height else "TAM GIÁC VUÔNG")
            m = measurements(self.state)
            self.stat_labels["area"].configure(text=f'{m["area"]:,.0f} px²')
            self.stat_labels["perimeter"].configure(text=f'{m["perimeter"]:,.1f} px')
            self.stat_labels["angle"].configure(text=f'{m["angle_a"]:.1f}°')
            for key, box in self.stat_boxes.items():
                self.fit_stat_value(key, box.winfo_width())
            self.undo_btn.configure(state="normal" if len(self.history) > 1 or self.state.to_dict() != self.history[-1] else "disabled")
            self.redo_btn.configure(state="normal" if self.future else "disabled")
            self.draw_preview()
            self.overlay.render()
        finally:
            self._syncing = False

    def draw_preview(self):
        if not hasattr(self, "canvas"):
            return
        c = self.canvas
        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 30 or ch < 30:
            return
        c.delete("all")
        if self.state.grid:
            for x in range(0, cw, 28):
                c.create_line(x, 0, x, ch, fill="#182837")
            for y in range(0, ch, 28):
                c.create_line(0, y, cw, y, fill="#182837")
            c.create_line(cw/2, 0, cw/2, ch, fill="#293B4C", dash=(3, 5))
            c.create_line(0, ch/2, cw, ch/2, fill="#293B4C", dash=(3, 5))
        pts = vertices(self.state)
        xmin, xmax = min(p[0] for p in pts), max(p[0] for p in pts)
        ymin, ymax = min(p[1] for p in pts), max(p[1] for p in pts)
        horizontal_space = cw-min(170, cw*.22)
        vertical_space = ch-min(140, ch*.30)
        scale = min(max(10, horizontal_space)/(xmax-xmin), max(10, vertical_space)/(ymax-ymin)) * self.zoom
        center = ((xmin+xmax)/2, (ymin+ymax)/2)
        shown = [((x-center[0])*scale+cw/2, (y-center[1])*scale+ch/2) for x, y in pts]
        flattened = [v for p in shown for v in p]
        color = self.blend(self.state.color, CANVAS, self.state.opacity)
        outline = self.blend(self.state.outline, CANVAS, self.state.opacity)
        c.create_polygon(*[v+5 for v in flattened], fill="#08121C" if self.state.filled else "", outline="")
        c.create_polygon(*flattened, fill=color if self.state.filled else "", outline=outline,
                         width=max(1, self.state.line_width*min(scale, 2)), joinstyle="round")
        a, b, d = shown
        def unit(p, q):
            dx, dy = p[0]-q[0], p[1]-q[1]
            length = math.hypot(dx, dy)
            return dx/length, dy/length
        u, v = unit(a, b), unit(d, b)
        size = min(18, self.state.width*scale*.12, self.state.height*scale*.12)
        right_mark = [(b[0]+u[0]*size, b[1]+u[1]*size),
                      (b[0]+(u[0]+v[0])*size, b[1]+(u[1]+v[1])*size),
                      (b[0]+v[0]*size, b[1]+v[1]*size)]
        c.create_line(*[val for p in right_mark for val in p], fill=outline, width=1.5)
        if self.state.labels:
            centroid = (sum(x for x, _ in shown)/3, sum(y for _, y in shown)/3)
            for name, (x, y) in zip("ABC", shown):
                c.create_oval(x-4, y-4, x+4, y+4, fill=CANVAS, outline=ACCENT, width=2)
                dx, dy = x-centroid[0], y-centroid[1]
                length = max(1, math.hypot(dx, dy))
                c.create_text(x+dx/length*23, y+dy/length*23, text=name, fill=TEXT, font=(FONT, 11, "bold"))
            m = measurements(self.state)
            for p, q, text in [(shown[0], shown[1], f"{self.state.height} px"),
                               (shown[1], shown[2], f"{self.state.width} px"),
                               (shown[0], shown[2], f'{m["hypotenuse"]:.1f} px')]:
                x, y = (p[0]+q[0])/2, (p[1]+q[1])/2
                dx, dy = q[1]-p[1], p[0]-q[0]
                length = max(1, math.hypot(dx, dy))
                dx, dy = dx/length, dy/length
                if dx*(x-centroid[0])+dy*(y-centroid[1]) < 0:
                    dx, dy = -dx, -dy
                tag = c.create_text(x+dx*27, y+dy*27, text=text, fill=MUTED, font=(FONT, 10))
                bb = c.bbox(tag)
                rect = c.create_rectangle(bb[0]-5, bb[1]-3, bb[2]+5, bb[3]+3, fill=CANVAS, outline="")
                c.tag_lower(rect, tag)
        self.preview_info.configure(text=f"{self.state.width} × {self.state.height} px  ·  Xem {scale:.0%}")

    @staticmethod
    def blend(fg, bg, alpha):
        vals = [round(int(fg[i:i+2], 16)*alpha+int(bg[i:i+2], 16)*(1-alpha)) for i in (1, 3, 5)]
        return "#"+"".join(f"{v:02x}" for v in vals)

    def fit_stat_value(self, key, width):
        if width < 50:
            return
        widget = self.stat_labels[key]
        for size in range(17, 9, -1):
            font = tkfont.Font(root=self.root, family=FONT, size=size, weight="bold")
            if font.measure(widget.cget("text")) <= width-28:
                break
        widget.configure(font=(FONT, size, "bold"))

    def change_zoom(self, factor):
        self.zoom = max(.25, min(2., self.zoom*factor))
        self.draw_preview()

    def fit_preview(self):
        self.zoom = 1.
        self.draw_preview()

    def change(self, **updates):
        if self.controls_changed():
            data = self.state.to_dict()
            data.update(updates)
            self.set_state(TriangleState.from_dict(data))

    def quick_preset(self, width, height, sync):
        # Presets also repair incomplete or invalid dimension entry fields.
        self.vars["width"].set(width)
        self.vars["height"].set(height)
        self.vars["sync"].set(sync)
        self.vars["rotation"].set(0)
        self.vars["flip_x"].set(False)
        self.vars["flip_y"].set(False)
        self.controls_changed()
        self.fit_preview()

    def rotate(self):
        self.change(rotation=(self.state.rotation+90)%360)

    def flip(self, key):
        self.change(**{key: not getattr(self.state, key)})

    def change_color(self, color):
        self.change(color=color)

    def pick_color(self, key):
        chosen = colorchooser.askcolor(getattr(self.state, key), parent=self.root, title="Chọn màu tam giác")
        if chosen[1]:
            self.change(**{key: chosen[1]})

    def aurora(self):
        self.change(color="#38D9AD", outline="#AAFFE7", line_width=2, opacity=.55, filled=True)

    def commit_history(self):
        if self._history_job:
            self.root.after_cancel(self._history_job)
            self._history_job = None
        data = self.state.to_dict()
        if data != self.history[-1]:
            self.history.append(data)
            self.history = self.history[-60:]
            self.future.clear()
        self.undo_btn.configure(state="normal" if len(self.history) > 1 else "disabled")
        self.redo_btn.configure(state="normal" if self.future else "disabled")

    def undo(self):
        self.commit_history()
        if len(self.history) > 1:
            self.future.append(self.history.pop())
            self.set_state(TriangleState.from_dict(self.history[-1]), remember=False)
            self.status("Đã hoàn tác · Ctrl+Y để làm lại")

    def redo(self):
        self.commit_history()
        if self.future:
            data = self.future.pop()
            self.history.append(data)
            self.set_state(TriangleState.from_dict(data), remember=False)
            self.status("Đã làm lại thao tác")

    def payload(self):
        return {"version": 2, "state": self.state.to_dict(), "anchor": list(self.overlay.anchor), "presets": self.presets}

    def queue_save(self):
        if self._save_job:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(800, self.persist)

    def persist(self):
        self._save_job = None
        try:
            self.store.save(self.payload())
            return True
        except (OSError, ValueError) as exc:
            self.status(f"Chưa lưu được cấu hình: {exc}", error=True)
            return False

    def save_now(self):
        if self.controls_changed() and self.persist():
            self.status("Đã lưu cấu hình hiện tại")

    def status(self, text, error=False):
        self.status_label.configure(text=text, fg="#FF9C9C" if error else MUTED)

    def toggle_overlay(self):
        if self.overlay.visible:
            self.overlay.hide()
        elif self.controls_changed():
            self.overlay.show()
            self.overlay_button.configure(text="Ẩn tam giác nổi  ·  F2")
            self.queue_save()
            self.status("Tam giác đang nổi · Esc để ẩn · Chuột trái để kéo" if self.overlay.color_key_supported
                        else "Tam giác đang nổi; hệ điều hành này dùng nền đặc thay cho nền trong suốt.")

    def overlay_hidden(self):
        self.overlay_button.configure(text="Bật tam giác nổi  ↗")
        self.status("Đã ẩn tam giác · Nhấn F2 để bật lại")

    def overlay_resize(self, width, height, final):
        data = self.state.to_dict()
        data.update(width=width, height=height)
        self.set_state(TriangleState.from_dict(data), remember=final)
        if final:
            self.commit_history()

    def overlay_move(self, _anchor):
        self.queue_save()

    def center_overlay(self):
        if self.controls_changed():
            self.overlay.center()
            self.status("Đã đặt vị trí tam giác ở giữa màn hình")

    def refresh_presets(self):
        self.preset_list.delete(0, "end")
        for name in self.presets:
            self.preset_list.insert("end", name)

    def save_preset(self):
        if not self.controls_changed():
            return
        name = simpledialog.askstring("Lưu mẫu", "Đặt tên mẫu (tối đa 40 ký tự):", parent=self.root)
        if name is None:
            return
        name = name.strip()
        if not 1 <= len(name) <= 40:
            self.status("Tên mẫu phải dài từ 1 đến 40 ký tự.", True)
            return
        if name in self.presets and not messagebox.askyesno("Ghi đè mẫu", f"Cập nhật mẫu “{name}”?", parent=self.root):
            return
        if name not in self.presets and len(self.presets) >= 50:
            self.status("Bạn đã có 50 mẫu. Hãy xóa một mẫu trước khi thêm.", True)
            return
        self.presets[name] = self.state.to_dict()
        self.refresh_presets()
        self.queue_save()
        self.status(f"Đã thêm mẫu: {name}")

    def selected_preset(self):
        selection = self.preset_list.curselection()
        if selection:
            return self.preset_list.get(selection[0])
        self.status("Chọn một mẫu trong danh sách trước nhé.")
        return None

    def load_preset(self):
        name = self.selected_preset()
        if name:
            self.set_state(TriangleState.from_dict(self.presets[name]))
            self.fit_preview()
            self.status(f"Đang sử dụng mẫu: {name}")

    def delete_preset(self):
        name = self.selected_preset()
        if name and messagebox.askyesno("Xóa mẫu", f"Xóa mẫu “{name}”?", parent=self.root):
            del self.presets[name]
            self.refresh_presets()
            self.queue_save()

    def export_menu(self):
        menu = tk.Menu(self.root, tearoff=0, bg=PANEL, fg=TEXT, activebackground=FIELD, activeforeground=ACCENT)
        menu.add_command(label="PNG · Ảnh nền trong suốt", command=lambda: self.export("png"))
        menu.add_command(label="SVG · Vector phóng to không vỡ", command=lambda: self.export("svg"))
        menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def export(self, kind):
        if not self.controls_changed():
            return
        path = filedialog.asksaveasfilename(parent=self.root, title="Xuất tam giác", defaultextension="."+kind,
                                           initialfile="tam-giac."+kind, filetypes=[(kind.upper(), "*."+kind)])
        if not path:
            return
        try:
            (export_png if kind == "png" else export_svg)(self.state, path)
            self.status(f"Đã xuất {kind.upper()}: {Path(path).name}")
        except ImportError:
            messagebox.showerror("Thiếu Pillow", "Chạy CAI_DAT.bat để cài Pillow, rồi xuất PNG lại.\nBạn vẫn có thể xuất SVG ngay.", parent=self.root)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Chưa xuất được ảnh", str(exc), parent=self.root)

    def export_config(self):
        if not self.controls_changed():
            return
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".json", initialfile="triangle-studio.json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                Path(path).write_text(json.dumps(self.payload(), indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
                self.status("Đã xuất cấu hình và toàn bộ mẫu đã lưu")
            except OSError as exc:
                messagebox.showerror("Chưa xuất được cấu hình", str(exc), parent=self.root)

    def import_config(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            if Path(path).stat().st_size > 1_000_000:
                raise ValueError("Tệp cấu hình quá lớn (tối đa 1 MB).")
            data = normalize_payload(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Cấu hình không hợp lệ", str(exc), parent=self.root)
            return
        if not messagebox.askyesno("Nhập cấu hình", "Thay thiết lập và bộ mẫu hiện tại bằng cấu hình này?", parent=self.root):
            return
        # Preserve current preset collection in a backup before a deliberate replacement.
        try:
            backup = self.store.path.with_name("before-import.json")
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(json.dumps(self.payload(), ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Chưa sao lưu được", str(exc), parent=self.root)
            return
        self.presets = data["presets"]
        self.overlay.anchor = data["anchor"]
        self.set_state(TriangleState.from_dict(data["state"]))
        self.refresh_presets()
        if self.overlay.visible:
            self.overlay.recover_if_offscreen()
        self.status("Đã nhập cấu hình · Bản trước đó được giữ trong before-import.json")

    def reset(self):
        self.set_state(TriangleState())
        self.fit_preview()
        self.status("Đã khôi phục hình mặc định · Các mẫu đã lưu vẫn được giữ")

    def help(self):
        messagebox.showinfo("Triangle Studio · Hướng dẫn nhanh",
            "1. Nhập chiều rộng và chiều cao, hoặc chọn mẫu nhanh.\n"
            "2. Chọn màu, độ hiển thị và góc xoay.\n"
            "3. Bật tam giác nổi để đặt hình lên màn hình.\n\n"
            "TAM GIÁC NỔI\nChuột trái: kéo di chuyển\nChuột phải: kéo sang phải để tăng rộng, kéo lên để tăng cao\n"
            "Con lăn: phóng to / thu nhỏ hình\nKhóa: ngăn kéo và đổi kích thước; vẫn chỉnh được từ bảng điều khiển\n\n"
            "PHÍM TẮT (khi ứng dụng đang được chọn)\nF2: hiện / ẩn hình  ·  Esc: ẩn hình\n"
            "Ctrl+Z / Ctrl+Y: hoàn tác / làm lại\nCtrl+S: lưu  ·  Ctrl+E: xuất PNG\n\n"
            "Con lăn trong khung xem trước chỉ thay độ phóng đại.\n"
            "Kích thước dùng pixel trong hệ tọa độ Tk, không phải cm vật lý.\n"
            "Nền tam giác nổi trong suốt được hỗ trợ trên Windows;\nhệ khác có thể hiển thị nền đặc.\n"
            "PNG/SVG luôn xuất riêng tam giác, không kèm lưới và nhãn.", parent=self.root)

    def close(self):
        if not self.controls_changed():
            if not messagebox.askyesno("Dữ liệu chưa hợp lệ", "Bỏ phần nhập chưa hợp lệ và đóng bằng thiết lập hợp lệ gần nhất?", parent=self.root):
                return
        if not self.persist():
            if not messagebox.askyesno("Chưa lưu được", "Không lưu được cấu hình. Vẫn đóng ứng dụng?", parent=self.root):
                return
        self.overlay.destroy()
        self.root.destroy()


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    TriangleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
