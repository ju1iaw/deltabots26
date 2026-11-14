# Coach_Test.py
# Robot test bench. Choose a test with LEFT/RIGHT (number on the hub
# display), then press and release CENTER to run it. Afterwards the next
# test is selected.
#   'move' tests: drive forward 1.5 m, pause 2 s, drive backward 1.5 m.
#   'turn' tests: turn 90 deg clockwise, pause 1 s, turn back.
# Press LEFT + RIGHT together to end the program.
#
# For each leg it prints the ACTUAL measured top speed, cruise speed,
# acceleration and deceleration (from the wheel motors' speed readings).
# Watch for wheel slip: the numbers come from the wheels, so slip won't show.
# Leave at least 2 m of clear space in front of and behind the robot.
#
# Run directly (not from the master):
#   .venv/bin/pybricksdev run ble --name "Alyssa" Coach_Test.py
#
# This file only changes limits while it runs; DeltaBots_Base.py is untouched.

from DeltaBots_Base import DeltaBots, Stop
from pybricks.parameters import Button, Color
from pybricks.tools import StopWatch

try:
    import gc
except ImportError:
    gc = None

# ----- TEST SETTINGS (edit these) -----
# ('move', speed cap deg/s, acceleration mm/s^2, deceleration mm/s^2, min_speed mm/s)
# ('turn', angle deg, velocity deg/s, min_rate deg/s)
# min_speed / min_rate = creep fix (0 = old behavior, slow crawl at the end).
# Speed: 1000 deg/s = 489 mm/s with 56 mm wheels.
# Hardware results 2026-11-13: top speed about 1100 deg/s (540 mm/s);
# wheel slip at 1600 mm/s^2, none at 1200. See CHANGELOG.md.
TESTS = (
    ('move', 1000, 400, 400, 0),     # 1: default accel/decel, old ending
    ('move', 1000, 400, 400, 40),    # 2: default accel/decel, creep fix (default)
    ('move', 1000, 800, 800, 0),     # 3: faster accel/decel, old ending
    ('move', 1000, 800, 800, 40),    # 4: faster accel/decel, creep fix
    ('move', 1000, 800, 800, 60),    # 5: faster accel/decel, stronger creep fix
    ('turn', 90, 90, 0),             # 6: turn without creep fix
    ('turn', 90, 90, 20),            # 7: turn with creep fix (default)
    ('turn', 90, 90, 30),            # 8: turn with stronger creep fix
    # Turn rows use the Gyro_Turn defaults kp=16, lead_ms=40.
)
DISTANCE = 1500        # mm per leg (longer = more time at top speed)
PAUSE_MS = 2000        # pause between forward and backward

# The drive motors also have firmware limits (default 1000 deg/s, 2000 deg/s^2).
# For this test we raise them so the settings above (or the hardware) limit.
FIRMWARE_SPEED_LIMIT = 2000    # deg/s
FIRMWARE_ACCEL_LIMIT = 10000   # deg/s^2 (about 4900 mm/s^2)

# Speed readings are kept in lists created once, so the hub does not run
# out of memory (10 ms per reading: 1000 readings = 10 s per leg).
MAX_SAMPLES = 1000
_times = [0] * MAX_SAMPLES      # ms
_speeds = [0] * MAX_SAMPLES     # mm/s


def Choose_Test(bot, index):
    """LEFT/RIGHT change the test number; CENTER press-and-release starts it."""
    bot.hub.display.number(index + 1)
    while bot.hub.buttons.pressed():            # wait until all buttons are up
        bot.Wait(10)
    while True:
        if bot.hub.buttons.pressed():
            held = set()
            while bot.hub.buttons.pressed():     # wait for release
                for button in bot.hub.buttons.pressed():
                    held.add(button)
                bot.Wait(10)
            if held == {Button.CENTER}:
                return index
            if held == {Button.RIGHT}:
                index = (index + 1) % len(TESTS)
            elif held == {Button.LEFT}:
                index = (index - 1) % len(TESTS)
            bot.hub.display.number(index + 1)
            print('Selected test %d %s' % (index + 1, TESTS[index]))
        bot.Wait(10)


def Drive_Speed(bot):
    """Measured driving speed in mm/s (average of both wheel motors)."""
    return ((bot.leftDriveMotor.speed() + bot.rightDriveMotor.speed()) / 2
            * bot.mm_per_degree)


def _Accel_Value(accel):
    """Firmware may report acceleration as a number or (accel, decel)."""
    return accel[0] if isinstance(accel, (tuple, list)) else accel


def Try_Raise_Firmware_Limits(bot):
    """Try to raise the drive motors' firmware limits; report what happened."""
    for label, motor in (('Left', bot.leftDriveMotor), ('Right', bot.rightDriveMotor)):
        speed, accel, torque = motor.control.limits()
        new_accel = ((FIRMWARE_ACCEL_LIMIT, FIRMWARE_ACCEL_LIMIT)
                     if isinstance(accel, (tuple, list)) else FIRMWARE_ACCEL_LIMIT)
        for name, kwargs in (('speed', {'speed': FIRMWARE_SPEED_LIMIT}),
                             ('acceleration', {'acceleration': new_accel})):
            try:
                motor.control.limits(**kwargs)
            except Exception as error:
                print('%s motor: firmware refused higher %s (%s)' % (label, name, error))


def Print_Firmware_Limits(bot, title):
    mm = bot.mm_per_degree
    for label, motor in (('Left ', bot.leftDriveMotor), ('Right', bot.rightDriveMotor)):
        speed, accel, torque = motor.control.limits()
        accel = _Accel_Value(accel)
        print('%s %s motor: speed %d deg/s = %d mm/s, acceleration %d deg/s^2 = %d mm/s^2'
              % (title, label, round(speed), round(speed * mm), round(accel), round(accel * mm)))


def _Average_Rate(first, last, from_speed, to_speed):
    """Average |speed change| per second between two speed crossings,
    searching readings first..last (inclusive)."""
    rising = to_speed > from_speed
    t_from = t_to = None
    for i in range(first, last + 1):
        speed = _speeds[i]
        if t_from is None:
            if (speed >= from_speed) if rising else (speed <= from_speed):
                t_from = _times[i]
        elif (speed >= to_speed) if rising else (speed <= to_speed):
            t_to = _times[i]
            break
    if t_from is None or t_to is None or t_to <= t_from:
        return 'n/a'
    return str(round(abs(to_speed - from_speed) * 1000 / (t_to - t_from)))


def Measured_Move(bot, name, distance, acceleration, deceleration, min_speed):
    """Gyro_Move while measuring actual speed, acceleration and deceleration.

    Top speed    = highest wheel speed reading.
    Cruise speed = average of readings within 5% of top speed.
    Acceleration = average while speeding up from 10% to 90% of top speed.
    Deceleration = average while slowing from 90% to 25% of top speed
                   (stops before the final brake, which would give a spike).
    """
    if gc is not None:
        gc.collect()
    velocity = bot.max_motor_speed * bot.mm_per_degree   # ask for the full cap
    start = bot.Get_Distance()
    near_ms = None        # first time within 10 mm of the target
    count = 0
    timer = StopWatch()
    task = bot.Gyro_Move(direction=0, distance=distance, velocity=velocity,
                         acceleration=acceleration, deceleration=deceleration,
                         min_speed=min_speed, stop=Stop.BRAKE, wait=False)
    while not task.done:
        bot.Wait(10)      # keeps the move running and allows cancelling
        now = timer.time()
        if count < MAX_SAMPLES:
            _times[count] = now
            _speeds[count] = int(abs(Drive_Speed(bot)))
            count += 1
        if near_ms is None and abs(distance - (bot.Get_Distance() - start)) <= 10:
            near_ms = now
    seconds = timer.time() / 1000
    near = 'n/a' if near_ms is None else '%.2f s' % (near_ms / 1000)
    print('  %s: %d mm in %.2f s (within 10 mm at %s), heading %d deg'
          % (name, round(task.result), seconds, near, round(bot.Get_YAW_Angle())))
    if count == 0:
        return

    top = 0
    peak = 0
    for i in range(count):
        if _speeds[i] > top:
            top = _speeds[i]
            peak = i
    total = 0
    n = 0
    for i in range(count):
        if _speeds[i] >= 0.95 * top:
            total += _speeds[i]
            n += 1
    cruise = total // n if n else 0
    accel = _Average_Rate(0, peak, 0.10 * top, 0.90 * top)
    decel = _Average_Rate(peak, count - 1, 0.90 * top, 0.25 * top)
    print('      top %d mm/s | cruise %d mm/s | accel %s mm/s^2 | decel %s mm/s^2'
          % (top, cruise, accel, decel))


def Measured_Turn(bot, name, angle, velocity, min_rate):
    """Gyro_Turn by angle; report time, time to within 2 deg, final error."""
    if gc is not None:
        gc.collect()
    start = bot.Get_YAW_Angle(wrapped=False)
    target = start + angle
    near_ms = None        # first time within 2 deg of the target
    timer = StopWatch()
    task = bot.Gyro_Turn(angle, velocity=velocity, min_rate=min_rate,
                         stop=Stop.BRAKE, wait=False)
    while not task.done:
        bot.Wait(10)
        if near_ms is None and abs(target - bot.Get_YAW_Angle(wrapped=False)) <= 2:
            near_ms = timer.time()
    seconds = timer.time() / 1000
    bot.Wait(300)         # let the robot settle, then measure the final error
    error = bot.Get_YAW_Angle(wrapped=False) - target
    near = 'n/a' if near_ms is None else '%.2f s' % (near_ms / 1000)
    print('  %s: %.2f s (within 2 deg at %s), final error %.1f deg'
          % (name, seconds, near, error))


def Run_Test(bot, number, test):
    bot.Reset_Gyro(0)
    if test[0] == 'move':
        kind, cap, acceleration, deceleration, min_speed = test
        bot.max_motor_speed = min(cap, FIRMWARE_SPEED_LIMIT)
        print('Test %d: move, speed cap %d deg/s (%d mm/s), accel %d, decel %d mm/s^2, '
              'min_speed %d mm/s'
              % (number, round(bot.max_motor_speed),
                 round(bot.max_motor_speed * bot.mm_per_degree),
                 acceleration, deceleration, min_speed))
        Measured_Move(bot, 'Forward ', DISTANCE, acceleration, deceleration, min_speed)
        bot.Wait(PAUSE_MS)
        Measured_Move(bot, 'Backward', -DISTANCE, acceleration, deceleration, min_speed)
    else:
        kind, angle, velocity, min_rate = test
        print('Test %d: turn %d deg, velocity %d deg/s, min_rate %d deg/s'
              % (number, angle, velocity, min_rate))
        Measured_Turn(bot, 'Turn  %+d' % angle, angle, velocity, min_rate)
        bot.Wait(1000)
        Measured_Turn(bot, 'Turn  %+d' % -angle, -angle, velocity, min_rate)


def main():
    bot = DeltaBots()
    # CENTER normally stops a Pybricks program; use LEFT+RIGHT to stop instead.
    bot.hub.system.set_stop_button((Button.LEFT, Button.RIGHT))
    motors = (bot.leftDriveMotor, bot.rightDriveMotor)
    original = [m.control.limits() for m in motors]
    try:
        Print_Firmware_Limits(bot, 'Default ')
        Try_Raise_Firmware_Limits(bot)
        Print_Firmware_Limits(bot, 'For test')
        index = 0
        while True:
            bot.hub.light.on(Color.GREEN)       # green = ready
            print('Ready: test %d %s. LEFT/RIGHT to change, CENTER to run, '
                  'LEFT+RIGHT to quit.' % (index + 1, TESTS[index]))
            index = Choose_Test(bot, index)
            bot.hub.light.on(Color.ORANGE)      # orange = running
            Run_Test(bot, index + 1, TESTS[index])
            index = (index + 1) % len(TESTS)
    finally:
        bot.Stop_All(stop=Stop.BRAKE)
        for motor, (speed, accel, torque) in zip(motors, original):
            try:
                motor.control.limits(speed=speed, acceleration=accel)
            except Exception:
                pass
        bot.hub.system.set_stop_button(Button.CENTER)


if __name__ == "__main__":
    main()
