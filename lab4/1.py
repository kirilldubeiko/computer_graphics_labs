import tkinter as tk
from tkinter import messagebox
import math

X_MIN, Y_MIN = 150, 150
X_MAX, Y_MAX = 650, 450

DEFAULT_POLYGON = [
    (400, 100),
    (600, 200),
    (550, 450),
    (250, 450),
    (200, 200)
]


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def is_convex(polygon):
    n = len(polygon)
    if n < 3:
        return False
    sign = 0
    for i in range(n):
        c = cross(polygon[i], polygon[(i + 1) % n], polygon[(i + 2) % n])
        if abs(c) < 1e-6:
            continue
        if sign == 0:
            sign = 1 if c > 0 else -1
        elif (c > 0) != (sign > 0):
            return False
    return sign != 0


def compute_outcode(x, y):
    code = 0
    if y > Y_MAX: code |= 8
    if y < Y_MIN: code |= 4
    if x > X_MAX: code |= 2
    if x < X_MIN: code |= 1
    return code


def cohen_sutherland(x1, y1, x2, y2):
    outcode1 = compute_outcode(x1, y1)
    outcode2 = compute_outcode(x2, y2)
    accept = False
    if x1 == x2:
        k = None; b = None
    else:
        k = (y2 - y1) / (x2 - x1)
        b = y1 - k * x1
    while True:
        if (outcode1 == 0) and (outcode2 == 0):
            accept = True; break
        elif (outcode1 & outcode2) != 0:
            break
        else:
            oc = outcode1 if outcode1 != 0 else outcode2
            x = y = 0
            if oc & 8:
                y = Y_MAX; x = x1 if k is None else (y - b) / k
            elif oc & 4:
                y = Y_MIN; x = x1 if k is None else (y - b) / k
            elif oc & 2:
                x = X_MAX; y = y1 if k is None else k * x + b
            elif oc & 1:
                x = X_MIN; y = y1 if k is None else k * x + b
            if oc == outcode1:
                x1, y1 = x, y
                outcode1 = compute_outcode(x1, y1)
            else:
                x2, y2 = x, y
                outcode2 = compute_outcode(x2, y2)
    return (x1, y1, x2, y2) if accept else None


def cyrus_beck(x1, y1, x2, y2, polygon):
    dx = x2 - x1
    dy = y2 - y1
    t_enter, t_leave = 0.0, 1.0

    cx = sum(p[0] for p in polygon) / len(polygon)
    cy = sum(p[1] for p in polygon) / len(polygon)

    for i in range(len(polygon)):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]

        ex = p2[0] - p1[0]
        ey = p2[1] - p1[1]
        nx, ny = ey, -ex

        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        if (mx - cx) * nx + (my - cy) * ny < 0:
            nx, ny = -nx, -ny

        length = math.hypot(nx, ny)
        if length < 1e-6:
            continue
        nx /= length
        ny /= length

        A = dx * nx + dy * ny
        B = (x1 - p1[0]) * nx + (y1 - p1[1]) * ny

        if abs(A) < 1e-9:
            if B > 0:
                return None
        elif A > 0:
            t = -B / A
            if t < t_leave:
                t_leave = t
        else:
            t = -B / A
            if t > t_enter:
                t_enter = t

    if t_enter > t_leave:
        return None

    return (x1 + t_enter * dx, y1 + t_enter * dy,
            x1 + t_leave * dx, y1 + t_leave * dy)


class ClippingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Отсечение отрезков")

        self.polygon = DEFAULT_POLYGON[:]
        self.drawing_points = []

        ctrl = tk.Frame(root)
        ctrl.pack(pady=5)

        self.mode = tk.StringVar(value="rect")

        tk.Radiobutton(ctrl, text="Прямоугольник (Сазерленд-Коэн)",
                       variable=self.mode, value="rect",
                       command=self.switch_mode).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(ctrl, text="Многоугольник (Кирус-Бек)",
                       variable=self.mode, value="poly",
                       command=self.switch_mode).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(ctrl, text="Нарисовать многоугольник",
                       variable=self.mode, value="draw",
                       command=self.switch_mode).pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl, text="Очистить холст",
                  command=self.redraw_canvas).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="Сбросить многоугольник",
                  command=self.reset_polygon).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.root.bind("<Escape>", self.on_escape)

        self.start_x = None
        self.start_y = None
        self.temp_line = None
        self.last_mouse = None

        self.redraw_canvas()

    def switch_mode(self):
        if self.mode.get() == "draw":
            self.drawing_points = []
            self.last_mouse = None
        self.redraw_canvas()

    def reset_polygon(self):
        self.polygon = DEFAULT_POLYGON[:]
        self.drawing_points = []
        self.last_mouse = None
        self.mode.set("poly")
        self.redraw_canvas()

    def redraw_canvas(self):
        self.canvas.delete("all")
        mode = self.mode.get()

        if mode == "rect":
            self.canvas.create_rectangle(X_MIN, Y_MIN, X_MAX, Y_MAX,
                                         outline="blue", width=2, fill="#f0f8ff")
            self.canvas.create_text(X_MIN - 10, Y_MIN, text="x_min", anchor="e")
            self.canvas.create_text(X_MAX + 10, Y_MIN, text="x_max", anchor="w")
            self.canvas.create_text(X_MIN, Y_MIN - 10, text="y_min", anchor="s")
            self.canvas.create_text(X_MIN, Y_MAX + 10, text="y_max", anchor="n")
            self.canvas.create_text(10, 10,
                text="Зажмите ЛКМ и ведите мышь для рисования отрезка",
                anchor="nw", fill="gray")

        elif mode == "poly":
            if len(self.polygon) >= 3:
                self.canvas.create_polygon(self.polygon, outline="blue",
                                           width=2, fill="#f0f8ff")
            self.canvas.create_text(10, 10,
                text="Зажмите ЛКМ и ведите мышь для рисования отрезка",
                anchor="nw", fill="gray")

        elif mode == "draw":
            if len(self.drawing_points) >= 2:
                self.canvas.create_line(self.drawing_points + [self.drawing_points[0]],
                                        fill="green", width=2, dash=(4, 4))
            for (x, y) in self.drawing_points:
                self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                                        outline="green", fill="lightgreen", width=2)
            if self.drawing_points and self.last_mouse:
                last = self.drawing_points[-1]
                self.canvas.create_line(last[0], last[1],
                                        self.last_mouse[0], self.last_mouse[1],
                                        fill="gray", dash=(2, 2))
            self.canvas.create_text(10, 10,
                text="ЛКМ: добавить вершину | ПКМ: завершить | Esc: отмена",
                anchor="nw", fill="green")

    def on_button_press(self, event):
        if self.mode.get() == "draw":
            if self.drawing_points:
                lx, ly = self.drawing_points[-1]
                if abs(lx - event.x) < 3 and abs(ly - event.y) < 3:
                    return
            self.drawing_points.append((event.x, event.y))
            self.last_mouse = (event.x, event.y)
            self.redraw_canvas()
            return

        self.start_x, self.start_y = event.x, event.y

    def on_motion(self, event):
        if self.mode.get() == "draw":
            self.last_mouse = (event.x, event.y)
            self.redraw_canvas()
            return

        if self.start_x is None:
            return
        if self.temp_line:
            self.canvas.delete(self.temp_line)
        self.temp_line = self.canvas.create_line(
            self.start_x, self.start_y, event.x, event.y,
            fill="gray", dash=(4, 4), width=2)

    def on_button_release(self, event):
        if self.mode.get() == "draw":
            return
        if self.start_x is None:
            return

        end_x, end_y = event.x, event.y

        if self.temp_line:
            self.canvas.delete(self.temp_line)
            self.temp_line = None

        self.canvas.create_line(self.start_x, self.start_y, end_x, end_y,
                                fill="#aaaaaa", dash=(4, 4), width=2)

        if self.mode.get() == "rect":
            clipped = cohen_sutherland(self.start_x, self.start_y, end_x, end_y)
        else:
            clipped = cyrus_beck(self.start_x, self.start_y, end_x, end_y, self.polygon)

        if clipped:
            cx1, cy1, cx2, cy2 = clipped
            self.canvas.create_line(cx1, cy1, cx2, cy2, fill="red", width=3)
            self.canvas.create_oval(cx1 - 3, cy1 - 3, cx1 + 3, cy1 + 3, fill="red")
            self.canvas.create_oval(cx2 - 3, cy2 - 3, cx2 + 3, cy2 + 3, fill="red")

        self.start_x = self.start_y = None

    def on_right_click(self, event):
        if self.mode.get() != "draw":
            return

        if len(self.drawing_points) < 3:
            messagebox.showwarning("Мало вершин",
                                   "Для многоугольника нужно минимум 3 вершины.")
            return

        if not is_convex(self.drawing_points):
            messagebox.showerror("Невыпуклый многоугольник",
                                 "Построенная фигура не является выпуклой.\n"
                                 "Попробуйте снова.")
            self.drawing_points = []
            self.last_mouse = None
            self.redraw_canvas()
            return

        self.polygon = self.drawing_points[:]
        self.drawing_points = []
        self.last_mouse = None
        self.mode.set("poly")
        self.redraw_canvas()

    def on_escape(self, event):
        if self.mode.get() == "draw":
            self.drawing_points = []
            self.last_mouse = None
            self.mode.set("poly")
            self.redraw_canvas()


if __name__ == "__main__":
    root = tk.Tk()
    app = ClippingApp(root)
    root.mainloop()