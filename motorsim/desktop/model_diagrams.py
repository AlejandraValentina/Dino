"""Engineering views of represented geometry; no inferred head or port layout."""
from math import isfinite
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter,QColor,QPen
from PySide6.QtWidgets import QWidget
from ..kinematics import piston_position


def can_edit_opening(port):
    return (port.family=='rectangular_window' and port.role in {'transfer','exhaust'}
            and port.roof_travel_mm==0 and port.discharge_coefficient>0)


def top_from_opening(port,stroke,rod,angle):
    if not can_edit_opening(port):
        raise ValueError('Sólo ventanas rectangulares de techo fijo admiten esta conversión.')
    if not isfinite(angle) or not 0<angle<180:
        raise ValueError('Apertura: ingresá un ángulo entre 0 y 180° (sin extremos).')
    top=piston_position(stroke,rod,angle)
    if not 0<top<stroke:raise ValueError('La apertura queda en un extremo no invertible con esta precisión.')
    return top


class PortGeometryView(QWidget):
    """Independent depth strips, never a fictitious circumferential port map."""
    def __init__(self,parent=None):
        super().__init__(parent);self.rows=[];self.stroke=50.;self.setMinimumHeight(150)
    def set_geometry(self,port_set,reed=False):
        self.stroke=port_set.stroke_mm
        self.rows=[dict(id=p.id,top=p.top_mm,height=p.height_mm,width=p.width_mm,
                       effective_top=None if p.top_mm is None else p.top_mm+p.roof_travel_mm*p.roof_position,
                       available=p.family!='effective_profile' and not (reed and p.role=='intake')) for p in port_set.ports]
        self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#101a28'))
        left=150.;right=self.width()-125.;span=max(1.,right-left)
        p.setPen(QColor('#cad8e7'));p.drawText(8,18,'Cotas desde PMS · filas independientes; sin posición circunferencial')
        p.drawText(round(left),38,'PMS 0 mm');p.drawText(round(right)-60,38,f'PMI {self.stroke:g} mm')
        step=max(22,min(32,(self.height()-45)/max(1,len(self.rows))))
        for i,row in enumerate(self.rows):
            y=50+i*step;p.setPen(QColor('#cad8e7'));p.drawText(6,round(y+12),row['id'])
            if not row['available']:
                p.drawText(round(left),round(y+12),'Geometría no identificada / control por Δp');continue
            top=row['effective_top'];end=top+row['height']
            if top>=self.stroke or end<=0:
                p.drawText(round(left),round(y+12),f'Fuera de la carrera visible · cota {top:g}, altura {row["height"]:g} mm');continue
            p.setPen(QPen(QColor('#40566a'),1));p.drawLine(round(left),round(y+8),round(right),round(y+8))
            # Clip the depth view to the represented stroke; dimensions remain explicit.
            a=left+max(0,min(self.stroke,top))/self.stroke*span
            b=left+max(0,min(self.stroke,end))/self.stroke*span
            p.fillRect(QRectF(a,y,max(1,b-a),16),QColor('#247da2'))
            p.setPen(QColor('#cad8e7'));p.drawText(round(right)+8,round(y+12),f'{top:.2f} / {row["height"]:g} mm')
        p.end()


class PortTimingView(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.rows=[];self.setMinimumHeight(145)
    def set_events(self,port_set,reed=False):
        self.rows=[]
        for port in port_set.ports:
            if reed and port.role=='intake':continue
            events=port_set.event_angles(port)
            intervals=[(a,b) for a,b in zip(events,events[1:]) if port_set.area_at(port,(a+b)/2)>1e-9]
            self.rows.append(dict(id=port.id,events=list(events),intervals=intervals))
        self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#101a28'));left=150.;span=max(1.,self.width()-left-24)
        p.setPen(QColor('#cad8e7'));p.drawText(8,18,'Aperturas de área efectiva · eventos del backend · grados de cigüeñal')
        for angle in (0,90,180,270,360):
            x=left+angle/360*span;p.drawText(round(x)-16,38,32,16,Qt.AlignmentFlag.AlignCenter,str(angle))
        step=max(22,min(30,(self.height()-48)/max(1,len(self.rows))))
        for i,row in enumerate(self.rows):
            y=52+i*step;p.setPen(QColor('#cad8e7'));p.drawText(6,round(y+12),row['id'])
            p.setPen(QPen(QColor('#40566a'),1));p.drawLine(round(left),round(y+8),round(left+span),round(y+8))
            for a,b in row['intervals']:p.fillRect(QRectF(left+a/360*span,y,max(1,(b-a)/360*span),16),QColor('#247da2'))
        p.end()
