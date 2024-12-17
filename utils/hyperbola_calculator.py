import numpy as np

def compute_hyperbola(rls1, rls2, c):
    """
    Расчёт точек гипербол по двум РЛС станциям
    
    :param rls1: Первый РЛС объект
    :param rls2: Второй РЛС объект
    :param c: Константа, характеризующая форму гипербол
    :return: Кортеж из x и у координат расчитанных гипербол
    """
    if c == 0:
        print("c=0.0, гипербола не может быть построена.")
        return [], [], [], []

    # Расчет центра гиперболы
    h = (rls1.x + rls2.x) / 2
    k = (rls1.y + rls2.y) / 2

    # Расчет расстояния между фокусами
    dx = rls2.x - rls1.x
    dy = rls2.y - rls1.y
    distance = np.hypot(dx, dy)

    if distance == 0:
        print("Фокусы совпадают. Гипербола не может быть построена.")
        return [], [], [], []

    # Угол наклона главной оси гиперболы
    phi = np.arctan2(dy, dx)

    # Параметры гиперболы
    a = abs(c) / 2
    c_focus = distance / 2

    if a >= c_focus:
        print(f"Невозможно построить гиперболу с c={c}, так как a={a} >= c_focus={c_focus}")
        return [], [], [], []

    # Вычисление b по формуле c_focus^2 = a^2 + b^2
    b = np.sqrt(c_focus**2 - a**2)

    # Параметризация гиперболы
    t = np.linspace(-6, 6, 2000)
    hyperbola_x = a * np.cosh(t)
    hyperbola_y = b * np.sinh(t)

    # Если c < 0, отзеркаливаем гиперболу относительно центра
    if c < 0:
        hyperbola_x = -hyperbola_x

    # Поворот гиперболы на угол phi и перенос в центр (h, k)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    rotated_x1 = h + hyperbola_x * cos_phi - hyperbola_y * sin_phi
    rotated_y1 = k + hyperbola_x * sin_phi + hyperbola_y * cos_phi

    rotated_x2 = h - hyperbola_x * cos_phi - hyperbola_y * sin_phi
    rotated_y2 = k - hyperbola_x * sin_phi + hyperbola_y * cos_phi

    return rotated_x1, rotated_y1, rotated_x2, rotated_y2