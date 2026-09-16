"""Automatización externa UIA/teclado del EXE: no se incorpora al paquete.

Etapas separadas para repetir únicamente comprobaciones afectadas. Las numéricas
rechazan destinos existentes y usan un presupuesto compartido de 300 s.
"""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import time

import win32con
import win32gui
import win32process
from pywinauto.uia_element_info import UIAElementInfo
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.keyboard import send_keys

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--exe',type=Path,required=True)
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--stage',choices=['editor','numerical','history','cancel','missing'],required=True)
args=parser.parse_args();exe=args.exe.resolve();work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from motorsim.reference_results import load_result
from motorsim.sweep import load_sweep

env=os.environ.copy()
for key in ('PYTHONPATH','PYTHONHOME','VIRTUAL_ENV','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH'):
    env.pop(key,None)
env.update(PATH=os.environ['SystemRoot']+'\\System32;'+os.environ['SystemRoot'],
    QT_SCALE_FACTOR='1.5',QT_QPA_PLATFORM='windows',LOCALAPPDATA=str(work/'Datos'))
cwd=work/'Directorio distinto';cwd.mkdir(exist_ok=True)
process=subprocess.Popen([str(exe)],cwd=cwd,env=env)
checks=[];workers=[];screens=[]
def note(text):checks.append(text);print('PASS',text,flush=True)
def wait(fn,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        result=fn()
        if result:return result
        time.sleep(.15)
    raise RuntimeError('Tiempo agotado: '+getattr(fn,'__name__','condición'))
def windows():
    found=[]
    def visit(h,_):
        if win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1]==process.pid:
            found.append((h,win32gui.GetWindowText(h)))
    win32gui.EnumWindows(visit,None);return found
def window(fragment):
    h=wait(lambda:next((h for h,title in windows() if fragment in title),None))
    return UIAWrapper(UIAElementInfo(h))
def front(w,width=1350,height=800):
    win32gui.ShowWindow(w.handle,win32con.SW_RESTORE)
    win32gui.SetWindowPos(w.handle,win32con.HWND_TOPMOST,20,20,width,height,win32con.SWP_SHOWWINDOW)
    try:win32gui.SetForegroundWindow(w.handle)
    except Exception:pass
def control(w,kind,name=None,suffix=None):
    return wait(lambda:next((x for x in w.descendants() if x.element_info.control_type==kind
        and (name is None or x.window_text()==name)
        and (suffix is None or x.element_info.automation_id.endswith(suffix))),None))
def button(w,name):
    # Invoke se bloquea en algunos diálogos modales Qt; teclado conserva el flujo real.
    b=control(w,'Button',name);b.set_focus();send_keys('{SPACE}');time.sleep(.2)
def tab(w,name):control(w,'TabItem',name).select();time.sleep(.2)
def combo(w,name,index):
    if name in ('Tipo de motor','Ejecución'):
        c=[x for x in w.descendants() if x.element_info.control_type=='ComboBox'][0 if name=='Tipo de motor' else 1]
    else:c=control(w,'ComboBox',name)
    c.set_focus();send_keys('{HOME}'+('{DOWN}'*index)+'{TAB}');time.sleep(.2)
def texts(w):return '\n'.join(x.window_text() for x in w.descendants() if x.element_info.control_type=='Text')
def file_dialog(fragment,path):
    d=window(fragment)
    edits=[x for x in d.descendants() if x.element_info.control_type=='Edit']
    e=next((x for x in edits if x.element_info.automation_id.endswith('fileNameEdit') or x.element_info.automation_id=='1148'),None)
    if e is not None:e.set_edit_text(str(path));e.set_focus()
    else:
        # Campo de nombre enfocado al abrir el diálogo nativo Windows.
        send_keys('^a');send_keys(str(path),with_spaces=True)
    send_keys('{ENTER}');time.sleep(.5)
def open_project(path):button(main,'Abrir');file_dialog('Abrir proyecto',path)
def save_as(path):button(main,'Guardar como');file_dialog('Guardar proyecto como',path)
def screenshot(w,name):
    from PySide6.QtWidgets import QApplication
    global capture_app
    capture_app=QApplication.instance() or QApplication([])
    front(w);time.sleep(.3);l,t,r,b=win32gui.GetWindowRect(w.handle)
    path=work/(name+'.png');pixels=capture_app.primaryScreen().grabWindow(0,l,t,r-l,b-t)
    assert pixels.save(str(path));screens.append(str(path));print('CAPTURE',path,flush=True)
def worker_paths():
    class Entry(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('usage',wintypes.DWORD),('pid',wintypes.DWORD),('heap',ctypes.c_size_t),
            ('module',wintypes.DWORD),('threads',wintypes.DWORD),('parent',wintypes.DWORD),('priority',wintypes.LONG),
            ('flags',wintypes.DWORD),('name',wintypes.WCHAR*260)]
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateToolhelp32Snapshot.restype=wintypes.HANDLE
    k.Process32FirstW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Entry)];k.Process32NextW.argtypes=k.Process32FirstW.argtypes
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.OpenProcess.restype=wintypes.HANDLE
    k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    snap=k.CreateToolhelp32Snapshot(2,0);e=Entry();e.size=ctypes.sizeof(e);found=[]
    try:
        valid=k.Process32FirstW(snap,ctypes.byref(e))
        while valid:
            if e.parent==process.pid:
                h=k.OpenProcess(0x1000,False,e.pid)
                try:
                    buf=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(buf))
                    if k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(size)):found.append((e.pid,buf.value))
                finally:k.CloseHandle(h)
            valid=k.Process32NextW(snap,ctypes.byref(e))
    finally:k.CloseHandle(snap)
    return found
def result_folders():
    root=work/'Datos/MotorSim/Resultados'
    return set(root.iterdir()) if root.exists() else set()
def start_calculation():
    before=result_folders();button(main,'Ejecutar')
    actual=wait(worker_paths)
    assert len(actual)==1 and Path(actual[0][1]).resolve()==exe.with_name('MotorSimWorker.exe')
    workers.extend(actual);note('Auxiliar real del paquete: '+actual[0][1])
    assert not control(main,'Button','Ejecutar').is_enabled()
    folder=wait(lambda:next((p for p in result_folders()-before if p.is_dir()),None))
    return folder
def account(folder):
    ledger_path=work/'budget.json'
    ledger=json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else dict(limit=300,seconds=0,runs=[])
    paths=[folder/'manifest.json'] if (folder/'manifest.json').exists() else [folder/p['result'] for p in json.loads((folder/'series.json').read_text(encoding='utf-8'))['points'] if p['result']]
    for path in paths:
        r=load_result(path);ledger['seconds']+=r['result']['seconds'];ledger['runs'].append(dict(path=str(path),status=r['status'],seconds=r['result']['seconds']))
    ledger_path.write_text(json.dumps(ledger,indent=2),encoding='utf-8');assert ledger['seconds']<=300
    return ledger
def finish_calculation(folder,series=False):
    wait(lambda:not worker_paths(),75 if not series else 140)
    wait(lambda:control(main,'Button','Ejecutar').is_enabled())
    account(folder)
    return load_sweep(folder/'series.json') if series else load_result(folder/'manifest.json')

try:
    main=window('MotorSim');front(main)
    note('GUI EXE directo, cwd distinto, PATH sistema, sin PYTHONPATH/VIRTUAL_ENV; factor Qt 1.5')
    if args.stage=='editor':
        control(main,'Edit',suffix='.project_name').set_edit_text('PRUEBA SINTÉTICA — cigüeñal á')
        button(main,'Guardar');file_dialog('Guardar proyecto como',work/'incompleto á.json')
        saved=json.loads((work/'incompleto á.json').read_text(encoding='utf-8'));assert saved['bore_mm'] is None
        note('Guardar incompleto con nombre/ruta Unicode')
        save_as(work/'copia ñ.json');assert (work/'copia ñ.json').exists();note('Guardar como')
        control(main,'Edit',suffix='.bore_mm').set_edit_text('inválido')
        button(main,'Guardar');button(window('MotorSim — Error'),'Aceptar')
        assert json.loads((work/'copia ñ.json').read_text(encoding='utf-8'))['bore_mm'] is None
        button(main,'Nuevo');button(window('Cambios pendientes'),'Cancelar')
        assert control(main,'Edit',suffix='.bore_mm').get_value()=='inválido'
        button(main,'Nuevo');button(window('Cambios pendientes'),'Descartar')
        note('Inválidos no guardados, Nuevo protegido por Cancelar/Descartar')
        open_project(exe.parent/'Ejemplos/EJEMPLO_SINTETICO_4T.json')
        combo(main,'Tipo de motor',0);combo(main,'Tipo de motor',1)
        save_as(work/'alternancia 4T.json')
        assert json.loads((work/'alternancia 4T.json').read_text(encoding='utf-8'))==json.loads((exe.parent/'Ejemplos/EJEMPLO_SINTETICO_4T.json').read_text(encoding='utf-8'))
        note('Abrir ejemplo y alternar 2T/4T sin pérdida')
        old=work/'antiguo v1.json';old.write_text(json.dumps(dict(format_version=1,name='ANTIGUO á',cycle='2T')),encoding='utf-8')
        open_project(old);save_as(work/'antiguo convertido.json')
        assert json.loads((work/'antiguo convertido.json').read_text(encoding='utf-8'))['format_version']==6
        assert json.loads(old.read_text())['format_version']==1
        open_project(exe.parent/'Ejemplos/EJEMPLO_SINTETICO_4T.json')
        note('Lectura v1 sin reescritura, conversión explícita v6')
        screenshot(main,'paquete-editor-150')
        front(main,1000,740)
        # Captura compacta sin restaurar el ancho grande.
        from PySide6.QtWidgets import QApplication
        capture_app=QApplication.instance() or QApplication([]);time.sleep(.3)
        l,t,r,b=win32gui.GetWindowRect(main.handle);path=work/'paquete-compacto-150.png'
        assert capture_app.primaryScreen().grabWindow(0,l,t,r-l,b-t).save(str(path));screens.append(str(path))
    elif args.stage=='numerical':
        if (work/'numerical.json').exists():raise RuntimeError('No repetir los puntos registrados.')
        ledger=work/'budget.json'
        if ledger.exists():assert json.loads(ledger.read_text())['seconds']+180<=300
        tab(main,'Simulación');first=start_calculation();two=finish_calculation(first)
        assert two['status']=='converged';note('Referencia 2T convergida')
        screenshot(main,'paquete-2t-150')
        open_project(exe.parent/'Ejemplos/EJEMPLO_SINTETICO_4T.json')
        tab(main,'Simulación');combo(main,'Origen de la próxima ejecución',1)
        # La segunda combo es modo de ejecución; selección por nombre accesible de formulario.
        combo(main,'Ejecución',1)
        control(main,'Edit','Final [rpm]').set_edit_text('3000')
        second=start_calculation();four=finish_calculation(second,True)
        assert four['index']['state']=='converged'
        dialog=window('Barrido de RPM');screenshot(dialog,'paquete-barrido-150');button(dialog,'Cerrar')
        paths=dict(two_stroke=str(first/'manifest.json'),four_stroke=str(second/'series.json'))
        (work/'numerical.json').write_text(json.dumps(paths,indent=2),encoding='utf-8')
        note('Barrido GUI 4T B2500/3000 convergido')
    elif args.stage=='cancel':
        tab(main,'Simulación');first=start_calculation()
        wait(lambda:'RHS:' in texts(main));button(main,'Cancelar')
        result=finish_calculation(first);assert result['status']=='cancelled'
        note('Cancelación cooperativa; diagnóstico no aceptado, sin hijo activo')
        second=start_calculation();wait(lambda:'RHS:' in texts(main))
        win32gui.PostMessage(main.handle,win32con.WM_CLOSE,0,0)
        process.wait(timeout=10);wait(lambda:not worker_paths());account(second)
        assert load_result(second/'manifest.json')['status']=='cancelled'
        note('Cierre durante cálculo sin huérfanos')
    elif args.stage=='missing':
        tab(main,'Simulación');button(main,'Ejecutar')
        assert 'Falta el auxiliar' in texts(main) and not worker_paths()
        note('Auxiliar ausente: error útil, botón disponible y sin cálculo ficticio')
    elif args.stage=='history':
        tab(main,'Simulación')
        source=Path(__file__).resolve().parents[1]/'results/simulacion-2t/cuatro-tiempos-20260916/R2'
        reference=work/'Historicos'
        if not reference.exists():
            for name in ('gui-sweep','gui-compression'):
                shutil.copytree(source/name,reference/name,ignore=shutil.ignore_patterns('attempts.csv'))
        button(main,'Abrir resultado…');file_dialog('Abrir resultado',reference/'gui-compression/manifest.json')
        assert 'Convergencia numérica alcanzada' in texts(main)
        note('Resultado 4T histórico reabierto')
        button(main,'Comparar resultados…');dialog=window('Comparar resultados')
        button(dialog,'Abrir resultado A…');file_dialog('Abrir resultado A',reference/'gui-sweep/point-02/manifest.json')
        button(dialog,'Abrir resultado B…');file_dialog('Abrir resultado B',reference/'gui-compression/manifest.json')
        assert 'Compatibles' in texts(dialog)
        screenshot(dialog,'paquete-comparacion-150')
        button(dialog,'Exportar CSV…');file_dialog('Crear carpeta nueva',work/'CSV comparación á')
        assert (work/'CSV comparación á/resumen.csv').exists()
        button(dialog,'Cerrar');note('Comparación y CSV sin reintegrar')
        button(main,'Abrir barrido…');file_dialog('Abrir barrido',reference/'gui-sweep/series.json')
        dialog=window('Barrido de RPM');button(dialog,'Exportar CSV…');file_dialog('Carpeta nueva para serie.csv',work/'CSV barrido á')
        assert (work/'CSV barrido á/serie.csv').exists();button(dialog,'Cerrar')
        note('Barrido histórico reabierto y exportado')
    if process.poll() is None:
        win32gui.PostMessage(main.handle,win32con.WM_CLOSE,0,0);process.wait(timeout=10)
    (work/(args.stage+'-evidence.json')).write_text(json.dumps(dict(stage=args.stage,exe=str(exe),
        cwd=str(cwd),pid=process.pid,workers=workers,qt_scale_factor='1.5',checks=checks,
        screenshots=screens,automated=True,manual_acceptance=False),ensure_ascii=False,indent=2),encoding='utf-8')
except Exception as exc:
    (work/(args.stage+'-failure.txt')).write_text(repr(exc),encoding='utf-8')
    print('FAILED',repr(exc),flush=True)
    raise
