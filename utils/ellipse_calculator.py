import numpy as np

def compute_ellipse(rls1, rls2, c):
    """
    Расчёт точек эллипса по двум РЛС станциям
    
    :param rls1: Первый РЛС объект
    :param rls2: Второй РЛС объект
    :param c: Константа, характеризующая размер эллипса
    :return: Кортеж из x и у координат расчитанного эллипса
    """
    # Расчет центра эллипса
    h = (rls1.x + rls2.x) / 2
    k = (rls1.y + rls2.y) / 2

    # Расчет расстояния между фокусами
    dx = rls2.x - rls1.x
    dy = rls2.y - rls1.y
    distance = np.hypot(dx, dy)

    if distance == 0:
        print("Фокусы совпадают. Эллипс не может быть построен.")
        return [], []

    # Расчет угла наклона главной оси эллипса
    phi = np.arctan2(dy, dx)

    # Полуоси эллипса
    a = c / 2
    if a < distance / 2:
        print(f"Невозможно построить эллипс с c={c}, так как a={a} < distance/2={distance/2}")
        return [], []
    
    b = np.sqrt(a**2 - (distance / 2)**2)

    # Параметризация эллипса
    theta = np.linspace(0, 2 * np.pi, 500)
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    ellipse_x = h + a * np.cos(theta) * cos_phi - b * np.sin(theta) * sin_phi
    ellipse_y = k + a * np.cos(theta) * sin_phi + b * np.sin(theta) * cos_phi
    
    return ellipse_x, ellipse_y