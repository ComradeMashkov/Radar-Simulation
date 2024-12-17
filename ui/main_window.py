import json
import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog 
from PyQt5.QtGui import QPolygonF
import pyqtgraph as pg
from shapely.geometry import Polygon, GeometryCollection

from models.rls import RLS
from utils.ellipse_calculator import compute_ellipse
from utils.hyperbola_calculator import compute_hyperbola

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._initialize_rls()
        self._setup_ui()
        self._setup_plot()
        self.update_plot()

    def _setup_ui(self):
        self.setWindowTitle("Моделирование двух угломерно-дальномерных систем (РЛС)")
        self.resize(1800, 800)
        
        # Создаем главную сетку
        main_layout = QtWidgets.QHBoxLayout(self)
        
        # Создаем виджет для графика
        self.plot_widget = self._create_plot_widget()
        main_layout.addWidget(self.plot_widget, 4)

        # Создаем панель управления
        control_layout = self._create_control_panel()
        main_layout.addLayout(control_layout, 1)

    def _initialize_rls(self, option: int = -1):
        # НАЧАЛЬНАЯ КОНФИГУРАЦИЯ СИСТЕМЫ
        if option < 0:
            # Инициализация конфигураций РЛС
            self.rls1 = RLS(x=0, y=-200, R=300, A=135, W=20)
            self.rls2 = RLS(x=500, y=-200, R=550, A=45, W=20)
            
            # Параметры ошибки
            self.E_ellipse = 10
            self.E_hyperbola = 15
            
            # Списки для отслеживания построенных графиков
            self.current_antennas_lobes = list()
            self.current_intersection_items = list()
 
            self.firstRun = True

        elif option == 0:
            # Инициализация конфигураций РЛС
            self.rls1 = RLS(x=0, y=-200, R=300, A=135, W=20)
            self.rls2 = RLS(x=500, y=-200, R=550, A=45, W=20)
            
            # Параметры ошибки
            self.E_ellipse = 10
            self.E_hyperbola = 15
            
            # Списки для отслеживания построенных графиков
            self.current_antennas_lobes = list()
            self.current_intersection_items = list()

        elif option == 1:
            # Инициализация конфигураций РЛС
            self.rls1 = RLS(x=0, y=-200, R=300, A=45, W=20)
            self.rls2 = RLS(x=500, y=-200, R=550, A=135, W=20)
            
            # Списки для отслеживания построенных графиков
            self.current_antennas_lobes = list()
            self.current_intersection_items = list()

        elif option == 2:
            # Инициализация конфигураций РЛС
            self.rls1 = RLS(x=0, y=-200, R=450, A=45, W=20)
            self.rls2 = RLS(x=500, y=-200, R=550, A=135, W=20)
            
            # Списки для отслеживания построенных графиков
            self.current_antennas_lobes = list()
            self.current_intersection_items = list()

    def _setup_plot(self):
        # Добавление элементов на график
        # Точки РЛС
        self.rls1_point = self.plot_widget.plot([], [], pen=None, symbol='o', symbolBrush='blue', symbolSize=10, name="РЛС 1")
        self.rls2_point = self.plot_widget.plot([], [], pen=None, symbol='o', symbolBrush='red', symbolSize=10, name="РЛС 2")

        # Эллипсы
        self.ellipse1 = self.plot_widget.plot([], [], pen=pg.mkPen(color='green', width=2), name="Эллипс 1 (Идеальный)")
        self.ellipse2 = self.plot_widget.plot([], [], pen=pg.mkPen(color='orange', width=2), name="Эллипс 2 (Погрешность)")

        # Гиперболы
        self.hyperbola1_uncertainty = self.plot_widget.plot([], [], pen=pg.mkPen(color='purple', width=2, style=QtCore.Qt.DashDotLine), name="Гипербола 1 (Погрешность)")
        self.hyperbola1_uncertainty_neg = self.plot_widget.plot([], [], pen=pg.mkPen(color='purple', width=2, style=QtCore.Qt.DotLine), name="Гипербола 1 (Погрешность Минус)")

        self.hyperbola2_uncertainty = self.plot_widget.plot([], [], pen=pg.mkPen(color='brown', width=2, style=QtCore.Qt.DashDotLine), name="Гипербола 2 (Погрешность)")
        self.hyperbola2_uncertainty_neg = self.plot_widget.plot([], [], pen=pg.mkPen(color='brown', width=2, style=QtCore.Qt.DotLine), name="Гипербола 2 (Погрешность Минус)")

    def _create_control_panel(self):
        control_layout = QtWidgets.QVBoxLayout()
        control_layout.setAlignment(QtCore.Qt.AlignTop)

        control_layout.addWidget(QtWidgets.QLabel("<b>Конфигурации РЛС</b>"))

        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(["Вариант 1", "Вариант 2", "Вариант 3"])
        self.combo_box.currentIndexChanged.connect(self._handle_combobox_change)

        label_combo = QtWidgets.QLabel("Выберите конфигурацию РЛС")
        h_layout_combo = QtWidgets.QHBoxLayout()
        h_layout_combo.addWidget(label_combo)
        h_layout_combo.addWidget(self.combo_box)
        control_layout.addLayout(h_layout_combo)

        self.dynamic_layout = QtWidgets.QVBoxLayout()
        control_layout.addLayout(self.dynamic_layout)

        control_layout.addStretch()

        self._load_option_1_ui()
        return control_layout
    
    def _clear_layout(self, layout: QtWidgets.QVBoxLayout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                sub_layout = item.layout()

                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
                elif sub_layout:
                    self._clear_layout(sub_layout)
                    sub_layout.deleteLater()

    def _clear_plot_items(self):
        for item in self.current_antennas_lobes:
            self.plot_widget.removeItem(item)
        self.current_antennas_lobes.clear()

        for item in self.current_intersection_items:
            self.plot_widget.removeItem(item)
        self.current_intersection_items.clear()

        # Очищаем статические элементы графика, такие как эллипсы и гиперболы
        self.plot_widget.removeItem(self.ellipse1)
        self.plot_widget.removeItem(self.ellipse2)
        self.plot_widget.removeItem(self.hyperbola1_uncertainty)
        self.plot_widget.removeItem(self.hyperbola1_uncertainty_neg)
        self.plot_widget.removeItem(self.hyperbola2_uncertainty)
        self.plot_widget.removeItem(self.hyperbola2_uncertainty_neg)

        # Очищаем точки РЛС (синие и красные точки)
        self.plot_widget.removeItem(self.rls1_point)
        self.plot_widget.removeItem(self.rls2_point)

        # Сброс элементов графика
        self.ellipse1.clear()
        self.ellipse2.clear()
        self.hyperbola1_uncertainty.clear()
        self.hyperbola1_uncertainty_neg.clear()
        self.hyperbola2_uncertainty.clear()
        self.hyperbola2_uncertainty_neg.clear()
        self.rls1_point.clear()
        self.rls2_point.clear()

    def _reset_input_values(self):
        """Сброс всех вводимых значений в состояние по умолчанию."""
        self.rls1.x, self.rls1.y, self.rls1.R, self.rls1.A, self.rls1.W = 0, -200, 300, 135, 20
        self.rls2.x, self.rls2.y, self.rls2.R, self.rls2.A, self.rls2.W = 500, -200, 550, 45, 20
        self.E_ellipse = 10
        self.E_hyperbola = 15
    
    def _handle_combobox_change(self):
        """Обработка изменений в ComboBox и перезагрузка соответствующего пользовательского интерфейса и графика."""
        # Рекурсивная очистка всех виджетов и макетов в dynamic_layout
        self._clear_layout(self.dynamic_layout)

        self.inputs_rls1 = {}
        self.inputs_rls2 = {}

        self._clear_plot_items()

        self._reset_input_values()

        # Загрузка пользовательского интерфейса и обновление графика в зависимости от выбранного варианта
        if self.combo_box.currentIndex() == 0:
            self._load_option_1_ui()
            self.update_plot()
        elif self.combo_box.currentIndex() == 1:
            self._load_option_2_ui()
            self.update_plot()
        elif self.combo_box.currentIndex() == 2:
            self._load_option_3_ui()
            self.update_plot()

    def _initialize_static_plot_items(self):
        """Переинициализация статических элементов графика, таких как точки, эллипсы и гиперболы."""
        # Повторное добавление точек РЛС (синие и красные точки)
        self.rls1_point = self.plot_widget.plot([], [], pen=None, symbol='o', symbolBrush='blue', symbolSize=10, name="РЛС 1")
        self.rls2_point = self.plot_widget.plot([], [], pen=None, symbol='o', symbolBrush='red', symbolSize=10, name="РЛС 2")

        # Повторное добавление эллипсов
        self.ellipse1 = self.plot_widget.plot([], [], pen=pg.mkPen(color='green', width=2), name="Эллипс 1 (Идеальный)")
        self.ellipse2 = self.plot_widget.plot([], [], pen=pg.mkPen(color='orange', width=2), name="Эллипс 2 (Погрешность)")

        # Повторное добавление гипербол
        self.hyperbola1_uncertainty = self.plot_widget.plot([], [], pen=pg.mkPen(color='purple', width=2, style=QtCore.Qt.DashDotLine), name="Гипербола 1 (Погрешность)")
        self.hyperbola1_uncertainty_neg = self.plot_widget.plot([], [], pen=pg.mkPen(color='purple', width=2, style=QtCore.Qt.DotLine), name="Гипербола 1 (Погрешность Минус)")

        self.hyperbola2_uncertainty = self.plot_widget.plot([], [], pen=pg.mkPen(color='brown', width=2, style=QtCore.Qt.DashDotLine), name="Гипербола 2 (Погрешность)")
        self.hyperbola2_uncertainty_neg = self.plot_widget.plot([], [], pen=pg.mkPen(color='brown', width=2, style=QtCore.Qt.DotLine), name="Гипербола 2 (Погрешность Минус)")

    def _sync_angles(self, value):
        """Синхронизация угла РЛС2 с углом РЛС1."""
        self.angle_spin_rls2.blockSignals(True)
        self.angle_spin_rls2.setValue(180-value)
        self.angle_spin_rls2.blockSignals(False)
        self.update_plot()

    def _toggle_beam_sync(self, state):
        """Включение или отключение синхронизации ДНА."""
        if state == QtCore.Qt.Checked:
            self.angle_spin_rls1.valueChanged.connect(self._sync_angles)
        else:
            self.angle_spin_rls1.valueChanged.disconnect(self._sync_angles)

    def _load_option_1_ui(self):
        """агрузка элементов пользовательского интерфейса для Варианта 1."""
        self._initialize_static_plot_items()

        self.dynamic_layout.addSpacing(20)

        # Параметры для первой РЛС
        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>РЛС 1</b>"))
        self.inputs_rls1 = {}
        for param in ['X', 'Y', 'R', 'A', 'W']:
            label = QtWidgets.QLabel(f"{param}:")
            spin = QtWidgets.QDoubleSpinBox()
            if param in ['X', 'Y']:
                spin.setRange(-1000, 1000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls1, param.lower()))
            elif param == 'R':
                spin.setRange(0, 10000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls1, param))
            elif param == 'A':
                spin.setRange(-180, 180)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls1, param))
            elif param == 'W':
                spin.setRange(1, 45)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls1, param))
            spin.valueChanged.connect(self.update_plot)
            self.inputs_rls1[param] = spin
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(spin)
            self.dynamic_layout.addLayout(h_layout)

        self.dynamic_layout.addSpacing(20)

        # Параметры для второй РЛС
        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>РЛС 2</b>"))
        self.inputs_rls2 = {}
        for param in ['X', 'Y', 'R', 'A', 'W']:
            label = QtWidgets.QLabel(f"{param}:")
            spin = QtWidgets.QDoubleSpinBox()
            if param in ['X', 'Y']:
                spin.setRange(-1000, 1000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls2, param.lower()))
            elif param == 'R':
                spin.setRange(0, 10000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls2, param))
            elif param == 'A':
                spin.setRange(-180, 180)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls2, param))
            elif param == 'W':
                spin.setRange(1, 45)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls2, param))
            spin.valueChanged.connect(self.update_plot)
            self.inputs_rls2[param] = spin
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(spin)
            self.dynamic_layout.addLayout(h_layout)

        self.dynamic_layout.addSpacing(20)

        # Глобальные погрешности
        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>Погрешности</b>"))

        # Погрешность для эллипсов
        label_E_ellipse = QtWidgets.QLabel("E_ellipse:")
        spin_E_ellipse = QtWidgets.QDoubleSpinBox()
        spin_E_ellipse.setRange(1, 1000)
        spin_E_ellipse.setDecimals(2)
        spin_E_ellipse.setValue(self.E_ellipse)
        spin_E_ellipse.valueChanged.connect(self.update_plot)
        self.spin_E_ellipse = spin_E_ellipse
        h_layout_E_ellipse = QtWidgets.QHBoxLayout()
        h_layout_E_ellipse.addWidget(label_E_ellipse)
        h_layout_E_ellipse.addWidget(spin_E_ellipse)
        self.dynamic_layout.addLayout(h_layout_E_ellipse)

        # Погрешность для гипербол
        label_E_hyperbola = QtWidgets.QLabel("E_hyperbola:")
        spin_E_hyperbola = QtWidgets.QDoubleSpinBox()
        spin_E_hyperbola.setRange(1, 110)
        spin_E_hyperbola.setDecimals(2)
        spin_E_hyperbola.setValue(self.E_hyperbola)
        spin_E_hyperbola.valueChanged.connect(self.update_plot)
        self.spin_E_hyperbola = spin_E_hyperbola
        h_layout_E_hyperbola = QtWidgets.QHBoxLayout()
        h_layout_E_hyperbola.addWidget(label_E_hyperbola)
        h_layout_E_hyperbola.addWidget(spin_E_hyperbola)
        self.dynamic_layout.addLayout(h_layout_E_hyperbola)

        self.dynamic_layout.addSpacing(20)
        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>Площади пересечения</b>"))

        self.label_area1 = QtWidgets.QLabel("Площадь 1: 0 м²")
        self.dynamic_layout.addWidget(self.label_area1)

        self.label_area2 = QtWidgets.QLabel("Площадь 2: 0 м²")
        self.dynamic_layout.addWidget(self.label_area2)

        self.dynamic_layout.addSpacing(20)

        # Кнопки сохранения/загрузки конфигурации
        save_button = QtWidgets.QPushButton("Сохранить конфигурацию")
        save_button.clicked.connect(self.save_configuration)
        self.dynamic_layout.addWidget(save_button)

        load_button = QtWidgets.QPushButton("Загрузить конфигурацию")
        load_button.clicked.connect(self.load_configuration)
        self.dynamic_layout.addWidget(load_button)

        self.dynamic_layout.addStretch()
    
    def _load_option_2_ui(self):
        """агрузка элементов пользовательского интерфейса для Варианта 2."""
        self._initialize_rls(1)
        self._initialize_static_plot_items()

        self.dynamic_layout.addSpacing(20)

        self.sync_checkbox = QtWidgets.QCheckBox("Синхронизировать поворот РЛС")
        self.sync_checkbox.stateChanged.connect(self._toggle_beam_sync)
        self.dynamic_layout.addWidget(self.sync_checkbox)

        self.dynamic_layout.addSpacing(10)

        # Параметры для первой РЛС
        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>РЛС 1</b>"))
        self.inputs_rls1 = {}
        for param in ['X', 'Y', 'R', 'A', 'W']:
            label = QtWidgets.QLabel(f"{param}:")
            spin = QtWidgets.QDoubleSpinBox()
            if param in ['X', 'Y']:
                spin.setRange(-1000, 1000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls1, param.lower()))
            elif param == 'R':
                spin.setRange(0, 10000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls1, param))
            elif param == 'A':
                spin.setRange(-180, 180)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls1, param))
                self.angle_spin_rls1 = spin
            elif param == 'W':
                spin.setRange(1, 45)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls1, param))
            spin.valueChanged.connect(self.update_plot)
            self.inputs_rls1[param] = spin
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(spin)
            self.dynamic_layout.addLayout(h_layout)

        self.dynamic_layout.addSpacing(20)

        # Параметры для второй РЛС
        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>РЛС 2</b>"))
        self.inputs_rls2 = {}
        for param in ['X', 'Y', 'R', 'A', 'W']:
            label = QtWidgets.QLabel(f"{param}:")
            spin = QtWidgets.QDoubleSpinBox()
            if param in ['X', 'Y']:
                spin.setRange(-1000, 1000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls2, param.lower()))
            elif param == 'R':
                spin.setRange(0, 10000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls2, param))
            elif param == 'A':
                spin.setRange(-180, 180)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls2, param))
                self.angle_spin_rls2 = spin
            elif param == 'W':
                spin.setRange(1, 45)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls2, param))
            spin.valueChanged.connect(self.update_plot)
            self.inputs_rls2[param] = spin
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(spin)
            self.dynamic_layout.addLayout(h_layout)

        self.dynamic_layout.addSpacing(20)

        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>Площадь пересечения</b>"))

        self.label_area1 = QtWidgets.QLabel("Площадь: 0 м²")
        self.dynamic_layout.addWidget(self.label_area1)

        self.dynamic_layout.addSpacing(20)

        # Кнопки сохранения/загрузки конфигурации
        save_button = QtWidgets.QPushButton("Сохранить конфигурацию")
        save_button.clicked.connect(self.save_configuration)
        self.dynamic_layout.addWidget(save_button)

        load_button = QtWidgets.QPushButton("Загрузить конфигурацию")
        load_button.clicked.connect(self.load_configuration)
        self.dynamic_layout.addWidget(load_button)

        self.dynamic_layout.addStretch()

    def _load_option_3_ui(self):
        """агрузка элементов пользовательского интерфейса для Варианта 3."""
        self._initialize_rls(2)
        self._initialize_static_plot_items()

        self.dynamic_layout.addSpacing(20)

        # Параметры для первой РЛС
        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>РЛС 1</b>"))
        self.inputs_rls1 = {}
        for param in ['X', 'Y', 'R', 'A', 'W']:
            label = QtWidgets.QLabel(f"{param}:")
            spin = QtWidgets.QDoubleSpinBox()
            if param in ['X', 'Y']:
                spin.setRange(-1000, 1000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls1, param.lower()))
            elif param == 'R':
                spin.setRange(0, 10000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls1, param))
            elif param == 'A':
                spin.setRange(-180, 180)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls1, param))
            elif param == 'W':
                spin.setRange(1, 45)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls1, param))
            spin.valueChanged.connect(self.update_plot)
            self.inputs_rls1[param] = spin
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(spin)
            self.dynamic_layout.addLayout(h_layout)

        self.dynamic_layout.addSpacing(20)

        # Параметры для второй РЛС
        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>РЛС 2</b>"))
        self.inputs_rls2 = {}
        for param in ['X', 'Y', 'R', 'A', 'W']:
            label = QtWidgets.QLabel(f"{param}:")
            spin = QtWidgets.QDoubleSpinBox()
            if param in ['X', 'Y']:
                spin.setRange(-1000, 1000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls2, param.lower()))
            elif param == 'R':
                spin.setRange(0, 10000)
                spin.setDecimals(2)
                spin.setValue(getattr(self.rls2, param))
            elif param == 'A':
                spin.setRange(-180, 180)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls2, param))
            elif param == 'W':
                spin.setRange(1, 45)
                spin.setDecimals(0)
                spin.setValue(getattr(self.rls2, param))
            spin.valueChanged.connect(self.update_plot)
            self.inputs_rls2[param] = spin
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(spin)
            self.dynamic_layout.addLayout(h_layout)

        self.dynamic_layout.addSpacing(20)

        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>Дальномерная конфигурация</b>"))

        label_radius_rls1 = QtWidgets.QLabel("Радиус действия РЛС 1:")
        self.spin_radius_rls1 = QtWidgets.QDoubleSpinBox()
        self.spin_radius_rls1.setRange(0, 1000)
        self.spin_radius_rls1.setValue(200)
        self.spin_radius_rls1.valueChanged.connect(self.update_plot)
        h_layout_radius_rls1 = QtWidgets.QHBoxLayout()
        h_layout_radius_rls1.addWidget(label_radius_rls1)
        h_layout_radius_rls1.addWidget(self.spin_radius_rls1)
        self.dynamic_layout.addLayout(h_layout_radius_rls1)

        label_error_rls1 = QtWidgets.QLabel("Погрешность для РЛС 1:")
        self.spin_error_rls1 = QtWidgets.QDoubleSpinBox()
        self.spin_error_rls1.setRange(0, 500)
        self.spin_error_rls1.setValue(10)
        self.spin_error_rls1.valueChanged.connect(self.update_plot)
        h_layout_error_rls1 = QtWidgets.QHBoxLayout()
        h_layout_error_rls1.addWidget(label_error_rls1)
        h_layout_error_rls1.addWidget(self.spin_error_rls1)
        self.dynamic_layout.addLayout(h_layout_error_rls1)

        self.dynamic_layout.addSpacing(10)

        label_radius_rls2 = QtWidgets.QLabel("Радиус действия РЛС 2:")
        self.spin_radius_rls2 = QtWidgets.QDoubleSpinBox()
        self.spin_radius_rls2.setRange(0, 1000)
        self.spin_radius_rls2.setValue(350)
        self.spin_radius_rls2.valueChanged.connect(self.update_plot)
        h_layout_radius_rls2 = QtWidgets.QHBoxLayout()
        h_layout_radius_rls2.addWidget(label_radius_rls2)
        h_layout_radius_rls2.addWidget(self.spin_radius_rls2)
        self.dynamic_layout.addLayout(h_layout_radius_rls2)

        label_error_rls2 = QtWidgets.QLabel("Погрешность для РЛС 2:")
        self.spin_error_rls2 = QtWidgets.QDoubleSpinBox()
        self.spin_error_rls2.setRange(0, 500)
        self.spin_error_rls2.setValue(15)
        self.spin_error_rls2.valueChanged.connect(self.update_plot)
        h_layout_error_rls2 = QtWidgets.QHBoxLayout()
        h_layout_error_rls2.addWidget(label_error_rls2)
        h_layout_error_rls2.addWidget(self.spin_error_rls2)
        self.dynamic_layout.addLayout(h_layout_error_rls2)

        self.dynamic_layout.addSpacing(20)

        self.dynamic_layout.addWidget(QtWidgets.QLabel("<b>Площадь пересечения</b>"))

        self.label_area1 = QtWidgets.QLabel("Площадь: 0 м²")
        self.dynamic_layout.addWidget(self.label_area1)
        
        self.dynamic_layout.addSpacing(20)

        # Кнопки сохранения/загрузки конфигурации
        save_button = QtWidgets.QPushButton("Сохранить конфигурацию")
        save_button.clicked.connect(self.save_configuration)
        self.dynamic_layout.addWidget(save_button)

        load_button = QtWidgets.QPushButton("Загрузить конфигурацию")
        load_button.clicked.connect(self.load_configuration)
        self.dynamic_layout.addWidget(load_button)

        self.dynamic_layout.addStretch()

    def _create_plot_widget(self):
        plot_widget = pg.PlotWidget()
        plot_widget.setAspectLocked(True)
        plot_widget.showGrid(x=True, y=True)
        plot_widget.setBackground('w')
        return plot_widget

    def save_configuration(self):
        """Сохранить текущую конфигурацию в JSON файл."""
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "Save Configuration", "", "JSON Files (*.json);;All Files (*)", options=options)
        if filename:
            config = {
                'current_option': self.combo_box.currentIndex(),
                'rls1': {
                    'x': self.rls1.x,
                    'y': self.rls1.y,
                    'R': self.rls1.R,
                    'A': self.rls1.A,
                    'W': self.rls1.W
                },
                'rls2': {
                    'x': self.rls2.x,
                    'y': self.rls2.y,
                    'R': self.rls2.R,
                    'A': self.rls2.A,
                    'W': self.rls2.W
                },
                'E_ellipse': self.E_ellipse,
                'E_hyperbola': self.E_hyperbola,
                'circle_radius_rls1': self.spin_radius_rls1.value(),
                'circle_error_rls1': self.spin_error_rls1.value(),
                'circle_radius_rls2': self.spin_radius_rls2.value(),
                'circle_error_rls2': self.spin_error_rls2.value()
            }
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                QtWidgets.QMessageBox.information(self, "Успех", "Конфигурация сохранена успешна.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить конфигурацию:\n{e}")

    def load_configuration(self):
        """Load the configuration from a JSON file."""
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Load Configuration", "", "JSON Files (*.json);;All Files (*)", options=options)
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self.combo_box.blockSignals(True)
                self.combo_box.setCurrentIndex(config['current_option'])
                self.combo_box.blockSignals(False)
                self._handle_combobox_change()
                
                # Update RLS1 parameters
                self.inputs_rls1['X'].setValue(config['rls1']['x'])
                self.inputs_rls1['Y'].setValue(config['rls1']['y'])
                self.inputs_rls1['R'].setValue(config['rls1']['R'])
                self.inputs_rls1['A'].setValue(config['rls1']['A'])
                self.inputs_rls1['W'].setValue(config['rls1']['W'])

                # Update RLS2 parameters
                self.inputs_rls2['X'].setValue(config['rls2']['x'])
                self.inputs_rls2['Y'].setValue(config['rls2']['y'])
                self.inputs_rls2['R'].setValue(config['rls2']['R'])
                self.inputs_rls2['A'].setValue(config['rls2']['A'])
                self.inputs_rls2['W'].setValue(config['rls2']['W'])

                # Update global errors
                self.spin_E_ellipse.setValue(config['E_ellipse'])
                self.spin_E_hyperbola.setValue(config['E_hyperbola'])

                # Update circle radii and errors
                self.spin_radius_rls1.setValue(config['circle_radius_rls1'])
                self.spin_error_rls1.setValue(config['circle_error_rls1'])
                self.spin_radius_rls2.setValue(config['circle_radius_rls2'])
                self.spin_error_rls2.setValue(config['circle_error_rls2'])

                QtWidgets.QMessageBox.information(self, "Успех", "Конфигурация загружена успешно.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить конфигурацию:\n{e}")

    def update_plot(self):
        current_option = self.combo_box.currentIndex()

        if not self.inputs_rls1 or not self.inputs_rls2:
            return

        if current_option == 0:
            # Обновление параметров РЛС из интерфейса
            self.rls1.x = self.inputs_rls1['X'].value()
            self.rls1.y = self.inputs_rls1['Y'].value()
            self.rls1.R = self.inputs_rls1['R'].value()
            self.rls1.A = self.inputs_rls1['A'].value()
            self.rls1.W = self.inputs_rls1['W'].value()
            position1 = np.array([self.rls1.x, self.rls1.y])
            main_lobe_direction_deg1 = self.rls1.A
            max_range1 = self.rls1.R * 1.5

            self.rls2.x = self.inputs_rls2['X'].value()
            self.rls2.y = self.inputs_rls2['Y'].value()
            self.rls2.R = self.inputs_rls2['R'].value()
            self.rls2.A = self.inputs_rls2['A'].value()
            self.rls2.W = self.inputs_rls2['W'].value()
            position2 = np.array([self.rls2.x, self.rls2.y])
            main_lobe_direction_deg2 = self.rls2.A
            max_range2 = self.rls2.R * 1.5

            # Обновление глобальных погрешностей
            self.E_ellipse = self.spin_E_ellipse.value()
            self.E_hyperbola = self.spin_E_hyperbola.value()

            # Обновление точек РЛС
            self.rls1_point.setData([self.rls1.x], [self.rls1.y])
            self.rls2_point.setData([self.rls2.x], [self.rls2.y])

            for item in self.current_antennas_lobes:
                self.plot_widget.getPlotItem().removeItem(item)
            self.current_antennas_lobes.clear()

            # Расчёт ДНА

            angles_deg = np.linspace(-360, 360, 3600)

            attenuation_factor1 = np.log(2) / (self.rls1.W / 2)**2
            main_lobe1 = np.exp(-attenuation_factor1 * (angles_deg - main_lobe_direction_deg1)**2)
            main_lobe1 = main_lobe1 / np.max(main_lobe1)

            attenuation_factor2 = np.log(2) / (self.rls2.W / 2)**2
            main_lobe2 = np.exp(-attenuation_factor2 * (angles_deg - main_lobe_direction_deg2)**2)
            main_lobe2 = main_lobe2 / np.max(main_lobe2)

            max_range_distances1 = main_lobe1 * max_range1
            max_range_distances2 = main_lobe2 * max_range2

            theta = np.deg2rad(angles_deg)
            x_fill1 = max_range_distances1 * np.cos(theta) + position1[0]
            y_fill1 = max_range_distances1 * np.sin(theta) + position1[1]

            x_fill2 = max_range_distances2 * np.cos(theta) + position2[0]
            y_fill2 = max_range_distances2 * np.sin(theta) + position2[1]

            poly1_coords = np.column_stack((x_fill1, y_fill1))
            poly1 = Polygon(poly1_coords)
            poly2_coords = np.column_stack((x_fill2, y_fill2))
            poly2 = Polygon(poly2_coords)

            angle_rad1 = np.deg2rad(main_lobe_direction_deg1)
            end_point1 = position1 + max_range1 * np.array([np.cos(angle_rad1), np.sin(angle_rad1)])
            line1 = self.plot_widget.plot([position1[0], end_point1[0]], [position1[1], end_point1[1]], pen=pg.mkPen('b', style=Qt.DashLine, width=1))
            self.current_antennas_lobes.append(line1)

            angle_rad2 = np.deg2rad(main_lobe_direction_deg2)
            end_point2 = position2 + max_range2 * np.array([np.cos(angle_rad2), np.sin(angle_rad2)])
            line2 = self.plot_widget.plot([position2[0], end_point2[0]], [position2[1], end_point2[1]], pen=pg.mkPen('r', style=Qt.DashLine, width=1))
            self.current_antennas_lobes.append(line2)

            points1 = [pg.QtCore.QPointF(x, y) for x, y in zip(x_fill1, y_fill1)]
            polygon1 = QPolygonF(points1)
            polygon_item1 = pg.QtWidgets.QGraphicsPolygonItem(polygon1)
            polygon_item1.setBrush(pg.mkBrush(0, 255, 255, 100))
            polygon_item1.setPen(pg.mkPen(color='blue', width=2))
            self.plot_widget.addItem(polygon_item1)
            self.current_antennas_lobes.append(polygon_item1)

            points2 = [pg.QtCore.QPointF(x, y) for x, y in zip(x_fill2, y_fill2)]
            polygon2 = QPolygonF(points2)
            polygon_item2 = pg.QtWidgets.QGraphicsPolygonItem(polygon2)
            polygon_item2.setBrush(pg.mkBrush(255, 0, 0, 100))
            polygon_item2.setPen(pg.mkPen(color='red', width=2))
            self.plot_widget.addItem(polygon_item2)
            self.current_antennas_lobes.append(polygon_item2)

            # Конец расчёта ДНА

            # Построение эллипсов
            c1 = self.rls1.R + self.rls2.R
            ellipse1_x, ellipse1_y = compute_ellipse(self.rls1, self.rls2, c1)
            if len(ellipse1_x) > 0:
                self.ellipse1.setData(ellipse1_x, ellipse1_y)
            else:
                self.ellipse1.clear()

            c2 = (self.rls1.R + self.E_ellipse) + (self.rls2.R + self.E_ellipse)
            ellipse2_x, ellipse2_y = compute_ellipse(self.rls1, self.rls2, c2)
            if len(ellipse2_x) > 0:
                self.ellipse2.setData(ellipse2_x, ellipse2_y)
            else:
                self.ellipse2.clear()

            # Построение гипербол
            # Гипербола 1: R2 - R1 = c
            c_h1 = self.rls2.R - self.rls1.R
            hyperbola1_ideal_x1, hyperbola1_ideal_y1, hyperbola1_ideal_x2, hyperbola1_ideal_y2 = compute_hyperbola(self.rls1, self.rls2, c_h1)

            # Гипербола 1 с погрешностью (положительная)
            c_h1_uncertainty_pos = c_h1 + 2 * self.E_hyperbola
            hyperbola1_uncertainty_x1, hyperbola1_uncertainty_y1, hyperbola1_uncertainty_x2, hyperbola1_uncertainty_y2 = compute_hyperbola(self.rls1, self.rls2, c_h1_uncertainty_pos)

            # Гипербола 1 с погрешностью (отрицательная)
            c_h1_uncertainty_neg = c_h1 - 2 * self.E_hyperbola
            hyperbola1_uncertainty_neg_x1, hyperbola1_uncertainty_neg_y1, hyperbola1_uncertainty_neg_x2, hyperbola1_uncertainty_neg_y2 = compute_hyperbola(self.rls1, self.rls2, c_h1_uncertainty_neg)

            # Гипербола 2: R1 - R2 = c
            c_h2 = self.rls1.R - self.rls2.R
            hyperbola2_ideal_x1, hyperbola2_ideal_y1, hyperbola2_ideal_x2, hyperbola2_ideal_y2 = compute_hyperbola(self.rls1, self.rls2, c_h2)

            # Гипербола 2 с погрешностью (положительная)
            c_h2_uncertainty_pos = c_h2 + 2 * self.E_hyperbola
            hyperbola2_uncertainty_x1, hyperbola2_uncertainty_y1, hyperbola2_uncertainty_x2, hyperbola2_uncertainty_y2 = compute_hyperbola(self.rls1, self.rls2, c_h2_uncertainty_pos)

            # Гипербола 2 с погрешностью (отрицательная)
            c_h2_uncertainty_neg = c_h2 - 2 * self.E_hyperbola
            hyperbola2_uncertainty_neg_x1, hyperbola2_uncertainty_neg_y1, hyperbola2_uncertainty_neg_x2, hyperbola2_uncertainty_neg_y2 = compute_hyperbola(self.rls1, self.rls2, c_h2_uncertainty_neg)

            # Гипербола 1 (Погрешность Плюс)
            if all([len(hyperbola1_uncertainty_x1) > 0, len(hyperbola1_uncertainty_y1) > 0,
                    len(hyperbola1_uncertainty_x2) > 0, len(hyperbola1_uncertainty_y2) > 0]):
                hyperbola1_uncertainty_x = np.concatenate([hyperbola1_uncertainty_x1, [np.nan], hyperbola1_uncertainty_x2])
                hyperbola1_uncertainty_y = np.concatenate([hyperbola1_uncertainty_y1, [np.nan], hyperbola1_uncertainty_y2])
                self.hyperbola1_uncertainty.setData(hyperbola1_uncertainty_x, hyperbola1_uncertainty_y)
            else:
                self.hyperbola1_uncertainty.clear()

            # Гипербола 1 (Погрешность Минус)
            if all([len(hyperbola1_uncertainty_neg_x1) > 0, len(hyperbola1_uncertainty_neg_y1) > 0,
                    len(hyperbola1_uncertainty_neg_x2) > 0, len(hyperbola1_uncertainty_neg_y2) > 0]):
                hyperbola1_uncertainty_neg_x = np.concatenate([hyperbola1_uncertainty_neg_x1, [np.nan], hyperbola1_uncertainty_neg_x2])
                hyperbola1_uncertainty_neg_y = np.concatenate([hyperbola1_uncertainty_neg_y1, [np.nan], hyperbola1_uncertainty_neg_y2])
                self.hyperbola1_uncertainty_neg.setData(hyperbola1_uncertainty_neg_x, hyperbola1_uncertainty_neg_y)
            else:
                self.hyperbola1_uncertainty_neg.clear()

            # Гипербола 2 (Погрешность Плюс)
            if all([len(hyperbola2_uncertainty_x1) > 0, len(hyperbola2_uncertainty_y1) > 0,
                    len(hyperbola2_uncertainty_x2) > 0, len(hyperbola2_uncertainty_y2) > 0]):
                hyperbola2_uncertainty_x = np.concatenate([hyperbola2_uncertainty_x1, [np.nan], hyperbola2_uncertainty_x2])
                hyperbola2_uncertainty_y = np.concatenate([hyperbola2_uncertainty_y1, [np.nan], hyperbola2_uncertainty_y2])
                self.hyperbola2_uncertainty.setData(hyperbola2_uncertainty_x, hyperbola2_uncertainty_y)
            else:
                self.hyperbola2_uncertainty.clear()

            # Гипербола 2 (Погрешность Минус)
            if all([len(hyperbola2_uncertainty_neg_x1) > 0, len(hyperbola2_uncertainty_neg_y1) > 0,
                    len(hyperbola2_uncertainty_neg_x2) > 0, len(hyperbola2_uncertainty_neg_y2) > 0]):
                hyperbola2_uncertainty_neg_x = np.concatenate([hyperbola2_uncertainty_neg_x1, [np.nan], hyperbola2_uncertainty_neg_x2])
                hyperbola2_uncertainty_neg_y = np.concatenate([hyperbola2_uncertainty_neg_y1, [np.nan], hyperbola2_uncertainty_neg_y2])
                self.hyperbola2_uncertainty_neg.setData(hyperbola2_uncertainty_neg_x, hyperbola2_uncertainty_neg_y)
            else:
                self.hyperbola2_uncertainty_neg.clear()

            for item in self.current_intersection_items:
                self.plot_widget.removeItem(item)
            self.current_intersection_items.clear()

            ellipse_inner_polygon = Polygon(list(zip(ellipse1_x, ellipse1_y)))
            ellipse_outer_polygon = Polygon(list(zip(ellipse2_x, ellipse2_y)))
            hyperbola1_outer_polygon = Polygon(list(zip(hyperbola1_uncertainty_neg_x2, hyperbola1_uncertainty_neg_y2)))
            hyperbola1_inner_polygon = Polygon(list(zip(hyperbola2_uncertainty_neg_x1, hyperbola2_uncertainty_neg_y1)))
            hyperbola2_outer_polygon = Polygon(list(zip(hyperbola1_uncertainty_neg_x1, hyperbola1_uncertainty_neg_y1)))
            hyperbola2_inner_polygon = Polygon(list(zip(hyperbola2_uncertainty_neg_x2, hyperbola2_uncertainty_neg_y2)))
            
            ellipse_difference = ellipse_outer_polygon.difference(ellipse_inner_polygon)
            hyperbola1_difference = hyperbola1_outer_polygon.difference(hyperbola1_inner_polygon)
            hyperbola2_difference = hyperbola2_outer_polygon.difference(hyperbola2_inner_polygon)
            ellipse_hyperbola1_intersection = ellipse_difference.intersection(hyperbola1_difference)
            ellipse_hyperbola2_intersection = ellipse_difference.intersection(hyperbola2_difference)

            final_intersection1 = poly1.intersection(ellipse_hyperbola1_intersection)
            final_intersection2 = poly2.intersection(ellipse_hyperbola2_intersection)

            x, y = final_intersection1.exterior.coords.xy
            points = [pg.QtCore.QPointF(xi, yi) for xi, yi in zip(x, y)]
            polygon_qt = QPolygonF(points)
            polygon_item = pg.QtWidgets.QGraphicsPolygonItem(polygon_qt)
            polygon_item.setBrush(pg.mkBrush(0, 255, 0, 255))  # Green with transparency
            polygon_item.setPen(pg.mkPen(None))
            self.plot_widget.addItem(polygon_item)
            self.current_intersection_items.append(polygon_item)

            x, y = final_intersection2.exterior.coords.xy
            points = [pg.QtCore.QPointF(xi, yi) for xi, yi in zip(x, y)]
            polygon_qt = QPolygonF(points)
            polygon_item = pg.QtWidgets.QGraphicsPolygonItem(polygon_qt)
            polygon_item.setBrush(pg.mkBrush(0, 255, 0, 255))  # Green with transparency
            polygon_item.setPen(pg.mkPen(None))
            self.plot_widget.addItem(polygon_item)
            self.current_intersection_items.append(polygon_item)

            if not final_intersection1.is_empty:
                area1 = final_intersection1.area
                self.label_area1.setText(f"Площадь 1: {area1:.2f} м²")
            else:
                self.label_area1.setText("Площадь 1: 0 м²")

            if not final_intersection2.is_empty:
                area2 = final_intersection2.area
                self.label_area2.setText(f"Площадь 2: {area2:.2f} м²")
            else:
                self.label_area2.setText("Площадь 2: 0 м²")

        elif current_option == 1:
            self.rls1.x = self.inputs_rls1['X'].value()
            self.rls1.y = self.inputs_rls1['Y'].value()
            self.rls1.R = self.inputs_rls1['R'].value()
            self.rls1.A = self.inputs_rls1['A'].value()
            self.rls1.W = self.inputs_rls1['W'].value()
            position1 = np.array([self.rls1.x, self.rls1.y])
            main_lobe_direction_deg1 = self.rls1.A
            max_range1 = self.rls1.R

            self.rls2.x = self.inputs_rls2['X'].value()
            self.rls2.y = self.inputs_rls2['Y'].value()
            self.rls2.R = self.inputs_rls2['R'].value()
            self.rls2.A = self.inputs_rls2['A'].value()
            self.rls2.W = self.inputs_rls2['W'].value()
            position2 = np.array([self.rls2.x, self.rls2.y])
            main_lobe_direction_deg2 = self.rls2.A
            max_range2 = self.rls2.R

            # Обновление точек РЛС
            self.rls1_point.setData([self.rls1.x], [self.rls1.y])
            self.rls2_point.setData([self.rls2.x], [self.rls2.y])

            for item in self.current_antennas_lobes:
                self.plot_widget.getPlotItem().removeItem(item)
            self.current_antennas_lobes.clear()
            
            # Расчёт ДНА

            angles_deg = np.linspace(-360, 360, 3600)

            attenuation_factor1 = np.log(2) / (self.rls1.W / 2)**2
            main_lobe1 = np.exp(-attenuation_factor1 * (angles_deg - main_lobe_direction_deg1)**2)
            main_lobe1 = main_lobe1 / np.max(main_lobe1)

            attenuation_factor2 = np.log(2) / (self.rls2.W / 2)**2
            main_lobe2 = np.exp(-attenuation_factor2 * (angles_deg - main_lobe_direction_deg2)**2)
            main_lobe2 = main_lobe2 / np.max(main_lobe2)

            max_range_distances1 = main_lobe1 * max_range1
            max_range_distances2 = main_lobe2 * max_range2

            theta = np.deg2rad(angles_deg)
            x_fill1 = max_range_distances1 * np.cos(theta) + position1[0]
            y_fill1 = max_range_distances1 * np.sin(theta) + position1[1]

            x_fill2 = max_range_distances2 * np.cos(theta) + position2[0]
            y_fill2 = max_range_distances2 * np.sin(theta) + position2[1]

            poly1_coords = np.column_stack((x_fill1, y_fill1))
            poly1 = Polygon(poly1_coords)
            poly2_coords = np.column_stack((x_fill2, y_fill2))
            poly2 = Polygon(poly2_coords)

            angle_rad1 = np.deg2rad(main_lobe_direction_deg1)
            end_point1 = position1 + max_range1 * np.array([np.cos(angle_rad1), np.sin(angle_rad1)])
            line1 = self.plot_widget.plot([position1[0], end_point1[0]], [position1[1], end_point1[1]], pen=pg.mkPen('b', style=Qt.DashLine, width=1))
            self.current_antennas_lobes.append(line1)

            angle_rad2 = np.deg2rad(main_lobe_direction_deg2)
            end_point2 = position2 + max_range2 * np.array([np.cos(angle_rad2), np.sin(angle_rad2)])
            line2 = self.plot_widget.plot([position2[0], end_point2[0]], [position2[1], end_point2[1]], pen=pg.mkPen('r', style=Qt.DashLine, width=1))
            self.current_antennas_lobes.append(line2)

            points1 = [pg.QtCore.QPointF(x, y) for x, y in zip(x_fill1, y_fill1)]
            polygon1 = QPolygonF(points1)
            polygon_item1 = pg.QtWidgets.QGraphicsPolygonItem(polygon1)
            polygon_item1.setBrush(pg.mkBrush(0, 255, 255, 100))
            polygon_item1.setPen(pg.mkPen(color='blue', width=2))
            self.plot_widget.addItem(polygon_item1)
            self.current_antennas_lobes.append(polygon_item1)

            points2 = [pg.QtCore.QPointF(x, y) for x, y in zip(x_fill2, y_fill2)]
            polygon2 = QPolygonF(points2)
            polygon_item2 = pg.QtWidgets.QGraphicsPolygonItem(polygon2)
            polygon_item2.setBrush(pg.mkBrush(255, 0, 0, 100))
            polygon_item2.setPen(pg.mkPen(color='red', width=2))
            self.plot_widget.addItem(polygon_item2)
            self.current_antennas_lobes.append(polygon_item2)

            # Конец расчёта ДНА

            for item in self.current_intersection_items:
                self.plot_widget.removeItem(item)
            self.current_intersection_items.clear()

            intersect_poly = poly1.intersection(poly2)

            if isinstance(intersect_poly, GeometryCollection):
                for geom in intersect_poly.geoms:
                    if isinstance(geom, Polygon):
                        x, y = geom.exterior.coords.xy
                        points = [pg.QtCore.QPointF(xi, yi) for xi, yi in zip(x, y)]
                        polygon_qt = QPolygonF(points)
                        polygon_item = pg.QtWidgets.QGraphicsPolygonItem(polygon_qt)
                        polygon_item.setBrush(pg.mkBrush(0, 255, 0, 255))
                        polygon_item.setPen(pg.mkPen(None))
                        self.plot_widget.addItem(polygon_item)
                        self.current_intersection_items.append(polygon_item)
            else:
                x, y = intersect_poly.exterior.coords.xy
                points = [pg.QtCore.QPointF(xi, yi) for xi, yi in zip(x, y)]
                polygon_qt = QPolygonF(points)
                polygon_item = pg.QtWidgets.QGraphicsPolygonItem(polygon_qt)
                polygon_item.setBrush(pg.mkBrush(0, 255, 0, 255))
                polygon_item.setPen(pg.mkPen(None))
                self.plot_widget.addItem(polygon_item)
                self.current_intersection_items.append(polygon_item)

            if not intersect_poly.is_empty:
                area = intersect_poly.area
                self.label_area1.setText(f"Площадь: {area:.2f} м²")
            else:
                self.label_area1.setText("Площадь: 0 м²")
        
        elif current_option == 2:
            self.rls1.x = self.inputs_rls1['X'].value()
            self.rls1.y = self.inputs_rls1['Y'].value()
            self.rls1.R = self.inputs_rls1['R'].value()
            self.rls1.A = self.inputs_rls1['A'].value()
            self.rls1.W = self.inputs_rls1['W'].value()

            position1 = np.array([self.rls1.x, self.rls1.y])
            main_lobe_direction_deg1 = self.rls1.A
            max_range1 = self.rls1.R

            self.rls2.x = self.inputs_rls2['X'].value()
            self.rls2.y = self.inputs_rls2['Y'].value()
            self.rls2.R = self.inputs_rls2['R'].value()
            self.rls2.A = self.inputs_rls2['A'].value()
            self.rls2.W = self.inputs_rls2['W'].value()

            position2 = np.array([self.rls2.x, self.rls2.y])
            main_lobe_direction_deg2 = self.rls2.A
            max_range2 = self.rls2.R

            radius_rls1 = self.spin_radius_rls1.value()
            error_rls1 = self.spin_error_rls1.value()
            radius_rls2 = self.spin_radius_rls2.value()
            error_rls2 = self.spin_error_rls2.value()

            # Обновление точек РЛС
            self.rls1_point.setData([self.rls1.x], [self.rls1.y])
            self.rls2_point.setData([self.rls2.x], [self.rls2.y])

            for item in self.current_antennas_lobes:
                self.plot_widget.getPlotItem().removeItem(item)
            self.current_antennas_lobes.clear()
            
            # Расчёт ДНА

            angles_deg = np.linspace(-360, 360, 3600)

            attenuation_factor1 = np.log(2) / (self.rls1.W / 2)**2
            main_lobe1 = np.exp(-attenuation_factor1 * (angles_deg - main_lobe_direction_deg1)**2)
            main_lobe1 = main_lobe1 / np.max(main_lobe1)

            attenuation_factor2 = np.log(2) / (self.rls2.W / 2)**2
            main_lobe2 = np.exp(-attenuation_factor2 * (angles_deg - main_lobe_direction_deg2)**2)
            main_lobe2 = main_lobe2 / np.max(main_lobe2)

            max_range_distances1 = main_lobe1 * max_range1
            max_range_distances2 = main_lobe2 * max_range2

            theta = np.deg2rad(angles_deg)
            x_fill1 = max_range_distances1 * np.cos(theta) + position1[0]
            y_fill1 = max_range_distances1 * np.sin(theta) + position1[1]

            x_fill2 = max_range_distances2 * np.cos(theta) + position2[0]
            y_fill2 = max_range_distances2 * np.sin(theta) + position2[1]

            poly1_coords = np.column_stack((x_fill1, y_fill1))
            poly1 = Polygon(poly1_coords)
            poly2_coords = np.column_stack((x_fill2, y_fill2))
            poly2 = Polygon(poly2_coords)

            angle_rad1 = np.deg2rad(main_lobe_direction_deg1)
            end_point1 = position1 + max_range1 * np.array([np.cos(angle_rad1), np.sin(angle_rad1)])
            line1 = self.plot_widget.plot([position1[0], end_point1[0]], [position1[1], end_point1[1]], pen=pg.mkPen('b', style=Qt.DashLine, width=1))
            self.current_antennas_lobes.append(line1)

            angle_rad2 = np.deg2rad(main_lobe_direction_deg2)
            end_point2 = position2 + max_range2 * np.array([np.cos(angle_rad2), np.sin(angle_rad2)])
            line2 = self.plot_widget.plot([position2[0], end_point2[0]], [position2[1], end_point2[1]], pen=pg.mkPen('r', style=Qt.DashLine, width=1))
            self.current_antennas_lobes.append(line2)

            points1 = [pg.QtCore.QPointF(x, y) for x, y in zip(x_fill1, y_fill1)]
            polygon1 = QPolygonF(points1)
            polygon_item1 = pg.QtWidgets.QGraphicsPolygonItem(polygon1)
            polygon_item1.setBrush(pg.mkBrush(0, 255, 255, 100))
            polygon_item1.setPen(pg.mkPen(color='blue', width=2))
            self.plot_widget.addItem(polygon_item1)
            self.current_antennas_lobes.append(polygon_item1)

            points2 = [pg.QtCore.QPointF(x, y) for x, y in zip(x_fill2, y_fill2)]
            polygon2 = QPolygonF(points2)
            polygon_item2 = pg.QtWidgets.QGraphicsPolygonItem(polygon2)
            polygon_item2.setBrush(pg.mkBrush(255, 0, 0, 100))
            polygon_item2.setPen(pg.mkPen(color='red', width=2))
            self.plot_widget.addItem(polygon_item2)
            self.current_antennas_lobes.append(polygon_item2)

            # Конец расчёта ДНА

            for item in self.current_intersection_items:
                self.plot_widget.removeItem(item)
            self.current_intersection_items.clear()

            # Дальность РЛС1 + погрешность

            circle_rls1 = pg.QtWidgets.QGraphicsEllipseItem(
                position1[0] - radius_rls1, position1[1] - radius_rls1, 2 * radius_rls1, 2 * radius_rls1
            )
            circle_rls1.setPen(pg.mkPen(color='blue', width=2))
            self.plot_widget.addItem(circle_rls1)
            self.current_antennas_lobes.append(circle_rls1)

            error_circle_rls1 = pg .QtWidgets.QGraphicsEllipseItem(
                position1[0] - (radius_rls1 + error_rls1), position1[1] - (radius_rls1 + error_rls1),
                2 * (radius_rls1 + error_rls1), 2 * (radius_rls1 + error_rls1)
            )
            error_circle_rls1.setPen(pg.mkPen(color='blue', style=QtCore.Qt.DashLine))
            self.plot_widget.addItem(error_circle_rls1)
            self.current_antennas_lobes.append(error_circle_rls1)

            # Дальность РЛС2 + погрешность

            circle_rls2 = pg.QtWidgets.QGraphicsEllipseItem(
                position2[0] - radius_rls2, position2[1] - radius_rls2, 2 * radius_rls2, 2 * radius_rls2
            )
            circle_rls2.setPen(pg.mkPen(color='red', width=2))
            self.plot_widget.addItem(circle_rls2)
            self.current_antennas_lobes.append(circle_rls2)

            error_circle_rls2 = pg.QtWidgets.QGraphicsEllipseItem(
                position2[0] - (radius_rls2 + error_rls2), position2[1] - (radius_rls2 + error_rls2),
                2 * (radius_rls2 + error_rls2), 2 * (radius_rls2 + error_rls2)
            )
            error_circle_rls2.setPen(pg.mkPen(color='red', style=QtCore.Qt.DashLine))
            self.plot_widget.addItem(error_circle_rls2)
            self.current_antennas_lobes.append(error_circle_rls2)

            # Пересечение

            theta = np.linspace(0, 2 * np.pi, 360)
           
            x_circle1 = self.rls1.x + radius_rls1 * np.cos(theta)
            y_circle1 = self.rls1.y + radius_rls1 * np.sin(theta)
            circle1_coords = list(zip(x_circle1, y_circle1))
            circle1_polygon = Polygon(circle1_coords)

            x_error_circle1 = self.rls1.x + (radius_rls1 + error_rls1) * np.cos(theta)
            y_error_circle1 = self.rls1.y + (radius_rls1 + error_rls1) * np.sin(theta)
            error_circle1_coords = list(zip(x_error_circle1, y_error_circle1))
            error_circle1_polygon = Polygon(error_circle1_coords)

            x_circle2 = self.rls2.x + radius_rls2 * np.cos(theta)
            y_circle2 = self.rls2.y + radius_rls2 * np.sin(theta)
            circle2_coords = list(zip(x_circle2, y_circle2))
            circle2_polygon = Polygon(circle2_coords)

            x_error_circle2 = self.rls2.x + (radius_rls2 + error_rls2) * np.cos(theta)
            y_error_circle2 = self.rls2.y + (radius_rls2 + error_rls2) * np.sin(theta)
            error_circle2_coords = list(zip(x_error_circle2, y_error_circle2))
            error_circle2_polygon = Polygon(error_circle2_coords)

            ring1 = error_circle1_polygon.difference(circle1_polygon)
            ring2 = error_circle2_polygon.difference(circle2_polygon)

            rings_intersection = ring1.intersection(ring2)
            beams_intersection = rings_intersection.intersection(poly1).intersection(poly2)

            x, y = beams_intersection.exterior.coords.xy
            points = [pg.QtCore.QPointF(xi, yi) for xi, yi in zip(x, y)]
            polygon_qt = QPolygonF(points)
            polygon_item = pg.QtWidgets.QGraphicsPolygonItem(polygon_qt)
            polygon_item.setBrush(pg.mkBrush(0, 255, 0, 255))  # Green with transparency
            polygon_item.setPen(pg.mkPen(None))
            self.plot_widget.addItem(polygon_item)
            self.current_intersection_items.append(polygon_item)

            if not beams_intersection.is_empty:
                area = beams_intersection.area
                self.label_area1.setText(f"Площадь: {area:.2f} м²")
            else:
                self.label_area1.setText("Площадь 1: 0 м²")

        if self.firstRun:
            # Настройка границ графика
            all_x = [self.rls1.x, self.rls2.x]
            all_y = [self.rls1.y, self.rls2.y]
            margin = max(c2, 800) * 1.1
            self.plot_widget.setXRange(min(all_x) - margin, max(all_x) + margin, padding=0)
            self.plot_widget.setYRange(min(all_y) - margin, max(all_y) + margin, padding=0)
            self.firstRun = False