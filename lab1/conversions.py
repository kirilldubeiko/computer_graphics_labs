def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


def rgb_to_cmyk(r, g, b):
    rp = r / 255.0
    gp = g / 255.0
    bp = b / 255.0

    k = min(1.0 - rp, 1.0 - gp, 1.0 - bp)

    if k >= 1.0:
        return 0.0, 0.0, 0.0, 100.0

    c = (1.0 - rp - k) / (1.0 - k)
    m = (1.0 - gp - k) / (1.0 - k)
    y = (1.0 - bp - k) / (1.0 - k)

    return c * 100.0, m * 100.0, y * 100.0, k * 100.0


def cmyk_to_rgb(c, m, y, k):
    c /= 100.0
    m /= 100.0
    y /= 100.0
    k /= 100.0

    r = 255.0 * (1.0 - c) * (1.0 - k)
    g = 255.0 * (1.0 - m) * (1.0 - k)
    b = 255.0 * (1.0 - y) * (1.0 - k)

    return clamp(r, 0.0, 255.0), clamp(g, 0.0, 255.0), clamp(b, 0.0, 255.0)


def rgb_to_hsv(r, g, b):
    rp = r / 255.0
    gp = g / 255.0
    bp = b / 255.0

    M = max(rp, gp, bp)
    m = min(rp, gp, bp)
    delta = M - m

    v = M
    s = 0.0 if M == 0.0 else delta / M

    if delta == 0.0:
        h = 0.0
    elif M == rp:
        h = 60.0 * (((gp - bp) / delta) % 6)
    elif M == gp:
        h = 60.0 * ((bp - rp) / delta + 2.0)
    else:
        h = 60.0 * ((rp - gp) / delta + 4.0)

    return h, s * 100.0, v * 100.0

def hsv_to_rgb(h, s, v):
    s = s / 100.0
    v = v / 100.0
    h = h % 360
    if s == 0:
        r = g = b = v
        return r * 255, g * 255, b * 255

    if h == 360:
        h = 0
    h = h / 60.0

    I = int(h)
    F = h - I

    M = v * (1 - s)
    N = v * (1 - s * F)
    K = v * (1 - s * (1 - F))

    if I == 0:
        R, G, B = v, K, M
    elif I == 1:
        R, G, B = N, v, M
    elif I == 2:
        R, G, B = M, v, K
    elif I == 3:
        R, G, B = M, N, v
    elif I == 4:
        R, G, B = K, M, v
    elif I == 5:
        R, G, B = v, M, N

    return R * 255, G * 255, B * 255