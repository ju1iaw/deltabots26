"""DeltaBots program selector for SPIKE Prime / Pybricks 4.0.1.

Save beside the current DeltaBots_Base.py (with Wait and Wait_All).
Run in PowerShell (set the variable to your own hub's Bluetooth name):
    $robot_name = "YOUR_HUB_NAME"
    py -3 -m pipx run pybricksdev run ble --name $robot_name DeltaBots_Master.py
The name is a computer-side connection option, not a hub-side Python setting.

CONTROLS (one action per debounced press-and-release):
  RIGHT: next ID, wrapping m-1 -> 0.
  LEFT: previous ID, wrapping 0 -> m-1.
  CENTER: stop attachment swinging, then run selected program; ID 0 quits.
  LEFT + RIGHT together: firmware stop; exits this entire master program.
  Restart the master after a firmware stop. Holding center can power off hub.

PROGRAM IDs AND FLL MISSIONS:
  The displayed ID selects a PROGRAM, not an FLL game mission number.
  A program may perform one or several of the team's 13 FLL missions.
  Write those mission actions inside Program_N in the desired execution order;
  they do not need to follow FLL mission-number order. Programs can also be
  selected in any order; finishing one never automatically starts another.
  One member may own multiple programs. The LUT position is only the program ID.

TEAM WORKFLOW:
  1. Set M to an integer 1..10; default 10 means quit plus nine runnable programs.
     DEFAULT_PROGRAM_ID chooses the initial ID (default 1; M=1 uses 0).
  2. Replace owner labels in PROGRAMS with team names. A member may own
     several programs; labels are descriptive and never control execution.
  3. Each member edits only their assigned Program_N(bot) function(s).
  4. Keep function names, the bot parameter, and table ordering unchanged.
  5. Use the supplied bot; never create another DeltaBots/PrimeHub/Motor.
  6. Call bot.Reset_Gyro() at the start if your mission needs heading zero.
     This releases all motors: support loaded attachments before launch.
  7. Use bot.Wait(ms), not tools.wait/time.sleep, during concurrent motions.
  8. Return normally at mission end. No infinite loop, main(), or sys.exit().
     The master waits for outstanding tracked motions, then brakes ALL motors.
     Continuous Attachment_Run must be stopped by the mission when appropriate.
  9. Mission exceptions are printed to the connected terminal; all motors
     brake and the menu becomes available again. Firmware stop is not caught.

OPTIONAL SEPARATE FILES (recommended as the five people's code grows):
  Keep Program_1(bot) here as a small adapter:
      from Member1_Missions import Run1
      Run1(bot)
  Put Run1(bot) in Member1_Missions.py beside this file. Import inside the
  adapter so a missing/broken team module is reported only when selected.
  Do not create hardware or run a mission at module import time.

ID 0 plays B4 for one second before quitting. Slots 1..9 play one-second
C-major scale tones from C4 through D5, without
robot movement. Replace only the desired function bodies. The selector uses
custom full-width 5x5 digits rotated 90 degrees clockwise.
Tones are nonblocking: the selector remains responsive while they sound.
A new tone replaces the previous tone because the hub has one speaker.
Sound deadlines are serviced by bot.Update/Wait/Wait_All and the menu loop.
Use bot.Wait during custom mission delays; raw blocking code can delay a
tone's stop time, just as it can delay custom gyro control.

ATTACHMENT LOADING:
  SWING_ON_STARTUP=True by default: swinging starts when the master opens.
  Or add bot.Swing_Attachments(x=90) at the end of a mission. This queues
  loading motion until that mission's tracked movements finish successfully.
  Each stroke is x degrees, from the current position to current+x and back.
  LEFT/RIGHT selection leaves swinging active; CENTER release brakes both
  attachments before launching the selected program. bot.Stop_Swing() also
  cancels it. Cancellation is serviced at the next menu/update cycle, not
  during arbitrary blocking code. Each stroke has a 20-second timeout.
  A stall against a hard stop (or a stroke timeout) ends swinging and brakes
  both attachments. The menu keeps running, ready for the next command.
  This does not reset the attachment encoder angles automatically.
"""

from DeltaBots_Base import DeltaBots, Stop, MotionTimeout
from pybricks.parameters import Button
from pybricks.tools import StopWatch


# ----- TEAM CONFIGURATION -----
M = 10                      # Number of selectable programs: integer 1..10 (IDs 0..9).
DEFAULT_PROGRAM_ID = 1      # Initial selection; M=1 automatically uses ID 0.
SWING_ON_STARTUP = True     # True starts attachment loading motion at startup.
SWING_DEGREES = 90          # Stroke from starting angle to starting angle + x.
SWING_ACCELERATION_FACTOR = 1.5  # 50% above pre-swing acceleration/deceleration.
POLL_MS = 10
DEBOUNCE_MS = 30
FINISH_TIMEOUT_MS = 20000    # Wait for remaining wait=False jobs after return.
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
    """Default program: show its ID and play a 1000 ms tone, with no motion.

    Returns immediately by default so menu selection can continue.
    ID 0 plays B4; IDs 1..9 follow C major from middle C (C4) through D5.
    """
    Show_Program_ID(bot, program_id)
    frequency = PROGRAM_TONES[program_id]
    print('Program', program_id, '- tone:', frequency, 'Hz for 1 second')
    bot.Beep(frequency=frequency, duration=1000, wait=wait)


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


def _validate_count(m):
    if type(m) is not int or not 1 <= m <= 10:
        raise ValueError('M must be an integer from 1 to 10')
    if len(PROGRAMS) < m:
        raise ValueError('PROGRAMS does not contain enough program slots')
    for function, owner in PROGRAMS[:m]:
        if not callable(function):
            raise ValueError('Each program must contain a program function')


def _run_selected(bot, selected):
    bot.Stop_Swing()
    if selected == 0:
        Program_0(bot)
        return False
    function, owner = PROGRAMS[selected]
    print('Starting program', selected, '-', owner)
    pending_swing = None
    bot._in_mission = True
    try:
        function(bot)
        # Keep custom gyro loops running until pending jobs have finished.
        bot.Wait_All(timeout_ms=FINISH_TIMEOUT_MS)
        pending_swing = bot._pending_swing
        print('Program', selected, 'finished')
    except Exception as error:
        bot.Stop_Sound()
        print('Program', selected, 'failed:', type(error).__name__, str(error))
    finally:
        bot._in_mission = False
        # Cancel remaining jobs, including any continuous attachment commands.
        bot.Stop_All(stop=Stop.BRAKE)
        Show_Program_ID(bot, selected)
    if pending_swing is not None:
        bot.Swing_Attachments(pending_swing)
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
        Show_Program_ID(bot, selected)
        if SWING_ON_STARTUP:
            bot.Swing_Attachments(SWING_DEGREES)
        print('DeltaBots selector: IDs 0 through', m - 1)
        print('Release RIGHT/LEFT to select; release CENTER to run.')
        print('Select ID 0 and release CENTER to quit.')
        print('Press LEFT+RIGHT together to stop the entire master.')
        while True:
            event = buttons.update(bot.hub.buttons.pressed(), timer.time())
            if event == Button.RIGHT:
                selected = (selected + 1) % m
                Show_Program_ID(bot, selected)
            elif event == Button.LEFT:
                selected = (selected - 1) % m
                Show_Program_ID(bot, selected)
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
    This starts loading/unloading motion after the mission has finished.
    """
    Default_Program(bot, 1)


def Program_2(bot):
    """ID 2 - Member 2. Add mission commands here."""
    Default_Program(bot, 2)


def Program_3(bot):
    """ID 3 - Member 3. Add mission commands here."""
    Default_Program(bot, 3)


def Program_4(bot):
    """ID 4 - Member 4. Add mission commands here."""
    Default_Program(bot, 4)


def Program_5(bot):
    """ID 5 - Member 5. Add mission commands here."""
    Default_Program(bot, 5)


def Program_6(bot):
    """ID 6 - Spare. Set M >= 7 to enable."""
    Default_Program(bot, 6)


def Program_7(bot):
    """ID 7 - Spare. Set M >= 8 to enable."""
    Default_Program(bot, 7)


def Program_8(bot):
    """ID 8 - Spare. Set M >= 9 to enable."""
    Default_Program(bot, 8)


def Program_9(bot):
    """ID 9 - Spare. Set M = 10 to enable."""
    Default_Program(bot, 9)


# ----- PROGRAM LOOKUP TABLE: TEAM MEMBERS EDIT OWNERS HERE -----
# Position IS the displayed program ID, not an FLL mission number.
# Each entry is (function, owner label). Repeating an owner is allowed.
# Example assignment only: Program_1 and Program_6 could both belong to Member 1.
# List FLL mission IDs/order in the corresponding program's comments/docstring.
# Do not call functions here. ID 0 stays reserved for quitting.
PROGRAMS = (
    (Program_0, 'Quit'),
    (Program_1, 'Member 1'),
    (Program_2, 'Member 2'),
    (Program_3, 'Member 3'),
    (Program_4, 'Member 4'),
    (Program_5, 'Member 5'),
    (Program_6, 'Unassigned'),
    (Program_7, 'Unassigned'),
    (Program_8, 'Unassigned'),
    (Program_9, 'Unassigned'),
)


# Keep startup last: all program functions and the LUT must exist first.
if __name__ == '__main__':
    main()
