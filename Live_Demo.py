from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Button, Stop
from pybricks.tools import wait, Matrix


# ============================================================
# USER-ADJUSTABLE SETTINGS
# ============================================================

# Blade motor - Port F
# Sign controls direction.
BLADE_SPEED = 1100             # deg/s

# Fan motor - Port D
# Sign controls direction.
FAN_SPEED = 1100                # deg/s

# Swing motor - Port B
SWING_ANGLE = 160               # degrees
SWING_SPEED = 1100              # deg/s

# Motor B homing
# Change sign if motor moves away from hard stop.
HOMING_SPEED = -180             # deg/s

# Reduced motor power while finding hard stop
HOMING_DUTY_LIMIT = 30          # percent


# ============================================================
# HUB SETUP
# ============================================================

hub = PrimeHub()

# CENTER is used by this program.
# CENTER + BLUETOOTH can still act as an emergency program stop.
hub.system.set_stop_button((Button.CENTER, Button.BLUETOOTH))


# ============================================================
# LARGE 3 x 5 MODE NUMBERS
# ============================================================

MODE_0 = Matrix([
    [0, 100, 100, 100, 0],
    [0, 100,   0, 100, 0],
    [0, 100,   0, 100, 0],
    [0, 100,   0, 100, 0],
    [0, 100, 100, 100, 0],
])

MODE_1 = Matrix([
    [0,   0, 100,   0, 0],
    [0, 100, 100,   0, 0],
    [0,   0, 100,   0, 0],
    [0,   0, 100,   0, 0],
    [0, 100, 100, 100, 0],
])

MODE_2 = Matrix([
    [0, 100, 100, 100, 0],
    [0,   0,   0, 100, 0],
    [0, 100, 100, 100, 0],
    [0, 100,   0,   0, 0],
    [0, 100, 100, 100, 0],
])


def display_mode(mode):
    """Display large 3x5 mode number."""

    if mode == 0:
        hub.display.icon(MODE_0)

    elif mode == 1:
        hub.display.icon(MODE_1)

    elif mode == 2:
        hub.display.icon(MODE_2)


# ============================================================
# OPTIONAL MOTOR
#
# Program continues even when B, D, or F is not connected.
# ============================================================

class OptionalMotor:

    def __init__(self, port):
        self.port = port
        self.motor = None
        self.connect()

    def connect(self):

        if self.motor is not None:
            return True

        try:
            self.motor = Motor(self.port)
            print("Motor connected:", self.port)
            return True

        except OSError:
            self.motor = None
            print("Motor not connected:", self.port)
            return False

    def run(self, speed):

        if not self.connect():
            return False

        try:
            self.motor.run(speed)
            return True

        except OSError:
            self.motor = None
            return False

    def brake(self):

        if self.motor is None:
            return

        try:
            self.motor.brake()

        except OSError:
            self.motor = None


# ============================================================
# MOTORS
# ============================================================

motor_B = OptionalMotor(Port.B)     # Swing
motor_D = OptionalMotor(Port.D)     # Fan
motor_F = OptionalMotor(Port.F)     # Blade


# ============================================================
# PROGRAM STATE
# ============================================================

mode = 0

# True when selected mode is operating
mode_running = False

# Motor B is homed only once per program execution
swing_homed = False

swing_target = 0


# Determine direction away from hard stop
if HOMING_SPEED < 0:
    SWING_END = SWING_ANGLE
else:
    SWING_END = -SWING_ANGLE


# ============================================================
# MOTOR CONTROL
# ============================================================

def stop_all_motors():

    motor_B.brake()
    motor_D.brake()
    motor_F.brake()


# ============================================================
# MOTOR B HOMING
# ============================================================

def home_motor_B():

    global swing_homed
    global swing_target

    if not motor_B.connect():
        print("Motor B not available - skipping homing.")
        return False

    print("Homing Motor B...")

    try:

        # Move toward mechanical hard stop
        motor_B.motor.run_until_stalled(
            HOMING_SPEED,
            then=Stop.HOLD,
            duty_limit=HOMING_DUTY_LIMIT
        )

        # Define hard stop as 0 degrees
        motor_B.motor.reset_angle(0)

        swing_homed = True
        swing_target = SWING_END

        print("Motor B homing complete.")
        print("Motor B position = 0 degrees")

        return True

    except OSError:

        motor_B.motor = None
        swing_homed = False

        print("Motor B homing failed.")
        return False


# ============================================================
# MOTOR B SWING
# ============================================================

def start_swing():

    global swing_target

    if not motor_B.connect():
        return

    try:

        swing_target = SWING_END

        motor_B.motor.run_target(
            SWING_SPEED,
            swing_target,
            then=Stop.HOLD,
            wait=False
        )

    except OSError:

        motor_B.motor = None


def update_swing():

    global swing_target
    global swing_homed

    if motor_B.motor is None:
        return

    try:

        if motor_B.motor.done():

            # Change endpoint
            if swing_target == SWING_END:
                swing_target = 0
            else:
                swing_target = SWING_END

            # Move to opposite endpoint
            motor_B.motor.run_target(
                SWING_SPEED,
                swing_target,
                then=Stop.HOLD,
                wait=False
            )

    except OSError:

        motor_B.motor = None
        swing_homed = False


# ============================================================
# MODE CHANGE
# ============================================================

def change_mode(new_mode):

    global mode
    global mode_running

    # Always stop everything when changing modes
    stop_all_motors()

    mode_running = False
    mode = new_mode

    display_mode(mode)

    print("Mode:", mode)


# ============================================================
# START CURRENT MODE
# ============================================================

def start_current_mode():

    global mode_running
    global swing_homed


    # --------------------------------------------------------
    # MODE 0
    #
    # F = Blade
    # --------------------------------------------------------

    if mode == 0:

        print("Mode 0 START")

        motor_F.run(BLADE_SPEED)

        mode_running = True


    # --------------------------------------------------------
    # MODE 1
    #
    # F = Blade
    # B = Swing
    # --------------------------------------------------------

    elif mode == 1:

        print("Mode 1 START")

        # Try Motor B
        motor_B.connect()

        # First time Motor B is used:
        # Find mechanical hard stop
        if motor_B.motor is not None and not swing_homed:

            home_motor_B()

        # Start blade
        motor_F.run(BLADE_SPEED)

        # Start swing
        if motor_B.motor is not None:

            start_swing()

        mode_running = True


    # --------------------------------------------------------
    # MODE 2
    #
    # F = Blade
    # D = Fan
    # --------------------------------------------------------

    elif mode == 2:

        print("Mode 2 START")

        # Blade
        motor_F.run(BLADE_SPEED)

        # Fan
        motor_D.run(FAN_SPEED)

        mode_running = True


# ============================================================
# STOP CURRENT MODE
# ============================================================

def stop_current_mode():

    global mode_running

    print("STOP")

    stop_all_motors()

    mode_running = False


# ============================================================
# CENTER BUTTON TOGGLE
# ============================================================

def toggle_current_mode():

    if mode_running:
        stop_current_mode()

    else:
        start_current_mode()


# ============================================================
# INITIAL STATE
# ============================================================

stop_all_motors()

mode = 0
mode_running = False

display_mode(0)

print("")
print("==============================")
print("DeltaBots Demo Ready")
print("==============================")
print("Blade Speed :", BLADE_SPEED)
print("Fan Speed   :", FAN_SPEED)
print("Swing Speed :", SWING_SPEED)
print("Swing Angle :", SWING_ANGLE)
print("------------------------------")
print("LEFT        = Previous mode")
print("RIGHT       = Next mode")
print("CENTER      = Start / Stop")
print("LEFT+RIGHT  = Quit")
print("==============================")


# ============================================================
# MAIN LOOP
# ============================================================

previous_buttons = set()


while True:

    current_buttons = hub.buttons.pressed()


    # ========================================================
    # LEFT + RIGHT TOGETHER
    #
    # Immediately stop everything and quit.
    # ========================================================

    if (
        Button.LEFT in current_buttons
        and Button.RIGHT in current_buttons
    ):

        print("LEFT + RIGHT pressed")
        print("Stopping all motors...")
        print("Program terminated.")

        stop_all_motors()

        raise SystemExit


    # ========================================================
    # BUTTON RELEASE DETECTION
    #
    # One complete press-and-release produces one action.
    # ========================================================

    released_buttons = previous_buttons - current_buttons


    # --------------------------------------------------------
    # RIGHT BUTTON
    #
    # 0 -> 1 -> 2 -> 0
    # --------------------------------------------------------

    if Button.RIGHT in released_buttons:

        new_mode = (mode + 1) % 3

        change_mode(new_mode)


    # --------------------------------------------------------
    # LEFT BUTTON
    #
    # 0 -> 2 -> 1 -> 0
    # --------------------------------------------------------

    elif Button.LEFT in released_buttons:

        new_mode = (mode - 1) % 3

        change_mode(new_mode)


    # --------------------------------------------------------
    # CENTER BUTTON
    #
    # Toggle Start / Stop
    # --------------------------------------------------------

    elif Button.CENTER in released_buttons:

        toggle_current_mode()


    # --------------------------------------------------------
    # MODE 1 SWING UPDATE
    # --------------------------------------------------------

    if mode == 1 and mode_running:

        update_swing()


    # Save button state
    previous_buttons = current_buttons

    wait(10)
