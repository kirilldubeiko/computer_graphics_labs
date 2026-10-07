import tkinter as tk
from tkinter import colorchooser
from conversions import (
    rgb_to_cmyk, cmyk_to_rgb,
    rgb_to_hsv, hsv_to_rgb,
)


class ColorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ЛР №1 CMYK  RGB  HSV")
        self.geometry("760x580")
        self.resizable(False, False)

        self.r, self.g, self.b = 142, 100, 200
        self.cmyk = list(rgb_to_cmyk(self.r, self.g, self.b))
        self.hsv = list(rgb_to_hsv(self.r, self.g, self.b))
        self.updating = False

        self.scales = {}
        self.vars = {}

        self.build_ui()
        self.update_all()

    def build_ui(self):
        cf = tk.LabelFrame(self, text="Цвет", padx=6, pady=6)
        cf.pack(fill="x", padx=10, pady=6)

        self.preview = tk.Canvas(cf, height=80,
                                 highlightthickness=1,
                                 highlightbackground="#000000")
        self.preview.pack(fill="x")

        self.hex_label = tk.Label(cf, text="#000000")
        self.hex_label.pack(side="right", pady=4)

        tk.Button(cf, text="Выбрать цвет из палитры",
                  command=self.open_palette).pack(side="left", pady=4)

        self.build_panel("RGB", ["R", "G", "B"],
                         {"R": (0, 255), "G": (0, 255), "B": (0, 255)})
        self.build_panel("CMYK", ["C", "M", "Y", "K"],
                         {"C": (0, 100), "M": (0, 100), "Y": (0, 100), "K": (0, 100)})
        self.build_panel("HSV", ["H", "S", "V"],
                         {"H": (0, 360), "S": (0, 100), "V": (0, 100)})

    def build_panel(self, title, keys, ranges):
        frame = tk.LabelFrame(self, text=title, padx=6, pady=6)
        frame.pack(fill="x", padx=10, pady=6)

        for k in keys:
            lo, hi = ranges[k]
            row = tk.Frame(frame)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=k, width=3).pack(side="left")

            var = tk.StringVar()
            self.vars[k] = var

            scale = tk.Scale(row, from_=lo, to=hi,
                             orient="horizontal", resolution=1,
                             showvalue=False)
            scale.pack(side="left", fill="x", expand=True, padx=4)
            scale.bind("<B1-Motion>", lambda e, key=k: self.on_slider(key))
            scale.bind("<ButtonRelease-1>", lambda e, key=k: self.on_slider(key))

            entry = tk.Entry(row, textvariable=var, width=7, justify="center")
            entry.pack(side="left")
            entry.bind("<Return>",   lambda e, key=k: self.on_entry(key))
            entry.bind("<FocusOut>", lambda e, key=k: self.on_entry(key))

            self.scales[k] = scale

    def on_slider(self, key):
        if self.updating:
            return
        self.apply_change(key, int(self.scales[key].get()))

    def on_entry(self, key):
        if self.updating:
            return
        try:
            val = int(round(float(self.vars[key].get().replace(",", "."))))
        except ValueError:
            self.update_all()
            return

        s = self.scales[key]
        lo = int(s.cget("from"))
        hi = int(s.cget("to"))
        if val < lo:
            val = lo
        elif val > hi:
            val = hi

        self.apply_change(key, val)

    def apply_change(self, key, value):
        if key in ("R", "G", "B"):
            rgb = [self.r, self.g, self.b]
            rgb["RGB".index(key)] = value
            self.r, self.g, self.b = [int(round(x)) for x in rgb]
            self.cmyk = list(rgb_to_cmyk(self.r, self.g, self.b))
            self.hsv = list(rgb_to_hsv(self.r, self.g, self.b))

        elif key in ("C", "M", "Y", "K"):
            cmyk = list(self.cmyk)
            cmyk["CMYK".index(key)] = value
            self.cmyk = cmyk
            r, g, b = cmyk_to_rgb(*cmyk)
            self.r, self.g, self.b = int(round(r)), int(round(g)), int(round(b))
            self.hsv = list(rgb_to_hsv(self.r, self.g, self.b))

        elif key in ("H", "S", "V"):
            hsv = list(self.hsv)
            hsv["HSV".index(key)] = value
            self.hsv = hsv
            r, g, b = hsv_to_rgb(*hsv)
            self.r, self.g, self.b = int(round(r)), int(round(g)), int(round(b))
            self.cmyk = list(rgb_to_cmyk(self.r, self.g, self.b))

        self.update_all()

    def update_all(self):
        self.updating = True
        try:
            r, g, b = self.r, self.g, self.b
            c, m, y, k = self.cmyk
            h, s, v = self.hsv

            values = {
                "R": r, "G": g, "B": b,
                "C": c, "M": m, "Y": y, "K": k,
                "H": h, "S": s, "V": v,
            }

            for key, val in values.items():
                new_val = int(round(val))

                if int(self.scales[key].get()) != new_val:
                    self.scales[key].set(new_val)

                new_str = str(new_val)
                if self.vars[key].get() != new_str:
                    self.vars[key].set(new_str)

            hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
            self.preview.configure(bg=hex_color)
            self.hex_label.configure(text=hex_color.upper())
        finally:
            self.updating = False

    def open_palette(self):
        rgb, _ = colorchooser.askcolor(
            color="#{:02x}{:02x}{:02x}".format(int(self.r), int(self.g), int(self.b))
        )
        if rgb:
            self.r = int(round(rgb[0]))
            self.g = int(round(rgb[1]))
            self.b = int(round(rgb[2]))
            self.cmyk = list(rgb_to_cmyk(self.r, self.g, self.b))
            self.hsv = list(rgb_to_hsv(self.r, self.g, self.b))
            self.update_all()


ColorApp().mainloop()