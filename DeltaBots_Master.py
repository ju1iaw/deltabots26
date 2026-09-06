"""DeltaBots program selector for SPIKE Prime / Pybricks.

Save beside DeltaBots_Base.py and all member route modules.
PowerShell upload (use your own hub name):
    $robot_name = "YOUR_HUB_NAME"
    py -3 -m pipx run pybricksdev run ble --name $robot_name DeltaBots_Master.py

MENU:
  LEFT/RIGHT press and release: select ID and apply its swing setting.
  CENTER press and release: stop swinging and launch selected program.
  ID 0: play optional exit tone and quit.
DURING A PROGRAM:
  A NEW CENTER press and release cancels the route and returns to the menu.
  Motors and sound stop; swinging stays off after cancellation or error until
  selection changes or a subsequent program completes successfully.
  LEFT+RIGHT remains the firmware stop combination for the entire master.

Cancellation is cooperative: bot.Update(), bot.Wait(), finite base movement
calls, and this class's Reset_Gyro service button events. Raw sleeps, blocking
motor calls, or long Python loops delay cancellation. Use bot.Wait(ms) for
pauses and call bot.Update() regularly in custom loops. Do not catch
BaseException in a route except to clean up and re-raise it.

PROGRAMS entries are (function, owner, swing). swing defaults to False;
legacy two-item entries also mean False. The selected entry controls swinging
at startup, on selection changes, and after successful program completion.
ID 0 never swings. An end-of-program Swing_Attachments(x) request supplies a
custom stroke only when that selected entry enables swinging. On a stall or
20-second stroke timeout, swinging stops and the menu remains responsive.
There is no automatic retry until selection changes or a program succeeds.

Program IDs differ from FLL game mission IDs. One member can own several
programs; each may perform any game missions in any order. Edit Program_N
functions and PROGRAMS near the bottom. Reuse the provided bot:
    def Program_1(bot):
        from Member1_Missions import Run_A
        Run_A(bot)
Never create another hub/robot/motor in an imported route. Keep module import
free of movement. Return normally; pending tracked movements are joined with
a 20-second finish timeout, then all motors brake. Continuous Attachment_Run
must be stopped explicitly when needed. Stop.HOLD does not persist through
the master's final cleanup.

PROGRAM_BEEP_ENABLED controls automatic program tones (including quit).
Program tones are 2000 ms by default, volume 30. Normal program tones start
without blocking; quit waits for its tone before exiting. Custom Beep calls
are separate and are not disabled by this automatic-tone option.
Digits use all five columns and are rotated 90 degrees clockwise.
"""

from DeltaBots_Base import DeltaBots, Stop, MotionTimeout
from pybricks.parameters import Button
from pybricks.tools import StopWatch


# ----- TEAM CONFIGURATION -----
M = 10                      # Number of selectable programs: integer 1..10 (IDs 0..9).
DEFAULT_PROGRAM_ID = 1      # Initial selection; M=1 automatically uses ID 0.
SWING_DEGREES = 90          # Default stroke for entries with swing=True.
SWING_ACCELERATION_FACTOR = 1.5  # 50% above pre-swing acceleration/deceleration.
POLL_MS = 10
DEBOUNCE_MS = 30
FINISH_TIMEOUT_MS = 20000    # Wait for remaining wait=False jobs after return.
PROGRAM_BEEP_ENABLED = True # False disables automatic start/exit tones.
PROGRAM_BEEP_DURATION_MS = 2000
TONE_VOLUME = 30            # Speaker volume in percent, 0..100.
PROGRAM_TONES = (494, 262, 294, 330, 349, 392, 440, 494, 523, 587)
# B4 (quit), C4, D4, E4, F4, G4, A4, B4, C5, D5; rounded Hz, A4 = 440 Hz.


# Each string is a row of five LEDs, from left to right; 1=on, 0=off.
BIG_DIGITS = (
    ('01110', '10001', '10001', '10001', '01110'),  # 0
    ('00100', '01100', '00100', '00100', '11111'),  # 1
    ('11110', '00001', '01110', '10000', '11111'),  # 2
    ('11110', '00001', '01110', '00001', '11110'),  # 3
    ('10010', '10010', '11111', '00010', '00010'),  # 4
    ('11111', '10000', '11110', '00001', '11110'),  # 5
    ('01111', '10000', '11110', '10001', '01110'),  # 6
    ('11111', '00001', '00010', '00100', '01000'),  # 7
    ('01110', '10001', '01110', '10001', '01110'),  # 8
    ('01110', '10001', '01111', '00001', '11110'),  # 9
)


class ProgramCancelled(BaseException):
    """Unwind a running route on CENTER release; caught only by the master."""


class MasterRobot(DeltaBots):
    """Adds timed audio and menu attachment swinging to the movement scheduler.

    Wait_All waits only for finite tracked movement, allowing menu helpers
    to continue. Stop_All stops all motors and swinging; Stop_Sound stops
    audio explicitly. No changes to DeltaBots_Base.py are required.
    """

    def __init__(self):
        DeltaBots.__init__(self)
        self._tone_timer = None
        self._tone_duration = 0
        self._tone_frequency = 100
        self._swing = None
        self._swing_limits = None
        self._pending_swing = None
        self._in_mission = False
        self._cancel_buttons = None
        self._button_clock = StopWatch()

    def Swing_Attachments(self, x=90):
        """Repeatedly swing both attachments through an x-degree stroke.

        Returns immediately. Uses smooth run_target strokes with acceleration
        and deceleration at 1.5 times the pre-swing settings (normally Pybricks
        defaults). SWING_ACCELERATION_FACTOR controls this multiplier.
        Speed/torque limits are unchanged. Original acceleration settings are
        restored on stop, stall, timeout, or error; restarts do not compound.
        Negative x reverses the
        initial direction. Both motors finish each stroke before reversing.
        Call at mission end to request swinging AFTER tracked jobs finish.
        Menu navigation stays available; CENTER release stops swinging before
        launching any program. Use Stop_Swing() to stop it explicitly.
        A detected stall or stroke timeout stops both attachments normally;
        the master stays running. Encoder angles are preserved.
        """
        if not isinstance(x, (int, float)) or not 0 < abs(x) < float('inf'):
            raise ValueError('x must be a finite, nonzero angle in degrees')
        if not 0 < SWING_ACCELERATION_FACTOR < float('inf'):
            raise ValueError('SWING_ACCELERATION_FACTOR must be finite and positive')
        if self._in_mission:
            self._pending_swing = x
            return
        self.Stop_Swing()
        self._available(-1)
        self._available(1)
        motors = (self._attachment(-1), self._attachment(1))
        origins = tuple(motor.angle() for motor in motors)
        tolerances = tuple(motor.control.target_tolerances() for motor in motors)
        self._swing_limits = tuple(motor.control.limits() for motor in motors)
        self._swing = (motors, origins, tolerances, x, True, StopWatch())
        try:
            for motor, limits in zip(motors, self._swing_limits):
                acceleration = limits[1]
                if isinstance(acceleration, (tuple, list)):
                    acceleration = tuple(value * SWING_ACCELERATION_FACTOR
                                         for value in acceleration)
                else:
                    acceleration *= SWING_ACCELERATION_FACTOR
                motor.control.limits(acceleration=acceleration)
            self._swing_leg()
        except BaseException:
            self.Stop_Swing()
            raise

    def _swing_leg(self):
        motors, origins, tolerances, x, outward, timer = self._swing
        for motor, origin, limits in zip(motors, origins, self._swing_limits):
            motor.run_target(limits[0], origin + (x if outward else 0),
                             then=Stop.HOLD, wait=False)
        timer.reset()

    def Stop_Swing(self):
        """Cancel active/queued swinging and brake immediately; no return stroke."""
        self._pending_swing = None
        swing = self._swing
        limits = self._swing_limits
        self._swing = None
        self._swing_limits = None
        if swing is not None:
            for motor in swing[0]:
                motor.brake()
            for motor, original in zip(swing[0], limits):
                motor.control.limits(acceleration=original[1])

    def Stop_All(self, stop=Stop.BRAKE):
        self.Stop_Swing()
        DeltaBots.Stop_All(self, stop)

    def _available(self, resource):
        # Normal attachment commands take ownership from the loading helper.
        if resource in (-1, 1):
            self.Stop_Swing()
        DeltaBots._available(self, resource)

    def Attachment_Stop(self, side, stop=Stop.HOLD):
        self.Stop_Swing()
        DeltaBots.Attachment_Stop(self, side, stop)

    def Attachment_Reset(self, side, angle=0):
        self.Stop_Swing()
        DeltaBots.Attachment_Reset(self, side, angle)

    def Reset_Gyro(self, angle=0, timeout_ms=20000):
        """Base reset behavior with cooperative CENTER cancellation."""
        if not timeout_ms > 0:
            raise ValueError('timeout_ms must be positive')
        self.Stop_All(stop=Stop.COAST)
        timer = StopWatch()
        self.Wait(1000)
        while not (self.hub.imu.ready() and self.hub.imu.stationary()):
            self._deadline(timer, timeout_ms, 'Reset_Gyro')
            self.Wait(self.loop_ms)
        self.hub.imu.reset_heading(angle)
        return self.Get_YAW_Angle(wrapped=False)

    def Beep(self, frequency=100, duration=1000, wait=False):
        """Play a timed tone; wait=False returns immediately (default).

        A new call replaces the old tone. Duration is in ms; frequency in Hz.
        """
        if not 64 <= frequency <= 24000 or duration < 0:
            raise ValueError('frequency must be 64..24000 Hz; duration >= 0')
        if not isinstance(wait, bool):
            raise ValueError('wait must be True or False')
        self.Stop_Sound()
        if duration == 0:
            return
        self._tone_frequency = frequency
        self._tone_duration = duration
        self.hub.speaker.volume(TONE_VOLUME)
        self.hub.speaker.beep(frequency=frequency, duration=-1)
        self._tone_timer = StopWatch()
        if wait:
            self.Wait(duration)

    def Stop_Sound(self):
        if self._tone_timer is not None:
            self.hub.speaker.beep(frequency=self._tone_frequency, duration=0)
            self._tone_timer = None

    def Update(self):
        try:
            if self._in_mission and self._cancel_buttons is not None:
                event = self._cancel_buttons.update(
                    self.hub.buttons.pressed(), self._button_clock.time())
                if event == Button.CENTER:
                    raise ProgramCancelled()
            if (self._tone_timer is not None
                    and self._tone_timer.time() >= self._tone_duration):
                self.Stop_Sound()
            active = DeltaBots.Update(self)
            if self._swing is not None:
                motors, origins, tolerances, x, outward, timer = self._swing
                if any(motor.stalled() for motor in motors):
                    self.Stop_Swing()
                    print('Attachment swing stopped: hard stop/stall detected. Ready for next command.')
                    return active
                # Check measured position/speed before reversing either motor.
                if all(abs(motor.angle() - origin - (x if outward else 0))
                       <= min(tolerance[1], abs(x) / 4)
                       and abs(motor.speed()) <= tolerance[0]
                       for motor, origin, tolerance in zip(motors, origins, tolerances)):
                    self._swing = (motors, origins, tolerances, x, not outward, timer)
                    self._swing_leg()
                elif timer.time() >= FINISH_TIMEOUT_MS:
                    self.Stop_Swing()
                    print('Attachment swing stopped: stroke timed out. Ready for next command.')
            return active
        except BaseException:
            self.Stop_All()
            self.Stop_Sound()
            raise


def Show_Program_ID(bot, program_id):
    """Draw a full-size digit rotated 90 degrees clockwise; overwrite LEDs."""
    if type(program_id) is not int or not 0 <= program_id < len(BIG_DIGITS):
        raise ValueError('program_id must be an integer from 0 to 9')
    for row in range(5):
        for column in range(5):
            brightness = 100 if BIG_DIGITS[program_id][4 - column][row] == '1' else 0
            bot.hub.display.pixel(row, column, brightness)


def Default_Program(bot, program_id, wait=False):
    """Show ID and optionally play its configured automatic program tone."""
    Show_Program_ID(bot, program_id)
    if PROGRAM_BEEP_ENABLED:
        bot.Beep(frequency=PROGRAM_TONES[program_id],
                 duration=PROGRAM_BEEP_DURATION_MS, wait=wait)


# ----- MENU ENGINE: TEAM MEMBERS NORMALLY LEAVE THIS SECTION UNCHANGED -----
class _ReleaseButtons:
    """Emit a single event after a stable press followed by stable release.

    Initially disarmed until all buttons are released. Mixed/overlapping
    button presses cancel the candidate, preventing accidental launches.
    """

    def __init__(self):
        self.raw = None
        self.stable = None
        self.changed_at = 0
        self.armed = False
        self.pending = None

    def update(self, pressed, now):
        pressed = set(pressed)
        if pressed != self.raw:
            self.raw = pressed
            self.changed_at = now
        if now - self.changed_at < DEBOUNCE_MS or pressed == self.stable:
            return None
        self.stable = pressed
        if not pressed:
            event = self.pending if self.armed else None
            self.pending = None
            self.armed = True
            return event
        if len(pressed) != 1:
            self.pending = None
            self.armed = False
            return None
        button = next(iter(pressed))
        if button not in (Button.LEFT, Button.RIGHT, Button.CENTER):
            self.armed = False
            self.pending = None
        elif self.armed:
            if self.pending is not None and self.pending != button:
                self.armed = False
                self.pending = None
            else:
                self.pending = button
        return None


def _program_entry(selected):
    entry = PROGRAMS[selected]
    if len(entry) not in (2, 3):
        raise ValueError('PROGRAMS entries need function, owner, optional swing')
    function, owner = entry[0], entry[1]
    swing = entry[2] if len(entry) == 3 else False
    if not callable(function) or type(swing) is not bool:
        raise ValueError('Program function must be callable; swing must be True/False')
    return function, owner, swing


def _validate_count(m):
    if type(m) is not int or not 1 <= m <= 10:
        raise ValueError('M must be an integer from 1 to 10')
    if len(PROGRAMS) < m:
        raise ValueError('PROGRAMS does not contain enough program slots')
    for selected in range(m):
        _program_entry(selected)
    if type(PROGRAM_BEEP_ENABLED) is not bool:
        raise ValueError('PROGRAM_BEEP_ENABLED must be True/False')
    if not 0 <= PROGRAM_BEEP_DURATION_MS < float('inf'):
        raise ValueError('PROGRAM_BEEP_DURATION_MS must be finite and nonnegative')


def _apply_selection(bot, selected, stroke=None):
    """Called on selection transitions, never repeatedly by the idle loop."""
    bot.Stop_Swing()
    Show_Program_ID(bot, selected)
    if selected != 0 and _program_entry(selected)[2]:
        bot.Swing_Attachments(SWING_DEGREES if stroke is None else stroke)


def _run_selected(bot, selected):
    bot.Stop_Swing()
    if selected == 0:
        Program_0(bot)
        return False
    function, owner, swing = _program_entry(selected)
    print('Starting program', selected, '-', owner)
    pending_swing = None
    succeeded = False
    bot._cancel_buttons = _ReleaseButtons()
    # Launch was triggered by a debounced release; require a fresh press.
    # If called directly while a button is held, leave the detector disarmed.
    if not bot.hub.buttons.pressed():
        bot._cancel_buttons.raw = set()
        bot._cancel_buttons.stable = set()
        bot._cancel_buttons.armed = True
    bot._in_mission = True
    try:
        Default_Program(bot, selected)
        function(bot)
        bot.Wait_All(timeout_ms=FINISH_TIMEOUT_MS)
        pending_swing = bot._pending_swing
        succeeded = True
        print('Program', selected, 'finished')
    except ProgramCancelled:
        bot.Stop_Sound()
        print('Program', selected, 'cancelled; ready for selection')
    except Exception as error:
        bot.Stop_Sound()
        print('Program', selected, 'failed:', type(error).__name__, str(error))
    finally:
        bot._in_mission = False
        bot._cancel_buttons = None
        bot.Stop_All(stop=Stop.BRAKE)
        Show_Program_ID(bot, selected)
    if succeeded:
        _apply_selection(bot, selected, pending_swing)
    return True


def main(m=M, default_program_id=None):
    _validate_count(m)
    if default_program_id is None:
        default_program_id = 0 if m == 1 else DEFAULT_PROGRAM_ID
    if type(default_program_id) is not int or not 0 <= default_program_id < m:
        raise ValueError('Default program ID must be an integer from 0 to M-1')
    bot = MasterRobot()
    selected = default_program_id
    timer = StopWatch()
    buttons = _ReleaseButtons()
    try:
        # Center normally stops a Pybricks script. Reassign that function so
        # CENTER can launch missions; LEFT+RIGHT remains a firmware-level stop.
        bot.hub.system.set_stop_button((Button.LEFT, Button.RIGHT))
        bot.Stop_All(stop=Stop.BRAKE)
        _apply_selection(bot, selected)
        print('DeltaBots selector: IDs 0 through', m - 1)
        print('Release RIGHT/LEFT to select; release CENTER to run/cancel.')
        print('Select ID 0 and release CENTER to quit.')
        print('Press LEFT+RIGHT together to stop the entire master.')
        while True:
            event = buttons.update(bot.hub.buttons.pressed(), timer.time())
            if event == Button.RIGHT:
                selected = (selected + 1) % m
                _apply_selection(bot, selected)
            elif event == Button.LEFT:
                selected = (selected - 1) % m
                _apply_selection(bot, selected)
            elif event == Button.CENTER:
                if not _run_selected(bot, selected):
                    break
                # Ignore presses held across mission completion. A new release
                # and fresh press are required before another command.
                buttons = _ReleaseButtons()
            bot.Wait(POLL_MS)
    finally:
        bot.Stop_Sound()
        bot.Stop_All(stop=Stop.BRAKE)
        bot.hub.system.set_stop_button(Button.CENTER)


# ----- PROGRAM FUNCTIONS: TEAM MEMBERS EDIT HERE -----
def Program_0(bot):
    """ID 0 - Reserved: quit the master program."""
    # Finish the exit tone before program shutdown stops the speaker.
    Default_Program(bot, 0, wait=True)
    print('Exiting DeltaBots master.')


def Program_1(bot):
    """ID 1 - Member 1. Add mission commands here.

    FLL missions / execution order: fill in your plan here.
    Example only: this program could perform FLL mission 8, then 3, then 12.
    Call those mission helpers in that order, always passing this same bot.
    The program ID does not determine which game missions it performs.

    Optional last line: bot.Swing_Attachments(x=90)
    This custom stroke is used after success only if this LUT entry enables swing.
    """
    pass  # Add route commands or import and call your member function.


def Program_2(bot):
    """ID 2 - Member 2. Add mission commands here."""
    pass  # Add route commands or import and call your member function.


def Program_3(bot):
    """ID 3 - Member 3. Add mission commands here."""
    pass  # Add route commands or import and call your member function.


def Program_4(bot):
    """ID 4 - Member 4. Add mission commands here."""
    pass  # Add route commands or import and call your member function.


def Program_5(bot):
    """ID 5 - Member 5. Add mission commands here."""
    pass  # Add route commands or import and call your member function.


def Program_6(bot):
    """ID 6 - Spare. Set M >= 7 to enable."""
    pass  # Add route commands or import and call your member function.


def Program_7(bot):
    """ID 7 - Spare. Set M >= 8 to enable."""
    pass  # Add route commands or import and call your member function.


def Program_8(bot):
    """ID 8 - Spare. Set M >= 9 to enable."""
    pass  # Add route commands or import and call your member function.


def Program_9(bot):
    """ID 9 - Robot self-inspection. Set M = 10 to enable."""
    from Robot_Self_Inspection import Robot_Self_Instpection
    Robot_Self_Instpection(bot)


# ----- PROGRAM LOOKUP TABLE: TEAM MEMBERS EDIT OWNERS HERE -----
# Position IS the displayed program ID, not an FLL mission number.
# Each entry is (function, owner label, swing_on_selection).
# Set True for programs needing loading swing; False is the default.
# Repeating an owner is allowed. Legacy (function, owner) entries mean False.
# Example assignment only: Program_1 and Program_6 could both belong to Member 1.
# List FLL mission IDs/order in the corresponding program's comments/docstring.
# Do not call functions here. ID 0 stays reserved for quitting.
PROGRAMS = (
    (Program_0, 'Quit', False),
    (Program_1, 'Member 1', False),
    (Program_2, 'Member 2', False),
    (Program_3, 'Member 3', False),
    (Program_4, 'Member 4', False),
    (Program_5, 'Member 5', False),
    (Program_6, 'Unassigned', False),
    (Program_7, 'Unassigned', False),
    (Program_8, 'Unassigned', False),
    (Program_9, 'Robot_self_inspection', True),
)


# Keep startup last: all program functions and the LUT must exist first.
if __name__ == '__main__':
    main()
