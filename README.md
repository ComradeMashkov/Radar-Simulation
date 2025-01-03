## Radar-Simulation

### Инструкция по использованию

**Моделирование двух угломерно-дальномерных систем (РЛС)**  

---

## Описание  
Данное приложение предназначено для моделирования двух угломерно-дальномерных систем (РЛС), включая:  
- Визуализацию диаграмм направленности антенн (ДНА)  
- Построение эллипсов и гипербол для учета погрешностей  
- Вычисление площадей пересечения областей покрытия  

### Инструкция по запуску

Создаём виртуальное окружение:
```shell
python -m venv .venv
.venv\Scripts\activate
```

Устанавливаем библиотеки:
```shell
python -m pip install -r requirements.txt
```

Запускаем:
```shell
python main.py
```

### Пояснения для документации

Площади пересечения областей моделируются с использованием библиотек `Shapely` и `numpy`. На примере рассмотрим два основных типа областей:  
- **Диаграммы направленности антенн (ДНА)**  
- **Эллипсы и гиперболы с учетом погрешностей**  

---

#### 1. Построение областей действия антенн (ДНА)

1. **Задаются параметры РЛС**:
- **X, Y** – координаты антенны.  
- **R** – радиус действия антенны.  
- **A** – угол направления ДНА.  
- **W** – ширина диаграммы.  

2. **Формируется диапазон углов** для построения ДНА:  
```python
angles_deg = np.linspace(-360, 360, 3600)
theta = np.deg2rad(angles_deg)
```


markdown
Копировать код
3. **Вычисляется затухание на границах диаграммы**:  
Формула затухания для построения диаграммы направленности антенны:  

\[
L(\theta) = e^{-\frac{\ln(2) \cdot (\theta - A)^2}{(W / 2)^2}}
\]  

Где:  
- \( \ln(2) \) – логарифмическое значение для нормализации.  
- \( \theta \) – текущий угол в радианах.  
- \( A \) – угол направления ДНА.  
- \( W \) – ширина диаграммы.  

4. **Построение полигонов ДНА**:  
Координаты областей рассчитываются на основе углов и радиуса действия антенны:  
```python
x_fill = L(angles) * max_range * np.cos(theta) + position_x
y_fill = L(angles) * max_range * np.sin(theta) + position_y
```

Далее создается полигон с использованием `Shapely`:
```python
poly1 = Polygon(np.column_stack((x_fill, y_fill)))
```

#### 2. Построение эллипсов и гипербол

1. **Эллипсы**  
Эллипсы строятся на основе суммы радиусов действия двух антенн. Формула для параметра \( c \):  

\( c = R_1 + R_2 \)  

Для построения эллипса вызывается функция `compute_ellipse`, которая возвращает координаты эллипса: 

```python
(x, y) = compute_ellipse(rls1, rls2, c)
```

- **Эллипс 1**: строится для идеального случая без учета погрешностей.  
- **Эллипс 2**: строится с учетом погрешностей, добавленных к радиусам \( R_1 \) и \( R_2 \):

\( c = (R_1 + E_{\text{ellipse}}) + (R_2 + E_{\text{ellipse}}) \)

2. **Гиперболы**  
Гипербола моделируется как разность радиусов действия двух антенн. Формула для параметра \( c_h \):  

\( c_h = R_2 - R_1 \)  

Для учета погрешностей строятся две дополнительные гиперболы:  
- **Гипербола с положительной погрешностью**: \( c_h + 2 \cdot E_{\text{hyperbola}} \)  
- **Гипербола с отрицательной погрешностью**: \( c_h - 2 \cdot E_{\text{hyperbola}} \)  

Координаты гиперболы вычисляются функцией `compute_hyperbola`, которая возвращает две ветви гиперболы:  

```python
hyperbola_x1, hyperbola_y1, hyperbola_x2, hyperbola_y2 = compute_hyperbola(rls1, rls2, c_h)
```

- **Гипербола 1**: \( R_2 - R_1 = c_h \)  
- **Гипербола 2**: \( R_1 - R_2 = c_h \)  

Полученные гиперболы с учетом погрешностей отображаются на графике.

#### 3. Вычисление пересечений 

1. **Создание полигонов**  
Все области (диаграммы направленности антенн, эллипсы и гиперболы) конвертируются в объекты `Polygon` из библиотеки `Shapely`.  
- Диаграммы направленности антенн (ДНА) формируются на основе вычисленных координат:  

```python
poly1 = Polygon(coords_1)  
poly2 = Polygon(coords_2)
```

- Эллипсы и гиперболы также преобразуются в полигональные области.

2. **Пересечение областей**  
Для поиска общей области между различными зонами используется метод `.intersection`. Этот метод находит геометрическое пересечение между полигонами:  

```python
intersection = poly1.intersection(poly2)  
```

**Пример:**  
- Пересечение двух ДНА: \( DНА_1 \cap DНА_2 \)  
- Пересечение ДНА с эллипсом: \( DНА_1 \cap \text{Эллипс} \)  
- Общее пересечение всех областей: \( DНА_1 \cap DНА_2 \cap \text{Эллипс} \cap \text{Гипербола} \).

3. **Вычисление разностей для учета погрешностей**  
Для учета погрешностей строятся внешние и внутренние границы областей. Метод `.difference` позволяет определить разницу между внешней и внутренней границей:  

```python
ring = outer_polygon.difference(inner_polygon)
```

- Например, для эллипса разница между большим эллипсом (с погрешностью) и идеальным эллипсом формирует "кольцо" погрешности.  
- Аналогично строятся зоны погрешностей для гипербол.

4. **Объединение пересечений**  
Конечная область пересечения формируется путем объединения всех пересечений и учета погрешностей:  

```python
final_intersection = poly1.intersection(ellipse_difference).intersection(hyperbola_difference)
```

В результате получается область, которая учитывает как пересечение зон покрытия, так и погрешности измерений.

5. **Проверка и обработка результата**  
   Для проверки пересечений используется метод `.is_empty`:  
   - Если пересечение не пустое, вычисляется площадь.  
   - Если пересечение пустое, площадь равна нулю.  

6. **Вывод результата**  
Площадь пересечения вычисляется с помощью метода `.area` и выводится на экран:  

```python
area = final_intersection.area
``` 

Результат отображается в панели управления:  
**Площадь: X.XX м²**  

На графике пересекающиеся области отображаются в виде зеленых полигонов для наглядности. 

---

### Метод `.area`

Метод `.area` в библиотеке **Shapely** используется для вычисления площади геометрических объектов, таких как **Polygon** (многоугольник).

#### Принцип работы  

Метод `.area` возвращает числовое значение, равное площади двумерного геометрического объекта в его собственной системе координат.  

- Площадь вычисляется на основе координат всех вершин многоугольника.  
- Метод учитывает как основную границу многоугольника (наружный контур), так и любые **внутренние отверстия** (вложенные полигоны).  

#### Формула для площади многоугольника

Площадь многоугольника, заданного последовательностью вершин \((x_1, y_1), (x_2, y_2), \dots, (x_n, y_n)\), вычисляется по формуле:  

\[
\text{Area} = \frac{1}{2} \left| \sum_{i=1}^{n-1} (x_i \cdot y_{i+1} - x_{i+1} \cdot y_i) \right|
\]  

Где:  
- \( n \) – количество вершин многоугольника.  
- \( (x_i, y_i) \) – координаты \( i \)-й вершины.  
- Координаты вершин перечисляются по часовой или против часовой стрелке.

#### Погрешности вычисления пощади

Погрешность вычисления площади заданного многоугольника исходит из представления чисел с плавающей запятой в ОЗУ компьютера, а также обеспечивается комплексностью геометрического объекта и многочисленными операциями над полигонами.

Примерная погрешность составляет 0.1 у.е.\(^2\)