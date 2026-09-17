"""Consulta de rendimiento indicado de barridos validados; nunca crea procesos."""
import math
from PySide6.QtCore import QPointF,QRectF,Qt,Signal
from PySide6.QtGui import QColor,QPainter,QPen
from PySide6.QtWidgets import (QWidget,QScrollArea,QVBoxLayout,QGridLayout,QPushButton,QFileDialog,
    QTableWidget,QTableWidgetItem,QHeaderView,QAbstractItemView,QLayout)
from .ui import Header,Panel,Columns,text,ValidationMessage,visual_state
from .performance import sweep_metrics,export_performance_csv,NOTICE
from .reference_results import ResultError
from .sweep import load_sweep
from .sweep_view import STATES
from .comparison import ComparisonError


class PerformancePlot(QWidget):
    selected=Signal(int)
    def __init__(self,fields):
        super().__init__();self.fields=fields;self.rows=[];self.current=-1;self.hits=[]
        self.setMinimumHeight(290 if len(fields)==2 else 250);self.setMinimumWidth(0)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(' / '.join(field[1] for field in fields)+' frente a RPM')
        self.setAccessibleDescription('Seleccionar punto con clic o flechas izquierda/derecha. Datos disponibles también en tabla.')
    def set_rows(self,rows):self.rows=rows;self.current=-1;self.update()
    def set_current(self,index):self.current=index;self.update()
    def series_segments(self,key,factor):
        segments=[];segment=[]
        for i,row in enumerate(self.rows):
            if row['metrics'] is None:
                if segment:segments.append(segment);segment=[]
            else:segment.append((i,row['rpm'],row['metrics'][key]/factor))
        if segment:segments.append(segment)
        return segments
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fm=p.fontMetrics();line=fm.height()+5;self.hits=[]
        for i,(_,title,unit,color,_) in enumerate(self.fields):
            p.setPen(QColor(color));suffix=(' · eje izquierdo' if i==0 else ' · eje derecho') if len(self.fields)>1 else ''
            p.drawText(QRectF(12,8+i*line*2,self.width()-24,line*2),Qt.TextFlag.TextWordWrap,title+' ['+unit+']'+suffix)
        box=QRectF(64,12+len(self.fields)*line*2,max(1,self.width()-128),max(1,self.height()-(len(self.fields)*2+3)*line-24))
        p.setPen(QColor('#324762'));p.drawRect(box)
        valid=[r for r in self.rows if r['metrics'] is not None]
        if not valid:
            p.setPen(QColor('#8ba2be'));p.drawText(box.adjusted(8,0,-8,0),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,'Sin puntos convergidos para graficar')
        if self.rows:
            lo,hi=min(r['rpm'] for r in self.rows),max(r['rpm'] for r in self.rows)
            span=hi-lo or 1
            for rpm in sorted(set(r['rpm'] for r in self.rows)):
                x=box.left()+(rpm-lo)/span*box.width()
                p.setPen(QColor('#8ba2be'));p.drawText(QRectF(x-30,box.bottom()+5,60,line),Qt.AlignmentFlag.AlignHCenter,str(rpm))
            for axis,(key,_,_,color,factor) in enumerate(self.fields):
                values=[r['metrics'][key]/factor for r in valid]
                if not values:continue
                bottom,top=min(0,min(values)),max(0,max(values))
                spread=top-bottom or 1
                if bottom<0:bottom-=spread*.08
                top+=spread*.08
                def mapped(rpm,value):return QPointF(box.left()+(rpm-lo)/span*box.width(),box.bottom()-(value-bottom)/(top-bottom)*box.height())
                p.setPen(QColor(color))
                for fraction in (0,.5,1):
                    y=box.bottom()-box.height()*fraction
                    x=box.right()+5 if axis else 0
                    p.drawText(QRectF(x,y-line/2,58,line),Qt.AlignmentFlag.AlignLeft if axis else Qt.AlignmentFlag.AlignRight,f'{bottom+(top-bottom)*fraction:.4g}')
                p.setPen(QPen(QColor(color),1.6))
                for segment in self.series_segments(key,factor):
                    previous=None
                    for index,rpm,value in segment:
                        position=mapped(rpm,value)
                        if previous is not None:p.drawLine(previous,position)
                        p.setBrush(QColor(color));p.drawEllipse(position,4,4)
                        if index==self.current:
                            p.setBrush(Qt.BrushStyle.NoBrush);p.drawEllipse(position,7,7)
                        previous=position;self.hits.append((index,position))
        p.setPen(QColor('#8ba2be'));p.drawText(QRectF(0,self.height()-line-3,self.width(),line),Qt.AlignmentFlag.AlignCenter,'RPM · puntos calculados; segmentos rectos')
        if self.hasFocus():p.setPen(QPen(QColor('#0284c7'),2));p.setBrush(Qt.BrushStyle.NoBrush);p.drawRect(self.rect().adjusted(1,1,-2,-2))
    def mousePressEvent(self,event):
        self.setFocus()
        if self.hits:
            index,point=min(self.hits,key=lambda item:math.hypot(item[1].x()-event.position().x(),item[1].y()-event.position().y()))
            if math.hypot(point.x()-event.position().x(),point.y()-event.position().y())<=18:self.selected.emit(index)
        super().mousePressEvent(event)
    def keyPressEvent(self,event):
        choices=[i for i,r in enumerate(self.rows) if r['metrics'] is not None]
        if choices and event.key() in (Qt.Key.Key_Left,Qt.Key.Key_Right,Qt.Key.Key_Home,Qt.Key.Key_End):
            if event.key()==Qt.Key.Key_Home:index=0
            elif event.key()==Qt.Key.Key_End:index=len(choices)-1
            elif self.current not in choices:index=0
            else:index=max(0,min(len(choices)-1,choices.index(self.current)+(1 if event.key()==Qt.Key.Key_Right else -1)))
            self.selected.emit(choices[index]);event.accept();return
        super().keyPressEvent(event)


class PerformanceSummary(QWidget):
    def __init__(self,names):
        super().__init__();self.values={};parts=[]
        for name in names:
            part=QWidget();layout=QVBoxLayout(part);layout.setContentsMargins(0,0,0,0);layout.setSpacing(5)
            layout.setVerticalSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
            layout.addWidget(text(name,'unit'));value=text('—','propertyValue');layout.addWidget(value)
            self.values[name]=value;parts.append(part)
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        layout.setVerticalSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(Columns(Columns(*parts[:2],400),Columns(*parts[2:],400),850))
    def set_value(self,name,value):self.values[name].setText(str(value))


class PerformanceView(QScrollArea):
    def __init__(self,controller):
        super().__init__();self.controller=controller;self.sweep=None;self.rows=[]
        self.setWidgetResizable(True);self.setFrameShape(QScrollArea.Shape.NoFrame)
        body=QWidget();self.setWidget(body);box=QVBoxLayout(body);box.setContentsMargins(20,16,20,16);box.setSpacing(12)
        box.addWidget(Header('Rendimiento','Curvas derivadas de los puntos simulados del barrido seleccionado.',
            'Potencia/par indicados · sin pérdidas mecánicas · no representan valores al eje.'))
        source=Panel('BARRIDO SELECCIONADO');box.addWidget(source)
        actions=QGridLayout();source.content.addLayout(actions)
        self.open_button=QPushButton('Abrir barrido…');self.open_button.setObjectName('primaryAction')
        self.reuse_button=QPushButton('Usar barrido actual');self.export_button=QPushButton('Exportar rendimiento CSV…')
        actions.addWidget(self.open_button,0,0);actions.addWidget(self.reuse_button,0,1);actions.addWidget(self.export_button,1,0,1,2)
        self.identity=text('No hay barrido seleccionado. Abrí uno guardado o usá el barrido actual.');source.content.addWidget(self.identity)
        self.error=ValidationMessage();source.content.addWidget(self.error)
        self.summary=PerformanceSummary(('Mayor potencia entre puntos calculados','Mayor par entre puntos calculados','Puntos convergidos','Rango RPM del barrido'))
        panel=Panel('RESUMEN DE LOS PUNTOS');panel.content.addWidget(self.summary);box.addWidget(panel)
        self.main_plot=PerformancePlot((('indicated_power_W','Potencia indicada','kW','#38bdf8',1000),('indicated_torque_Nm','Par indicado equivalente','N·m','#f59e0b',1)))
        plot_panel=Panel('POTENCIA Y PAR INDICADOS');plot_panel.content.addWidget(self.main_plot);box.addWidget(plot_panel)
        self.detail=text('Seleccioná un punto en el gráfico o una fila en la tabla.');plot_panel.content.addWidget(self.detail)
        self.point_button=QPushButton('Abrir resultado del punto');plot_panel.content.addWidget(self.point_button)
        plot_panel.content.addWidget(text(NOTICE,'unit'))
        self.secondary=[];panels=[]
        for key,title,unit,factor in (('W_C_J','Trabajo indicado','J/ciclo',1),('p_max_Pa','Presión máxima absoluta','kPa',1000)):
            plot=PerformancePlot(((key,title,unit,'#38bdf8',factor),));self.secondary.append(plot)
            panel=Panel(title.upper());panel.content.addWidget(plot);panels.append(panel)
        box.addWidget(Columns(*panels,850))
        panel=Panel('PUNTOS DEL BARRIDO');box.addWidget(panel)
        self.table=QTableWidget(0,6);self.table.setAccessibleName('Puntos de rendimiento indicado')
        self.table.setStyleSheet('QTableWidget::item:selected { color: #e5edf7; background: #213a52; }')
        self.table.setHorizontalHeaderLabels(['RPM','Estado','W_C [J/ciclo]','Potencia indicada [kW]','Par indicado equivalente [N·m]','pmax [kPa abs]'])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection);self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setMinimumHeight(220);panel.content.addWidget(self.table)
        self.open_button.clicked.connect(self.open_sweep);self.reuse_button.clicked.connect(self.reuse_current)
        self.export_button.clicked.connect(self.export);self.point_button.clicked.connect(self.open_point)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        for plot in (self.main_plot,*self.secondary):plot.selected.connect(self.table.selectRow)
        self.controller.idle.connect(self.refresh_available)
        self.refresh_available();self.selection_changed();box.addStretch()
    def refresh_available(self):
        self.reuse_button.setEnabled(self.controller.sweep is not None and not self.controller.active)
        self.export_button.setEnabled(self.sweep is not None)
        self.selection_changed()
    def open_sweep(self,checked=False,*,path=None):
        if path is None:path,_=QFileDialog.getOpenFileName(self,'Abrir barrido para Rendimiento','','Barrido (series.json)')
        if not path:return
        try:self.set_sweep(load_sweep(path))
        except (ResultError,ValueError) as exc:self.error.setText(str(exc)+' Se conserva la selección anterior.')
    def reuse_current(self):
        if self.controller.sweep is not None and not self.controller.active:self.set_sweep(self.controller.sweep)
    def set_sweep(self,sweep):
        rows=sweep_metrics(sweep)  # Validar antes de sustituir la selección.
        self.sweep,self.rows=sweep,rows;index=sweep['index'];inputs=index['common_inputs'];case=inputs['case']
        origin=inputs.get('origin');name=origin['project_name'] if origin else case['identifier']
        cycle=case['project_geometry']['cycle']
        self.identity.setText(f"{name} · {cycle} · {STATES[index['state']]}\nRPM: "+', '.join(str(r['rpm']) for r in rows)+f"\n{str(sweep['path'])}")
        self.identity.setToolTip(str(sweep['path']));self.error.clear()
        valid=[row['metrics'] for row in rows if row['metrics'] is not None]
        for key,caption,factor,unit in (('indicated_power_W','Mayor potencia entre puntos calculados',1000,'kW'),('indicated_torque_Nm','Mayor par entre puntos calculados',1,'N·m')):
            best=max(valid,key=lambda r:r[key]) if valid else None
            self.summary.set_value(caption,f"{best[key]/factor:.6f} {unit} · {best['rpm']} rpm" if best else '—')
        self.summary.set_value('Puntos convergidos',f'{len(valid)} / {len(rows)}')
        self.summary.set_value('Rango RPM del barrido',f"{min(r['rpm'] for r in rows)}–{max(r['rpm'] for r in rows)} rpm")
        self.table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            metrics=row['metrics']
            values=[str(row['rpm']),STATES[row['state']]]+[f'{metrics[key]/factor:.9g}' if metrics else '—' for key,factor in (('W_C_J',1),('indicated_power_W',1000),('indicated_torque_Nm',1),('p_max_Pa',1000))]
            for col,value in enumerate(values):
                item=QTableWidgetItem(value);item.setToolTip(row['reason']);self.table.setItem(i,col,item)
        for plot in (self.main_plot,*self.secondary):plot.set_rows(rows)
        self.table.resizeRowsToContents();self.table.selectRow(0);self.selection_changed();self.refresh_available()
    def selection_changed(self):
        index=self.table.currentRow();row=self.rows[index] if 0<=index<len(self.rows) else None
        metrics=row['metrics'] if row else None;self.point_button.setEnabled(metrics is not None and not self.controller.active)
        for plot in (self.main_plot,*self.secondary):plot.set_current(index)
        if row is None:self.detail.setText('Seleccioná un punto en el gráfico o una fila en la tabla.');return
        if metrics:
            self.detail.setText(f"{row['rpm']} rpm · {STATES[row['state']]}\nPotencia indicada: {metrics['indicated_power_W']/1000:.6f} kW · Par indicado equivalente: {metrics['indicated_torque_Nm']:.6f} N·m\nW_C: {metrics['W_C_J']:.9g} J/ciclo · pmax: {metrics['p_max_Pa']/1000:.9g} kPa abs")
        else:self.detail.setText(f"{row['rpm']} rpm · {STATES[row['state']]} · {row['reason']}\nSin magnitudes indicadas disponibles.")
    def open_point(self):
        index=self.table.currentRow()
        if self.controller.active:return
        if 0<=index<len(self.rows) and self.rows[index]['metrics'] is not None:
            self.controller._show_series_point(self.sweep['results'][index])
    def export(self,checked=False,*,folder=None):
        if self.sweep is None:return
        if folder is None:folder,_=QFileDialog.getSaveFileName(self,'Carpeta nueva para rendimiento.csv','','Carpeta (*)')
        if not folder:return
        try:
            export_performance_csv(folder,self.sweep);self.error.setText('CSV guardado en '+str(folder));visual_state(self.error,'success')
        except (ComparisonError,ResultError) as exc:self.error.setText(str(exc))
