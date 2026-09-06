"""DeltaBots SPIKE Prime base functions for Pybricks 3.6+/4.x.

Cooperative synchronous API: call from a normal script, not an async task.
All finite movement methods accept wait=True (default) or wait=False.
wait=True returns the usual result; wait=False returns a MotionTask handle.
Use bot.Wait(ms), bot.Wait_All(), bot.Wait_For(task), or bot.Update() to
service concurrent jobs. Plain pybricks.tools.wait/time.sleep, long user code,
and blocking raw motor commands DO NOT service custom gyro control or its
timeouts. Motors can continue at their last speed during those gaps.
Call bot.Update() roughly every loop_ms in custom loops. Do not exit the
mission before Wait_All(), unless deliberately cancelling with Stop_All().
One drive job and one job per attachment may overlap; a second command on
an occupied resource raises RuntimeError. Stop_Drive/Attachment_Stop cancel jobs.
All job failures brake/cancel tracked jobs and propagate at the next service.
Ports: drive A/E, attachments B/F, color sensors C/D. Forward motor
directions assume the same build as the original DeltaBots base_robot.py.
Units: distance mm, driving velocity mm/s, motor velocity deg/s,
turn velocity deg/s, acceleration mm/s^2 or deg/s^2 as appropriate.
Positive heading/turn = clockwise; negative distance = reverse.
Stop modes: Stop.BRAKE, Stop.HOLD, Stop.COAST (not SPIKE motor.BRAKE).

Quick start (save this file beside your mission):
    from DeltaBots_Base import DeltaBots, Stop
    bot = DeltaBots()
    bot.Reset_Gyro()
    bot.Gyro_Move(direction=0, distance=300, velocity=150)
    bot.Gyro_Turn(270, pivot=-1)  # relative clockwise 270, left wheel held
    bot.Gyro_Move(direction=270, distance=-100)
    bot.Stop_Line(sensor=0, velocity=60, reflectance=35)
    bot.Attachment_Angle(-1, 90)
    bot.Stop_All()

Concurrent example:
    bot.Reset_Gyro()
    move = bot.Gyro_Move(distance=600, velocity=100, wait=False)
    bot.Wait(2000)  # Driving continues during this delay.
    bot.Attachment_Time(1, 1000, velocity=300, wait=False)
    bot.Attachment_Angle(-1, 90, velocity=200, wait=False)
    bot.Wait_All()
    print(move.result)

Gyro_Turn: relative by default, inclusive [-355,355]; absolute=True means
an accumulated target, NOT the shortest route to a wrapped compass angle.
For example, current 170 -> absolute -170 means -340 degrees.
Get_YAW_Angle defaults to [-180,180); wrapped=False returns accumulated yaw.
Gyro_Move holds a compass direction, using shortest heading correction.
It measures wheel travel, not world-coordinate displacement. Face roughly
the requested direction first; it is not a navigate-to-point command.

Stop_Line with sensor=-1/+1 stops at the selected sensor's threshold.
sensor=0 approaches until EITHER detects the line, then independently
adjusts both wheels until BOTH readings reach reflectance +/- tolerance.
both_mode='any' explicitly selects stop-on-either without alignment.
All line routines require calibration at the actual sensor mounting height.
Two-sensor alignment assumes two sensors mounted ahead of the wheels at equal offsets,
approaching a transverse edge from white into black (or vice versa).

Blocking drive/line/attachment routines have timeouts and raise MotionTimeout
on failure; they brake the drive motors on exceptions. Call Stop_All in a
mission-level finally block if attachments may be running concurrently.
Nonblocking Attachment_Run requires an explicit Attachment_Stop/Stop_All.
Timeouts do not prove stall detection; wheel slip cannot be inferred from
encoders. Motor speed/acceleration and controller gains require field tuning.
Move_Straight uses an internal native DriveBase with IMU enabled. It holds
the starting heading; use Gyro_Turn first to face a different direction.
The module releases native control before custom drive or pivot commands.
Do not create another DriveBase using this robot's drive motors.

Suggested first checks: wheels lifted for direction/port checks, then low
speed +/-90 and +/-355 turns for every pivot, 300 mm forward/reverse,
line tests from both sides and no-line timeout tests. Keep the hub still
during Reset_Gyro. No movement runs just by importing this module.

API reference: docs.pybricks.com/en/stable/hubs/primehub.html and
docs.pybricks.com/en/stable/pupdevices/motor.html.
"""

from math import pi, sqrt
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Axis, Stop
from pybricks.tools import wait, StopWatch

DEFAULT_TIMEOUT_MS = 20000


class MotionTimeout(Exception):
    """Requested motion or sensor condition did not finish in time."""


class MotionTask:
    """Handle returned by wait=False. done/result/cancelled are properties.

    Query after bot.Update() for fresh state, or use bot.Wait_For(handle).
    """

    def __init__(self, owner, resource, iterator):
        self.owner = owner
        self.resource = resource
        self.iterator = iterator
        self.done = False
        self.cancelled = False
        self.result = None
        self.next_poll = -1


def _positive(value, name):
    if not value > 0:
        raise ValueError(name + ' must be positive')


def _clip(value, limit):
    return max(-limit, min(limit, value))


def _wrap(angle):
    return (angle + 180) % 360 - 180


def _mode(stop):
    if stop not in (Stop.BRAKE, Stop.HOLD, Stop.COAST):
        raise ValueError('Use Stop.BRAKE, Stop.HOLD, or Stop.COAST')


def _stop_motor(motor, stop):
    if stop == Stop.HOLD:
        motor.hold()
    elif stop == Stop.BRAKE:
        motor.brake()
    else:
        motor.stop()


class DeltaBots:
    """Create one shared instance per running script; all devices are required."""

    def __init__(self, wheel_diameter=56, axle_track=113,
                 left_drive=Port.A, right_drive=Port.E,
                 left_attachment=Port.B, right_attachment=Port.F,
                 left_sensor=Port.C, right_sensor=Port.D,
                 top_side=Axis.Z, front_side=Axis.X,
                 max_motor_speed=800, loop_ms=10):
        for value, name in ((wheel_diameter, 'wheel_diameter'),
                            (axle_track, 'axle_track'),
                            (max_motor_speed, 'max_motor_speed'),
                            (loop_ms, 'loop_ms')):
            _positive(value, name)
        self.hub = PrimeHub(top_side=top_side, front_side=front_side)
        self.leftDriveMotor = Motor(left_drive, Direction.COUNTERCLOCKWISE)
        self.rightDriveMotor = Motor(right_drive)
        self.leftAttachmentMotor = Motor(left_attachment)
        self.rightAttachmentMotor = Motor(right_attachment)
        self.colorSensorLeft = ColorSensor(left_sensor)
        self.colorSensorRight = ColorSensor(right_sensor)
        self.wheel_diameter = wheel_diameter
        self.axle_track = axle_track
        self.mm_per_degree = pi * wheel_diameter / 360
        self.max_motor_speed = max_motor_speed
        self.loop_ms = loop_ms
        self._tasks = {}
        self._scheduler_clock = StopWatch()
        self._native_drive = None  # Created only when Move_Straight is used.
        self._native_drive_active = False

    def _cancel(self, resource):
        task = self._tasks.pop(resource, None)
        if task is not None:
            task.done = True
            task.cancelled = True
            task.iterator.close()

    def _available(self, resource):
        self.Update()
        if resource in self._tasks:
            raise RuntimeError('Motor resource busy; wait for it or stop it first')

    def _start(self, resource, iterator, wait):
        if not isinstance(wait, bool):
            raise ValueError('wait must be True or False')
        self._available(resource)
        task = MotionTask(self, resource, iterator)
        self._tasks[resource] = task
        self.Update()  # Start immediately; do not defer validation or targets.
        return self.Wait_For(task) if wait else task

    def Update(self):
        """Service all active jobs once, without sleeping; return busy state."""
        try:
            for resource in tuple(self._tasks):
                task = self._tasks.get(resource)
                if task is None:
                    continue
                now = self._scheduler_clock.time()
                if now < task.next_poll:
                    continue
                try:
                    next(task.iterator)
                    task.next_poll = self._scheduler_clock.time() + self.loop_ms
                except StopIteration as finished:
                    task.result = finished.args[0] if finished.args else None
                    task.done = True
                    del self._tasks[resource]
        except BaseException:
            self.Stop_All()
            raise
        return bool(self._tasks)

    def Wait(self, millis):
        """Delay while servicing concurrent jobs. Use instead of tools.wait."""
        if millis < 0:
            raise ValueError('millis must be nonnegative')
        timer = StopWatch()
        try:
            self.Update()
            while timer.time() < millis:
                wait(min(self.loop_ms, max(1, millis - timer.time())))
                self.Update()
        except BaseException:
            self.Stop_All()
            raise

    def Wait_For(self, task):
        """Wait for one handle while servicing every job; return its result."""
        if not isinstance(task, MotionTask) or task.owner is not self:
            raise ValueError('task must belong to this robot')
        while not task.done:
            self.Wait(self.loop_ms)
        if task.cancelled:
            raise RuntimeError('Motion was cancelled')
        return task.result

    def Wait_All(self, timeout_ms=DEFAULT_TIMEOUT_MS):
        """Wait for all tracked finite jobs; does not stop continuous Run.

        Individual deadlines start when each movement is issued. This extra
        timeout starts when Wait_All is called. Override for longer missions.
        """
        _positive(timeout_ms, 'timeout_ms')
        timer = StopWatch()
        try:
            self.Update()
            while self._tasks:
                self._deadline(timer, timeout_ms, 'Wait_All')
                self.Wait(self.loop_ms)
        except BaseException:
            self.Stop_All()
            raise

    def _deadline(self, timer, timeout_ms, operation):
        if timer.time() >= timeout_ms:
            raise MotionTimeout(operation + ' timed out')

    def Stop_Drive(self, stop=Stop.BRAKE):
        """Cancel drive job and stop wheels; attachments retain their state."""
        _mode(stop)
        self._cancel('drive')
        self._stop_drive(stop)

    def _stop_drive(self, stop=Stop.BRAKE):
        _mode(stop)
        self._release_native_drive()
        _stop_motor(self.leftDriveMotor, stop)
        _stop_motor(self.rightDriveMotor, stop)

    def _release_native_drive(self):
        # Stop native control (including a completed HOLD) before individual
        # motor commands. Do this once per handoff, never every control tick.
        if self._native_drive_active:
            self._native_drive.stop()
            self._native_drive_active = False

    def Stop_All(self, stop=Stop.BRAKE):
        """Stop drive wheels and both attachments with explicit stop mode."""
        self.Stop_Drive(stop)
        self._cancel(-1)
        self._cancel(1)
        _stop_motor(self.leftAttachmentMotor, stop)
        _stop_motor(self.rightAttachmentMotor, stop)

    def _tank(self, left, right):
        self._release_native_drive()
        # Inputs are wheel-ground speeds in mm/s. Scale both together to
        # preserve curvature when requested motor speeds exceed our limit.
        left /= self.mm_per_degree
        right /= self.mm_per_degree
        scale = max(1, abs(left) / self.max_motor_speed,
                    abs(right) / self.max_motor_speed)
        self.leftDriveMotor.run(left / scale)
        self.rightDriveMotor.run(right / scale)

    def _drive(self, velocity, turn_rate):
        differential = turn_rate * pi / 180 * self.axle_track / 2
        self._tank(velocity + differential, velocity - differential)

    def Get_Distance(self):
        """Average encoder distance in mm; zero is startup motor reference."""
        return (self.leftDriveMotor.angle() + self.rightDriveMotor.angle()) * self.mm_per_degree / 2


    def Reset_Gyro(self, angle=0, timeout_ms=DEFAULT_TIMEOUT_MS):
        """Coast all motors, wait for ready/stationary IMU, reset yaw.

        Rest loaded attachments on supports before calling: motors release.
        """
        _positive(timeout_ms, 'timeout_ms')
        self.Stop_All(stop=Stop.COAST)
        timer = StopWatch()
        wait(1000)
        while not (self.hub.imu.ready() and self.hub.imu.stationary()):
            self._deadline(timer, timeout_ms, 'Reset_Gyro')
            wait(self.loop_ms)
        self.hub.imu.reset_heading(angle)
        return self.Get_YAW_Angle(wrapped=False)

    def Get_YAW_Angle(self, wrapped=True):
        """Clockwise-positive yaw: wrapped [-180,180), or accumulated."""
        heading = self.hub.imu.heading()
        return _wrap(heading) if wrapped else heading

    def Gyro_Turn(self, angle, pivot=0, velocity=90, acceleration=200,
                  deceleration=300, tolerance=1, stop=Stop.BRAKE,
                  timeout_ms=DEFAULT_TIMEOUT_MS, absolute=False, kp=3, wait=True):
        """Relative/absolute gyro turn; wait=False starts concurrent control.

        pivot: any finite value; -1 left wheel, 0 center, +1 right wheel.
        Use Wait/Wait_All/Update to service the nonblocking controller.
        """
        return self._start('drive', self._gyro_turn(angle, pivot, velocity,
            acceleration, deceleration, tolerance, stop, timeout_ms, absolute, kp), wait)

    def _gyro_turn(self, angle, pivot, velocity, acceleration, deceleration,
                   tolerance, stop, timeout_ms, absolute, kp):
        """Turn signed degrees; pivot -1=left, 0=center, +1=right.

        Any finite pivot is supported, including fractional values.
        Turning point offset to the right of axle center is
        pivot * axle_track / 2 mm. Values below -1 place it left of the
        left wheel; values above +1 place it right of the right wheel.
        Large offsets can reduce actual turn rate due to motor speed limits.
        Angle, not
        velocity sign, selects direction. Returns final accumulated heading.
        Accel/decel bound the requested angular speed ramp, subject to motor
        controller limits. Three stable samples within tolerance finish.
        """
        _mode(stop)
        for v, n in ((velocity, 'velocity'), (acceleration, 'acceleration'),
                     (deceleration, 'deceleration'), (tolerance, 'tolerance'),
                     (timeout_ms, 'timeout_ms'), (kp, 'kp')):
            _positive(v, n)
        if not -float('inf') < pivot < float('inf'):
            raise ValueError('pivot must be finite')
        start = self.Get_YAW_Angle(False)
        target = angle if absolute else start + angle
        if not -355 <= target - start <= 355:
            raise ValueError('requested rotation must be within [-355,355]')
        timer = StopWatch()
        previous_time = 0
        rate = 0
        stable = 0
        previous_heading = start
        try:
            self._stop_drive()
            while True:
                self._deadline(timer, timeout_ms, 'Gyro_Turn')
                now = timer.time()
                dt = max(1, now - previous_time) / 1000
                previous_time = now
                heading = self.Get_YAW_Angle(False)
                error = target - heading  # NEVER wrap long-turn error
                measured_rate = (heading - previous_heading) / dt
                previous_heading = heading
                if abs(error) <= tolerance:
                    self._stop_drive(Stop.BRAKE)
                    rate = 0
                    stable = stable + 1 if abs(measured_rate) < 5 else 0
                    if stable >= 3:
                        break
                else:
                    stable = 0
                    desired = min(velocity, kp * abs(error),
                                  sqrt(2 * deceleration * abs(error)))
                    desired *= 1 if error > 0 else -1
                    limit = acceleration if rate * desired >= 0 and abs(desired) > abs(rate) else deceleration
                    rate += _clip(desired - rate, limit * dt)
                    # Pivot sign selects lateral center of rotation.
                    differential = rate * pi / 180 * self.axle_track / 2
                    if pivot == -1:
                        self.leftDriveMotor.hold()
                        self.rightDriveMotor.run(_clip(-2 * differential / self.mm_per_degree, self.max_motor_speed))
                    elif pivot == 1:
                        self.rightDriveMotor.hold()
                        self.leftDriveMotor.run(_clip(2 * differential / self.mm_per_degree, self.max_motor_speed))
                    else:
                        self._tank(differential * (1 + pivot), differential * (pivot - 1))
                yield
        except BaseException:
            self._stop_drive(Stop.BRAKE)
            raise
        self._stop_drive(stop)
        return self.Get_YAW_Angle(False)

    def Gyro_Move(self, direction=None, distance=100, velocity=150,
                  acceleration=200, deceleration=400, stop=Stop.BRAKE,
                  timeout_ms=DEFAULT_TIMEOUT_MS, tolerance=2, heading_kp=1.5,
                  max_turn_rate=60, distance_kp=4, wait=True,
                  heading_kd=0.5, turn_acceleration=120):
        """Drive signed mm along heading; wait=False starts concurrent control.

        direction=None holds starting heading. Driving units mm/s, mm/s^2.
        Returns travel if blocking, otherwise a MotionTask handle.
        Steering uses heading_kp * heading_error - heading_kd * yaw_rate.
        The yaw rate is estimated from heading and filtered over 50 ms.
        heading_kd >= 0 damps steering; turn_acceleration (deg/s^2) limits
        changes in steering rate. These defaults need testing on your robot.
        Existing positional arguments keep their meaning; new options are last.
        """
        return self._start('drive', self._gyro_move(direction, distance, velocity,
            acceleration, deceleration, stop, timeout_ms, tolerance, heading_kp,
            max_turn_rate, distance_kp, heading_kd, turn_acceleration), wait)

    def _gyro_move(self, direction, distance, velocity, acceleration,
                   deceleration, stop, timeout_ms, tolerance, heading_kp,
                   max_turn_rate, distance_kp, heading_kd, turn_acceleration):
        """Drive signed mm while maintaining direction (None=current yaw).

        Velocity is a positive magnitude in mm/s. Distance controls reverse.
        Returns actual signed encoder travel. Heading gains are turn-rate
        per degree; acceleration/deceleration shape commanded linear speed.
        """
        _mode(stop)
        for v, n in ((velocity, 'velocity'), (acceleration, 'acceleration'),
                     (deceleration, 'deceleration'), (timeout_ms, 'timeout_ms'),
                     (tolerance, 'tolerance'), (heading_kp, 'heading_kp'),
                     (max_turn_rate, 'max_turn_rate'), (distance_kp, 'distance_kp'),
                     (turn_acceleration, 'turn_acceleration')):
            _positive(v, n)
        if not 0 <= heading_kd < float('inf'):
            raise ValueError('heading_kd must be finite and nonnegative')
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
                self._deadline(timer, timeout_ms, 'Gyro_Move')
                now = timer.time()
                dt = max(1, now - last_time) / 1000
                last_time = now
                heading = self.Get_YAW_Angle(False)
                measured_rate = _wrap(heading - previous_heading) / dt
                previous_heading = heading
                yaw_rate += dt / (0.05 + dt) * (measured_rate - yaw_rate)
                error = distance - (self.Get_Distance() - start)
                if abs(error) <= tolerance:
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
                    desired_correction = _clip(
                        heading_kp * _wrap(target_heading - heading)
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

    def Move_Straight(self, distance=100, velocity=150, acceleration=200,
                      deceleration=400, stop=Stop.BRAKE,
                      timeout_ms=DEFAULT_TIMEOUT_MS, wait=True):
        """Native DriveBase distance driving with IMU enabled.

        Holds the heading at the start of this call; does not reset the gyro
        or turn to a supplied direction. Positive distance moves forward,
        negative moves backward. Velocity is positive mm/s; acceleration
        and deceleration are positive mm/s^2. Uses native stopping criteria.

        Default wait=True returns actual signed encoder travel in mm after
        completion. Master cancellation remains responsive while waiting.
        Optional wait=False returns a MotionTask; use Wait/Wait_All as usual.
        Shares the drive resource with Gyro_Move, Gyro_Turn and Stop_Line.
        """
        return self._start('drive', self._move_straight(distance, velocity,
            acceleration, deceleration, stop, timeout_ms), wait)

    def _move_straight(self, distance, velocity, acceleration, deceleration,
                       stop, timeout_ms):
        _mode(stop)
        if not -float('inf') < distance < float('inf'):
            raise ValueError('distance must be finite')
        for value, name in ((velocity, 'velocity'),
                            (acceleration, 'acceleration'),
                            (deceleration, 'deceleration'),
                            (timeout_ms, 'timeout_ms')):
            if not 0 < value < float('inf'):
                raise ValueError(name + ' must be finite and positive')
        timer = StopWatch()
        start = self.Get_Distance()
        try:
            self._stop_drive(Stop.BRAKE)
            if self._native_drive is None:
                from pybricks.robotics import DriveBase
                self._native_drive = DriveBase(
                    self.leftDriveMotor, self.rightDriveMotor,
                    self.wheel_diameter, self.axle_track)
            drive = self._native_drive
            drive.use_gyro(True)  # Also releases the preceding native target.
            drive.settings(
                straight_speed=min(velocity, self.max_motor_speed * self.mm_per_degree),
                straight_acceleration=(acceleration, deceleration))
            self._native_drive_active = True
            # Native firmware controls the motors; Python only monitors
            # completion/deadline so menu cancellation still gets serviced.
            drive.straight(distance, then=stop, wait=False)
            while not drive.done():
                self._deadline(timer, timeout_ms, 'Move_Straight')
                yield
        except BaseException:
            self._stop_drive(Stop.BRAKE)
            raise
        # Preserve native then=stop, including gyro HOLD until the next move.
        return self.Get_Distance() - start

    def Drive_Time(self, millis, velocity=100, direction=None, stop=Stop.BRAKE,
                   timeout_ms=DEFAULT_TIMEOUT_MS, wait=True):
        """Timed gyro drive in signed mm/s; optionally start without waiting."""
        return self._start('drive', self._drive_time(millis, velocity, direction,
                                                    stop, timeout_ms), wait)

    def _drive_time(self, millis, velocity, direction, stop, timeout_ms):
        """Timed gyro drive; millis >=0, signed mm/s, 20 s default timeout.

        For durations above 20 s, explicitly increase timeout_ms too.
        """
        if millis < 0:
            raise ValueError('millis must be nonnegative')
        _positive(timeout_ms, 'timeout_ms')
        if millis > timeout_ms:
            raise ValueError('millis must not exceed timeout_ms')
        _mode(stop)
        heading = self.Get_YAW_Angle(False) if direction is None else direction
        timer = StopWatch()
        try:
            while timer.time() < millis:
                self._deadline(timer, timeout_ms, 'Drive_Time')
                self._drive(velocity, _clip(3 * _wrap(heading - self.Get_YAW_Angle(False)), 60))
                yield
        except BaseException:
            self._stop_drive()
            raise
        self._stop_drive(stop)

    def Read_Reflectance(self, sensor=0):
        """-1=left, +1=right, 0=(left,right); readings in percent."""
        if sensor == -1:
            return self.colorSensorLeft.reflection()
        if sensor == 1:
            return self.colorSensorRight.reflection()
        if sensor == 0:
            return (self.colorSensorLeft.reflection(), self.colorSensorRight.reflection())
        raise ValueError('sensor must be -1, 0, or +1')

    def Print_Reflectance(self):
        """Print both color sensor reflectances once; return (left, right).

        Example: bot.Print_Reflectance()
        For repeated readings, call in a loop with bot.Wait(200).
        Does not change any motor state.
        """
        left, right = self.Read_Reflectance()
        print('Left:', left, 'Right:', right)
        return left, right

    def Stop_Line(self, sensor=0, velocity=80, reflectance=50,
                  stop=Stop.BRAKE, timeout_ms=DEFAULT_TIMEOUT_MS, both_mode='all',
                  stop_below=True, consecutive=3, max_distance=1000,
                  tolerance=2, fine_velocity=30, align_kp=1.5, wait=True):
        """Find a line, optionally concurrently. sensor=0/all aligns both.

        -1/+1 stop on a single threshold; 0/any stops on either threshold.
        0/all approaches then adjusts each wheel to reflectance +/- tolerance.
        Timeout spans both phases. Use Wait/Wait_All to service wait=False.
        """
        return self._start('drive', self._stop_line(sensor, velocity, reflectance,
            stop, timeout_ms, both_mode, stop_below, consecutive, max_distance,
            tolerance, fine_velocity, align_kp), wait)

    def _stop_line(self, sensor, velocity, reflectance, stop, timeout_ms,
                   both_mode, stop_below, consecutive, max_distance,
                   tolerance, fine_velocity, align_kp):
        """Find a line using -1=left, +1=right, 0=both sensors.

        Single sensors retain threshold-only stopping. sensor=0/all follows
        the reference SPIKE routine: approach until either sensor detects,
        brake, then independently drive each wheel forward/backward toward
        the target reflectance band. An in-band wheel brakes, and can correct
        again if its reading leaves the band. Both must remain in band for
        consecutive samples. No gyro heading hold during alignment.

        sensor=0/any stops on either sensor without fine alignment.
        stop_below=False reverses polarity for dark-to-bright approaches.
        Negative velocity reverses travel and the fine correction direction.
        Fine wheel speed is proportional, capped by fine_velocity (mm/s).
        Matched sensor geometry and a reachable line-edge target are required.
        Timeout covers BOTH phases together, not 20 s for each phase.
        max_distance limits cumulative travel of either wheel across phases.
        Returns (left,right); timeout/travel limit raises MotionTimeout.
        """
        _mode(stop)
        if sensor not in (-1, 0, 1) or both_mode not in ('all', 'any'):
            raise ValueError('invalid sensor or both_mode')
        if not 0 <= reflectance <= 100 or velocity == 0:
            raise ValueError('reflectance must be 0..100 and velocity nonzero')
        _positive(timeout_ms, 'timeout_ms')
        _positive(max_distance, 'max_distance')
        if not isinstance(consecutive, int) or consecutive < 1:
            raise ValueError('consecutive must be a positive integer')
        align_both = sensor == 0 and both_mode == 'all'
        if align_both:
            for v, n in ((tolerance, 'tolerance'), (fine_velocity, 'fine_velocity'),
                         (align_kp, 'align_kp')):
                _positive(v, n)
            if not tolerance < reflectance < 100 - tolerance:
                raise ValueError('choose an edge reflectance away from 0/100')
        motors = (self.leftDriveMotor, self.rightDriveMotor)
        previous_angles = [motor.angle() for motor in motors]
        travel = [0, 0]
        heading = self.Get_YAW_Angle(False)
        timer = StopWatch()
        count = 0
        fine = False
        travel_sign = 1 if velocity > 0 else -1
        polarity = 1 if stop_below else -1
        try:
            while True:
                self._deadline(timer, timeout_ms, 'Stop_Line')
                for i, motor in enumerate(motors):
                    angle = motor.angle()
                    travel[i] += abs(angle - previous_angles[i]) * self.mm_per_degree
                    previous_angles[i] = angle
                if max(travel) >= max_distance:
                    raise MotionTimeout('Stop_Line exceeded max_distance')
                left, right = self.Read_Reflectance()
                hits = (left <= reflectance, right <= reflectance) if stop_below else (left >= reflectance, right >= reflectance)
                if align_both:
                    if not fine and any(hits):
                        self._stop_drive(Stop.BRAKE)
                        fine = True
                        yield
                        continue  # Read fresh samples after approach braking.
                    if fine:
                        errors = (left - reflectance, right - reflectance)
                        in_range = [abs(e) <= tolerance for e in errors]
                        count = count + 1 if all(in_range) else 0
                        if count >= consecutive:
                            break
                        for motor, error, ok in zip(motors, errors, in_range):
                            if ok:
                                motor.brake()
                            else:
                                speed = travel_sign * polarity * _clip(align_kp * error, fine_velocity)
                                motor.run(_clip(speed / self.mm_per_degree, self.max_motor_speed))
                    else:
                        self._drive(velocity, _clip(3 * _wrap(heading - self.Get_YAW_Angle(False)), 60))
                    yield
                    continue
                hit = hits[0] if sensor == -1 else hits[1] if sensor == 1 else any(hits)
                count = count + 1 if hit else 0
                if hit:
                    self._stop_drive(Stop.BRAKE)
                    if count >= consecutive:
                        break
                else:
                    self._drive(velocity, _clip(3 * _wrap(heading - self.Get_YAW_Angle(False)), 60))
                yield
        except BaseException:
            self._stop_drive()
            raise
        self._stop_drive(stop)
        return self.Read_Reflectance()


    def _attachment(self, side):
        if side == -1:
            return self.leftAttachmentMotor
        if side == 1:
            return self.rightAttachmentMotor
        raise ValueError('attachment side must be -1 (left) or +1 (right)')

    def _attachment_motion(self, side, kind, amount, velocity, stop, timeout_ms):
        motor = self._attachment(side)
        timer = StopWatch()
        try:
            if kind == 'angle':
                motor.run_angle(velocity, amount, then=stop, wait=False)
            elif kind == 'target':
                motor.run_target(velocity, amount, then=stop, wait=False)
            else:
                motor.run_time(velocity, amount, then=stop, wait=False)
            while not motor.done():
                self._deadline(timer, timeout_ms, 'Attachment')
                yield
        except BaseException:
            motor.brake()
            raise
        return motor.angle()

    def Attachment_Angle(self, side, angle, velocity=300,
                         stop=Stop.HOLD, timeout_ms=DEFAULT_TIMEOUT_MS, wait=True):
        """Relative signed motor degrees; wait=False returns a MotionTask."""
        _mode(stop)
        _positive(velocity, 'velocity')
        _positive(timeout_ms, 'timeout_ms')
        self._attachment(side)
        return self._start(side, self._attachment_motion(side, 'angle', angle,
            velocity, stop, timeout_ms), wait)

    def Attachment_Target(self, side, angle, velocity=300,
                          stop=Stop.HOLD, timeout_ms=DEFAULT_TIMEOUT_MS, wait=True):
        """Absolute motor target; establish mechanical zero explicitly first."""
        _mode(stop)
        _positive(velocity, 'velocity')
        _positive(timeout_ms, 'timeout_ms')
        self._attachment(side)
        return self._start(side, self._attachment_motion(side, 'target', angle,
            velocity, stop, timeout_ms), wait)

    def Attachment_Time(self, side, millis, velocity=300, stop=Stop.HOLD,
                        timeout_ms=DEFAULT_TIMEOUT_MS, wait=True):
        """Timed motor movement, signed deg/s; wait=False returns immediately."""
        _mode(stop)
        _positive(millis, 'millis')
        _positive(timeout_ms, 'timeout_ms')
        if millis > timeout_ms:
            raise ValueError('millis must not exceed timeout_ms')
        self._attachment(side)
        return self._start(side, self._attachment_motion(side, 'time', millis,
            velocity, stop, timeout_ms), wait)

    def Attachment_Run(self, side, velocity=300):
        """Continuous nonblocking motor command. Caller MUST stop it."""
        motor = self._attachment(side)
        self._available(side)
        motor.run(velocity)

    def Attachment_Stop(self, side, stop=Stop.HOLD):
        _mode(stop)
        motor = self._attachment(side)
        self._cancel(side)
        _stop_motor(motor, stop)

    def Attachment_Reset(self, side, angle=0):
        """Assign motor encoder reference; does NOT mechanically home arm."""
        motor = self._attachment(side)
        self._cancel(side)
        motor.brake()
        motor.reset_angle(angle)
