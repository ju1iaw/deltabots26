# DeltaBots Master — Application Notes

**Applies to:** the current `DeltaBots_Master.py` with `Program_0`–`Program_9`, CENTER cancellation, per-program swing settings, optional two-second tones, and a swing acceleration factor of 1.5. Use it with the team’s current `DeltaBots_Base.py` supporting `Wait`, `Wait_All`, and `wait=False` movements.

## 1. Program selection and controls

The master creates one shared robot instance, displays a program ID, and waits for button commands. A short wrapper function connects each selectable ID to a route in a separate Python file. It calls the selected program, then returns to the selector when that program finishes.

**Program IDs are not FLL mission IDs.** The team’s 13 game missions can be grouped into the nine runnable program slots however the team chooses. A program may complete several game missions in a chosen order. One team member may own several programs.

For example, Program 1 could perform game missions 8, 3, and 12 in that order, while Program 6 belongs to the same member and performs a different route. This is an illustration, not an assignment. Neither game mission numbers nor program IDs force an execution sequence. The operator chooses which program to run next.

| Control | Action |
|---|---|
| RIGHT press and release, in the menu | Select the next ID, wrapping 9 → 0, and apply its swing setting. |
| LEFT press and release, in the menu | Select the previous ID, wrapping 0 → 9, and apply its swing setting. |
| CENTER press and release, in the menu | Stop swinging, then run the selected program. |
| A new CENTER press and release, while a program runs | Cancel the route, stop motors and sound, and return to selection. |
| Select ID 0, then CENTER press and release | Stop swinging, play the optional B4 exit tone for two seconds, and quit the master. |
| LEFT + RIGHT together | Stop the entire master through the hub’s configured stop-button combination. Restart the master to continue. |

A held LEFT or RIGHT button does not repeatedly change the selection. The display uses full-size digits rotated 90° clockwise. After a runnable program finishes, its ID stays selected; there is no automatic advance.

**CENTER cancellation is cooperative.** The master checks buttons during base movement updates, `bot.Wait()`, `bot.Wait_All()`, `bot.Wait_For()`, and the master’s `Reset_Gyro()`. A fresh CENTER press and release unwinds the route, including pending tracked movements, so commands later in the route do not run.

Raw sleeps, blocking raw motor calls, or long Python loops delay cancellation. Use `bot.Wait(ms)` for delays and `bot.Update()` regularly in custom loops. Do not swallow `BaseException` in member code; re-raise it after any necessary cleanup so `ProgramCancelled` can reach the master. Ordinary `except Exception` does not catch this cancellation signal.

LEFT/RIGHT do not select another route while one is running. Cancel first, then select. LEFT+RIGHT still stops the entire master through the firmware. Button events are debounced (30 ms) and normally polled every 10 ms; a physical stop is not instantaneous.

After cancellation or an ordinary program error, the selected ID stays displayed and swinging stays off. Change selection or complete a subsequent program successfully to apply swinging again. Default placeholder programs return immediately, so after their return CENTER starts another run rather than cancelling the previous one.

## 2. File organization and team ownership

Keep these files in the same project folder:

| File | Purpose | Who normally edits it |
|---|---|---|
| `DeltaBots_Master.py` | Configuration, selector, program wrappers, and lookup table | Integrator; members edit their assigned wrappers only |
| `DeltaBots_Base.py` | Shared movement and sensor functions | Person maintaining the shared library |
| `Member1_Missions.py` | Member 1’s routes and game-mission helpers | Member 1 |
| `Member2_Missions.py` | Member 2’s routes and helpers | Member 2 |
| Additional member files | Other members’ routes and helpers | Assigned owners |

Use Python filenames with letters, numbers, and underscores; avoid spaces and hyphens. Match filename capitalization in imports. Each member can put multiple route functions in their own file.

The editable **PROGRAM FUNCTIONS** and **PROGRAM LOOKUP TABLE** sections are near the bottom of the master. Keep the final `if __name__ == '__main__': main()` block last, after all program definitions and the lookup table.

## 3. Integrating a member’s program: step by step

### Step 1 — Agree on the assigned program slots

Before editing, record the owner, route entry function, game missions in execution order, required attachment, starting pose, and loading requirements for each assigned program ID. Reserve ID 0 for quitting.

An owner can have both Program 1 and Program 6. The game missions covered by those programs need not include game missions 1 or 6.

### Step 2 — Put the member’s route inside a function accepting `bot`

Create `Member1_Missions.py`. This complete example is a simple integration test route; replace its movement commands with the tested mission route before competition.

```python
# Member1_Missions.py
from pybricks.parameters import Stop


def Run_A(bot):
    """Owner: Member 1. Record game missions and starting pose here."""
    bot.Reset_Gyro()
    bot.Gyro_Move(direction=0, distance=300, velocity=150,
                  acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, 45, velocity=300, stop=Stop.HOLD, wait=True)
    bot.Gyro_Move(direction=0, distance=-300, velocity=150,
                  acceleration=200, stop=Stop.BRAKE, wait=True)


def Run_B(bot):
    """A second independently selectable route for the same member."""
    bot.Attachment_Time(-1, 500, velocity=200, stop=Stop.HOLD, wait=True)
```

The examples move real motors. Set the intended starting pose and attachment before running them. `Reset_Gyro()` releases the motors while preparing the IMU; consider this when an attachment depends on motor holding force.

If a route contains several game-mission helper functions, call them in the desired order inside `Run_A(bot)`. Pass the same `bot` to every helper.

### Step 3 — Make the assigned master wrapper call that function

Replace the body of `Program_1` in `DeltaBots_Master.py`:

```python
def Program_1(bot):
    """Member 1: route A. Document game-mission order here."""
    from Member1_Missions import Run_A
    Run_A(bot)
```

For the member’s second program:

```python
def Program_6(bot):
    """Member 1: route B."""
    from Member1_Missions import Run_B
    Run_B(bot)
```

This is what “merging” normally means: include the member’s file and connect its entry function to the assigned master wrapper. There is no need to paste the entire member file into the master.

Imports inside the wrapper delay loading until the program is selected. A missing module or function is reported as a program error, and the selector can recover. Module-level code still executes on its first import, so keep motor activity out of module-level statements.

The master now starts the optional program tone automatically before calling the route. Do not add `Default_Program(bot, N)` inside a wrapper just to get a start tone; that would restart the tone. Disable automatic tones with `PROGRAM_BEEP_ENABLED = False`.

### Step 4 — Update the owner labels in the lookup table

The following complete table illustrates one member owning Programs 1 and 6. Keep the program functions in ID order, change labels to match assignments, and set each swing flag for that program’s loading needs.

```python
PROGRAMS = (
    (Program_0, 'Quit', False),
    (Program_1, 'Member 1', False),
    (Program_2, 'Member 2', False),
    (Program_3, 'Member 3', False),
    (Program_4, 'Member 4', False),
    (Program_5, 'Member 5', False),
    (Program_6, 'Member 1', False),
    (Program_7, 'Unassigned', False),
    (Program_8, 'Unassigned', False),
    (Program_9, 'Robot_self_inspection', True),
)
```

Each entry is `(function, owner_label, swing_on_selection)`. The third value must be the Boolean `True` or `False`, without quotes. Legacy two-item entries are accepted and mean `False`. The position of an entry determines its program ID, counting from zero. Store function references without parentheses: `Program_1`, not `Program_1(bot)`. The master passes `bot` when it runs the selected function. ID 0 is reserved for quitting and is handled separately by the menu code.

Owner labels are printed in the terminal. They do not restrict ownership, determine execution order, or control the motors. Do not move a row merely to group entries by owner; that would change the displayed ID associated with the row.

### Step 5 — Use the master’s existing robot

The master creates `bot = MasterRobot()` once. `MasterRobot` inherits the movement functions from `DeltaBots` and adds the master’s sound and swing helpers.

Inside imported member files:

- Accept the supplied `bot` parameter and use it throughout.
- Do not create another `DeltaBots()`, `MasterRobot()`, `PrimeHub()`, or motor object.
- Do not call a route or launch a selector at import time.
- Return normally when finished. Do not call `sys.exit()` or leave an infinite loop running.

For an optional separate standalone test launcher, use a different file:

```python
# Test_Member1.py — run this file separately from the master.
from DeltaBots_Master import MasterRobot
from Member1_Missions import Run_A

if __name__ == '__main__':
    bot = MasterRobot()
    try:
        Run_A(bot)
        bot.Wait_All()
    finally:
        bot.Stop_All()
        bot.Stop_Sound()
```

Importing `MasterRobot` does not start the menu because the master’s startup call is guarded. This separate launcher does not activate the selector’s cancellation monitor, automatic tones, or selection-based swing policy. Verify those behaviors through the actual master.

### Step 6 — Handle movement completion correctly

Movement functions default to `wait=True`. Use that default for ordinary sequential routes. If using `wait=False`, the custom movement scheduler must keep receiving updates:

```python
bot.Gyro_Move(direction=0, distance=600, velocity=150,
              acceleration=200, stop=Stop.BRAKE, wait=False)
bot.Wait(1500)  # Continue driving before starting the attachment.
bot.Attachment_Time(1, 1000, velocity=300, stop=Stop.HOLD, wait=False)
bot.Wait_All()  # Finish both tracked movements before proceeding.
```

Use `bot.Wait(ms)` instead of `time.sleep()` or raw `pybricks.tools.wait()` during concurrent movements. Long blocking code delays gyro updates, CENTER cancellation, sound timing, and swing monitoring.

Do not start a second tracked command on the same motor resource before its earlier command finishes or is stopped. The two attachments and the drive are separate resources.

When a program returns, the master waits for remaining tracked movements, with a 20,000 ms finish timeout, then brakes all motors. Continuous `Attachment_Run` commands are not completed by `Wait_All`; stop them explicitly when appropriate. Normal return does not preserve a `Stop.HOLD` state through the master’s final all-motor brake.

### Step 7 — Save, integrate, and verify

1. Save the member file and the edited master. Include both in the shared project change.
2. When combining Git changes, preserve other members’ wrappers, owner labels, and shared configuration. Resolve overlapping edits to the master together.
3. Confirm `M` includes the assigned ID. With `M = 10`, IDs 0–9 are enabled.
4. Upload/run the master from the project directory using the team’s existing command:

```powershell
$robot_name = "YOUR_HUB_NAME"
py -3 -m pipx run pybricksdev run ble --name $robot_name DeltaBots_Master.py
```

5. Select the assigned ID and press/release CENTER. Confirm the intended member function runs and the selector returns afterward.
6. Verify a second program owned by the same member, if applicable, and check that another member’s program still works.
7. Test the planned loading transition and confirm startup/idle swinging stops before the next route begins.

## 4. Attachment swinging

### Purpose and movement

`bot.Swing_Attachments(x=90)` repeatedly swings both attachment motors to help load/unload an attachment. Each motor moves from its starting encoder angle to **starting angle + x**, then back. A 90° setting is a 90° stroke, not ±90° around the starting position. Negative `x` reverses the initial direction.

Both motors finish each stroke before either reverses. Swinging is nonblocking and is monitored through the menu loop and `bot.Update`/`bot.Wait`.

Choose one swing call for the required stroke; these are alternatives, not a sequence to run together.

| Call | Effect |
|---|---|
| `bot.Swing_Attachments()` | Request a 90-degree stroke. |
| `bot.Swing_Attachments(x=45)` | Request a shorter 45-degree stroke. |
| `bot.Swing_Attachments(x=-90)` | Start in the opposite direction. |
| `bot.Stop_Swing()` | Cancel active or queued swinging; brake both motors without a return stroke. |

### Configure swinging for each program

The third item in each `PROGRAMS` entry decides whether to swing while that ID is selected:

```python
    (Program_1, 'Member 1', False),
    (Program_2, 'Member 2', True),
```

These are example rows inside the full table, not a replacement for it. Set `True` if loading for that program benefits from swinging. Set `False` if its attachment must stay still. Most supplied entries are `False`; Program 9 is configured as `True`. ID 0 never swings, even if its flag is accidentally set to True.

There is no longer a `SWING_ON_STARTUP` setting. At startup, the master applies the initially selected entry’s flag. With the supplied `DEFAULT_PROGRAM_ID = 1` and Program 1 set to False, startup swinging is off. If the initial ID is 9, startup swinging is on.

| Event | Swing behavior |
|---|---|
| Master starts | Apply the initial ID’s flag. |
| LEFT/RIGHT selects another ID | Stop the previous swing, then start or leave off according to the newly selected entry. |
| CENTER release launches a program | Stop swinging before calling the route. |
| Program finishes successfully | Apply the same selected ID’s flag again. |
| Program is cancelled or fails | Stop and keep swinging off; return to the menu. |
| Swing stalls or times out | Stop and keep it off; do not retry on every menu update. |
| Selection changes after a stall/cancellation | Apply the newly selected ID’s flag. |

For example: select Program 9 → swinging starts → press/release CENTER → swinging stops and self-inspection starts → press/release CENTER again → self-inspection is cancelled and motors remain stopped in the menu.

### Stroke and acceleration

```python
SWING_DEGREES = 90
SWING_ACCELERATION_FACTOR = 1.5
```

`SWING_DEGREES` supplies the default stroke whenever the selector starts swinging. The factor 1.5 increases the acceleration and deceleration settings read before swinging by 50%. These are normally Pybricks defaults unless member code changed them. The helper uses smooth target movements, leaves speed/torque limits unchanged, and restores the original acceleration settings on stop, stall, timeout, or error. Restarts do not compound the multiplier.

### Optional custom stroke after a program

A route can request a custom stroke at its end:

```python
def Program_2(bot):
    from Member2_Missions import Run_A
    Run_A(bot)
    bot.Swing_Attachments(x=45)
```

For this example, set Program 2’s LUT swing flag to `True`. Within the running program, this call queues the requested stroke. After successful completion and tracked-movement cleanup, the selector uses that stroke only if the selected entry enables swinging. A False flag suppresses the request. Cancellation or failure discards it.

A later LEFT/RIGHT selection transition uses `SWING_DEGREES` again. A direct `Swing_Attachments()` call without `x` uses its function default of 90°.

`bot.Stop_Swing()` stops active swinging and clears a queued request. It does not change the entry’s flag: after a successful program, an enabled entry will start swinging again with the default stroke. To configure no automatic swinging for a program, set its LUT flag to False.

### Stopping, stalls, and alignment

CENTER release is detected using the menu’s debounce and polling logic (30 ms debounce; 10 ms menu polling). The stop command is sent before the next route starts; physical braking is not instantaneous.

If either attachment stalls against a hard stop during swinging, both attachment motors brake and the swing ends. The menu stays running for the next command. A stroke exceeding 20,000 ms has the same recoverable behavior. There is no automatic retry while the selection stays idle; a selection transition or later successful program can start swinging again.

Hard-stop contact **does not automatically reset encoder angles** and does not establish that both attachments have reached their intended alignment stops. The two-motor swing stops when either stalls. Use an explicit, separately tested alignment procedure when a repeatable reference position is required.

This recovery behavior applies specifically to the swing helper. It does not turn every `Attachment_Angle`, `Attachment_Target`, or `Attachment_Time` call into a run-until-stalled alignment function.

## 5. Configuration quick reference

| Setting | Current value | Meaning |
|---|---:|---|
| `M` | 10 | Total selectable entries, including quit; IDs 0–9. Allowed count: 1–10. |
| `DEFAULT_PROGRAM_ID` | 1 | Starting display ID. With `M = 1`, the master uses the only available ID, 0. |
| LUT swing flag | False, except ID 9 True | Controls swinging at startup, selection changes, and successful return. |
| `SWING_DEGREES` | 90 | Default automatic swing stroke in motor degrees. |
| `SWING_ACCELERATION_FACTOR` | 1.5 | Multiply pre-swing acceleration and deceleration by this factor. |
| `PROGRAM_BEEP_ENABLED` | `True` | Enable automatic start/exit tones. |
| `PROGRAM_BEEP_DURATION_MS` | 2000 | Automatic tone duration in milliseconds. |
| `TONE_VOLUME` | 30 | Speaker volume percentage. |
| `FINISH_TIMEOUT_MS` | 20000 | Outstanding-movement finish timeout and individual swing-stroke timeout. |

Default program tones are ID 0: B4; IDs 1–9: C4, D4, E4, F4, G4, A4, B4, C5, D5. Automatic tones last two seconds and are started for custom routes as well as placeholder programs. Normal tones are nonblocking: the route starts without waiting for the tone. After route completion, the selector may be used while the tone continues. ID 0 waits for its exit tone before quitting.

```python
PROGRAM_BEEP_ENABLED = False  # Disable automatic program and exit tones.
PROGRAM_BEEP_DURATION_MS = 2000
TONE_VOLUME = 30
```

This option does not disable explicit custom `bot.Beep(...)` calls. Cancelling a running program stops its current sound. Stopping sound at the configured time requires normal bot updates; blocking code can delay it.

## 6. Program 9: robot self-inspection

Program 9 is already connected in the supplied master. Save `Robot_Self_Inspection.py` beside the master and base. Its wrapper is:

```python
def Program_9(bot):
    from Robot_Self_Inspection import Robot_Self_Instpection
    Robot_Self_Instpection(bot)
```

The supplied self-inspection module supports this function spelling. It also provides `Robot_Self_Inspection` as a correctly spelled alias.

Its configured lookup-table entry is `(Program_9, 'Robot_self_inspection', True)`. Keep `M = 10`. Save the files, run the master, select 9, then press and release CENTER.

The master stops swinging before entering the self-check. The check uses the shared bot and tests driving, turning, reflectance readings, and attachment motion; it does not require a black line. Provide clearance for the 500 mm square route and pivot sweeps, and use attachments that can rotate through the requested two revolutions. Its nominal return to the start requires physical verification.

## 7. Common integration problems

| Symptom | Check |
|---|---|
| Import/module error | Member file is included, saved beside the master, and spelled exactly as the import. |
| Imported function not found | The imported name matches the function definition in the member file. |
| Program runs when imported | Remove top-level route calls and hardware creation; put activity inside `Run_A(bot)` or another entry function. |
| Duplicate hardware or wrong robot object | Use the supplied `bot`. `bot = DeltaBots` is a class reference, and `DeltaBots()` creates another instance; neither belongs inside the imported route. |
| Motor resource busy | Wait for or stop the previous tracked command before starting another on the same resource. |
| Swing does not start inside a route | The request is deferred until successful return and only used when the selected entry’s swing flag is True. |
| Swing stopped after touching a hard stop | Expected recovery behavior. Both attachment motors stop; use the menu for the next command. |
| Swinging continues after selecting another ID | Check the new entry’s flag; True starts a new swing for that selection. False leaves it off. |
| CENTER does not promptly cancel | Replace raw sleeps/blocking motor calls with bot methods; service `bot.Update()` in custom loops. |
| A False swing setting is rejected | Use `False`, not the string `'False'`; the flag must be a Boolean. |
| New program ID is missing | Check `M`, the wrapper definition, and the entry’s position in the lookup table. |
| Changes do not appear on the hub | Save all edited files and upload/run the intended master from the correct project folder. |

These notes were checked against the current source. Code examples are integration templates, not validated competition routes; verify the actual routes and attachment transitions on the team’s robot.

## 8. Compatibility with the current base

Use the simplified `DeltaBots_Base.py` with `DeltaBots`, `Stop_Drive`, and `Stop_All`. Older names `BaseRobot`, `bot.Stop()`, `Align_Line`, `Degrees_For_Distance`, and `Wait_For_Button` have been removed. The `Stop` enum remains available for stop modes.

The master handles program-selection buttons. Member routes should return control to the master after their work rather than implement another menu. The exact gyro reset name is `Reset_Gyro()`.

`MasterRobot` inherits the base movement functions and adds the master’s sound and swing behavior. It is compatible with route functions that accept the existing `bot`; there is no need to change those functions to create a different robot.
