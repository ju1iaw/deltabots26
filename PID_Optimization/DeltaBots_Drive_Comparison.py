"""Standalone A/B test for straight-driving wiggle.

Save beside DeltaBots_Base.py and run this file directly, outside the master.
Uses one robot; select both controllers or either controller with TEST_MODE.
Each selected controller runs forward and backward. Gyro_Move sweeps KP, KD, or KI using SWEEP_PARAMETER;
Move_Straight runs once per trial because Heading_KP does not apply to it.
Requires the existing DeltaBots_Base.py with Move_Straight and PD steering.
No base changes needed: KP=0 uses a test-local copy of its drive controller.
Clear space for 2000 mm travel plus drift. CENTER press/release starts each
forward/backward round. Backward starts automatically after the 1-second pause. LEFT+RIGHT together stops the script; CENTER stop is restored on exit.
The backward leg is not guaranteed to return to the exact starting position.
Heading traces are buffered during motion. Summaries print after stopping;
set PRINT_DETAILED_DATA=True to also print every recorded sample. This switch
also controls CSV detail when using the PC capture launcher. Sampling and
summary calculations are identical in both modes.
This measures yaw, not lateral position; also observe the physical path.
The signed time-weighted mean uses trapezoidal integration of heading change
relative to each leg's starting heading, divided by sampled duration.
SAMPLE_MS requests a logging interval, not a controller update interval.
Actual timestamps are stored; hub workload can make samples arrive later.
Summary mode keeps only running statistics and repeats EXPERIMENT_REPEATS
times for each gain. Only the forward leg requires a button press/release in either mode.
Detailed mode runs one set; at 20 ms and a 20 s timeout it uses 8016 buffer bytes.
SWEEP_PARAMETER selects KP, KD, or KI; the other gains stay fixed.
KI mode uses a test-local finite-window integral; the official base is untouched.
The integral resets each leg and its output is limited. It is not standard Ti.
KP=0 disables P only; KD=0 disables D only. Other Gyro_Move settings retain
their base defaults; native gains are untouched.
"""

from DeltaBots_Base import DeltaBots, Stop, _mode, _positive, _clip, _wrap
from math import sqrt
from ustruct import pack_into, unpack_from
from gc import collect
from pybricks.tools import StopWatch
from pybricks.parameters import Button

DISTANCE = 2000
VELOCITY = 500
ACCELERATION = 200
DECELERATION = 200  # Matches original driveForDistance's scalar acceleration.
TIMEOUT_MS = 20000
SAMPLE_MS = 20
# Choose which gain to sweep. The other gain uses its FIXED value below.
SWEEP_PARAMETER = 'KI'  # 'KP', 'KD', or 'KI'
FIXED_HEADING_KP = 5
FIXED_HEADING_KD = 0.6  # Set KP/KD to the pair chosen from your own results.
HEADING_KI_VALUES = (0, 5, 10, 20, 40, 60, 100, 150)  # Units: 1/s^2.
INTEGRAL_WINDOW_MS = 1000  # Fixed rolling integration window, not scanned.
INTEGRAL_TURN_LIMIT = 15  # Max absolute I contribution, deg/s; not scanned.
# KP/KD sweeps keep KI=0, preserving the earlier PD experiments.
HEADING_KP_VALUES = (0, 3, 5, 8, 10, 15, 20)
HEADING_KD_VALUES = (0, 0.1, 0.3, 0.6, 1.0, 2.0, 5.0)
# 1 = Gyro_Move gain sweep + one Move_Straight round per trial
# 2 = Gyro_Move gain sweep only
# 3 = Move_Straight only (one round per trial)
TEST_MODE = 2
PRINT_DETAILED_DATA = False  # False: summaries only; True: include all samples.
EXPERIMENT_REPEATS = 1  # Summary mode only; detailed mode runs one set.

# One reusable buffer: timestamp uint32 + heading float32 = 8 bytes/sample.
# No growing lists, per-sample tuples, or second list for summary statistics.
_RECORD_FORMAT = '<If'
_RECORD_BYTES = 8


class WindowIntegral:
    """Time-weighted rolling integral, deg*s, with bounded preallocated storage.

    Store piecewise-constant error over each measured controller interval.
    Expire old intervals and trim the boundary interval exactly in time.
    """
    def __init__(self, window_ms, loop_ms):
        self.window_ms = window_ms
        self.capacity = int(window_ms // loop_ms) + 3
        self.buffer = bytearray(self.capacity * 12)
        self.clear(0)

    def clear(self, now):
        self.head = 0
        self.count = 0
        self.total = 0.0
        self.last = now

    def update(self, now, error):
        cutoff = now - self.window_ms
        while self.count:
            offset = self.head * 12
            start, end, value = unpack_from('<IIf', self.buffer, offset)
            if end <= cutoff:
                self.total -= value * (end - start) / 1000
                self.head = (self.head + 1) % self.capacity
                self.count -= 1
            else:
                if start < cutoff:
                    self.total -= value * (cutoff - start) / 1000
                    pack_into('<IIf', self.buffer, offset, cutoff, end, value)
                break
        if not self.count:
            self.total = 0.0
        start = max(self.last, cutoff)
        if now > start:
            if self.count >= self.capacity:
                raise RuntimeError('Integral buffer full; controller polling too fast')
            offset = ((self.head + self.count) % self.capacity) * 12
            pack_into('<IIf', self.buffer, offset, start, now, error)
            # Use stored float precision for both addition and subtraction.
            _, _, value = unpack_from('<IIf', self.buffer, offset)
            self.total += value * (now - start) / 1000
            self.count += 1
        self.last = now
        return self.total


class ComparisonRobot(DeltaBots):
    """Test-local zero-P and experimental integral support.

    KP/KD sweeps delegate positive KP to the unchanged base.
    KI sweeps use the local controller for all KI values, including zero.
    turn = KP*error + clip(KI*integral(error dt), I_limit) - KD*yaw_rate.
    Error is in degrees, time in seconds, KI in 1/s^2, turn in deg/s.
    Integral is over the rolling window, resets each leg, and forgets old
    error. The I output cap bounds its contribution; this is not full
    actuator-aware anti-windup or stall detection. Test on a clear path.
    """

    def _gyro_move(self, direction, distance, velocity, acceleration,
                   deceleration, stop, timeout_ms, tolerance, heading_kp,
                   max_turn_rate, distance_kp, heading_kd, turn_acceleration,
                   time_ms=None):
        args = (direction, distance, velocity, acceleration, deceleration,
                stop, timeout_ms, tolerance, heading_kp, max_turn_rate,
                distance_kp, heading_kd, turn_acceleration)
        if heading_kp == 0 or getattr(self, 'integral_test', False):
            return self._zero_gain_move(*args, time_ms=time_ms)
        # Omitting the optional limit also supports the earlier base signature.
        if time_ms is None:
            return super()._gyro_move(*args)
        return super()._gyro_move(*args, time_ms=time_ms)

    def _zero_gain_move(self, direction, distance, velocity, acceleration,
                   deceleration, stop, timeout_ms, tolerance, heading_kp,
                   max_turn_rate, distance_kp, heading_kd, turn_acceleration,
                   time_ms=None):
        """Drive signed mm while maintaining direction (None=current yaw).

        Velocity is a positive magnitude in mm/s. Distance controls reverse.
        An optional time_ms adds an earlier normal stopping condition.
        Returns actual signed encoder travel. Heading gains are turn-rate
        per degree; acceleration/deceleration shape commanded linear speed.
        """
        _mode(stop)
        timed = time_ms is not None
        if timed:
            if not 0 <= time_ms < float('inf'):
                raise ValueError('time_ms must be finite and nonnegative')
            if not 0 < timeout_ms < float('inf'):
                raise ValueError('timeout_ms must be finite and positive')
            if time_ms > timeout_ms:
                raise ValueError('time_ms must not exceed timeout_ms')
        for v, n in ((velocity, 'velocity'), (acceleration, 'acceleration'),
                     (deceleration, 'deceleration'), (timeout_ms, 'timeout_ms'),
                     (tolerance, 'tolerance'),
                     (max_turn_rate, 'max_turn_rate'), (distance_kp, 'distance_kp'),
                     (turn_acceleration, 'turn_acceleration')):
            _positive(v, n)
        if not 0 <= heading_kp < float('inf'):
            raise ValueError('heading_kp must be finite and nonnegative')
        if not 0 <= heading_kd < float('inf'):
            raise ValueError('heading_kd must be finite and nonnegative')
        ki = getattr(self, 'experiment_ki', 0)
        if not 0 <= ki < float('inf'):
            raise ValueError('KI must be finite and nonnegative')
        integral = WindowIntegral(min(INTEGRAL_WINDOW_MS, timeout_ms), self.loop_ms) if ki else None
        previous_heading = self.Get_YAW_Angle(False)
        target_heading = previous_heading if direction is None else direction
        yaw_rate = 0
        correction = 0
        # Prevent the linear ramp from building an unreachable speed while
        # _tank silently scales the wheel commands down to the motor limit.
        velocity = min(velocity, self.max_motor_speed * self.mm_per_degree)
        start = self.Get_Distance()
        timer = StopWatch()
        last_time = 0
        speed = 0
        stable = 0
        try:
            self._stop_drive()
            while True:
                now = timer.time()
                # Completion wins when duration equals timeout, as in Drive_Time.
                if timed and now >= time_ms:
                    break
                self._deadline(timer, timeout_ms, 'Gyro_Move')
                dt = max(1, now - last_time) / 1000
                last_time = now
                heading = self.Get_YAW_Angle(False)
                measured_rate = _wrap(heading - previous_heading) / dt
                previous_heading = heading
                yaw_rate += dt / (0.05 + dt) * (measured_rate - yaw_rate)
                error = distance - (self.Get_Distance() - start)
                if abs(error) <= tolerance:
                    if integral is not None:
                        integral.clear(now)
                    self._stop_drive(Stop.BRAKE)
                    speed = 0
                    correction = 0
                    stable += 1
                    if stable >= 3:
                        break
                else:
                    stable = 0
                    desired = min(velocity, distance_kp * abs(error), sqrt(2 * deceleration * abs(error)))
                    desired *= 1 if error > 0 else -1
                    limit = acceleration if desired * speed >= 0 and abs(desired) > abs(speed) else deceleration
                    speed += _clip(desired - speed, limit * dt)
                    # Damping opposes actual turning, including in reverse.
                    # Differentiate measured heading, not the target, to avoid
                    # a derivative kick when a new direction is requested.
                    heading_error = _wrap(target_heading - heading)
                    integral_turn = 0
                    if integral is not None:
                        integral_turn = _clip(ki * integral.update(now, heading_error),
                                              INTEGRAL_TURN_LIMIT)
                    desired_correction = _clip(
                        heading_kp * heading_error + integral_turn
                        - heading_kd * yaw_rate, max_turn_rate)
                    correction += _clip(desired_correction - correction,
                                        turn_acceleration * dt)
                    self._drive(speed, correction)
                yield
        except BaseException:
            self._stop_drive(Stop.BRAKE)
            raise
        self._stop_drive(stop)
        return self.Get_Distance() - start


def _record(bot, task, timer, initial_heading, buffer):
    count = 0
    next_sample = 0
    capacity = len(buffer) // _RECORD_BYTES if buffer is not None else 0
    first_time = 0
    previous_time = 0
    previous_heading = 0
    minimum = 0
    maximum = 0
    area = 0
    signed_area = 0
    while True:
        elapsed = timer.time()
        finished = task.done
        if task.cancelled:
            raise RuntimeError('Comparison movement was cancelled')
        if elapsed >= next_sample or finished:
            heading = bot.Get_YAW_Angle(False) - initial_heading
            if buffer is not None:
                if count >= capacity:
                    raise RuntimeError('Sample buffer full; check sampling settings')
                pack_into(_RECORD_FORMAT, buffer, count * _RECORD_BYTES,
                          elapsed, heading)
            if count == 0:
                first_time = elapsed
                minimum = heading
                maximum = heading
            else:
                dt = elapsed - previous_time
                area += dt * (previous_heading ** 2 + heading ** 2) / 2
                signed_area += dt * (previous_heading + heading) / 2
                minimum = min(minimum, heading)
                maximum = max(maximum, heading)
            previous_time = elapsed
            previous_heading = heading
            count += 1
            next_sample = elapsed + SAMPLE_MS
        if finished:
            duration = previous_time - first_time
            rms = sqrt(area / duration) if duration > 0 else abs(previous_heading)
            mean = signed_area / duration if duration > 0 else previous_heading
            return count, previous_time, previous_heading, maximum - minimum, rms, mean
        if elapsed >= TIMEOUT_MS:
            raise RuntimeError('Comparison movement timed out')
        bot.Wait(10)


def _report(label, buffer, stats, travel):
    count, elapsed, final_heading, peak_to_peak, rms, mean = stats
    print(label, 'completed')
    print('Elapsed time (ms):', elapsed)
    print('Measured encoder travel (mm):', travel)
    print('Final heading change (deg):', final_heading)
    print('Heading peak-to-peak (deg):', peak_to_peak)
    print('Time-weighted RMS heading error (deg):', rms)
    print('Time-weighted mean heading error (deg):', mean)
    print('Samples recorded:', count)
    if not PRINT_DETAILED_DATA:
        return
    print('Time_ms, heading_change_deg')
    for i in range(count):
        elapsed, heading = unpack_from(_RECORD_FORMAT, buffer, i * _RECORD_BYTES)
        print(elapsed, heading)


def _wait_for_start(bot):
    """Require a fresh debounced CENTER press and release before each round."""
    # Ignore a held button from the preceding movement. Motors coast so
    # the robot can be repositioned before the next measurement.
    bot.Stop_All(stop=Stop.COAST)
    print('Align robot. Press and release CENTER to start; LEFT+RIGHT exits.')
    phase = 0
    stable = 0
    while True:
        pressed = bot.hub.buttons.pressed()
        wanted = not pressed if phase in (0, 2) else Button.CENTER in pressed
        stable = stable + 10 if wanted else 0
        if stable >= 30:
            phase += 1
            stable = 0
            if phase == 3:
                return
        bot.Wait(10)


def main():
    if not isinstance(SAMPLE_MS, int) or SAMPLE_MS <= 0:
        raise ValueError('SAMPLE_MS must be a positive integer')
    if not isinstance(TIMEOUT_MS, int) or not 0 < TIMEOUT_MS < 1000000000:
        raise ValueError('TIMEOUT_MS must be a positive integer below 1000000000')
    if type(TEST_MODE) is not int or TEST_MODE not in (1, 2, 3):
        raise ValueError('TEST_MODE must be 1, 2, or 3')
    if SWEEP_PARAMETER not in ('KP', 'KD', 'KI'):
        raise ValueError("SWEEP_PARAMETER must be 'KP', 'KD', or 'KI'")
    if TEST_MODE in (1, 2):
        gains = {'KP': HEADING_KP_VALUES, 'KD': HEADING_KD_VALUES,
                 'KI': HEADING_KI_VALUES}[SWEEP_PARAMETER]
        fixed_gains = ((FIXED_HEADING_KD,) if SWEEP_PARAMETER == 'KP' else
                       (FIXED_HEADING_KP,) if SWEEP_PARAMETER == 'KD' else
                       (FIXED_HEADING_KP, FIXED_HEADING_KD))
        if not gains:
            raise ValueError('Selected gain list must not be empty')
        for gain in tuple(gains) + fixed_gains:
            if not 0 <= gain < float('inf'):
                raise ValueError('Heading gains must be finite and nonnegative')
    if SWEEP_PARAMETER == 'KI':
        if type(INTEGRAL_WINDOW_MS) is not int or not 0 < INTEGRAL_WINDOW_MS <= 60000:
            raise ValueError('INTEGRAL_WINDOW_MS must be an integer from 1 to 60000')
        if not 0 < INTEGRAL_TURN_LIMIT < float('inf'):
            raise ValueError('INTEGRAL_TURN_LIMIT must be finite and positive')
    if not isinstance(PRINT_DETAILED_DATA, bool):
        raise ValueError('PRINT_DETAILED_DATA must be True or False')
    if type(EXPERIMENT_REPEATS) is not int or EXPERIMENT_REPEATS < 1:
        raise ValueError('EXPERIMENT_REPEATS must be a positive integer')
    # Reserve storage before initializing motors. Extra slots cover the first
    # and final samples. Reuse this allocation for every leg.
    collect()
    try:
        buffer = bytearray((TIMEOUT_MS // SAMPLE_MS + 2) * _RECORD_BYTES) if PRINT_DETAILED_DATA else None
    except MemoryError:
        raise MemoryError('Sample buffer allocation failed; increase SAMPLE_MS or reduce TIMEOUT_MS')
    bot = ComparisonRobot()
    try:
        tests = (('Gyro_Move', 'Move_Straight'), ('Gyro_Move',), ('Move_Straight',))[TEST_MODE - 1]
        cases = []
        for name in tests:
            if name == 'Move_Straight':
                cases.append((name, None, None, None))
            else:
                for gain in gains:
                    kp = gain if SWEEP_PARAMETER == 'KP' else FIXED_HEADING_KP
                    kd = gain if SWEEP_PARAMETER == 'KD' else FIXED_HEADING_KD
                    ki = gain if SWEEP_PARAMETER == 'KI' else 0
                    cases.append((name, kp, kd, ki))
        print('Comparison:', ' + '.join(tests), 'Velocity:', VELOCITY)
        bot.hub.system.set_stop_button((Button.LEFT, Button.RIGHT))
        repeats = 1 if PRINT_DETAILED_DATA else EXPERIMENT_REPEATS
        print('Summary columns:', not PRINT_DETAILED_DATA)
        print('Test mode:', TEST_MODE)
        print('Experiment repeats:', repeats)
        print('Expected movements:', len(cases) * 2 * repeats)
        print('Distance per leg (mm):', DISTANCE)
        print('Acceleration / deceleration:', ACCELERATION, DECELERATION)
        if TEST_MODE in (1, 2):
            print('Sweep parameter:', SWEEP_PARAMETER)
            print('Sweep values:', gains)
        print('Requested sample interval (ms):', SAMPLE_MS)
        print('Reusable sample buffer (bytes):', len(buffer) if buffer is not None else 0)
        for trial in range(1, repeats + 1):
            for name, heading_kp, heading_kd, heading_ki in cases:
                # Emit before each pair so the CSV records the correct gain.
                if name == 'Gyro_Move':
                    print('Gyro_Move Heading_KP:', heading_kp)
                    print('Gyro_Move Heading_KD:', heading_kd)
                    print('Gyro_Move Heading_KI:', heading_ki)
                    print('Integral window (ms):', INTEGRAL_WINDOW_MS if SWEEP_PARAMETER == 'KI' else 0)
                    print('Integral turn limit (deg/s):', INTEGRAL_TURN_LIMIT if SWEEP_PARAMETER == 'KI' else 0)
                    bot.integral_test = SWEEP_PARAMETER == 'KI'
                    bot.experiment_ki = heading_ki
                for distance in (DISTANCE, -DISTANCE):
                    collect()  # Reclaim temporary objects between legs, before movement.
                    print('Next movement:', 'trial', trial, name, 'distance', distance)
                    if distance == DISTANCE:  # Wait only before the forward leg.
                        _wait_for_start(bot)
                    bot.Reset_Gyro()
                    print('Trial:', trial)
                    print('Starting', name, 'distance:', distance)
                    heading = bot.Get_YAW_Angle(False)
                    timer = StopWatch()
                    if name == 'Gyro_Move':
                        task = bot.Gyro_Move(
                            direction=None, distance=distance, velocity=VELOCITY,
                            heading_kp=heading_kp, heading_kd=heading_kd,
                            acceleration=ACCELERATION, deceleration=DECELERATION,
                            stop=Stop.BRAKE, timeout_ms=TIMEOUT_MS, wait=False)
                    else:
                        task = bot.Move_Straight(
                            distance=distance, velocity=VELOCITY,
                            acceleration=ACCELERATION, deceleration=DECELERATION,
                            stop=Stop.BRAKE, timeout_ms=TIMEOUT_MS, wait=False)
                    # Both hold each leg's starting heading. wait=False lets us
                    # record yaw; bot.Wait inside _record services the scheduler.
                    stats = _record(bot, task, timer, heading, buffer)
                    _report(name + ' ' + str(distance), buffer, stats, task.result)
                    bot.Wait(1000)
    finally:
        try:
            bot.Stop_All(stop=Stop.BRAKE)
        finally:
            bot.hub.system.set_stop_button(Button.CENTER)


if __name__ == '__main__':
    main()
