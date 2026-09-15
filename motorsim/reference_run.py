"""Una ejecución fija de S2T-0D-01: python -m motorsim.reference_run."""
import argparse
import csv
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import threading
import time

from .adaptive import run_adaptive
from .simulation import Model
from .prototype import Monitor, environment, memory_mib
from .reference_results import BAND_PA, PROFILE, new_output_path, reference_inputs, save_result


def emit(data):
    print(json.dumps(data, ensure_ascii=True, allow_nan=False), flush=True)


def execute(folder, cancelled, report=emit):
    folder.mkdir(parents=True, exist_ok=False)
    inputs = reference_inputs()
    started = time.monotonic()
    monitor = Monitor(PROFILE.max_step_deg, started, cancelled.is_set, emit=lambda *a, **k: None)
    last = started-1
    def progress(cycle, angle, rhs, completed=False):
        nonlocal last
        monitor(cycle, angle, rhs, completed)
        now = time.monotonic()
        if completed or now-last >= .5:
            report(dict(event='progress', cycle=cycle, completed_cycles=cycle if completed else cycle-1,
                        seconds=now-started, rhs=rhs, calculation_MiB=monitor.peak_mib))
            last = now
    try:
        with (folder/'attempts.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=[
                'angle_deg', 'proposed_deg', 'substep_deg', 'error', 'worst', 'accepted', 'cause', 'rhs'])
            writer.writeheader()
            result = run_adaptive(PROFILE, progress, Model(external_band_pa=BAND_PA), trace=writer.writerow)
        status = 'converged' if result['converged'] else 'not_converged'
        if cancelled.is_set():
            status = 'cancelled'
            result['converged'] = False
            result['stop'] = 'cancelación solicitada'
    except Exception as exc:
        status = 'error'
        result = dict(profile=asdict(PROFILE), converged=False, cycles=[], last_two_cycles=[],
                      partial=None, seconds=time.monotonic()-started, stop=f'{type(exc).__name__}: {exc}')
    result['peak_process_MiB'] = max(monitor.peak_mib, memory_mib())
    save_result(folder, result, status, inputs, environment())
    report(dict(event='finished', status=status, manifest=str((folder/'manifest.json').resolve())))
    return 0 if status == 'converged' else (130 if status == 'cancelled' else 2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--control-stdin', action='store_true', help='Control cooperativo por pipe: cancel + salto de línea.')
    args = parser.parse_args(argv)
    cancelled = threading.Event()
    def control():
        # os.read evita el bloqueo del búfer Python al terminar un hilo daemon.
        buffer = b''
        try:
            while not cancelled.is_set():
                chunk = os.read(0, 1024)
                if not chunk:  # El padre desapareció/cerró el canal: no seguir huérfano.
                    cancelled.set()
                    return
                buffer = (buffer+chunk)[-1024:]
                if b'cancel\n' in buffer:
                    cancelled.set()
        except OSError:
            cancelled.set()
    if args.control_stdin:
        threading.Thread(target=control, daemon=True).start()
    previous = signal.signal(signal.SIGINT, lambda *a: cancelled.set())
    try:
        return execute(args.output or new_output_path(), cancelled)
    except (OSError, ValueError) as exc:
        emit(dict(event='error', message=str(exc)))
        return 2
    finally:
        signal.signal(signal.SIGINT, previous)


if __name__ == '__main__':
    raise SystemExit(main())
