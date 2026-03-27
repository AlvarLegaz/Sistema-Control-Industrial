from PySide6.QtWidgets import (
    QWidget
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QPolygon

# ------------------ TANQUE ------------------
class TankWidget(QWidget):
    def __init__(self, name, level="MID"):
        super().__init__()
        self.name = name
        self.level = level
        self.setMinimumSize(100, 180)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(Qt.white, 2))
        painter.drawRect(20, 20, 60, 140)

        if self.level == "HIGH":
            height = 120
        elif self.level == "LOW":
            height = 40
        else:
            height = 80

        painter.setBrush(QColor("#3daee9"))
        painter.setPen(Qt.NoPen)
        painter.drawRect(22, 160 - height, 56, height)

        painter.setPen(Qt.white)
        painter.drawText(0, 15, self.name)


# ------------------ VALVULA NORMALIZADA ------------------
class ValveWidget(QWidget):
    def __init__(self, name="V", open_state=False):
        super().__init__()
        self.name = name
        self.open_state = open_state
        self.setFixedSize(80, 180)

    def set_open(self, value):
        self.open_state = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color = QColor("lime") if self.open_state else QColor("#aaaaaa")

        painter.setPen(QPen(color, 3))
        painter.drawLine(0, 90, 25, 90)

        painter.setBrush(color)

        left_triangle = QPolygon([
            QPoint(25, 90),
            QPoint(45, 70),
            QPoint(45, 110)
        ])

        right_triangle = QPolygon([
            QPoint(65, 90),
            QPoint(45, 70),
            QPoint(45, 110)
        ])

        painter.drawPolygon(left_triangle)
        painter.drawPolygon(right_triangle)

        painter.setPen(QPen(Qt.white, 2))
        painter.drawLine(45, 70, 45, 110)

        painter.setPen(Qt.white)
        painter.drawText(25, 140, self.name)

