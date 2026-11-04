import math
import time
import tkinter as tk
from tkinter import scrolledtext

LOG_LIMIT = 300


def rn(v):
    return math.floor(v + 0.5 + 1e-9)


def _add(log, s):
    if log is not None and len(log) < LOG_LIMIT:
        log.append(s)


def step(x1, y1, x2, y2, log=None):
    if abs(x2 - x1) >= abs(y2 - y1):
        if x1 > x2:
            x1, x2, y1, y2 = x2, x1, y2, y1
        if x1 == x2:
            if log is not None:
                _add(log, "Вырожденный отрезок (точка)")
            return [(x1, y1)]
        k = (y2 - y1) / (x2 - x1)
        if log is not None:
            _add(log, "Пошаговый: ведущая ось X")
            _add(log, f"k = Dy/Dx = {k:.4f};  y = round(y1 + k·(x−x1))")
        pts = []
        for x in range(x1, x2 + 1):
            y = rn(y1 + k * (x - x1))
            pts.append((x, y))
            if log is not None:
                _add(log, f"  x={x:5d}   y = round({y1} + {k:.3f}·{x - x1:<3}) = {y}")
        return pts
    if y1 > y2:
        x1, x2, y1, y2 = x2, x1, y2, y1
    k = (x2 - x1) / (y2 - y1)
    if log is not None:
        _add(log, "Пошаговый: ведущая ось Y")
        _add(log, f"k = Dx/Dy = {k:.4f};  x = round(x1 + k·(y−y1))")
    pts = []
    for y in range(y1, y2 + 1):
        x = rn(x1 + k * (y - y1))
        pts.append((x, y))
        if log is not None:
            _add(log, f"  y={y:5d}   x = round({x1} + {k:.3f}·{y - y1:<3}) = {x}")
    return pts


def dda(x1, y1, x2, y2, log=None):
    dx, dy = x2 - x1, y2 - y1
    L = max(abs(dx), abs(dy))
    if log is not None:
        _add(log, "ЦДА")
        _add(log, f"Dx={dx}, Dy={dy}, L=max(|Dx|,|Dy|)={L}")
    if L == 0:
        if log is not None:
            _add(log, "Вырожденный отрезок (точка)")
        return [(x1, y1)]
    if (abs(dx) >= abs(dy) and dx < 0) or (abs(dx) < abs(dy) and dy < 0):
        x1, y1, x2, y2 = x2, y2, x1, y1
        dx, dy = -dx, -dy
        if log is not None:
            _add(log, f"Концы переставлены: старт ({x1},{y1})")
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    ix, iy = abs(dx) / L, abs(dy) / L
    if log is not None:
        _add(log, f"Приращения за шаг: Dx/L={dx / L:.4f}, Dy/L={dy / L:.4f}; точек {L + 1}")
    pts = []
    ax = ay = 0.0
    for i in range(L + 1):
        xf, yf = x1 + sx * ax, y1 + sy * ay
        x, y = rn(xf), rn(yf)
        pts.append((x, y))
        if log is not None:
            _add(log, f"  i={i:3d}:  x={xf:8.3f}:{x:5d},  y={yf:8.3f}:{y:5d}")
        ax += ix
        ay += iy
    return pts


def bres_line(x1, y1, x2, y2, log=None):
    ox = (x1, y1, x2, y2)
    steep = abs(y2 - y1) > abs(x2 - x1)
    if steep:
        x1, y1, x2, y2 = y1, x1, y2, x2
    if x1 > x2:
        x1, x2, y1, y2 = x2, x1, y2, y1
    dx, dy = x2 - x1, abs(y2 - y1)
    E, ys, y = 2 * dy - dx, (1 if y1 < y2 else -1), y1

    if log is not None:
        _add(log, "Брезенхем (линия)")
        if steep or (x1, y1, x2, y2) != ox:
            _add(log, f"Исходный ({ox[0]},{ox[1]})–({ox[2]},{ox[3]}) : 1-й октант ({x1},{y1})–({x2},{y2})")
            if steep:
                _add(log, "(X и Y в формулах поменяны местами)")
        _add(log, f"Dx={dx}, Dy={dy}, E'₀ = 2·Dy−Dx = {E}")

    pts = [(y, x1) if steep else (x1, y)]
    if log is not None:
        _add(log, f"  шаг 0:  X={x1}, Y={y}, E'={E} : {pts[-1]}")

    for x in range(x1 + 1, x2 + 1):
        if E >= 0:
            y += ys
            E += 2 * (dy - dx)
            dec = "E'≥0 : Y+1"
        else:
            E += 2 * dy
            dec = "E'<0 : Y без изм."
        pix = (y, x) if steep else (x, y)
        pts.append(pix)
        if log is not None:
            _add(log, f"  шаг {x - x1}:  X={x}, Y={y}, {dec}, E'={E} : {pix}")
    return pts


def _sym8(cx, cy, x, y):
    return [(cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y), (cx - x, cy - y),
            (cx + y, cy + x), (cx - y, cy + x), (cx + y, cy - x), (cx - y, cy - x)]


def bres_circle(cx, cy, r, log=None):
    if r < 0:
        if log is not None:
            _add(log, f"Центр ({cx},{cy}), R={r} < 0 — некорректный радиус")
        return []
    x, y, d = 0, r, 3 - 2 * r
    if log is not None:
        _add(log, "Брезенхем (окружность)")
        _add(log, f"Центр ({cx},{cy}),  R={r}")
        _add(log, f"Старт:  X=0, Y={r}, d = 3−2R = {d}")
    pts = _sym8(cx, cy, x, y)
    i = 0
    while x < y:
        if d < 0:
            d += 4 * x + 6
            dec = "d<0 : d+=4X+6"
        else:
            d += 4 * (x - y) + 10
            y -= 1
            dec = "d≥0 : d+=4(X−Y)+10, Y−1"
        x += 1
        pts += _sym8(cx, cy, x, y)
        i += 1
        if log is not None:
            _add(log, f"  шаг {i}:  X={x}, Y={y}, {dec}, d={d}")
    return pts


class App:
    S = 30
    CW, CH = 580, 620
    LW = 420

    def __init__(self, root):
        self.root = root
        root.title("Лаб. 3 — Базовые растровые алгоритмы")
        root.resizable(False, False)
        self.OX, self.OY = self.CW // 2, self.CH // 2
        self.scale = self.S
        self._last = None
        self._build()

    def _build(self):
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        left = tk.Frame(main, width=self.LW)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        self._build_left(left)

        right = tk.Frame(main)
        right.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(right, width=self.CW, height=self.CH,
                                bg="white",
                                highlightthickness=1, highlightbackground="#999")
        self.canvas.pack(anchor="nw")

        tk.Label(self.root, justify="left", anchor="w",
                 font=("TkDefaultFont", 8), fg="#333",
                 wraplength=1000,
                 text=("Пиксель (x, y) — клетка [x, x+1) × [y, y+1), центр (x+0.5, y+0.5). "
                       "Ось Y вверх; на экране верх клетки = OY − (y+1)·scale. "
                       "Подписи осей — на левой/нижней границе клетки с этим индексом.")
                 ).pack(fill="x", padx=8, pady=(0, 6))

        for e in (self.ex1, self.ey1, self.ex2, self.ey2,
                  self.ecx, self.ecy, self.er):
            e.bind("<Return>", lambda _ev: self.draw())

        self._draw_grid()

    def _build_left(self, parent):
        seg = tk.LabelFrame(parent, text="Отрезок")
        seg.pack(fill="x", pady=(0, 4))
        row = tk.Frame(seg);
        row.pack(pady=(4, 2))
        self.ex1 = self._e(row, "x₁", "0")
        self.ey1 = self._e(row, "y₁", "0")
        row = tk.Frame(seg);
        row.pack(pady=(0, 4))
        self.ex2 = self._e(row, "x₂", "10")
        self.ey2 = self._e(row, "y₂", "5")

        cir = tk.LabelFrame(parent, text="Окружность")
        cir.pack(fill="x", pady=(0, 4))
        row = tk.Frame(cir);
        row.pack(pady=4)
        self.ecx = self._e(row, "cx", "0")
        self.ecy = self._e(row, "cy", "0")
        self.er = self._e(row, "R", "5")

        sc = tk.LabelFrame(parent, text="Масштаб")
        sc.pack(fill="x", pady=(0, 4))
        row = tk.Frame(sc);
        row.pack(pady=4)
        self.scale_var = tk.IntVar(value=self.S)
        tk.Spinbox(row, from_=1, to=100, increment=1, width=4,
                   textvariable=self.scale_var,
                   command=self._on_scale).pack(side="left", padx=4)
        self.auto = tk.BooleanVar(value=True)
        tk.Checkbutton(row, text="авто", variable=self.auto).pack(side="left")

        alg = tk.LabelFrame(parent, text="Алгоритм")
        alg.pack(fill="x", pady=(0, 4))
        self.alg = tk.StringVar(value="bres_line")
        for txt, val in [("Пошаговый", "step"),
                         ("ЦДА", "dda"),
                         ("Брезенхем (линия)", "bres_line"),
                         ("Брезенхем (окружность)", "bres_circle")]:
            tk.Radiobutton(alg, text=txt, variable=self.alg, value=val,
                           command=self.draw, anchor="w"
                           ).pack(fill="x", padx=4, pady=1)

        act = tk.Frame(parent)
        act.pack(fill="x", pady=(2, 4))
        tk.Button(act, text="Нарисовать", command=self.draw).pack(fill="x", pady=1)
        tk.Button(act, text="Очистить", command=self.clear).pack(fill="x", pady=1)
        tk.Button(act, text="Замерить все 4", command=self.measure_all).pack(fill="x", pady=1)

        self.t_lbl = tk.Label(parent, text="Время: —", fg="#003366", anchor="w")
        self.t_lbl.pack(fill="x", pady=(2, 4))

        lf = tk.LabelFrame(parent, text="Сопроводительные вычисления")
        lf.pack(fill="both", expand=True)
        self.log = scrolledtext.ScrolledText(lf, height=10, wrap="char",
                                             font=("Courier New", 8))
        self.log.pack(fill="both", expand=True)

    def _e(self, parent, label, default):
        f = tk.Frame(parent)
        f.pack(side="left", padx=3)
        tk.Label(f, text=label).pack(side="left")
        e = tk.Entry(f, width=5, justify="center")
        e.pack(side="left")
        e.insert(0, default)
        return e

    def _draw_grid(self):
        c, s = self.canvas, self.scale
        W, H, OX, OY = self.CW, self.CH, self.OX, self.OY
        c.delete("grid")
        imin, imax = -OX // s - 1, OX // s + 2
        jmin, jmax = -OY // s - 1, OY // s + 2
        lab = 1 if s >= 28 else 5 if s >= 12 else 10
        for i in range(imin, imax):
            x = OX + i * s
            c.create_line(x, 0, x, H, fill="#ececec", tags="grid")
        for j in range(jmin, jmax):
            y = OY - j * s
            c.create_line(0, y, W, y, fill="#ececec", tags="grid")
        c.create_line(0, OY, W, OY, fill="#000", width=2, tags="grid")
        c.create_line(OX, 0, OX, H, fill="#000", width=2, tags="grid")
        c.create_polygon(W - 12, OY - 5, W - 2, OY, W - 12, OY + 5, fill="#000", tags="grid")
        c.create_polygon(OX - 5, 12, OX, 2, OX + 5, 12, fill="#000", tags="grid")
        c.create_text(W - 18, OY - 14, text="X",
                      font=("TkDefaultFont", 10, "bold"), tags="grid")
        c.create_text(OX + 14, 14, text="Y",
                      font=("TkDefaultFont", 10, "bold"), tags="grid")
        c.create_text(OX - 8, OY + 10, text="0",
                      font=("TkDefaultFont", 7), fill="#555", tags="grid")
        for i in range(imin, imax):
            if i != 0 and i % lab == 0:
                c.create_text(OX + i * s, OY + 12, text=str(i),
                              font=("TkDefaultFont", 7), fill="#555", tags="grid")
        for j in range(jmin, jmax):
            if j != 0 and j % lab == 0:
                c.create_text(OX - 12, OY - j * s, text=str(j),
                              font=("TkDefaultFont", 7), fill="#555", tags="grid")
        c.tag_lower("grid")

    def _pixel(self, x, y):
        s = self.scale
        x0, y0 = self.OX + x * s, self.OY - (y + 1) * s
        self.canvas.create_rectangle(x0, y0, x0 + s, y0 + s,
                                     fill="black", outline="", tags="pixel")

    def _redraw_last(self):
        if not self._last:
            return
        self.canvas.delete("pixel")
        for x, y in self._last:
            self._pixel(x, y)

    def _log(self, lines):
        for line in lines:
            self.log.insert("end", line + "\n")

    @staticmethod
    def _bench(fn, args):
        size = max(abs(args[2] - args[0]), abs(args[3] - args[1])) if len(args) == 4 else args[2]
        n = max(20, min(1000, 100000 // max(1, size)))
        t0 = time.perf_counter()
        for _ in range(n):
            fn(*args)
        return (time.perf_counter() - t0) / n * 1e6, n

    def _autoscale(self, extent):
        if not self.auto.get():
            return
        s = int(min(self.OX, self.OY) / (extent + 2))
        self.scale = max(1, min(100, s))
        self.scale_var.set(self.scale)

    def _on_scale(self):
        self.auto.set(False)
        self.scale = max(1, min(100, self.scale_var.get()))
        self.scale_var.set(self.scale)
        self._draw_grid()
        self._redraw_last()

    def clear(self):
        self.canvas.delete("pixel")
        self.log.delete("1.0", "end")
        self.t_lbl.config(text="Время: —")
        self._last = None

    def draw(self):
        self.canvas.delete("pixel")
        self.log.delete("1.0", "end")
        try:
            if self.alg.get() == "bres_circle":
                cx, cy, r = int(self.ecx.get()), int(self.ecy.get()), int(self.er.get())
                extent = max(abs(cx), abs(cy)) + abs(r)
                self._autoscale(extent)
                self._draw_grid()
                log = []
                pts = bres_circle(cx, cy, r, log)
                t, n = self._bench(bres_circle, (cx, cy, r))
            else:
                x1, y1 = int(self.ex1.get()), int(self.ey1.get())
                x2, y2 = int(self.ex2.get()), int(self.ey2.get())
                extent = max(abs(x1), abs(y1), abs(x2), abs(y2))
                self._autoscale(extent)
                self._draw_grid()
                fn = {"step": step, "dda": dda, "bres_line": bres_line}[self.alg.get()]
                log = []
                pts = fn(x1, y1, x2, y2, log)
                t, n = self._bench(fn, (x1, y1, x2, y2))
            for x, y in set(pts):
                self._pixel(x, y)
            self._last = set(pts)
            self._log(log)
            self._log(["", f"Уникальных пикселей: {len(set(pts))}",
                       f"Среднее время вызова: {t:.2f} мкс (из {n})"])
            self.t_lbl.config(text=f"Время: {t:.2f} мкс/вызов")
        except ValueError:
            self._log(["Ошибка: введите целые числа."])

    def measure_all(self):
        try:
            x1, y1 = int(self.ex1.get()), int(self.ey1.get())
            x2, y2 = int(self.ex2.get()), int(self.ey2.get())
            cx, cy, r = int(self.ecx.get()), int(self.ecy.get()), int(self.er.get())
        except ValueError:
            return
        self.log.delete("1.0", "end")
        self._log(["Временные характеристики (среднее по многим вызовам, без лога)",
                   f"Отрезок: ({x1},{y1})–({x2},{y2})   Окружность: ({cx},{cy}), R={r}",
                   ""])
        for name, fn, args in [
            ("Пошаговый (отрезок)", step, (x1, y1, x2, y2)),
            ("ЦДА (отрезок)", dda, (x1, y1, x2, y2)),
            ("Брезенхем (отрезок)", bres_line, (x1, y1, x2, y2)),
            ("Брезенхем (окружность)", bres_circle, (cx, cy, r)),
        ]:
            self._log([f"  {name:30s} {self._bench(fn, args)[0]:9.2f} мкс"])


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
