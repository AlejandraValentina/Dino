"""Pestaña del caso de referencia; QProcess asíncrono, independiente del editor."""
import json
import math
from pathlib import Path
import sys
import time

from PySide6.QtCore import QPointF, QProcess, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QGridLayout,
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from .prototype import memory_mib
from .reference_results import ResultError, load_result, new_output_path, reference_inputs


class PressurePlot(QWidget):
    def __init__(self, pv=False):
        super().__init__()
        self.pv, self.points = pv, []
        self.setMinimumHeight(270)
        self.setMinimumWidth(260)
        self.setAccessibleName('Presión-volumen en orden temporal' if pv else 'Presión absoluta frente al ángulo continuo')

    def set_rows(self, rows):
        # No ordenar V ni aplicar módulo a ángulos: preservar la trayectoria.
        origin = rows[0]['angle_deg']-180 if rows else 0
        self.points = [(r['V_m3'][2]*1e6 if self.pv else r['angle_deg']-origin,
                        r['p_T_Y'][2][0]/1000) for r in rows]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor('#b4d9f5'))
        fm = p.fontMetrics()
        line = fm.height()+5
        title = 'Presión–volumen · orden temporal' if self.pv else 'Presión–ángulo · PMI → PMS → PMI'
        p.drawText(QRectF(8, 4, self.width()-16, line), title)
        p.drawText(QRectF(8, line+4, self.width()-16, line), 'Presión absoluta [kPa]')
        if not self.points:
            p.drawText(QRectF(8, 3*line, self.width()-16, line*2), Qt.TextFlag.TextWordWrap,
                       'Sin ciclo convergido para mostrar.')
            return
        xs, ys = zip(*self.points)
        lo, hi = (0., max(xs)*1.05) if self.pv else (180., 540.)
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
                caption += '\n'+('PMS' if fraction == .5 else 'PMI')
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

    def __init__(self):
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
        label('Caso de referencia S2T-0D-01', 'pageTitle')
        label('Caso sintético, no motor medido. Ejecuta el caso de referencia. No utiliza los datos del proyecto abierto.')
        case = self.inputs['case']
        geometry = case['project_geometry']
        label(f"{case['rpm']:g} rpm · {geometry['bore_mm']:g} × {geometry['stroke_mm']:g} mm · "
              f"Compresión {geometry['compression_ratio']:g}:1 · Banda {self.inputs['variant']['delta_p_Pa']} Pa · "
              f"Perfil {self.inputs['profile']['name']}", 'sectionTitle')
        actions = QHBoxLayout()
        self.run_button = QPushButton('&Ejecutar')
        self.cancel_button = QPushButton('&Cancelar')
        self.open_button = QPushButton('&Abrir resultado…')
        self.details_button = QPushButton('&Parámetros…')
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
        label('Modelo 0D con energía prescrita; sin ondas de escape ni validación experimental.', 'unit')
        layout.addStretch()
        self.setWidget(body)
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._tick)
        self.run_button.clicked.connect(self.start)
        self.cancel_button.clicked.connect(self.cancel)
        self.open_button.clicked.connect(self.open_result)
        self.details_button.clicked.connect(self.show_details)
        self._arrange()

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
        self.output = Path(output) if output is not None else new_output_path()
        self.result = None
        self.angle_plot.set_rows([])
        self.pv_plot.set_rows([])
        self.summary_label.clear()
        self.error_label.clear()
        self.memory_label.clear()
        self._buffer = self._stderr = b''
        self.cancel_requested = self.forced = False
        self.completed_cycles = 0
        self._started = time.monotonic()
        self.state_label.setText('En ejecución')
        self.progress_label.setText('Ciclos completos: 0 · Esperando avance del cálculo…')
        self.path_label.setText(str(self.output))
        self.run_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        process = QProcess(self)
        self.process = process
        process.setWorkingDirectory(str(Path(__file__).resolve().parent.parent))
        executable = Path(sys.executable)
        if executable.name.lower() == 'pythonw.exe':
            executable = executable.with_name('python.exe')
        process.setProgram(str(executable))
        process.setArguments(['-u', '-m', 'motorsim.reference_run', '--output', str(self.output), '--control-stdin'])
        process.readyReadStandardOutput.connect(self._read_progress)
        process.readyReadStandardError.connect(self._read_error)
        process.finished.connect(self._finished)
        process.errorOccurred.connect(self._process_error)
        self.timer.start()
        process.start()

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
                if data.get('event') == 'progress':
                    count, seconds = data['completed_cycles'], data['seconds']
                    if type(count) is int and 0 <= count <= 30 and math.isfinite(seconds) and seconds >= 0:
                        self.completed_cycles = count
                        self.progress_label.setText(f'Ciclos completos: {count} · Integración: {seconds:.1f} s · RHS: {data["rhs"]}')
            except (ValueError, KeyError, TypeError):
                self.error_label.setText('Se recibió un mensaje de avance ilegible.')
        self._buffer = self._buffer[-8192:]

    def _tick(self):
        elapsed = time.monotonic()-self._started
        self.memory_label.setText(f'Tiempo de ejecución: {elapsed:.1f} s · Pico de interfaz: {memory_mib():.1f} MiB (proceso separado)')
        # Límite de supervisión, no ampliación de los 60 s de integración del hijo.
        if elapsed >= 65 and not self.cancel_requested:
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
            self.error_label.setText('No se pudo iniciar Python: '+self.process.errorString())
            self._finish_cleanup('Error de ejecución')

    def _finished(self, code, exit_status):
        self._read_progress()
        self._read_error()
        if self.cancel_requested:
            self._finish_cleanup('Cancelado')
            self.summary_label.setText('Diagnóstico no aceptado. La ejecución fue cancelada.')
            return
        try:
            if exit_status != QProcess.ExitStatus.NormalExit:
                raise ResultError('El proceso de cálculo terminó inesperadamente.')
            result = load_result(self.output/'manifest.json')
            if result['status'] == 'converged' and code != 0:
                raise ResultError('Código de salida incompatible con el resultado.')
            self._display(result)
            self._finish_cleanup()
        except ResultError as exc:
            self.error_label.setText(str(exc)+' '+self._stderr.decode('utf-8', errors='replace')[:2000])
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
        self.idle.emit()

    def _display(self, result):
        self.result = result
        state = result['status']
        r = result['result']
        self.state_label.setText(dict(converged='Convergencia numérica alcanzada', cancelled='Cancelado',
            not_converged='Sin convergencia / presupuesto agotado', error='Error de ejecución')[state])
        self.progress_label.setText(f'Ciclos completos: {len(r["cycles"])} · Integración: {r["seconds"]:.3f} s')
        self.memory_label.setText(f'Pico del cálculo: {r["peak_process_MiB"]:.1f} MiB · Pico de interfaz: {memory_mib():.1f} MiB')
        self.path_label.setText(str(result['path']))
        self.angle_plot.set_rows([])
        self.pv_plot.set_rows([])
        if state == 'converged':
            cycle = r['cycles'][-1]
            worst = max(v for b in cycle['independent'].values() for v in b['normalized_m_u_f'])
            self.summary_label.setText(
                f'Último ciclo completo: {cycle["cycle"]} · Trabajo indicado: {cycle["W_C_J"]:.6f} J/ciclo\n'
                f'Cárter (diagnóstico): {cycle["W_K_J"]:.6f} J/ciclo · Presión máxima: {cycle["p_max_Pa"]/1000:.3f} kPa abs.\n'
                f'Balances aprobados · Mayor residuo independiente: {100*worst:.6f} % (límite 0,1 %)\n'
                f'Parada: {r["stop"]}. Esta ejecución individual no comprueba sensibilidad.')
            rows = result['samples']['cycles'][-1]
            self.angle_plot.set_rows(rows)
            self.pv_plot.set_rows(rows)
        else:
            self.summary_label.setText(f'Diagnóstico no aceptado. Motivo: {r["stop"]}.\n'
                                       'Los datos parciales se conservan en la carpeta; no se presentan como ciclo aceptado.')

    def open_result(self, checked=False, *, path=None):
        if self.active:
            return
        if path is None:
            name, _ = QFileDialog.getOpenFileName(self, 'Abrir resultado del caso de referencia',
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
