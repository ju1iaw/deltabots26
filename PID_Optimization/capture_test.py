"""PC Python 3: run hub test and save samples.csv and summary.csv; standard library only."""
import argparse
import csv
import os
import datetime
import json
import math
from pathlib import Path
import re
import subprocess
import sys


def analyze(text):
    records = {"META": [], "FIELDS": [], "DATA": [], "END": []}
    for line in text.splitlines():
        line = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line)
        match = re.search(r"SF_(META|FIELDS|DATA|END) (.*)", line)
        if match:
            records[match[1]].append(json.loads(match[2]))
    if len(records['META']) != 1 or len(records['FIELDS']) != 1:
        raise ValueError("Expected exactly one run's metadata and field header.")
    if len(records['END']) > 1:
        raise ValueError("Multiple runs in transcript; analyze one run at a time.")
    fields = records['FIELDS'][0]
    if any(len(row) != len(fields) for row in records['DATA']):
        raise ValueError("Truncated data row.")
    rows = [dict(zip(fields, row)) for row in records['DATA']]
    if len(rows) < 2:
        raise ValueError("Fewer than two samples; no analysis possible.")
    if any(not math.isfinite(v) for row in rows for v in row.values()):
        raise ValueError("Non-finite measurement.")
    meta = records['META'][0]
    end = records['END'][0] if records['END'] else {}
    intervals = [b['time_ms']-a['time_ms'] for a,b in zip(rows,rows[1:])]
    if min(intervals) <= 0:
        raise ValueError("Sample timestamps must increase strictly.")
    duration = sum(intervals)
    def time_mean(fn):
        return sum(dt*(fn(a)+fn(b))/2 for a,b,dt in zip(rows,rows[1:],intervals))/duration
    mean = time_mean(lambda r: r['error_deg'])
    square = time_mean(lambda r: r['error_deg']**2)
    complete = bool(end) and end.get('samples') == len(rows)
    # Estimated yaw/path position is deliberately not presented as measured lateral error.
    summary = {
        'trial_id': meta.get('trial_id'), 'road_condition': meta.get('road_condition'),
        'correction_enabled': meta.get('correction_enabled'),
        'kp_configured_per_s': meta.get('kp_per_s'),
        'kp_effective_per_s': meta.get('kp_per_s') if meta.get('correction_enabled') else 0,
        'requested_distance_mm': meta.get('distance_mm'),
        'requested_velocity_mm_s': meta.get('velocity_mm_s'),
        'status': end.get('status','incomplete_transfer'),
        'complete_transfer': complete,
        'valid_completed_trial': complete and end.get('status') == 'completed',
        'samples': len(rows), 'recorded_duration_s': duration/1000,
        'heading_mean_error_deg': mean,
        'heading_mean_absolute_error_deg': time_mean(lambda r: abs(r['error_deg'])),
        'heading_rmse_deg': math.sqrt(square),
        'heading_std_about_mean_deg': math.sqrt(max(0,square-mean*mean)),
        'heading_max_absolute_error_deg': max(abs(r['error_deg']) for r in rows),
        'heading_peak_to_peak_deg': max(r['heading_deg'] for r in rows)-min(r['heading_deg'] for r in rows),
        'heading_error_at_brake_deg': rows[-1]['error_deg'],
        'loop_interval_mean_ms': duration/len(intervals),
        'loop_interval_min_ms': min(intervals), 'loop_interval_max_ms': max(intervals),
        'achieved_loop_rate_hz': 1000*len(intervals)/duration,
        'intervals_above_150_percent_requested': sum(dt>1.5*meta['control_interval_ms'] for dt in intervals),
        'command_limited_time_percent': 100*sum(dt*a['limited'] for a,dt in zip(rows,intervals))/duration,
        'encoder_distance_at_brake_mm': rows[-1]['encoder_distance_mm'],
        'external_final_lateral_error_mm': None,
        'external_max_lateral_deviation_mm': None,
        'external_actual_travel_mm': None,
        'notes': 'Heading metrics cover sampled motion through brake command; time-weighted trapezoidal estimates. Error = target minus heading. Encoder distance is not ground truth.'
    }
    if end:
        summary['final_heading_error_after_brake_deg'] = meta['target_heading_deg']-end['final_heading_deg']
        summary['final_encoder_distance_mm'] = end['final_encoder_distance_mm']
        summary['encoder_distance_error_mm'] = end['final_encoder_distance_mm']-meta['distance_mm']
        summary['brake_command_time_s'] = end['brake_time_ms']/1000
    return {'metadata':meta,'end':end,'samples':rows},summary


def write_csv_files(folder, detailed, summary, filename_time):
    """Comma-separated UTF-8 CSVs readable by Excel; one folder per trial."""
    distance = format(float(summary['requested_distance_mm']), '.12g')
    kp = format(float(summary['kp_effective_per_s']), '.12g')
    prefix = f'{filename_time}_{distance}_{kp}'
    samples_path = folder / f'{prefix}_samples.csv'
    summary_path = folder / f'{prefix}_summary.csv'
    columns = [
        'correction_enabled', 'kp_configured_per_s', 'kp_effective_per_s',
        'time_ms', 'heading_deg', 'error_deg', 'yaw_rate_deg_s',
        'pitch_deg', 'roll_deg', 'encoder_distance_mm',
        'command_turn_deg_s', 'limited']
    settings = {key: summary.get(key) for key in columns[:3]}
    with samples_path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in detailed['samples']:
            values = {**settings, **row}
            writer.writerow({key: values.get(key) for key in columns})
    # Preserve all summary settings/results, now vertically as Item / Value.
    summary_row = {**detailed['metadata'], **summary}
    with summary_path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Item', 'Value'])
        writer.writerows(summary_row.items())
    return samples_path, summary_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='Alyssa', help='Bluetooth hub name')
    parser.add_argument('--script', type=Path, default=Path(__file__).with_name('ScienceFair_Straight_Test.py'))
    parser.add_argument('--out', type=Path, default=Path('results'))
    parser.add_argument('--analyze', type=Path, help='Analyze existing transcript without connecting')
    args = parser.parse_args()
    started_at = datetime.datetime.now()
    stamp = started_at.strftime('%Y%m%d_%H%M%S_%f')
    filename_time = started_at.strftime('%Y%m%d_%H%M')
    folder = args.out / stamp
    folder.mkdir(parents=True, exist_ok=False)
    exit_code = None if args.analyze else 0
    if args.analyze:
        # Also accepts Windows PowerShell UTF-16 transcripts.
        raw = args.analyze.read_bytes()
        text = raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
    else:
        if not args.script.is_file():
            parser.error('Hub script does not exist: '+str(args.script))
        command = [sys.executable,'-u','-m','pipx','run','pybricksdev','run','ble',
                   '--name',args.name,str(args.script.resolve())]
        print('Connecting. Close other Bluetooth connections to the hub.')
        print('Saving to:',folder.resolve())
        captured_lines = []
        process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                   text=True,encoding='utf-8',errors='replace',bufsize=1,
                                   env={**os.environ, 'PYTHONUNBUFFERED': '1', 'PYTHONIOENCODING': 'utf-8'})
        try:
            for line in process.stdout:
                print(line,end='',flush=True)
                captured_lines.append(line)
            exit_code = process.wait()
        except KeyboardInterrupt:
            process.terminate()
            print('\nCapture interrupted. Press CENTER on the hub to stop it.')
            return 130
        finally:
            process.stdout.close()
        text = ''.join(captured_lines)
    try:
        detailed,summary = analyze(text)
    except (ValueError,KeyError,TypeError) as exc:
        print('No valid analysis:',exc)
        print('No CSV analysis saved. Review the output above in the terminal.')
        return 1
    summary['capture_process_exit_code'] = exit_code
    summary['capture_process_ok'] = None if exit_code is None else exit_code == 0
    # A return-movement error does not invalidate a fully received completed test.
    # Record process status separately so users can inspect the transcript.
    summary['return_done_reported'] = 'RETURN_DONE:' in text
    samples_path, summary_path = write_csv_files(folder, detailed, summary, filename_time)
    lines = [f'{key}: {value}' for key,value in summary.items()]
    print('\n'+'\n'.join(lines))
    print('\nSaved CSV files:', samples_path.resolve(), summary_path.resolve(), sep='\n')
    return 0 if summary['valid_completed_trial'] and exit_code in (None, 0) else 1

if __name__ == '__main__':
    raise SystemExit(main())
