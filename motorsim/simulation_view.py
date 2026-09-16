"""Simulación de referencia o copia del editor mediante QProcess asíncrono."""
import json
import math
from pathlib import Path
import sys
import tempfile
import time

from PySide6.QtCore import QPointF, QProcess, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QGridLayout,
    QComboBox, QLineEdit, QFormLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from .prototype import memory_mib, write_json
from .reference_results import ResultError, load_result, new_output_path, reference_inputs, project_inputs
from .project import Project, ProjectError
from .simulation import TWO_LAYOUT, FOUR_LAYOUT
from .project_case import configuration_key, validate_rpm
from .sweep import plan_rpms, load_sweep, write_index
from .sweep_view import SweepDialog
from .comparison_view import ComparisonDialog
from .external_view import ExternalDialog
from .runtime import worker_command, diagnostic


class PressurePlot(QWidget):
    def __init__(self, pv=False):
        super().__init__()
        self.pv, self.points = pv, []
        self.layout = TWO_LAYOUT
        self.setMinimumHeight(270)
        self.setMinimumWidth(260)
        self.setAccessibleName('Presión-volumen en orden temporal' if pv else 'Presión absoluta frente al ángulo continuo')

    def set_rows(self, rows, layout=TWO_LAYOUT):
        self.layout=layout
        # No ordenar V ni aplicar módulo a ángulos: preservar la trayectoria.
        origin = rows[0]['angle_deg']-(0 if layout.period==720 else 180) if rows else 0
        self.points = [(r['V_m3'][layout.cylinder]*1e6 if self.pv else r['angle_deg']-origin,
                        r['p_T_Y'][layout.cylinder][0]/1000) for r in rows]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor('#b4d9f5'))
        fm = p.fontMetrics()
        line = fm.height()+5
        title = 'Presión–volumen · orden temporal' if self.pv else f'Presión–ángulo · ciclo {self.layout.period}°'
        p.drawText(QRectF(8, 4, self.width()-16, line), title)
        p.drawText(QRectF(8, line+4, self.width()-16, line), 'Presión absoluta [kPa]')
        if not self.points:
            p.drawText(QRectF(8, 3*line, self.width()-16, line*2), Qt.TextFlag.TextWordWrap,
                       'Sin ciclo convergido para mostrar.')
            return
        xs, ys = zip(*self.points)
        lo, hi = (0., max(xs)*1.05) if self.pv else ((0.,720.) if self.layout.period==720 else (180.,540.))
        top = max(ys)*1.05
        margin = max(55, fm.horizontalAdvance(f'{top:.0f}')+12)
        box = QRectF(margin, 2*line+12, max(1, self.width()-margin-24), max(1, self.height()-5*line-20))
        p.setPen(QColor('#61758f'))
        p.drawLine(box.topLeft(), box.bottomLeft())
        p.drawLine(box.bottomLeft(), box.bottomRight())
        for fraction in (0, .5, 1):
            y = box.bottom()-box.height()*fraction
            p.drawText(QRectF(0, y-line/2, margin-7, line), Qt.AlignmentFlag.AlignRight, f'{top*fraction:.0f}')
            x = box.left()+box.width()*fraction
            caption = f'{lo+(hi-lo)*fraction:.0f}'
            if not self.pv:
                caption += '\n'+('PMS' if self.layout.period==720 or fraction == .5 else 'PMI')
            p.drawText(QRectF(x-28, box.bottom()+5, 56, line*2), Qt.AlignmentFlag.AlignHCenter, caption)
        path = QPainterPath()
        for i, (x, y) in enumerate(self.points):
            point = QPointF(box.left()+(x-lo)/(hi-lo)*box.width(), box.bottom()-y/top*box.height())
            path.moveTo(point) if i == 0 else path.lineTo(point)
        p.setPen(QPen(QColor('#69baf0'), 2))
        p.drawPath(path)
        p.drawText(QRectF(margin, self.height()-line, box.width(), line), Qt.AlignmentFlag.AlignCenter,
                   'Volumen del cilindro [cm³]' if self.pv else 'Ángulo continuo del ciclo [°]')


class SimulationView(QScrollArea):
    idle = Signal()

    def __init__(self, project_snapshot=None):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.process = None
        self.result = None
        self.output = None
        self.cancel_requested = False
        self.forced = False
        self._buffer = b''
        self._stderr = b''
        self._started = 0.
        self.completed_cycles = 0
        self.inputs = reference_inputs()
        self.project_snapshot = project_snapshot
        self._request_path = None
        self.sweep = None
        self.sweep_dialog = None
        self._running_sweep = False
        self._point_started = 0.
        self._point_caption = ""
        self._captured_rpms = [3000]
        self._series_id = None
        self._finished_manifest = None
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)
        def label(text, style=''):
            widget = QLabel(text)
            widget.setTextFormat(Qt.TextFormat.PlainText)
            widget.setWordWrap(True)
            widget.setObjectName(style)
            layout.addWidget(widget)
            return widget
        self.origin_combo = QComboBox()
        self.origin_combo.addItems(['Caso de referencia S2T-0D-01', 'Proyecto actual, con condiciones de referencia', 'Caso de referencia S4T-0D-01'])
        self.origin_combo.setAccessibleName('Origen de la próxima ejecución')
        layout.addWidget(self.origin_combo)
        self.options = QWidget()
        form = QFormLayout(self.options)
        self.mode_combo = QComboBox();self.mode_combo.addItems(['Punto individual','Barrido corto'])
        self.rpm_edit = QLineEdit('3000')
        self.start_rpm_edit, self.end_rpm_edit, self.step_rpm_edit = QLineEdit('2500'), QLineEdit('3500'), QLineEdit('500')
        form.addRow('Ejecución',self.mode_combo)
        for title,edit in [('Punto [rpm]',self.rpm_edit),('Inicio [rpm]',self.start_rpm_edit),('Final [rpm]',self.end_rpm_edit),('Incremento [rpm]',self.step_rpm_edit)]:
            edit.setMaximumWidth(150);edit.setAccessibleName(title);form.addRow(title,edit)
        self.plan_label=QLabel();self.plan_label.setWordWrap(True);form.addRow(self.plan_label)
        layout.addWidget(self.options)
        self.options.setVisible(False)
        self.title_label = label('', 'pageTitle')
        self.description_label = label('')
        self.parameters_label = label('', 'sectionTitle')
        self.identity_label = label('')
        self.stale_label = label('', 'fieldError')
        actions = QHBoxLayout()
        self.run_button = QPushButton('&Ejecutar')
        self.cancel_button = QPushButton('&Cancelar')
        self.open_button = QPushButton('&Abrir resultado…')
        self.details_button = QPushButton('&Parámetros…')
        self.check_button = QPushButton('Compro&bar entradas')
        self.compare_button = QPushButton('Comparar resultados…')
        self.comparison_dialog = None
        preparation = QHBoxLayout()
        preparation.addWidget(self.check_button)
        preparation.addWidget(self.compare_button)
        self.sweep_button=QPushButton('Ver barrido…')
        self.open_sweep_button=QPushButton('Abrir barrido…')
        preparation.addWidget(self.sweep_button);preparation.addWidget(self.open_sweep_button)
        self.sweep_button.setEnabled(False)
        self.external_button=QPushButton('Datos externos…')
        self.external_dialog=None
        self.external_button.clicked.connect(self.show_external)
        preparation.addWidget(self.external_button)
        preparation.addStretch()
        layout.addLayout(preparation)
        for button in (self.run_button, self.cancel_button, self.open_button, self.details_button):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.cancel_button.setEnabled(False)
        self.state_label = label('Listo para ejecutar', 'sectionTitle')
        self.progress_label = label('Ciclos completos: 0 · Tiempo: 0,0 s', 'unit')
        self.error_label = label('', 'fieldError')
        self.summary_label = label('')
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.plots_grid = QGridLayout()
        self.angle_plot, self.pv_plot = PressurePlot(), PressurePlot(True)
        layout.addLayout(self.plots_grid)
        self.path_label = label('Cada ejecución se guarda en una carpeta nueva de MotorSim/Resultados.', 'unit')
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.memory_label = label('', 'unit')
        label('Modelo 0D con alzada idealizada (4T) y energía prescrita, sin validación experimental. Conductos: almacenamiento y restricciones, sin propagación de ondas ni acreditación de sintonía.', 'unit')
        layout.addStretch()
        self.setWidget(body)
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._tick)
        self.run_button.clicked.connect(self.start)
        self.cancel_button.clicked.connect(self.cancel)
        self.open_button.clicked.connect(self.open_result)
        self.details_button.clicked.connect(self.show_details)
        self.check_button.clicked.connect(self.check_inputs)
        self.compare_button.clicked.connect(self.show_comparison)
        self.origin_combo.currentIndexChanged.connect(self._origin_changed)
        self.sweep_button.clicked.connect(self.show_sweep)
        self.open_sweep_button.clicked.connect(self.open_sweep)
        self.mode_combo.currentIndexChanged.connect(self._options_changed)
        for edit in (self.rpm_edit,self.start_rpm_edit,self.end_rpm_edit,self.step_rpm_edit):
            edit.textChanged.connect(self._options_changed)
        self._options_changed()
        self._describe_inputs()
        self._arrange()

    def _rpms(self):
        def integer(edit):
            value=edit.text().strip()
            if not value or not value.isascii() or not value.isdigit():
                raise ProjectError('RPM e incremento: ingresá enteros, sin separadores ni unidades.')
            return int(value)
        if self.mode_combo.currentIndex()==0:
            return [validate_rpm(integer(self.rpm_edit))]
        return plan_rpms(integer(self.start_rpm_edit),integer(self.end_rpm_edit),integer(self.step_rpm_edit))

    def _options_changed(self):
        sweep=self.mode_combo.currentIndex()==1
        self.rpm_edit.setEnabled(not sweep)
        for edit in (self.start_rpm_edit,self.end_rpm_edit,self.step_rpm_edit):edit.setEnabled(sweep)
        try:self.plan_label.setText('Lista exacta: '+', '.join(map(str,self._rpms()))+' rpm')
        except ProjectError as exc:self.plan_label.setText(str(exc))
        self.project_changed()

    def show_sweep(self):
        if not self.sweep or self.active:return
        if self.sweep_dialog is None:self.sweep_dialog=SweepDialog(self,self._display)
        self.sweep_dialog.set_sweep(self.sweep)
        self.sweep_dialog.show();self.sweep_dialog.raise_();self.sweep_dialog.activateWindow()

    def open_sweep(self,checked=False,*,path=None):
        if self.active:return
        if path is None:
            path,_=QFileDialog.getOpenFileName(self,'Abrir barrido','','Índice (series.json)')
        if not path:return
        try:loaded=load_sweep(path)
        except ResultError as exc:self.error_label.setText(str(exc));return
        self.sweep=loaded;self.result=None;self.inputs=loaded['index']['common_inputs']
        self._describe_inputs();self.angle_plot.set_rows([]);self.pv_plot.set_rows([])
        self.summary_label.clear();self.error_label.clear()
        self.state_label.setText('Barrido: '+loaded['index']['reason'])
        self.progress_label.setText(f"Integración de la serie: {loaded['index']['integration_seconds']:.3f} s")
        self.path_label.setText(str(loaded['path']));self.sweep_button.setEnabled(True)
        self.show_sweep()

    def show_external(self):
        if self.external_dialog is None:self.external_dialog=ExternalDialog(self)
        self.external_dialog.show();self.external_dialog.raise_();self.external_dialog.activateWindow()

    def show_comparison(self):
        if self.comparison_dialog is None:
            self.comparison_dialog = ComparisonDialog(self)
        self.comparison_dialog.show()
        self.comparison_dialog.raise_()
        self.comparison_dialog.activateWindow()

    def _capture(self):
        if self.origin_combo.currentIndex() != 1:
            return reference_inputs('4T' if self.origin_combo.currentIndex()==2 else '2T')
        if self.project_snapshot is None:
            raise ProjectError('No hay editor de proyecto disponible.')
        project, origin = self.project_snapshot()
        return project_inputs(project, origin, rpm=self._rpms()[0])

    def check_inputs(self):
        try:
            inputs = self._capture()
        except (ProjectError, ResultError) as exc:
            self.error_label.setText(str(exc))
            return
        self.error_label.setText('Entradas admitidas para este modelo. La convergencia no está garantizada.')
        if self.result is None and self.sweep is None and not self.active:
            self.inputs = inputs
            self._describe_inputs()

    def _origin_changed(self):
        self.options.setVisible(self.origin_combo.currentIndex()==1)
        # La selección prepara la próxima ejecución; no cambia la procedencia de evidencia abierta.
        if self.result is None and self.sweep is None and not self.active:
            try:
                self.inputs = self._capture()
                self.error_label.clear()
                self._describe_inputs()
            except (ProjectError, ResultError) as exc:
                self.error_label.setText(str(exc))
                self.title_label.setText('Geometría del proyecto · ensayo 0D')
                self.description_label.setText('Las condiciones son supuestos de referencia, no mediciones ni una calibración del motor ingresado.')
                self.parameters_label.clear()
                self.identity_label.clear()

    def _describe_inputs(self):
        origin = self.inputs.get('origin')
        self.title_label.setText('Geometría del proyecto · ensayo 0D' if origin else 'Caso de referencia '+self.inputs['case']['identifier'])
        self.description_label.setText('Las condiciones son supuestos de referencia, no mediciones ni una calibración del motor ingresado.'
            if origin else 'Caso sintético, no motor medido. No utiliza los datos del proyecto abierto.')
        case = self.inputs['case']
        geometry = case['project_geometry']
        regime = f"{geometry['cycle']} · {case['rpm']:g} rpm"
        if self.active and self._running_sweep:regime='Barrido '+', '.join(map(str,self._captured_rpms))+' rpm'
        elif self.sweep and self.result is None:regime='Barrido '+', '.join(map(str,self.sweep['index']['rpms']))+' rpm'
        self.parameters_label.setText(f"{regime} · {geometry['bore_mm']:g} × {geometry['stroke_mm']:g} mm · "
            f"Compresión {geometry['compression_ratio']:g}:1 · Banda {self.inputs['variant']['delta_p_Pa']} Pa · Perfil {self.inputs['profile']['name']}")
        self.identity_label.setText((f"Proyecto utilizado: {origin['project_name']} · "
            + ('con cambios sin guardar' if origin['dirty'] else 'sin cambios pendientes')
            + f"\nArchivo al ejecutar: {origin['source_path'] or 'sin archivo asociado'}") if origin else '')
        self.project_changed()

    def project_changed(self):
        stale = False
        if self.inputs.get('origin') and (self.active or self.result is not None or self.sweep is not None):
            try:
                current, origin = self.project_snapshot()
                stale = (configuration_key(current) != configuration_key(Project.from_dict(self.inputs['project_snapshot']))
                         or origin['source_path'] != self.inputs['origin']['source_path'])
                expected = (self._captured_rpms if self.active else
                    (self.sweep['index']['rpms'] if self.sweep and (self.result is None or
                        self.inputs.get('series_context',{}).get('series_id')==self.sweep['index']['series_id']) else [self.inputs['case']['rpm']]))
                stale = stale or self._rpms() != expected
            except (ProjectError, TypeError):
                stale = True
        self.stale_label.setText('El resultado corresponde a una configuración anterior' if stale else '')
        if self.sweep_dialog:self.sweep_dialog.stale_label.setText(self.stale_label.text())

    @property
    def active(self):
        return self.process is not None

    def _arrange(self):
        wide = self.viewport().width() >= 850
        self.plots_grid.addWidget(self.angle_plot, 0, 0)
        self.plots_grid.addWidget(self.pv_plot, 0 if wide else 1, 1 if wide else 0)
        self.plots_grid.setColumnStretch(0, 1)
        self.plots_grid.setColumnStretch(1, 1 if wide else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'plots_grid'):
            self._arrange()

    def show_details(self):
        if self.result is None and self.sweep is None and not self.active:
            try:
                self.inputs = self._capture()
                self._describe_inputs()
            except (ProjectError, ResultError) as exc:
                self.error_label.setText(str(exc))
                return
        dialog = QDialog(self)
        dialog.setWindowTitle('Parámetros efectivos · solo lectura')
        dialog.resize(680, 540)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(json.dumps(self.inputs, ensure_ascii=False, indent=2))
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def start(self, checked=False, *, output=None):
        if self.active:
            return
        try:
            inputs = self._capture()
            executable,prefix,working_directory=worker_command()
            rpms = self._rpms() if 'origin' in inputs else [3000]
            running_sweep = len(rpms)>1
            target = Path(output) if output is not None else new_output_path()
            if target.exists():raise ProjectError('El destino ya existe; elegí una carpeta nueva. No se sobrescriben resultados.')
            request = None
            if 'origin' in inputs:
                target.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', prefix='motorsim-input-',
                        suffix='.json', dir=target.parent, delete=False) as stream:
                    request = Path(stream.name)
                    json.dump(dict(common_inputs=inputs,rpms=rpms) if running_sweep else inputs, stream, ensure_ascii=False, allow_nan=False)
        except (OSError, ProjectError, ResultError) as exc:
            self.error_label.setText(str(exc))
            return
        self.inputs = inputs
        self.sweep = None
        self._series_id = None
        self._finished_manifest = None
        self._running_sweep = running_sweep
        self._captured_rpms = rpms
        self._point_caption = ""
        if self.sweep_dialog:self.sweep_dialog.hide()
        self._request_path = request
        self._describe_inputs()
        self.output = target
        self.result = None
        self.angle_plot.set_rows([])
        self.pv_plot.set_rows([])
        self.summary_label.clear()
        self.error_label.clear()
        self.memory_label.clear()
        self._buffer = self._stderr = b''
        self.cancel_requested = self.forced = False
        self.completed_cycles = 0
        self._started = self._point_started = time.monotonic()
        self.state_label.setText('En ejecución')
        self.progress_label.setText('Ciclos completos: 0 · Esperando avance del cálculo…')
        self.path_label.setText(str(self.output))
        self.run_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.origin_combo.setEnabled(False)
        self.check_button.setEnabled(False)
        self.options.setEnabled(False)
        self.open_sweep_button.setEnabled(False)
        self.sweep_button.setEnabled(False)
        process = QProcess(self)
        self.process = process
        process.setWorkingDirectory(working_directory)
        process.setProgram(executable)
        arguments = [*prefix, '--output', str(self.output), '--control-stdin', '--cycle', self.inputs['case']['project_geometry']['cycle']]
        if request:
            arguments += ['--sweep-input' if running_sweep else '--project-input', str(request)]
        process.setArguments(arguments)
        process.readyReadStandardOutput.connect(self._read_progress)
        process.readyReadStandardError.connect(self._read_error)
        process.finished.connect(self._finished)
        process.errorOccurred.connect(self._process_error)
        self.timer.start()
        process.start()
        self._describe_inputs()

    def _read_error(self):
        if self.process:
            self._stderr = (self._stderr+bytes(self.process.readAllStandardError()))[-8192:]

    def _read_progress(self):
        if not self.process:
            return
        self._buffer += bytes(self.process.readAllStandardOutput())
        while b'\n' in self._buffer:
            line, self._buffer = self._buffer.split(b'\n', 1)
            try:
                data = json.loads(line)
                if data.get('event') == 'sweep_started':
                    self._series_id=data['series_id']
                elif data.get('event') == 'finished':
                    self._finished_manifest=Path(data['manifest']).resolve()
                elif data.get('event') == 'point_start':
                    self._point_started=time.monotonic()
                    self._point_caption=f"Punto {data['point_index']+1}/{data['point_total']} · {data['rpm']} rpm · "
                    self.progress_label.setText(self._point_caption+'Iniciando…')
                elif data.get('event') == 'progress':
                    count, seconds = data['completed_cycles'], data['seconds']
                    if type(count) is int and 0 <= count <= 30 and math.isfinite(seconds) and seconds >= 0:
                        self.completed_cycles = count
                        self.progress_label.setText(self._point_caption+f'Ciclos completos: {count} · Integración: {seconds:.1f} s · RHS: {data["rhs"]}')
                elif data.get('event') == 'error':
                    self._stderr += str(data.get('message', '')).encode('utf-8')
            except (ValueError, KeyError, TypeError):
                self.error_label.setText('Se recibió un mensaje de avance ilegible.')
        self._buffer = self._buffer[-8192:]

    def _tick(self):
        elapsed = time.monotonic()-self._started
        self.memory_label.setText(f'Tiempo de serie/ejecución: {elapsed:.1f} s · Punto: {time.monotonic()-self._point_started:.1f} s · Pico de interfaz: {memory_mib():.1f} MiB (proceso separado)')
        # Límite de supervisión, no ampliación de los 60 s de integración del hijo.
        if time.monotonic()-self._point_started >= 65 and not self.cancel_requested:
            self.cancel()

    def cancel(self):
        if not self.active or self.cancel_requested:
            return
        self.cancel_requested = True
        self.cancel_button.setEnabled(False)
        self.state_label.setText('Cancelando…')
        process = self.process
        process.write(b'cancel\n')
        QTimer.singleShot(3000, lambda: self._kill_if_active(process))

    def _kill_if_active(self, process):
        if self.process is process:
            self.forced = True
            self.error_label.setText('El cálculo no respondió a la cancelación; se detuvo el proceso.')
            process.kill()

    def _process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.error_label.setText('No se pudo iniciar el auxiliar de cálculo: '+self.process.errorString())
            self._save_error_diagnostic()
            self._finish_cleanup('Error de ejecución')

    def _save_error_diagnostic(self):
        try:
            path=diagnostic(self.error_label.text()+'\n'+self._stderr.decode('utf-8',errors='replace'))
            self.error_label.setText(self.error_label.text()+f'\nDiagnóstico: {path}')
        except OSError as exc:
            self.error_label.setText(self.error_label.text()+f'\nNo se pudo guardar diagnóstico: {exc}')

    def _finished(self, code, exit_status):
        self._read_progress()
        self._read_error()
        if self._running_sweep:
            try:
                if self._series_id is None:raise ResultError('El proceso no confirmó una carpeta de serie propia.')
                loaded=load_sweep(self.output/'series.json')
                if loaded['index']['series_id']!=self._series_id:raise ResultError('Índice ajeno a la ejecución iniciada.')
                if loaded['index']['state']=='running':
                    reason='Cancelación forzada' if self.cancel_requested else 'El proceso terminó sin cerrar la serie'
                    loaded['index'].update(state='cancelled' if self.cancel_requested else 'stopped',reason=reason)
                    for point in loaded['index']['points']:
                        if point['state']=='running':point.update(state='error',reason=reason)
                        elif point['state']=='not_executed':point['reason']='No ejecutado: '+reason
                if loaded['index']['state']=='converged' and (code!=0 or exit_status!=QProcess.ExitStatus.NormalExit):
                    raise ResultError('Salida del proceso incompatible con un barrido convergido.')
                loaded['index']['interface_wall_seconds']=time.monotonic()-self._started
                write_index(self.output,loaded['index'])
                self.sweep=loaded;self.result=None
                self.state_label.setText('Barrido: '+loaded['index']['reason'])
                self.progress_label.setText(f"Integración total: {loaded['index']['integration_seconds']:.3f} s")
                self._finish_cleanup()
                if self.window().isEnabled():self.show_sweep()
                self.project_changed()
            except (ResultError,OSError) as exc:
                self.error_label.setText(str(exc)+' '+self._stderr.decode('utf-8',errors='replace')[:2000])
                self._save_error_diagnostic()
                self._finish_cleanup('Cancelado / índice incompleto' if self.cancel_requested else 'Error de barrido')
            return
        if self.cancel_requested:
            try:
                result = load_result(self.output/'manifest.json')
                if result['status'] == 'cancelled':
                    self._display(result)
            except ResultError:
                pass  # Puede no existir un manifiesto si hubo parada forzada.
            self._finish_cleanup('Cancelado')
            self.summary_label.setText('Diagnóstico no aceptado. La ejecución fue cancelada.')
            return
        try:
            if exit_status != QProcess.ExitStatus.NormalExit:
                raise ResultError('El proceso de cálculo terminó inesperadamente.')
            result = load_result(self.output/'manifest.json')
            if result['status'] == 'converged' and code != 0:
                raise ResultError('Código de salida incompatible con el resultado.')
            if result['manifest']['version']>=3 and self._finished_manifest==result['path'] and 'timings' in result['manifest']:
                result['manifest']['timings']['interface_wall_seconds']=time.monotonic()-self._started
                write_json(result['path'],result['manifest'])
            self._display(result)
            self._finish_cleanup()
        except (ResultError,OSError) as exc:
            self.error_label.setText(str(exc)+' '+self._stderr.decode('utf-8', errors='replace')[:2000])
            self._save_error_diagnostic()
            self._finish_cleanup('Error de ejecución o resultado ilegible')

    def _finish_cleanup(self, state=None):
        process, self.process = self.process, None
        if process:
            process.deleteLater()
        self.timer.stop()
        if state:
            self.state_label.setText(state)
        self.run_button.setEnabled(True)
        self.open_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.origin_combo.setEnabled(True)
        self.check_button.setEnabled(True)
        self.options.setEnabled(True)
        self.open_sweep_button.setEnabled(True)
        self.sweep_button.setEnabled(self.sweep is not None)
        if self._request_path:
            try:
                self._request_path.unlink(missing_ok=True)
            except OSError as exc:
                self.error_label.setText(f'No se pudo retirar la copia temporal {self._request_path}: {exc}')
            self._request_path = None
        self.idle.emit()

    def _display(self, result):
        self.result = result
        self.inputs = result['inputs']
        self._describe_inputs()
        state = result['status']
        r = result['result']
        self.state_label.setText(dict(converged='Convergencia numérica alcanzada', cancelled='Cancelado',
            not_converged='Sin convergencia / presupuesto agotado', error='Error de ejecución')[state])
        self.progress_label.setText(f'Ciclos completos: {len(r["cycles"])} · Integración: {r["seconds"]:.3f} s')
        self.memory_label.setText(f'Pico del cálculo: {r["peak_process_MiB"]:.1f} MiB · Pico de interfaz: {memory_mib():.1f} MiB')
        timing=result['manifest'].get('timings')
        if timing:
            self.memory_label.setText(self.memory_label.text()+f" · Preparación: {timing['setup_seconds']:.3f} s · Escritura: {timing['writing_seconds']:.3f} s · Total del punto: {timing['wall_seconds']:.3f} s"+
                (f" · Percibido: {timing['interface_wall_seconds']:.3f} s" if 'interface_wall_seconds' in timing else ''))
        self.path_label.setText(str(result['path']))
        self.angle_plot.set_rows([])
        self.pv_plot.set_rows([])
        if state == 'converged':
            cycle = r['cycles'][-1]
            worst = max(v for b in cycle['independent'].values() for v in b['normalized_m_u_f'])
            self.summary_label.setText(
                f'Último ciclo completo: {cycle["cycle"]} · Trabajo indicado: {cycle["W_C_J"]:.6f} J/ciclo\n'+
                (f'Cárter (diagnóstico): {cycle["W_K_J"]:.6f} J/ciclo · ' if 'W_K_J' in cycle else 'Ciclo 720° · ')+
                f'Presión máxima: {cycle["p_max_Pa"]/1000:.3f} kPa abs.\n'+
                f'Balances aprobados · Mayor residuo independiente: {100*worst:.6f} % (límite 0,1 %)\n'
                f'Parada: {r["stop"]}. Esta ejecución individual no comprueba sensibilidad.')
            layout=FOUR_LAYOUT if self.inputs['case']['project_geometry']['cycle']=='4T' else TWO_LAYOUT
            self.summary_label.setText(self.summary_label.text()+'\nFracciones frescas: '+', '.join(f'{name}={y:.8f}' for name,y in zip(layout.cv,cycle['Y'])))
            rows = result['samples']['cycles'][-1]
            self.angle_plot.set_rows(rows,layout)
            self.pv_plot.set_rows(rows,layout)
        else:
            self.summary_label.setText(f'Diagnóstico no aceptado. Motivo: {r["stop"]}.\n'
                                       'Los datos parciales se conservan en la carpeta; no se presentan como ciclo aceptado.')

    def open_result(self, checked=False, *, path=None):
        if self.active:
            return
        if path is None:
            name, _ = QFileDialog.getOpenFileName(self, 'Abrir resultado de simulación',
                str(new_output_path().parent), 'Manifiesto (manifest.json)')
            if not name:
                return
            path = Path(name)
        try:
            result = load_result(path)
        except ResultError as exc:
            self.error_label.setText(str(exc)+(' Se conserva el resultado previamente abierto.' if self.result else ''))
            return
        self.error_label.clear()
        self._display(result)
