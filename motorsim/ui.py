"""Contenedores visuales compartidos; sin estado ni reglas del dominio."""
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout, QGridLayout, QSizePolicy


def text(value='',role=''):
    widget=QLabel(value);widget.setObjectName(role)
    widget.setTextFormat(Qt.TextFormat.PlainText);widget.setWordWrap(True)
    widget.setMinimumWidth(0)
    return widget


class Header(QWidget):
    def __init__(self,title,subtitle,notice=''):
        super().__init__();box=QVBoxLayout(self);box.setContentsMargins(0,0,0,6);box.setSpacing(5)
        box.addWidget(text(title,'pageTitle'));box.addWidget(text(subtitle,'subtitle'))
        if notice:box.addWidget(text(notice,'unit'))


class Panel(QFrame):
    def __init__(self,title):
        super().__init__();self.setObjectName('panel')
        self.content=QVBoxLayout(self);self.content.setContentsMargins(16,14,16,16);self.content.setSpacing(10)
        self.heading=text(title,'panelTitle');self.content.addWidget(self.heading)
        self.content.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)


class Columns(QWidget):
    """Dos paneles adyacentes o apilados según el ancho realmente disponible."""
    def __init__(self,left,right,threshold=850,ratios=(1,1)):
        super().__init__();self.left,self.right=left,right;self.threshold=threshold;self.ratios=ratios
        self.grid=QGridLayout(self);self.grid.setContentsMargins(0,0,0,0);self.grid.setSpacing(16)
        self.wide=None;self.arrange()
    def arrange(self):
        wide=self.width()>=self.threshold
        if wide==self.wide:return
        self.wide=wide
        self.grid.addWidget(self.left,0,0)
        self.grid.addWidget(self.right,0 if wide else 1,1 if wide else 0)
        self.grid.setColumnStretch(0,self.ratios[0] if wide else 1)
        self.grid.setColumnStretch(1,self.ratios[1] if wide else 0)
    def resizeEvent(self,event):
        super().resizeEvent(event);self.arrange()
    def minimumSizeHint(self):
        # El mínimo de la disposición ancha no debe impedir que colapse.
        hint=super().minimumSizeHint()
        return QSize(0,hint.height())
