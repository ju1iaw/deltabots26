"""PC-only video launcher. Keep beside the video program, Base and CSV exporter.

Setup once: py -3 -m pip install pybricksdev==2.3.2
Run: py -3 DeltaBots_Video_Terminal.py --name "Pybricks"
Commands: go + Enter starts the next ready round; quit + Enter stops the hub.
LEFT+RIGHT on the hub also stops the test. Ctrl+C exits this launcher.
The normal comparison program and Base are not modified.
"""
import argparse
import asyncio
import codecs
from datetime import datetime
from pathlib import Path
import sys
import threading

from DeltaBots_Comparison_To_CSV import ReportWriter


def read_commands(loop, queue):
    """Daemon reader: do not block the Bluetooth event loop or shutdown."""
    while True:
        line = sys.stdin.readline()
        try:
            loop.call_soon_threadsafe(queue.put_nowait, line if line else 'quit\n')
        except RuntimeError:
            return
        if not line:
            return


class VideoOutput:
    def __init__(self, report):
        self.report = report
        self.ready = False
        self.pending = ''
        self.decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')

    def receive(self, data):
        self.pending += self.decoder.decode(data)
        while '\n' in self.pending:
            line, self.pending = self.pending.split('\n', 1)
            line = line.rstrip('\r')
            if line == 'VIDEO_READY':
                self.ready = True
            elif line == 'VIDEO_START':
                self.ready = False
            print(line, flush=True)
            self.report.feed(line)


async def capture(args):
    from pybricksdev.ble import find_device
    from pybricksdev.connections.pybricks import PybricksHubBLE

    program = Path(__file__).resolve().with_name('DeltaBots_Drive_Comparison_Video.py')
    if not program.is_file():
        raise FileNotFoundError(program)
    output = args.output or program.parent / 'results' / (
        'DeltaBots_Video_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.csv')
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    print('Searching for', args.name, flush=True)
    hub = PybricksHubBLE(await find_device(args.name))
    await hub.connect()
    running = None
    subscription = None
    stopped = False
    try:
        with output.open('x', newline='', encoding='utf-8-sig') as stream:
            report = ReportWriter(stream, args.layout)
            receiver = VideoOutput(report)
            subscription = hub.stdout_observable.subscribe(receiver.receive)
            running = asyncio.create_task(hub.run(
                str(program), wait=True, print_output=False, line_handler=False))
            queue = asyncio.Queue()
            loop = asyncio.get_running_loop()
            threading.Thread(target=read_commands, args=(loop, queue), daemon=True).start()
            print('Wait for VIDEO_READY, then type go + Enter. Type quit + Enter to stop.', flush=True)
            try:
                while not running.done():
                    try:
                        line = await asyncio.wait_for(queue.get(), timeout=0.1)
                    except asyncio.TimeoutError:
                        continue
                    command = line.strip().lower()
                    if command in ('quit', 'q', 'stop'):
                        stopped = True
                        await hub.stop_user_program()
                        break
                    if command == 'go':
                        if receiver.ready:
                            receiver.ready = False
                            await hub.write_line('go')
                        else:
                            print('Not ready; command ignored. Wait for VIDEO_READY.', flush=True)
                    elif command:
                        print('Commands: go, quit', flush=True)
                if stopped:
                    await asyncio.wait_for(asyncio.shield(running), timeout=3)
                else:
                    await running
            finally:
                # Stop before closing the CSV stream, including on Ctrl+C/error.
                if not running.done():
                    try:
                        await asyncio.wait_for(hub.stop_user_program(), timeout=3)
                    finally:
                        running.cancel()
                        await asyncio.gather(running, return_exceptions=True)
                subscription.dispose()
                subscription = None
            print('CSV saved:', output)
            if (stopped or report.failed or report.rows == 0 or
                    (report.expected is not None and report.completed != report.expected)):
                print('Session stopped or incomplete; received results are retained.')
                return 1
            return 0
    finally:
        if subscription is not None:
            subscription.dispose()
        await hub.disconnect()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--name', required=True, help='Bluetooth hub name')
    parser.add_argument('--output', type=Path, help='New CSV path; existing files are not overwritten')
    parser.add_argument('--layout', choices=('auto', 'rounds', 'detailed'), default='auto')
    args = parser.parse_args()
    try:
        return asyncio.run(capture(args))
    except ModuleNotFoundError as error:
        print('Missing dependency:', error, file=sys.stderr)
        print('Install with: py -3 -m pip install pybricksdev==2.3.2', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('\nVideo session interrupted. Received CSV data is retained.')
        return 130
    except Exception as error:
        print('Video session error:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
