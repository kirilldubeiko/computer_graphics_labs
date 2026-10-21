import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import cv2
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def to_gray(rgb):
    if rgb.ndim == 2:
        return rgb
    g = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    return np.clip(np.round(g), 0, 255).astype(np.uint8)


def histogram(gray):
    return np.bincount(gray.ravel(), minlength=256)


def linear_contrast(img):
    f = img.astype(np.float64)
    fmin, fmax = f.min(), f.max()
    if fmax == fmin:
        return img.copy()
    return np.round((f - fmin) * 255.0 / (fmax - fmin)).astype(np.uint8)


def equalize_gray(gray):
    h = histogram(gray).astype(np.float64)
    cdf = np.cumsum(h / h.sum())
    lut = np.round(255.0 * cdf).astype(np.uint8)
    return lut[gray]


def equalize_rgb(rgb):
    return np.dstack([equalize_gray(rgb[..., c]) for c in range(3)])


def equalize_hsv(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hsv[..., 2] = equalize_gray(hsv[..., 2])
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)


def filter2d(gray, kernel):
    f = gray.astype(np.float64)
    k = np.asarray(kernel, dtype=np.float64)
    kh, kw = k.shape
    p = np.pad(f, ((kh // 2,) * 2, (kw // 2,) * 2), mode="edge")
    H, W = f.shape
    out = np.zeros_like(f)
    for i in range(kh):
        for j in range(kw):
            out += k[i, j] * p[i:i + H, j:j + W]
    return out


def binarize_by_max(resp, ratio):
    m = np.abs(resp).max()
    if m <= 0:
        return np.zeros(resp.shape, np.uint8)
    T = ratio * m
    return (np.abs(resp) > T).astype(np.uint8) * 255


POINT = [[-1, -1, -1],
         [-1,  8, -1],
         [-1, -1, -1]]

LINES = [
    [[-1, -1, -1], [ 2,  2,  2], [-1, -1, -1]],
    [[-1,  2, -1], [-1,  2, -1], [-1,  2, -1]],
    [[-1, -1,  2], [-1,  2, -1], [ 2, -1, -1]],
    [[ 2, -1, -1], [-1,  2, -1], [-1, -1,  2]],
]

EDGES = {
    "Собель": (
        [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
        [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
    ),
    "Превитт": (
        [[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]],
        [[-1, -1, -1], [0, 0, 0], [1, 1, 1]],
    ),
}


def detect_points(gray, ratio):
    return binarize_by_max(filter2d(gray, POINT), ratio)


def detect_lines(gray, ratio):
    responses = np.stack([filter2d(gray, k) for k in LINES])
    r = np.max(np.abs(responses), axis=0)
    m = r.max()
    if m <= 0:
        return np.zeros(gray.shape, np.uint8)
    T = ratio * m
    return (r > T).astype(np.uint8) * 255


def detect_edges(gray, ratio, operator="Собель"):
    kx, ky = EDGES[operator]
    gx = filter2d(gray, kx)
    gy = filter2d(gray, ky)
    g = np.hypot(gx, gy)
    return binarize_by_max(g, ratio)


SEG = {
    "Точки": detect_points,
    "Линии": detect_lines,
    "Перепады яркости": detect_edges,
}

MODE_GRAY  = "Полутон: линейное контрастирование и эквализация"
MODE_COLOR = "Цвет: эквализация RGB и HSV"


def plot_hist(ax, img):
    if img.ndim == 2:
        ax.bar(range(256), histogram(img), width=1.0, color="gray")
    else:
        for c, col in enumerate("rgb"):
            ax.plot(histogram(img[..., c]), color=col, lw=0.8)
    ax.set_xlim(0, 255)
    ax.tick_params(labelsize=7)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная 2, вариант 4 сегментация: точки, линии, перепады")
        self.geometry("1300x800")
        self.img = None

        top = ttk.Frame(self)
        top.pack(fill="x", padx=6, pady=4)
        ttk.Button(top, text="Открыть изображение…",
                   command=self.open_image).pack(side="left")
        self.info = ttk.Label(top, text="Файл не выбран")
        self.info.pack(side="left", padx=10)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.left1, self.fig1, self.cv1 = self.make_tab(nb, "Гистограмма и контраст")
        ttk.Label(self.left1, text="Режим:").pack(anchor="w")
        self.mode = tk.StringVar(value=MODE_GRAY)
        cb1 = ttk.Combobox(self.left1, textvariable=self.mode,
                           state="readonly", width=42,
                           values=[MODE_GRAY, MODE_COLOR])
        cb1.pack(anchor="w")
        cb1.bind("<<ComboboxSelected>>", lambda e: self.run1())

        self.left2, self.fig2, self.cv2 = self.make_tab(nb, "Сегментация (вариант 4)")

        ttk.Label(self.left2, text="Метод обнаружения:").pack(anchor="w")
        self.seg = tk.StringVar(value="Точки")
        cb2 = ttk.Combobox(self.left2, textvariable=self.seg,
                           state="readonly", width=30,
                           values=list(SEG))
        cb2.pack(anchor="w", pady=(0, 8))
        cb2.bind("<<ComboboxSelected>>", lambda e: self.run2())

        ttk.Label(self.left2, text="Оператор для перепадов:").pack(anchor="w")
        self.op = tk.StringVar(value="Собель")
        cb3 = ttk.Combobox(self.left2, textvariable=self.op,
                           state="readonly", width=30,
                           values=list(EDGES))
        cb3.pack(anchor="w", pady=(0, 8))
        cb3.bind("<<ComboboxSelected>>", lambda e: self.run2())

        ttk.Label(self.left2, text="Порог T (доля от max|R|):").pack(anchor="w")
        self.ratio = tk.DoubleVar(value=0.5)
        sc = tk.Scale(self.left2, from_=0.05, to=1.0, resolution=0.05,
                      orient="horizontal", length=240, variable=self.ratio)
        sc.pack(anchor="w")
        sc.bind("<ButtonRelease-1>", lambda e: self.run2())

    def make_tab(self, nb, title):
        tab = ttk.Frame(nb)
        nb.add(tab, text=title)
        left = ttk.Frame(tab, padding=8)
        left.pack(side="left", fill="y")
        fig = Figure(figsize=(9, 6), dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.get_tk_widget().pack(side="right", fill="both", expand=True)
        return left, fig, canvas

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if not path:
            return
        bgr = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if bgr is None:
            messagebox.showerror("Ошибка", "Не удалось прочитать изображение")
            return
        self.img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        self.info.config(text=path)
        self.run1()
        self.run2()

    @staticmethod
    def show(ax, im, title):
        if im.ndim == 2:
            ax.imshow(im, cmap="gray", vmin=0, vmax=255)
        else:
            ax.imshow(im)
        ax.set_title(title, fontsize=9)
        ax.axis("off")

    def run1(self):
        if self.img is None:
            return
        if self.mode.get() == MODE_GRAY:
            g = to_gray(self.img)
            res = [("Исходное", g),
                   ("Линейное контрастирование", linear_contrast(g)),
                   ("Эквализация гистограммы", equalize_gray(g))]
        else:
            res = [("Исходное", self.img),
                   ("Эквализация RGB", equalize_rgb(self.img)),
                   ("Эквализация HSV (V)", equalize_hsv(self.img))]
        self.fig1.clear()
        axes = self.fig1.subplots(2, len(res), squeeze=False)
        for k, (title, im) in enumerate(res):
            self.show(axes[0][k], im, title)
            plot_hist(axes[1][k], im)
        self.fig1.tight_layout()
        self.cv1.draw()

    def run2(self):
        if self.img is None:
            return
        g = to_gray(self.img)
        method = self.seg.get()
        ratio = float(self.ratio.get())

        if method == "Перепады яркости":
            res = detect_edges(g, ratio, operator=self.op.get())
            subtitle = f"Перепады яркости (оператор {self.op.get()})"
        else:
            res = SEG[method](g, ratio)
            subtitle = method

        self.fig2.clear()
        a, b = self.fig2.subplots(1, 2)
        self.show(a, g, "Исходное (полутон)")
        self.show(b, res, subtitle)
        self.fig2.tight_layout()
        self.cv2.draw()


if __name__ == "__main__":
    App().mainloop()