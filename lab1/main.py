import tkinter as tk
from tkinter import colorchooser
from convertions import (
    rgb_to_cmyk, cmyk_to_rgb,
    rgb_to_hsv, hsv_to_rgb,
)


class ColorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ЛР №1 CMYK  RGB  HSV")
        self.geometry("760x580")
        self.resizable(False, False)

        self.r, self.g, self.b = 142.0, 100.0, 200.0
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
                             showvalue=False,
                             command=lambda v, key=k: self.on_slider(key))
            scale.pack(side="left", fill="x", expand=True, padx=4)

            entry = tk.Entry(row, textvariable=var, width=7, justify="center")
            entry.pack(side="left")
            entry.bind("<Return>",   lambda e, key=k: self.on_entry(key))
            entry.bind("<FocusOut>", lambda e, key=k: self.on_entry(key))

            self.scales[k] = scale

    def on_slider(self, key):
        if self.updating:
            return
        self.apply_change(key, int(round(float(self.scales[key].get()))))

    def on_entry(self, key):
        if self.updating:
            return
        try:
            val = int(round(float(self.vars[key].get().replace(",", "."))))
        except ValueError:
            self.update_all()
            return

        s = self.scales[key]
        lo = int(float(s.cget("from")))
        hi = int(float(s.cget("to")))
        val = max(lo, min(hi, val))

        self.apply_change(key, val)


    def current(self, key):
        vals = dict(zip("RGB", (self.r, self.g, self.b)))
        vals.update(zip("CMYK", self.cmyk))
        vals.update(zip("HSV", self.hsv))
        return vals[key]

    def sync_from_rgb(self):
        c, m, y, k = rgb_to_cmyk(self.r, self.g, self.b)
        if k >= 100:
            c, m, y = self.cmyk[:3]
        self.cmyk = [c, m, y, k]

        h, s, v = rgb_to_hsv(self.r, self.g, self.b)
        if s == 0 or v == 0:
            h = self.hsv[0]
        if v == 0:
            s = self.hsv[1]
        self.hsv = [h, s, v]

    def apply_change(self, key, value):
        if int(round(self.current(key))) == value:
            self.update_all()
            return

        if key in "RGB":
            rgb = [self.r, self.g, self.b]
            rgb["RGB".index(key)] = float(value)
            self.r, self.g, self.b = rgb
            self.sync_from_rgb()

        elif key in "CMYK":
            cmyk = list(self.cmyk)
            cmyk["CMYK".index(key)] = float(value)
            self.r, self.g, self.b = cmyk_to_rgb(*cmyk)
            self.sync_from_rgb()
            self.cmyk = cmyk

        else:
            hsv = list(self.hsv)
            hsv["HSV".index(key)] = float(value)
            self.r, self.g, self.b = hsv_to_rgb(*hsv)
            self.sync_from_rgb()
            self.hsv = hsv

        self.update_all()

    def update_all(self):
        self.updating = True
        try:
            values = {
                "R": self.r, "G": self.g, "B": self.b,
                "C": self.cmyk[0], "M": self.cmyk[1],
                "Y": self.cmyk[2], "K": self.cmyk[3],
                "H": self.hsv[0], "S": self.hsv[1], "V": self.hsv[2],
            }

            for key, val in values.items():
                new_val = int(round(val))
                if int(float(self.scales[key].get())) != new_val:
                    self.scales[key].set(new_val)
                new_str = str(new_val)
                if self.vars[key].get() != new_str:
                    self.vars[key].set(new_str)

            ri, gi, bi = (max(0, min(255, int(round(x))))
                          for x in (self.r, self.g, self.b))
            hex_color = "#{:02x}{:02x}{:02x}".format(ri, gi, bi)
            self.preview.configure(bg=hex_color)
            self.hex_label.configure(text=hex_color.upper())
        finally:
            self.updating = False

    def open_palette(self):
        ri, gi, bi = (int(round(x)) for x in (self.r, self.g, self.b))
        rgb, _ = colorchooser.askcolor(
            color="#{:02x}{:02x}{:02x}".format(ri, gi, bi)
        )
        if rgb:
            self.r, self.g, self.b = (float(round(x)) for x in rgb)
            self.sync_from_rgb()
            self.update_all()


if __name__ == "__main__":
    ColorApp().mainloop()