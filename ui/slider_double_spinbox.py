from PyQt5.QtWidgets import QWidget, QSlider, QDoubleSpinBox, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal


class SliderDoubleSpinBox(QWidget):
    """Custom input element with a slider and QDoubleSpinBox for double and integer values."""
    valueChanged = pyqtSignal(float)  # Signal emitted when the value changes

    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Scale factor for handling float values in the slider
        self.scale = 1  # Default scale for integer-like values

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.layout.addWidget(self.slider)

        # SpinBox
        self.spinbox = QDoubleSpinBox()
        self.layout.addWidget(self.spinbox)

        # Connect slider and spinbox
        self.slider.valueChanged.connect(self._sync_spinbox)
        self.spinbox.valueChanged.connect(self._sync_slider)

    def _sync_spinbox(self, slider_value):
        """Synchronize spinbox when slider changes."""
        value = slider_value / self.scale if self.scale > 1 else slider_value
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)
        self.valueChanged.emit(value)

    def _sync_slider(self, spinbox_value):
        """Synchronize slider when spinbox changes."""
        value = round(spinbox_value * self.scale)  # Ensure alignment
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.valueChanged.emit(spinbox_value)

    def setRange(self, min_val, max_val):
        """Set the range for both slider and spinbox."""
        self.slider.setRange(int(min_val * self.scale), int(max_val * self.scale))
        self.spinbox.setRange(min_val, max_val)

    def setValue(self, value):
        """Set the value for both slider and spinbox."""
        self.slider.setValue(int(value * self.scale))
        self.spinbox.setValue(value)

    def value(self):
        """Get the current value."""
        return self.spinbox.value()

    def setDecimals(self, decimals):
        """Set the number of decimals for the spinbox."""
        self.spinbox.setDecimals(decimals)
        self.scale = 10 ** decimals if decimals > 0 else 1  # Adjust scale for precision
        self.setRange(self.spinbox.minimum(), self.spinbox.maximum())  # Reapply range
        self.setValue(self.value())  # Reapply value with updated scale

    def setSingleStep(self, step):
        """Set the step size for the spinbox and slider."""
        self.spinbox.setSingleStep(step)
        self.slider.setSingleStep(int(step * self.scale))
        self.slider.setTickInterval(int(step * self.scale))

    def setTickInterval(self, interval):
        """Set tick interval for the slider."""
        self.slider.setTickInterval(int(interval * self.scale))
