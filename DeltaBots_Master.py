"""DeltaBots mission selector for SPIKE Prime / Pybricks 4.0.1.

Save beside the current DeltaBots_Base.py (with Wait and Wait_All).
Run in PowerShell (set the variable to your own hub's Bluetooth name):
    $robot_name = "YOUR_HUB_NAME"
    py -3 -m pipx run pybricksdev run ble --name $robot_name DeltaBots_Master.py
The name is a computer-side connection option, not a hub-side Python setting.

CONTROLS (one action per debounced press-and-release):
  RIGHT: next ID, wrapping m-1 -> 0.
  LEFT: previous ID, wrapping 0 -> m-1.
  CENTER: stop attachment swinging, then run selected mission; ID 0 quits.
  LEFT + RIGHT together: firmware stop; exits this entire master program.
  Restart the master after a firmware stop. Holding center can power off hub.

TEAM WORKFLOW:
  1. Set M to an integer 1..9; default 6 means quit plus five missions.
     DEFAULT_PROGRAM_ID chooses the initial ID (default 1; M=1 uses 0).
  2. Replace Member 1..5 labels below with team names. Ownership is editable.
  3. Each member edits only their assigned Mission_N(bot) function(s).
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
  Keep Mission_1(bot) here as a small adapter:
      from Member1_Missions import Run1
      Run1(bot)
  Put Run1(bot) in Member1_Missions.py beside this file. Import inside the
  adapter so a missing/broken team module is reported only when selected.
  Do not create hardware or run a mission at module import time.

ID 0 is reserved for quitting. Slots 1..8 play a one-second tone at ID * 80 + 100 Hz, without
robot movement. Replace only the desired function bodies. The selector uses
custom full-width 5x5 digits rotated 90 degrees clockwise.
Tones are nonblocking: the selector remains responsive while they sound.
A new tone replaces the previous tone because the hub has one speaker.
Sound deadlines are serviced by bot.Update/Wait/Wait_All and the menu loop.
Use bot.Wait during custom mission delays; raw blocking code can delay a
tone's stop time, just as it can delay custom gyro control.

ATTACHMENT LOADING:
  Set SWING_ON_STARTUP=True to start swinging when the master opens.
  Or add bot.Swing_Attachments(x=90) at the end of a mission. This queues
  loading motion until that mission's tracked movements finish successfully.
  Each stroke is x degrees, from the current position to current+x and back.
  LEFT/RIGHT selection leaves swinging active; CENTER release brakes both
  attachments before launching the selected program. bot.Stop_Swing() also
  cancels it. Cancellation is serviced at the next menu/update cycle, not
  during arbitrary blocking code. Each stroke has a 20-second timeout.
"""

from DeltaBots_Base import DeltaBots, Stop, MotionTimeout
from pybricks.parameters import Button
from pybricks.tools import StopWatch


# ----- TEAM CONFIGURATION -----
M = 6                       # Number of selectable programs: integer 1..9.
DEFAULT_PROGRAM_ID = 1      # Initial selection; M=1 automatically uses ID 0.
SWING_ON_STARTUP = False    # True starts attachment loading motion at startup.
SWING_DEGREES = 90          # Stroke from starting angle to starting angle + x.
POLL_MS = 10
DEBOUNCE_MS = 30
FINISH_TIMEOUT_MS = 20000    # Wait for remaining wait=False jobs after return.
TONE_VOLUME = 70            # Speaker volume in percent, 0..100.


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
        self._pending_swing = None
        self._in_mission = False

    def Swing_Attachments(self, x=90):
        """Repeatedly swing both attachments through an x-degree stroke.

        Returns immediately. Uses each motor's configured maximum speed and
        acceleration; does not change torque limits. Negative x reverses the
        initial direction. Both motors finish each stroke before reversing.
        Call at mission end to request swinging AFTER tracked jobs finish.
        Menu navigation stays available; CENTER release stops swinging before
        launching any program. Use Stop_Swing() to stop it explicitly.
        """
        if not isinstance(x, (int, float)) or not 0 < abs(x) < float('inf'):
            raise ValueError('x must be a finite, nonzero angle in degrees')
        if self._in_mission:
            self._pending_swing = x
            return
        self.Stop_Swing()
        self._available(-1)
        self._available(1)
        motors = (self._attachment(-1), self._attachment(1))
        origins = tuple(motor.angle() for motor in motors)
        speeds = tuple(motor.control.limits()[0] for motor in motors)
        if min(speeds) <= 0:
            raise ValueError('Attachment motor speed limits must be positive')
        self._swing = (motors, origins, speeds, x, True, StopWatch())
        try:
            self._swing_leg()
        except BaseException:
            self.Stop_Swing()
            raise

    def _swing_leg(self):
        motors, origins, speeds, x, outward, timer = self._swing
        for motor, origin, speed in zip(motors, origins, speeds):
            motor.run_target(speed, origin + (x if outward else 0),
                             then=Stop.HOLD, wait=False)
        timer.reset()

    def Stop_Swing(self):
        """Cancel active/queued swinging and brake immediately; no return stroke."""
        self._pending_swing = None
        swing = self._swing
        self._swing = None
        if swing is not None:
            for motor in swing[0]:
                motor.brake()

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
                motors, origins, speeds, x, outward, timer = self._swing
                if any(motor.stalled() for motor in motors):
                    raise RuntimeError('Attachment swing stalled')
                if all(motor.done() for motor in motors):
                    self._swing = (motors, origins, speeds, x, not outward, timer)
                    self._swing_leg()
                elif timer.time() >= FINISH_TIMEOUT_MS:
                    raise MotionTimeout('Attachment swing stroke timed out')
            return active
        except BaseException:
            self.Stop_All()
            self.Stop_Sound()
            raise


def Show_Program_ID(bot, program_id):
    """Draw a full-size digit rotated 90 degrees clockwise; overwrite LEDs."""
    if type(program_id) is not int or not 0 <= program_id < len(BIG_DIGITS):
        raise ValueError('program_id must be an integer from 0 to 8')
    for row in range(5):
        for column in range(5):
            brightness = 100 if BIG_DIGITS[program_id][4 - column][row] == '1' else 0
            bot.hub.display.pixel(row, column, brightness)


def Default_Program(bot, program_id, wait=False):
    """Default mission: show its ID and play a 1000 ms tone, with no motion.

    Returns immediately by default so menu selection can continue.
    Frequencies for IDs 0..8 are 100,180,260,340,420,500,580,660,740 Hz.
    """
    Show_Program_ID(bot, program_id)
    frequency = program_id * 80 + 100
    print('Program', program_id, '- tone:', frequency, 'Hz for 1 second')
    bot.Beep(frequency=frequency, duration=1000, wait=wait)


# ----- MISSION FUNCTIONS: TEAM MEMBERS EDIT HERE -----
def Mission_0(bot):
    """ID 0 - Reserved: quit the master program."""
    print('Exiting DeltaBots master.')


def Mission_1(bot):
    """ID 1 - Member 1. Add mission commands here.

    Optional last line: bot.Swing_Attachments(x=90)
    This starts loading/unloading motion after the mission has finished.
    """
    Default_Program(bot, 1)


def Mission_2(bot):
    """ID 2 - Member 2. Add mission commands here."""
    Default_Program(bot, 2)


def Mission_3(bot):
    """ID 3 - Member 3. Add mission commands here."""
    Default_Program(bot, 3)


def Mission_4(bot):
    """ID 4 - Member 4. Add mission commands here."""
    Default_Program(bot, 4)


def Mission_5(bot):
    """ID 5 - Member 5. Add mission commands here."""
    Default_Program(bot, 5)


def Mission_6(bot):
    """ID 6 - Spare. Set M >= 7 to enable."""
    Default_Program(bot, 6)


def Mission_7(bot):
    """ID 7 - Spare. Set M >= 8 to enable."""
    Default_Program(bot, 7)


def Mission_8(bot):
    """ID 8 - Spare. Set M = 9 to enable."""
    Default_Program(bot, 8)


# Position in this tuple IS the program ID. Do not call functions here.
PROGRAMS = (
    (Mission_0, 'Quit'),
    (Mission_1, 'Member 1'),
    (Mission_2, 'Member 2'),
    (Mission_3, 'Member 3'),
    (Mission_4, 'Member 4'),
    (Mission_5, 'Member 5'),
    (Mission_6, 'Unassigned'),
    (Mission_7, 'Unassigned'),
    (Mission_8, 'Unassigned'),
)


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
    if type(m) is not int or not 1 <= m <= 9:
        raise ValueError('M must be an integer from 1 to 9')
    if len(PROGRAMS) < m:
        raise ValueError('PROGRAMS does not contain enough mission slots')
    for function, owner in PROGRAMS[:m]:
        if not callable(function):
            raise ValueError('Each program must contain a mission function')


def _run_selected(bot, selected):
    bot.Stop_Swing()
    if selected == 0:
        Mission_0(bot)
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


if __name__ == '__main__':
    main()
