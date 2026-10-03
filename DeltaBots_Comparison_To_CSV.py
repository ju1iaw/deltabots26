"""Run on your COMPUTER, not on the hub.

Live run (all three Python files in the same folder):
  py -3 DeltaBots_Comparison_To_CSV.py --name YOUR_HUB_NAME
Convert an existing console log or old CSV without running the robot:
  py -3 DeltaBots_Comparison_To_CSV.py --input Comparison.txt
Optional: --output results/my_test.csv
Use --layout rounds to explicitly request one forward/backward pair per column.

Summary mode writes Item, Round 1, Round 2, ... in one CSV for the session.
One round is a forward/backward pair for one function. Forward and backward
results occupy separate rows in the same column, labeled with trial/function.
Detailed mode preserves the robot's report order, labels and values. Whitespace separates
CSV columns; existing commas (including the sample header) also separate
columns. Summary rows therefore have varying numbers of columns. Numeric
sample rows have two columns: time_ms and heading_change_deg.
"""
import argparse
import csv
from datetime import datetime
from pathlib import Path
import os
import re
import subprocess
import sys

EXPORTER_VERSION = "7 - mean heading error"


class ReportWriter:
    def __init__(self, stream, layout="auto"):
        self.writer = csv.writer(stream)
        self.stream = stream
        self.started = False
        self.rows = 0
        self.completed = 0
        self.expected = None
        self.failed = False
        self.layout = layout
        self.wide = layout == "rounds"
        self.columns = []
        self.metadata = {}
        self.trial = '1'
        self.direction = None

    def _write_wide(self):
        self.stream.seek(0)
        self.stream.truncate()
        self.writer.writerow(['Item'] + ['Round ' + str(i + 1) for i in range(len(self.columns))])
        keys = []
        for column in self.columns:
            for key in column:
                if key not in keys:
                    keys.append(key)
        for key in keys:
            self.writer.writerow([key] + [column.get(key, '') for column in self.columns])
        self.stream.flush()

    def _feed_wide(self, line):
        if line.startswith('Trial:'):
            self.trial = line.split(':', 1)[1].strip()
        start = re.match(r'^Starting (Gyro_Move|Move_Straight) distance: (.+)$', line)
        if start:
            function, distance = start.groups()
            self.direction = 'Backward' if float(distance) < 0 else 'Forward'
            # The script emits each forward leg followed by its backward leg.
            # Do not combine different trials/functions or repeated backward legs.
            pair_matches = (
                self.direction == 'Backward' and self.columns
                and self.columns[-1]['Trial'] == self.trial
                and self.columns[-1]['Function'] == function
                and 'Forward requested distance (mm)' in self.columns[-1]
                and 'Backward requested distance (mm)' not in self.columns[-1]
                and float(self.columns[-1]['Forward requested distance (mm)']) == -float(distance))
            if pair_matches:
                column = self.columns[-1]
            else:
                column = {'Trial': self.trial, 'Function': function}
                column.update(self.metadata)
                if function == 'Move_Straight':
                    column['Gyro_Move Heading_KP'] = 'Not applicable'
                    column['Gyro_Move Heading_KD'] = 'Not applicable'
                    for key in ('Gyro_Move Heading_KI', 'Integral window (ms)',
                                'Integral turn limit (deg/s)'):
                        column[key] = 'Not applicable'
                column['Status'] = 'Incomplete'
                self.columns.append(column)
            column[self.direction + ' requested distance (mm)'] = distance
            column[self.direction + ' status'] = 'Started'
        elif self.columns and self.direction:
            column = self.columns[-1]
            if line.startswith('Traceback') or 'Error:' in line:
                column['Status'] = 'Error / incomplete'
                column[self.direction + ' status'] = 'Error / incomplete'
                column[self.direction + ' error'] = line
            elif ':' in line:
                key, value = line.split(':', 1)
                if key in ('Elapsed time (ms)', 'Measured encoder travel (mm)',
                           'Final heading change (deg)', 'Heading peak-to-peak (deg)',
                           'Time-weighted RMS heading error (deg)',
                           'Time-weighted mean heading error (deg)', 'Samples recorded'):
                    column[self.direction + ' ' + key] = value.strip()
                    if key == 'Samples recorded':
                        column[self.direction + ' status'] = 'Completed'
                        if all(column.get(side + ' status') == 'Completed'
                               for side in ('Forward', 'Backward')):
                            column['Status'] = 'Completed'
        if self.columns:
            self._write_wide()

    def feed(self, line):
        # Accept both raw console lines and the old whitespace-to-CSV export.
        line = re.sub(r'\[[0-?]*[ -/]*[@-~]', '', line).strip().lstrip('\ufeff')
        if ',' in line:
            line = ' '.join(next(csv.reader([line])))
        line = ' '.join(line.split())
        if line.startswith(('Comparison:', 'Drive comparison:')):
            self.started = True
        # Keep connection/progress messages out of the CSV.
        if not self.started or not line:
            return
        if self.layout == 'auto' and line.startswith('Summary columns:'):
            self.wide = line.endswith('True')
        if line.startswith('Comparison:') and 'Velocity:' in line:
            self.metadata['Velocity (mm/s)'] = line.rsplit('Velocity:', 1)[1].strip()
        if ':' in line:
            key, value = line.split(':', 1)
            if key in ('Test mode', 'Experiment repeats', 'Acceleration / deceleration',
                       'Gyro_Move Heading_KP', 'Gyro_Move Heading_KD', 'Gyro_Move Heading_KI',
                       'Integral window (ms)', 'Integral turn limit (deg/s)',
                       'Sweep parameter', 'Requested sample interval (ms)'):
                self.metadata[key] = value.strip()
        if line.startswith('Expected movements:'):
            self.expected = int(line.split(':', 1)[1].strip())
        if line.startswith('Move_Straight enabled:'):
            self.expected = 4 if line.endswith('True') else 2
        if line.startswith('Traceback') or 'Error:' in line:
            self.failed = True
        if re.match(r'^(Gyro_Move|Move_Straight|CUSTOM|NATIVE)\s+-?\d+(?:\.\d+)?\s+completed$', line):
            self.completed += 1
        if self.wide:
            self._feed_wide(line)
            self.rows += 1
            return
        self.writer.writerow(re.split(r'[\s,]+', line))
        self.stream.flush()  # Preserve each received row if a run is interrupted.
        self.rows += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--name', help='Bluetooth hub name; uploads and runs the test')
    mode.add_argument('--input', type=Path, help='Convert an existing console log instead')
    parser.add_argument('--program', type=Path,
                        default=Path(__file__).resolve().with_name('DeltaBots_Drive_Comparison.py'))
    parser.add_argument('--layout', choices=('auto', 'rounds', 'detailed'), default='auto',
                        help='rounds forces one forward/backward pair per column; auto follows robot settings')
    parser.add_argument('--output', type=Path, help='New CSV filename; existing files are not overwritten')
    args = parser.parse_args()
    print("CSV exporter:", EXPORTER_VERSION)
    print("Exporter file:", Path(__file__).resolve())
    print("Requested layout:", args.layout)
    if args.input and not args.input.is_file():
        parser.error('Input log not found: ' + str(args.input))
    if args.name and not args.program.is_file():
        parser.error('Robot program not found: ' + str(args.program))
    output = args.output or Path(__file__).resolve().parent / 'results' / (
        'DeltaBots_Comparison_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.csv')
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    process = None
    exit_code = 0
    try:
        # UTF-8 BOM lets Excel recognize the encoding when opening the file.
        with output.open('x', newline='', encoding='utf-8-sig') as stream:
            report = ReportWriter(stream, args.layout)
            if args.input:
                with args.input.open(encoding='utf-8-sig') as source:
                    for line in source:
                        report.feed(line)
            else:
                program = args.program.resolve()
                command = [sys.executable, '-m', 'pipx', 'run', 'pybricksdev',
                           'run', 'ble', '--name', args.name, program.name]
                environment = os.environ.copy()
                environment['PYTHONUNBUFFERED'] = '1'
                # stderr remains on the console (connection/progress/errors).
                process = subprocess.Popen(command, cwd=str(program.parent),
                    stdout=subprocess.PIPE, text=True, encoding='utf-8',
                    errors='replace', bufsize=1, env=environment)
                for line in process.stdout:
                    print(line, end='', flush=True)
                    report.feed(line)
                process.stdout.close()
                exit_code = process.wait()
        print('CSV saved:', output)
        if report.wide:
            print('Round columns saved:', len(report.columns))
        else:
            print('Layout saved: detailed rows')
        if report.rows == 0 or (report.wide and not report.columns):
            print('No robot report was received.', file=sys.stderr)
            return exit_code or 1
        if exit_code or report.failed or (report.expected is not None and report.completed != report.expected):
            print('Run/log is incomplete or contains an error; the CSV retains received output.', file=sys.stderr)
            return exit_code or 1
        return 0
    except KeyboardInterrupt:
        print('\nCapture interrupted. Received rows remain in:', output, file=sys.stderr)
        return 130
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    sys.exit(main())
