"""Composición por tareas. No contiene validadores, persistencia ni cálculo físico."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,
    QTreeWidget,QTreeWidgetItem,QStackedWidget,QScrollArea,QTabWidget,QPushButton,
    QPlainTextEdit,QSizePolicy)
from .project import ProjectError


def label(text='',style=''):
    w=QLabel(text);w.setWordWrap(True);w.setTextFormat(Qt.TextFormat.PlainText)
    w.setObjectName(style);w.setMinimumWidth(0);return w


def scroll(widget):
    w=QScrollArea();w.setWidgetResizable(True);w.setFrameShape(QScrollArea.Shape.NoFrame)
    w.setWidget(widget);return w


class Navigation(QWidget):
    selected=Signal(str)
    def __init__(self):
        super().__init__();layout=QHBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0)
        self.tree=QTreeWidget();self.tree.setObjectName('navigation');self.tree.setHeaderHidden(True)
        self.tree.setAccessibleName('Navegación principal');self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(10);self.tree.setMinimumWidth(145);self.tree.setMaximumWidth(190)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stack=QStackedWidget();self.stack.setMinimumWidth(0)
        layout.addWidget(self.tree);layout.addWidget(self.stack,1)
        self.items={};self.pages={};self.aliases={};self.groups={};self.cycle='2T';self.current=''
        self.tree.currentItemChanged.connect(self._select)
    def add_page(self,group,key,title,page):
        if group not in self.groups:
            node=QTreeWidgetItem(self.tree,[group]);node.setFlags(Qt.ItemFlag.ItemIsEnabled)
            node.setExpanded(True);self.groups[group]=node
        item=QTreeWidgetItem(self.groups[group],[title]);item.setData(0,Qt.ItemDataRole.UserRole,key)
        item.setToolTip(0,title);self.items[key]=item;self.pages[key]=page;self.stack.addWidget(page)
    def _select(self,item,previous):
        key=item.data(0,Qt.ItemDataRole.UserRole) if item else None
        if key in self.pages:
            self.current=key;self.stack.setCurrentWidget(self.pages[key]);self.selected.emit(key)
    def go(self,key):
        if key in ('motor2','motor4'):key='motor2' if self.cycle=='2T' else 'motor4'
        self.tree.setCurrentItem(self.items[key])
        if self.current==key:self.selected.emit(key)
    def set_cycle(self,cycle):
        self.cycle=cycle;self.items['motor2'].setHidden(cycle!='2T');self.items['motor4'].setHidden(cycle!='4T')
        if self.current in ('motor2','motor4'):self.go('motor2' if cycle=='2T' else 'motor4')
    def setCurrentWidget(self,widget):
        # Conserva accesos internos a editores; no existe una segunda navegación visible.
        key,callback=self.aliases.get(widget,('summary',None));self.go(key)
        if callback:callback()
    def setCurrentIndex(self,index):self.go(list(self.pages)[index])
    def currentWidget(self):return self.stack.currentWidget()


class SummaryPage(QScrollArea):
    def __init__(self,owner):
        super().__init__();self.owner=owner;self.setWidgetResizable(True);self.setFrameShape(QScrollArea.Shape.NoFrame)
        body=QWidget();box=QVBoxLayout(body);box.setContentsMargins(24,20,24,20);box.setSpacing(16)
        box.addWidget(label('Resumen del proyecto','pageTitle'))
        self.tabs=QTabWidget();box.addWidget(self.tabs)
        summary=QWidget();layout=QVBoxLayout(summary);layout.setSpacing(18)
        self.identity=label('','sectionTitle');layout.addWidget(self.identity)
        self.facts=label();self.facts.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);layout.addWidget(self.facts)
        self.file=label('','unit');layout.addWidget(self.file)
        self.ready=label('','sectionTitle');layout.addWidget(self.ready)
        self.attention=QVBoxLayout();layout.addLayout(self.attention);layout.addStretch()
        self.tabs.addTab(summary,'Resumen');self.tabs.addTab(owner.general_group,'Datos del proyecto')
        box.addStretch();self.setWidget(body);self.issue_routes={}
    def refresh(self):
        w=self.owner;cycle=w.cycle_combo.currentText();name=w.name_edit.text() or 'Sin nombre'
        self.identity.setText(name+' · '+cycle+'\nFabricante / modelo: '+' / '.join(x.text() or '—' for x in w.text_edits.values()))
        def value(key):return w.numeric_edits[key].text() or '—'
        self.facts.setText(f'Cilindros: {value("cylinder_count")}    ·    Diámetro × carrera: {value("bore_mm")} × {value("stroke_mm")} mm\n'
            f'Cilindrada: {w.total_volume_label.text()} cm³    ·    Compresión: {value("compression_ratio")}:1')
        self.file.setText(w.state_label.text()+'\n'+(str(w.path) if w.path else 'Sin archivo asociado'))
        try:
            w.execution_snapshot()
            errors=[]
        except ProjectError as exc:errors=str(exc).splitlines()
        self.ready.setText('Listo para simular' if not errors else 'Faltan datos · revisar configuración')
        while self.attention.count():
            item=self.attention.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        self.issue_routes={}
        for error in errors:
            lower=error.lower()
            key=('motor2' if cycle=='2T' else 'motor4') if any(t in lower for t in ('lumbr','ventana','falda','admis','cárter','conduct','válv','escape','transfer','distribu','alzada','garganta','asiento')) else 'geometry'
            if 'nombre' in lower:key='summary'
            self.issue_routes.setdefault(key,[]).append(error)
        for key,messages in self.issue_routes.items():
            title={'geometry':'Geometría','summary':'Datos del proyecto'}.get(key,'Motor '+cycle)
            button=QPushButton(title+' · '+str(len(messages))+' observaciones →')
            button.setToolTip('\n'.join(dict.fromkeys(messages)));button.clicked.connect(lambda checked=False,k=key:w.navigation.go(k))
            if key=='summary':button.clicked.connect(lambda:self.tabs.setCurrentIndex(1))
            self.attention.addWidget(button)
        for page in (w.motor2_page,w.motor4_page):
            page.errors.setText('\n'.join(self.issue_routes.get(page.key,[])))


class MotorPage(QWidget):
    def __init__(self,cycle,sections):
        super().__init__();self.key='motor2' if cycle=='2T' else 'motor4'
        box=QVBoxLayout(self);box.setContentsMargins(18,12,18,12)
        box.addWidget(label('Motor '+cycle+' · Configuración admitida','pageTitle'))
        self.tabs=QTabWidget();box.addWidget(self.tabs,1)
        for title,widget in sections:
            for heading in widget.findChildren(QLabel,'pageTitle'):heading.hide()
            self.tabs.addTab(widget,title)
        self.overview=label('','unit');box.addWidget(self.overview)
        self.context=QPlainTextEdit();self.context.setReadOnly(True);self.context.setMaximumHeight(155);self.context.hide()
        self.errors=label('','fieldError');self.errors.hide()
        self.context_button=QPushButton('Contexto y observaciones');self.context_button.setCheckable(True)
        self.context_button.toggled.connect(self.context.setVisible);box.addWidget(self.context_button);box.addWidget(self.context)
    def refresh_context(self,text):
        self.overview.setText('\n'.join(text.splitlines()[:2]))
        self.context.setPlainText(text+'\n\nEjecutabilidad\n'+(self.errors.text() or 'Sin observaciones en esta sección.'))
        count=len(self.errors.text().splitlines()) if self.errors.text() else 0
        self.context_button.setText('Contexto y observaciones'+(f' · {count} por revisar' if count else ''))


class ResultWorkspace(QWidget):
    def __init__(self,simulation):
        super().__init__();self.simulation=simulation;layout=QVBoxLayout(self);layout.setContentsMargins(18,12,18,12)
        layout.addWidget(label('Resultados','pageTitle'))
        actions=QGridLayout();layout.addLayout(actions)
        for i,button in enumerate((simulation.open_button,simulation.open_sweep_button,simulation.sweep_button)):actions.addWidget(button,i//2,i%2)
        self.message_host=QVBoxLayout();layout.addLayout(self.message_host)
        self.tabs=QTabWidget();layout.addWidget(self.tabs,1)
        self.detail=QWidget();self.detail_layout=QVBoxLayout(self.detail);self.detail_layout.setContentsMargins(0,0,0,0)
        self.tabs.addTab(scroll(self.detail),'Resultado actual')
        self.series=QWidget();self.series_layout=QVBoxLayout(self.series);self.series_layout.setContentsMargins(0,0,0,0)
        self.tabs.addTab(scroll(self.series),'Barrido cargado')
        self.empty=label('Abrí un barrido guardado para consultar sus puntos.','unit');self.series_layout.addWidget(self.empty)
    def show_series(self,dialog):
        self.empty.hide()
        dialog.setWindowFlags(Qt.WindowType.Widget);self.series_layout.addWidget(dialog)
        for button in dialog.findChildren(QPushButton):
            if button.text()=='Cerrar':button.hide()
        dialog.show();self.tabs.setCurrentIndex(1)
    def show_result(self):self.tabs.setCurrentIndex(0)


def refresh_motor_context(owner):
    """Formatea salidas de las funciones geométricas existentes, sin otras reglas."""
    from .ports import port_results
    from .ducts import route_geometry, format_geometry
    from .valves import area
    w=owner
    try:
        try:project=w.project()
        except ProjectError:project,_=w.execution_snapshot()
    except ProjectError:
        w.motor2_page.refresh_context('Borrador con entradas inválidas · revisar campos\n'+w.ports_view.input_error.text())
        w.motor4_page.refresh_context('Borrador con entradas inválidas · revisar campos\n'+w.valves_view.crossing.text())
        return
    two=['Cárter PMI: '+(str(project.crankcase_volume_bdc_cm3) if project.crankcase_volume_bdc_cm3 is not None else '—')+' cm³']
    for p in project.ports:
        r=port_results(p,project.stroke_mm,project.rod_length_mm)
        two.append(f'{p.function or "Sin función"} · {p.name or "Sin nombre"}: '+
            (f'{r.opening:g}°–{r.closing:g}°' if r.opening is not None and r.closing is not None else '—'))
    two.append(w.ports_view.intake.results.text())
    four=[w.valves_view.crossing.text()]
    for route,title in (('intake','Admisión'),('exhaust','Escape')):
        valve=getattr(project.four_stroke,route)
        four.append(title+': '+w.valves_view.outputs[route].text())
        if w.valves_view.plots[route][0].values:
            four.append(f'Alzada máxima: {valve.lift_mm:g} mm · Área máxima: {area(valve,valve.opening_deg+valve.duration_deg/2):.2f} mm²')
    for target,ducts in ((two,project.ducts),(four,project.four_stroke.ducts)):
        for route,title in (('intake','Admisión'),('exhaust','Escape')):
            data=route_geometry(getattr(ducts,route))
            target.append(f'Conducto {title}: {format_geometry(data.length)} mm · {format_geometry(data.volume)} cm³')
    w.motor2_page.refresh_context('\n'.join(two));w.motor4_page.refresh_context('\n'.join(four))
