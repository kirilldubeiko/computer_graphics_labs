import tkinter as tk
from tkinter import messagebox, filedialog
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


def compute_outcode(x, y, x_min, x_max, y_min, y_max):
    code = 0
    if y > y_max: code |= 8
    if y < y_min: code |= 4
    if x > x_max: code |= 2
    if x < x_min: code |= 1
    return code


def cohen_sutherland(x1, y1, x2, y2, x_min, x_max, y_min, y_max):
    outcode1 = compute_outcode(x1, y1, x_min, x_max, y_min, y_max)
    outcode2 = compute_outcode(x2, y2, x_min, x_max, y_min, y_max)
    accept = False
    if x1 == x2:
        k = None
        b = None
    else:
        k = (y2 - y1) / (x2 - x1)
        b = y1 - k * x1
    while True:
        if (outcode1 == 0) and (outcode2 == 0):
            accept = True
            break
        elif (outcode1 & outcode2) != 0:
            break
        else:
            oc = outcode1 if outcode1 != 0 else outcode2
            x = y = 0
            if oc & 8:
                y = y_max
                x = x1 if k is None else (y - b) / k
            elif oc & 4:
                y = y_min
                x = x1 if k is None else (y - b) / k
            elif oc & 2:
                x = x_max
                y = y1 if k is None else k * x + b
            elif oc & 1:
                x = x_min
                y = y1 if k is None else k * x + b
            if oc == outcode1:
                x1, y1 = x, y
                outcode1 = compute_outcode(x1, y1, x_min, x_max, y_min, y_max)
            else:
                x2, y2 = x, y
                outcode2 = compute_outcode(x2, y2, x_min, x_max, y_min, y_max)
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
        self.root.title("Лабораторная работа 4 - Отсечение отрезков")

        self.x_min, self.y_min = X_MIN, Y_MIN
        self.x_max, self.y_max = X_MAX, Y_MAX
        self.polygon = DEFAULT_POLYGON[:]
        self.segments = []

        ctrl = tk.Frame(root)
        ctrl.pack(pady=5)

        self.mode = tk.StringVar(value="rect")

        tk.Radiobutton(ctrl, text="Прямоугольник (Сазерленд-Коэн)",
                       variable=self.mode, value="rect",
                       command=self.redraw_canvas).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(ctrl, text="Многоугольник (Кирус-Бек)",
                       variable=self.mode, value="poly",
                       command=self.redraw_canvas).pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl, text="Загрузить из файла", bg="#d0e8ff",
                  command=self.load_from_file).pack(side=tk.LEFT, padx=10)
        tk.Button(ctrl, text="Очистить",
                  command=self.clear_canvas).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.try_load_default_file()

    def try_load_default_file(self):
        try:
            with open("input.txt", "r", encoding="utf-8") as f:
                self.parse_file_lines(f.readlines())
        except FileNotFoundError:
            self.redraw_canvas()

    def load_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл с исходными данными",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.parse_file_lines(f.readlines())
            messagebox.showinfo("Успех", f"Загружено отрезков: {len(self.segments)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{e}")

    def parse_file_lines(self, lines):
        clean_lines = [line.strip() for line in lines if line.strip()]
        if not clean_lines:
            return

        n = int(clean_lines[0])
        loaded_segments = []

        idx = 1
        for i in range(n):
            if idx < len(clean_lines):
                parts = list(map(float, clean_lines[idx].split()))
                if len(parts) == 4:
                    loaded_segments.append((parts[0], parts[1], parts[2], parts[3]))
                idx += 1

        if idx < len(clean_lines):
            window_coords = list(map(float, clean_lines[idx].split()))
            if len(window_coords) == 4:
                self.x_min, self.y_min, self.x_max, self.y_max = window_coords
            idx += 1

        if idx < len(clean_lines):
            try:
                m = int(clean_lines[idx])
                idx += 1
                loaded_polygon = []
                for i in range(m):
                    if idx < len(clean_lines):
                        p_parts = list(map(float, clean_lines[idx].split()))
                        if len(p_parts) == 2:
                            loaded_polygon.append((p_parts[0], p_parts[1]))
                        idx += 1
                if len(loaded_polygon) >= 3 and is_convex(loaded_polygon):
                    self.polygon = loaded_polygon
            except ValueError:
                pass

        self.segments = loaded_segments
        self.redraw_canvas()

    def clear_canvas(self):
        self.segments = []
        self.redraw_canvas()

    def draw_coordinate_system(self):
        self.canvas.create_line(50, 550, 750, 550, arrow=tk.LAST, fill="#666666", width=1.5)
        self.canvas.create_text(760, 550, text="X", font=("Arial", 10, "bold"), fill="#666666")

        self.canvas.create_line(50, 550, 50, 50, arrow=tk.LAST, fill="#666666", width=1.5)
        self.canvas.create_text(50, 35, text="Y", font=("Arial", 10, "bold"), fill="#666666")

        for x in range(100, 751, 100):
            self.canvas.create_line(x, 545, x, 555, fill="#666666")
            self.canvas.create_text(x, 565, text=str(x), font=("Arial", 8), fill="#666666")
            self.canvas.create_line(x, 50, x, 550, fill="#f0f0f0", dash=(2, 4))

        for y in range(100, 551, 100):
            val = 600 - y
            self.canvas.create_line(45, y, 55, y, fill="#666666")
            self.canvas.create_text(25, y, text=str(val), font=("Arial", 8), fill="#666666")
            self.canvas.create_line(50, y, 750, y, fill="#f0f0f0", dash=(2, 4))

    def redraw_canvas(self):
        self.canvas.delete("all")

        self.draw_coordinate_system()

        mode = self.mode.get()

        if mode == "rect":
            self.canvas.create_rectangle(self.x_min, self.y_min, self.x_max, self.y_max,
                                         outline="blue", width=2, fill="#f0f8ff")
        elif mode == "poly":
            if len(self.polygon) >= 3:
                self.canvas.create_polygon(self.polygon, outline="blue",
                                           width=2, fill="#f0f8ff")

        if not self.segments:
            self.canvas.create_text(70, 70,
                                    text="Нажмите «Загрузить из файла» для отображения отрезков из input.txt",
                                    anchor="nw", fill="gray", font=("Arial", 11, "bold"))
            return

        for (x1, y1, x2, y2) in self.segments:
            self.canvas.create_line(x1, y1, x2, y2, fill="#aaaaaa", dash=(4, 4), width=2)

            if mode == "rect":
                clipped = cohen_sutherland(x1, y1, x2, y2, self.x_min, self.x_max, self.y_min, self.y_max)
            else:
                clipped = cyrus_beck(x1, y1, x2, y2, self.polygon)

            if clipped:
                cx1, cy1, cx2, cy2 = clipped
                self.canvas.create_line(cx1, cy1, cx2, cy2, fill="red", width=3)
                self.canvas.create_oval(cx1 - 3, cy1 - 3, cx1 + 3, cy1 + 3, fill="red")
                self.canvas.create_oval(cx2 - 3, cy2 - 3, cx2 + 3, cy2 + 3, fill="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = ClippingApp(root)
    root.mainloop()
