# Turn_Tuner.py
# Automatic Gyro_Turn tuning. First runs the BASELINE setting, then every
# combination of KP_VALUES and LEAD_VALUES, on turns of 30, 90 and 180 degrees
# (each turn and its return). Measures time, overshoot and final error, then
# prints a summary with the fastest settings that did NOT overshoot.
#
#   kp      = how strongly the turn slows down near the target.
#   lead_ms = brake early to make up for gyro/motor delay (0 = off).
# Gyro_Turn defaults since 2026-11-13: kp=16, lead_ms=40 (from round 2).
#
# Place the robot on the mat with about 40 cm of free space around it; it
# turns in place. Press and release CENTER to start (takes about 4-5 minutes).
# Press LEFT + RIGHT together to stop at any time.
#
# Run directly (not from the master):
#   .venv/bin/pybricksdev run ble --name "Alyssa" Turn_Tuner.py
# Then copy everything it printed and send it back for analysis.

from DeltaBots_Base import DeltaBots, Stop, MotionTimeout
from pybricks.parameters import Button, Color
from pybricks.tools import StopWatch

# ----- TEST SETTINGS (edit these) -----
VELOCITY = 200          # deg/s (the value most programs use)
ACCELERATION = 200      # deg/s^2 (Gyro_Turn default)
DECELERATION = 300      # deg/s^2 (Gyro_Turn default)
MIN_RATE = 20           # deg/s (creep fix default)
ANGLES = (30, 90, 180)  # each angle is turned, then turned back
BASELINE = (3, 0)       # (kp, lead_ms) of the OLD setting, for comparison
# Round 1 (2026-11-13): kp 3/5/8/12 x lead 0/40/80/120 -> best kp 12, lead 40.
# Round 1 was on the floor. Round 2 is on the game mat (fine sweep, with 60 ms
# added in case the mat needs more brake-early than the floor):
KP_VALUES = (8, 12, 16)
LEAD_VALUES = (20, 30, 40, 50, 60)  # ms
OVERSHOOT_LIMIT = 0.5   # deg: a setting passes only if no turn went further
                        # past its target than this
FINAL_LIMIT = 1.0       # deg: and every final error is within this
SETTLE_MS = 300         # keep watching this long after each turn stops
PAUSE_MS = 300          # pause between turns
TURN_TIMEOUT_MS = 5000  # a turn that takes longer counts as failed


def Wait_For_Center(bot):
    """Return after CENTER is pressed and released."""
    while bot.hub.buttons.pressed():
        bot.Wait(10)
    while Button.CENTER not in bot.hub.buttons.pressed():
        bot.Wait(10)
    while Button.CENTER in bot.hub.buttons.pressed():
        bot.Wait(10)


def Measure_Turn(bot, angle, kp, lead):
    """Return (seconds, overshoot deg, final error deg) for one turn.

    overshoot = furthest the robot went PAST the target (0 if never past).
    final     = error after settling: + past the target, - short of it.
    """
    start = bot.Get_YAW_Angle(False)
    target = start + angle
    sign = 1 if angle > 0 else -1
    over = 0
    timer = StopWatch()
    task = bot.Gyro_Turn(angle, pivot=0, velocity=VELOCITY,
                         acceleration=ACCELERATION, deceleration=DECELERATION,
                         kp=kp, min_rate=MIN_RATE, lead_ms=lead,
                         timeout_ms=TURN_TIMEOUT_MS, stop=Stop.BRAKE, wait=False)
    while not task.done:
        bot.Wait(10)
        over = max(over, (bot.Get_YAW_Angle(False) - target) * sign)
    seconds = timer.time() / 1000
    settle = StopWatch()
    while settle.time() < SETTLE_MS:
        bot.Wait(10)
        over = max(over, (bot.Get_YAW_Angle(False) - target) * sign)
    final = (bot.Get_YAW_Angle(False) - target) * sign
    return seconds, over, final


def Test_Setting(bot, number, total, kp, lead):
    """Run all angles (there and back) for one kp/lead combination."""
    bot.hub.display.number(number)
    times = []
    worst_over = 0
    worst_final = 0
    failed = False
    for angle in ANGLES:
        pair = 0
        for signed in (angle, -angle):
            try:
                seconds, over, final = Measure_Turn(bot, signed, kp, lead)
            except MotionTimeout:
                bot.Stop_Drive()
                print('  kp %d lead %d: %+d deg turn timed out' % (kp, lead, signed))
                failed = True
                seconds, over, final = TURN_TIMEOUT_MS / 1000, 0, 0
            pair += seconds
            worst_over = max(worst_over, over)
            worst_final = max(worst_final, abs(final))
            bot.Wait(PAUSE_MS)
        times.append(pair / 2)
    ok = (not failed and worst_over <= OVERSHOOT_LIMIT
          and worst_final <= FINAL_LIMIT)
    line = '%2d/%d kp %2d lead %2d ms |' % (number, total, kp, lead)
    for angle, seconds in zip(ANGLES, times):
        line += ' %3d deg %.2f s |' % (angle, seconds)
    line += ' overshoot %.1f | final %.1f | %s' % (
        worst_over, worst_final, 'OK' if ok else 'FAIL')
    print(line)
    return (kp, lead, sum(times), worst_over, worst_final, ok)


def Run_Sweep(bot):
    combos = [(kp, lead) for lead in LEAD_VALUES for kp in KP_VALUES]
    if BASELINE not in combos:
        combos.insert(0, BASELINE)
    print('Turn tuning: velocity %d, accel %d, decel %d, min_rate %d; '
          'pass = overshoot <= %.1f and final <= %.1f deg'
          % (VELOCITY, ACCELERATION, DECELERATION, MIN_RATE,
             OVERSHOOT_LIMIT, FINAL_LIMIT))
    bot.Reset_Gyro(0)
    results = []
    for i, (kp, lead) in enumerate(combos):
        results.append(Test_Setting(bot, i + 1, len(combos), kp, lead))

    baseline = None
    for r in results:
        if (r[0], r[1]) == BASELINE:
            baseline = r
    passing = sorted([r for r in results if r[5]], key=lambda r: r[2])
    print('----- SUMMARY -----')
    if baseline is not None:
        print('Baseline   kp %2d, lead %2d: %.2f s per set of turns, overshoot %.1f deg (%s)'
              % (baseline[0], baseline[1], baseline[2], baseline[3],
                 'OK' if baseline[5] else 'FAIL'))
    if not passing:
        print('No setting passed. Try a lower DECELERATION or VELOCITY.')
        return
    for rank, r in enumerate(passing[:3]):
        faster = ''
        if baseline is not None and baseline[2] > 0:
            faster = ', %d%% faster than baseline' % round(100 * (1 - r[2] / baseline[2]))
        print('Best #%d    kp %2d, lead %2d: %.2f s per set of turns, overshoot %.1f, final %.1f deg%s'
              % (rank + 1, r[0], r[1], r[2], r[3], r[4], faster))
    print('To use the best: Gyro_Turn(..., kp=%d, lead_ms=%d)'
          % (passing[0][0], passing[0][1]))


def main():
    bot = DeltaBots()
    bot.hub.system.set_stop_button((Button.LEFT, Button.RIGHT))
    try:
        while True:
            bot.hub.light.on(Color.GREEN)
            print('Ready: press and release CENTER to start the turn tuning. '
                  'LEFT+RIGHT to quit.')
            Wait_For_Center(bot)
            bot.hub.light.on(Color.ORANGE)
            Run_Sweep(bot)
    finally:
        bot.Stop_All(stop=Stop.BRAKE)
        bot.hub.system.set_stop_button(Button.CENTER)


if __name__ == "__main__":
    main()
