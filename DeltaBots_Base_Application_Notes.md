# DeltaBots Base — Application Notes

This guide explains how to use the current `DeltaBots_Base.py` to build robot routes. It covers the eight main movement and attachment functions first, followed by concurrent operation, supporting functions, configuration, and troubleshooting.

Examples use the exact function names and parameters from the source. The gyro reset function is `Reset_Gyro()`. Use one robot instance per running script and pass it to each route function.

## 1. Program setup and master integration

When your program runs from the master, it receives the robot as `bot`. Use that robot; do not create another one.

```python
# My_Program.py
from DeltaBots_Base import Stop


def Run(bot):
    bot.Reset_Gyro(0)
    bot.Gyro_Move(direction=0, distance=300, velocity=150,
                  acceleration=200, stop=Stop.BRAKE, wait=True)
```

This route sets its starting heading to 0°, drives forward 300 mm, and stops.

To connect the route to Program 1 in the master, use:

```python
def Program_1(bot):
    from My_Program import Run
    Run(bot)
```

Save `My_Program.py` beside `DeltaBots_Master.py` and `DeltaBots_Base.py`. Save both edited files, run the master, select ID 1 with LEFT/RIGHT, then press and release CENTER.

The program ID is not a game mission number. One program can perform several game missions in any order. If your program number is not 1, edit your assigned `Program_N` instead.

## 2. Units and conventions

| Item | Rule | Example |
|---|---|---|
| Driving distance | Use millimeters. | 500 mm = 50 cm. |
| Time | Use milliseconds. | 1000 ms = 1 second. |
| Heading and turning | Positive is clockwise; negative is counterclockwise. | Turn +90° to turn right. |
| Attachment selection | `-1` is left; `1` is right. | `Attachment_Time(-1, ...)` uses the left motor. |
| Parameter names | Python names are case-sensitive. | Write `velocity`, not `Velocity`; `False`, not `false`. |
| Normal sequence | Use `wait=True`. | Finish this action before starting the next. |
| Concurrent actions | Use `wait=False`, then service them with the bot’s waiting functions. | Drive and move an attachment together. |

`velocity` means speed. For driving it is **mm/s**. For turning and attachments it is **degrees/s**. Use the units appropriate to each function.

| Stop setting | What it does |
|---|---|
| `Stop.BRAKE` | Brakes the motor. A useful default for driving. |
| `Stop.HOLD` | Actively holds the motor’s position. Useful for attachments. |
| `Stop.COAST` | Releases the motor so it can move freely. |

The master brakes all motors when your program finishes. An attachment’s HOLD setting does not stay active through that final cleanup.

## 3. The eight main functions

### 1 — Reset_Gyro: choose the robot’s heading reference

```python
bot.Reset_Gyro(0)
```

This says: **“The direction the robot faces now is 0°.”** It does not turn the robot.

Place the robot in its intended starting direction and keep it still. This function releases all motors while it waits for the IMU, so support any attachment that depends on the motor holding it up.

Normally call it once at the beginning of a route. Resetting it again changes what all later direction numbers mean.

### 2 — Gyro_Move: drive while facing a direction

Drive forward 50 cm:

```python
bot.Gyro_Move(direction=0, distance=500, velocity=150,
              acceleration=200, stop=Stop.BRAKE, wait=True)
```

Drive backward 50 cm while still facing the same direction:

```python
bot.Gyro_Move(direction=0, distance=-500, velocity=150,
              acceleration=200, stop=Stop.BRAKE, wait=True)
```

| Parameter | Meaning |
|---|---|
| `direction` | Heading to face while moving. |
| `distance` | How far to move: positive forward, negative backward. |
| `velocity` | Maximum requested driving speed. Keep it positive here. |
| `acceleration` | How quickly the requested driving speed increases. |
| `stop` | How to stop at the end. |
| `wait` | Whether to finish this movement before continuing. |

**Turn toward the desired direction first.** This function holds a heading; it is not a command to drive to a location on the mat.

Start with the example speeds. A very large speed number does not guarantee faster travel because the motors have limits.

### 3 — Gyro_Turn: turn through an angle

Turn clockwise 90° around the robot’s axle center:

```python
bot.Gyro_Turn(90, pivot=0, velocity=90,
              acceleration=200, stop=Stop.BRAKE, wait=True)
```

Turn counterclockwise 90°:

```python
bot.Gyro_Turn(-90, pivot=0, velocity=90,
              acceleration=200, stop=Stop.BRAKE, wait=True)
```

**The first number means how much to turn from the current direction.** If the robot faces 90° and you call `Gyro_Turn(90)`, it ends facing 180°.

| `pivot` | Where the robot turns around |
|---:|---|
| `0` | Center between the driving wheels. |
| `-1` | Left wheel. |
| `1` | Right wheel. |

Example: turn around the left wheel:

```python
bot.Gyro_Turn(90, pivot=-1, velocity=90,
              acceleration=200, stop=Stop.BRAKE, wait=True)
```

A wheel-pivot turn also shifts the robot’s center. Account for that when planning a route. Each turn must be between -355° and +355°. Use two 180° turns for a full circle.

**Additional turn options:** fractional pivots and pivots outside -1 to +1 are supported. The pivot point is `pivot * axle_track / 2` mm to the right of axle center.

`absolute=True` uses an accumulated heading target, not a shortest-path compass target. From accumulated +170° to absolute -170°, the commanded rotation is -340°. The difference between target and starting heading must still be within ±355°. Read accumulated heading with `Get_YAW_Angle(wrapped=False)`.

For example, to face wrapped heading -90° from heading 180°, a relative +90° turn reaches 270°, which wraps to -90°. Passing -90 without `absolute=True` would instead turn from 180° to 90°.

### 4 — Stop_Line: move until a color sensor finds a line

Use the left color sensor:

```python
bot.Stop_Line(sensor=-1, velocity=60, reflectance=40,
              stop=Stop.BRAKE, wait=True)
```

The value 40 is an example. Measure your mat first, then choose a suitable value.

| `sensor` | Behavior with the default settings |
|---:|---|
| `-1` | Stop using the left sensor. |
| `1` | Stop using the right sensor. |
| `0` | Use both sensors and adjust the wheels to line up on the edge. |

For two-sensor alignment:

```python
bot.Stop_Line(sensor=0, velocity=60, reflectance=40,
              stop=Stop.BRAKE, wait=True)
```

Both-sensor mode may move each wheel forward or backward to reach the chosen reflectance. It does not simply stop when both sensors are over solid black.

Print the readings to choose a threshold:

```python
bot.Print_Reflectance()
```

Compare readings over bright and dark parts of the mat. The default detects a reading at or below your threshold. Sensors should be mounted at matching positions for two-sensor alignment. If there is no suitable line, do not run this test.

**Later options:** `both_mode='any'` stops when either sensor detects the line without fine alignment; `stop_below=False` detects a rise in reflectance instead.

### 5 — Attachment_Reset: set an attachment’s position number

```python
bot.Attachment_Reset(-1, 0)
```

This says: **“The left attachment’s current position is now 0°.”** It brakes the motor and changes the position number reported by its encoder. It does not move the attachment to a physical starting position.

Place the attachment at a known position before assigning zero. Resetting while it is in a different position changes where later absolute targets will go.

### 6 — Attachment_Angle: move by an amount

Move the right attachment another 90°:

```python
bot.Attachment_Angle(1, 90, velocity=300,
                     stop=Stop.HOLD, wait=True)
```

Move it back by 90°:

```python
bot.Attachment_Angle(1, -90, velocity=300,
                     stop=Stop.HOLD, wait=True)
```

Keep `velocity` positive. The sign of the angle chooses the motor direction. Positive motor rotation may raise or lower your attachment depending on its construction—check your mechanism.

### 7 — Attachment_Time: run for a duration

Run the left attachment for one second:

```python
bot.Attachment_Time(-1, 1000, velocity=300,
                    stop=Stop.HOLD, wait=True)
```

Run it in the opposite direction:

```python
bot.Attachment_Time(-1, 1000, velocity=-300,
                    stop=Stop.HOLD, wait=True)
```

Here, the sign of **velocity** chooses direction. The second number is time in milliseconds. A timed movement does not guarantee a particular final angle.

### 8 — Attachment_Target: move to a position

```python
bot.Attachment_Reset(-1, 0)

bot.Attachment_Target(-1, 90, velocity=300,
                      stop=Stop.HOLD, wait=True)

bot.Attachment_Target(-1, 0, velocity=300,
                      stop=Stop.HOLD, wait=True)
```

Keep velocity positive. The motor chooses the direction needed to reach the target.

| If the attachment is currently at 30°… | Result |
|---|---|
| `Attachment_Angle(1, 90, ...)` | Adds 90° and ends near 120°. |
| `Attachment_Target(1, 90, ...)` | Goes to position 90°, moving about 60°. |

Calling `Attachment_Target` with the same target twice does not request another full movement. The motor is already near that position.

## 4. Moving an attachment while driving or turning

Use `wait=True` for sequential actions. To overlap actions on different motor resources, use `wait=False`:

```python
bot.Gyro_Turn(90, pivot=0, velocity=90,
              acceleration=200, stop=Stop.BRAKE, wait=False)

bot.Attachment_Time(1, 1000, velocity=300,
                    stop=Stop.HOLD, wait=False)

bot.Wait_All()
```

`wait=False` means the command starts and the next Python statement can run. The movement may still be running at that point. `bot.Wait_All()` keeps the movements running correctly and waits until all tracked movements finish.

To start an attachment after the robot has already been driving for 1.5 seconds:

```python
bot.Gyro_Move(direction=0, distance=600, velocity=150,
              acceleration=200, stop=Stop.BRAKE, wait=False)

bot.Wait(1500)

bot.Attachment_Time(1, 1000, velocity=300,
                    stop=Stop.HOLD, wait=False)

bot.Wait_All()
```

**Use `bot.Wait()`, not ordinary sleep or raw Pybricks wait.** The bot’s waiting functions continue updating the custom gyro controller.

You may run driving/turning and both attachments together. You may not start driving and turning at the same time because they use the same driving motors. Likewise, finish or stop one attachment command before starting another on the same attachment.

For both attachments, call each side separately:

```python
bot.Attachment_Time(-1, 1000, velocity=300,
                    stop=Stop.HOLD, wait=False)
bot.Attachment_Time(1, 1000, velocity=300,
                    stop=Stop.HOLD, wait=False)
bot.Wait_All()
```

## 5. Supporting functions

| Function | Purpose |
|---|---|
| `bot.Wait(1500)` | Wait 1.5 seconds while updating movements. |
| `bot.Wait_All()` | Wait for all tracked finite movements to finish. |
| `bot.Stop_Drive(stop=Stop.BRAKE)` | Stop the driving motors and cancel their current movement. |
| `bot.Attachment_Stop(-1, stop=Stop.BRAKE)` | Stop the left attachment and cancel its movement. |
| `bot.Stop_All(stop=Stop.BRAKE)` | Stop all motors. |
| `bot.Get_YAW_Angle()` | Read the heading; +180° is displayed as -180°. |
| `bot.Print_Reflectance()` | Print both color sensor readings. |

| Additional function | Purpose and key behavior |
|---|---|
| `Read_Reflectance(sensor=0)` | Returns `(left, right)`; use sensor -1 or +1 for one reading. |
| `Drive_Time(millis, velocity=100, direction=None, ...)` | Timed heading-controlled drive. Velocity is signed mm/s; no configurable acceleration parameter. |
| `Get_Distance()` | Average signed wheel encoder travel in mm, not an x/y position or total path length. |
| `Attachment_Run(side, velocity=300)` | Continuous rotation. Requires an explicit stop and has no automatic timeout. |
| `Wait_For(task)` | Waits for one task while updating all jobs, then returns its result. |
| `Update()` | Services active tracked jobs once without sleeping; returns whether tracked jobs remain. |

`Wait_All` does not stop or wait for continuous `Attachment_Run` commands. A `wait=False` call returns a `MotionTask` with `done`, `cancelled`, and `result` fields. Refresh its state using `Update` or a bot waiting function before checking it. A cancelled task is not a successfully completed movement.

Use the master’s existing robot for routes. For a standalone launcher:

```python
from DeltaBots_Base import DeltaBots, Stop
from My_Program import Run

if __name__ == '__main__':
    bot = DeltaBots()
    try:
        Run(bot)
        bot.Wait_All()
    finally:
        bot.Stop_All(stop=Stop.BRAKE)
```

## 6. Timeouts and troubleshooting

Most movements have a **20-second timeout**: a `MotionTimeout` exception is raised if the command does not finish in time. The master normally stops the motors and returns to the menu. Check the printed message before trying again.

| Problem | What to check |
|---|---|
| `Gyro_Reset` is not found | Use the exact name `Reset_Gyro`. |
| Robot moves the wrong way | Check distance sign, motor ports, and motor mounting. |
| Robot turns to the wrong heading | `Gyro_Turn(90)` means turn another 90°, not face 90°. |
| Negative attachment velocity is rejected | Angle/Target require positive velocity. Use angle/target to choose direction. |
| Motor resource busy | A previous command on that motor is still active. Finish or stop it first. |
| `wait=False` motion behaves incorrectly | Use `bot.Wait`, `bot.Wait_All`, or another bot scheduler helper. |
| Line test does not finish | Check the line, sensor placement, and measured reflectance threshold. |
| Attachment hits a mechanical stop | Stop and check the mechanism. Angle/Target/Time are not automatic homing functions. |

The master’s attachment **swing** helper can stop normally on a detected stall. That special behavior does not mean every base attachment command will treat a hard stop as a successful movement.

## 7. Route verification

1. Choose the correct attachment and starting pose.
2. Test a short movement at a modest speed.
3. Use a blocking call or `Wait_All()` before checking the completed movement.
4. Check the robot’s actual position; a completed command does not prove perfect physical accuracy.
5. Combine tested actions into a route.
6. Save your member file and test it through its assigned master program.

The master provides `Swing_Attachments`, `Stop_Swing`, and `Beep`; these are not methods of a standalone `DeltaBots()` object. See the separate master application notes for loading/unloading behavior and program integration.

**For older team code:** `BaseRobot`, `bot.Stop()`, `Align_Line`, `Degrees_For_Distance`, and `Wait_For_Button` were removed from the simplified base. Use `DeltaBots`, `Stop_Drive`, and `Stop_Line(sensor=0)` as appropriate. The `Stop` enum is still available.

Examples were checked for syntax and parameter compatibility against the current base. Their physical movements must still be tested with the team’s robot and attachments.

## 8. Hardware configuration

| Setting | Default | Purpose |
|---|---|---|
| Drive motors | Left A, right E | Left positive direction configured counterclockwise; right uses its default. |
| Attachment motors | Left B, right F | Both use default motor positive direction. |
| Color sensors | Left C, right D | Both required by initialization. |
| `wheel_diameter` | 56 mm | Motor-angle to wheel-travel conversion. |
| `axle_track` | 113 mm | Wheel spacing used for motor mixing and pivots. |
| `top_side`, `front_side` | `Axis.Z`, `Axis.X` | Hub mounting orientation. |
| `max_motor_speed` | 800 deg/s | Software drive-motor speed cap; does not configure attachments. |
| `loop_ms` | 10 ms | Nominal controller update interval. |

All four motors and both sensors must be present. Configure the hardware once at robot creation. Do not create a separate `DriveBase` to control the same driving motors.

With 56 mm wheels and the default 800 deg/s cap, straight-line speed is limited to approximately 391 mm/s. A higher requested velocity cannot override that cap. Steering correction and physical load may reduce actual speed further.

## 9. Parameter defaults and behavior details

The examples deliberately keep the commonly changed parameters visible. Other parameters have defaults and can be omitted. The exact signatures in Section 10 list every supported argument.

| Function | Additional defaults and behavior |
|---|---|
| `Reset_Gyro` | `angle=0`, timeout 20000 ms. Coasts all motors, waits one second, then requires IMU ready and stationary. Returns accumulated heading. It resets the heading reference, not the physical robot pose. |
| `Gyro_Move` | `direction=None` holds starting heading; `distance=100`, velocity 150, acceleration 200, deceleration 400. Distance tolerance 2 mm; heading gain 3; correction cap 60 deg/s; distance gain 4. Returns signed encoder travel. |
| `Gyro_Turn` | Relative by default; pivot 0, velocity 90, acceleration 200, deceleration 300, tolerance 1°, gain 3. Returns final accumulated heading. |
| `Stop_Line` | Sensor 0, velocity 80, reflectance 50, both mode `'all'`, `stop_below=True`, 3 consecutive samples, maximum travel 1000 mm, reflectance tolerance 2, fine speed 30 mm/s, alignment gain 1.5. Returns both final reflectances. |
| `Attachment_Angle` / `Attachment_Target` | Velocity 300 deg/s, stop HOLD, timeout 20000 ms, wait True. Return final encoder angle. |
| `Attachment_Time` | Same defaults; duration must be positive and no greater than timeout. Returns final encoder angle. |
| `Attachment_Reset` | New angle defaults to 0. Brakes and assigns the encoder reference; does not home mechanically. |

Finite drive/line methods default to BRAKE, timeout 20000 ms, and `wait=True`. `wait=False` returns a task instead of the blocking result. Continuous and immediate helper functions do not take a `wait` parameter.

### Two-sensor line alignment

The approach continues until either sensor detects the threshold. The robot then independently adjusts the wheels until both readings settle within `reflectance ± tolerance`. Gyro heading correction is used during approach, not during this independent alignment phase.

Use matched sensor positions ahead of the wheels and a reachable transverse edge. For alignment, the target must satisfy `tolerance < reflectance < 100 - tolerance`. A wide uniformly black area is not an intermediate-reflectance edge.

Negative velocity reverses travel and the alignment correction direction. `stop_below=False` changes detection from dark-line entry to increasing reflectance. The timeout covers approach and alignment together. `max_distance` limits the cumulative absolute travel of either wheel across both phases, not just the robot’s net displacement.

### Concurrent control and failure handling

At most one tracked drive job and one job per attachment may run at once. Calling another command on a busy tracked resource raises `RuntimeError`. Finish the earlier job or cancel it with the appropriate stop function first.

The scheduler runs when serviced by `Wait`, `Wait_For`, `Wait_All`, or `Update`; it is not a background thread. Raw sleeps and blocking raw motor commands can prevent gyro updates and delay timeout detection. Motors can continue at their last command during that gap.

Each movement’s deadline starts when it is issued. `Wait_All(timeout_ms=...)` adds its own deadline starting when called. The master also uses `FINISH_TIMEOUT_MS` when joining pending work after a program returns.

Tracked-job failures trigger motor cleanup and propagate to the caller when the scheduler runs. A standalone launcher should stop motors in `finally`; the master provides its own program cleanup. A timeout is not proof of stall detection, and command completion does not prove exact physical travel.

## 10. Exact public function signatures

These signatures are extracted from the current source. Call methods as `bot.Function(...)`; call the constructor as `DeltaBots(...)`. `DEFAULT_TIMEOUT_MS` is 20000.

```text
DeltaBots(wheel_diameter=56, axle_track=113, left_drive=Port.A, right_drive=Port.E, left_attachment=Port.B, right_attachment=Port.F, left_sensor=Port.C, right_sensor=Port.D, top_side=Axis.Z, front_side=Axis.X, max_motor_speed=800, loop_ms=10)
```

```text
Update()
```

```text
Wait(millis)
```

```text
Wait_For(task)
```

```text
Wait_All(timeout_ms=DEFAULT_TIMEOUT_MS)
```

```text
Stop_Drive(stop=Stop.BRAKE)
```

```text
Stop_All(stop=Stop.BRAKE)
```

```text
Get_Distance()
```

```text
Reset_Gyro(angle=0, timeout_ms=DEFAULT_TIMEOUT_MS)
```

```text
Get_YAW_Angle(wrapped=True)
```

```text
Gyro_Turn(angle, pivot=0, velocity=90, acceleration=200, deceleration=300, tolerance=1, stop=Stop.BRAKE, timeout_ms=DEFAULT_TIMEOUT_MS, absolute=False, kp=3, wait=True)
```

```text
Gyro_Move(direction=None, distance=100, velocity=150, acceleration=200, deceleration=400, stop=Stop.BRAKE, timeout_ms=DEFAULT_TIMEOUT_MS, tolerance=2, heading_kp=3, max_turn_rate=60, distance_kp=4, wait=True)
```

```text
Drive_Time(millis, velocity=100, direction=None, stop=Stop.BRAKE, timeout_ms=DEFAULT_TIMEOUT_MS, wait=True)
```

```text
Read_Reflectance(sensor=0)
```

```text
Print_Reflectance()
```

```text
Stop_Line(sensor=0, velocity=80, reflectance=50, stop=Stop.BRAKE, timeout_ms=DEFAULT_TIMEOUT_MS, both_mode='all', stop_below=True, consecutive=3, max_distance=1000, tolerance=2, fine_velocity=30, align_kp=1.5, wait=True)
```

```text
Attachment_Angle(side, angle, velocity=300, stop=Stop.HOLD, timeout_ms=DEFAULT_TIMEOUT_MS, wait=True)
```

```text
Attachment_Target(side, angle, velocity=300, stop=Stop.HOLD, timeout_ms=DEFAULT_TIMEOUT_MS, wait=True)
```

```text
Attachment_Time(side, millis, velocity=300, stop=Stop.HOLD, timeout_ms=DEFAULT_TIMEOUT_MS, wait=True)
```

```text
Attachment_Run(side, velocity=300)
```

```text
Attachment_Stop(side, stop=Stop.HOLD)
```

```text
Attachment_Reset(side, angle=0)
```

