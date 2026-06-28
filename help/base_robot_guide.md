# BaseRobot Function Reference

This guide explains every helper in `base_robot.py`: what each function does, what each parameter means in physical terms, and how to use them in mission code.

---

## Getting started

Mission files import and use `BaseRobot` like this:

```python
from base_robot import *

def Run(br: BaseRobot):
    br.driveForDistance(500, speed=250)
    br.turnForAngle(90, speed=100)

if __name__ == "__main__":
    br = BaseRobot()
    Run(br)
```

- **`br`** is your robot object. Create it once per run (`BaseRobot()`).
- **`Run(br)`** is the pattern this team uses so `master_program.py` can chain missions.
- Do **not** run `base_robot.py` directly — it has nothing to execute on its own.

Upload to the hub with:

```bash
pybricksdev run ble --name YOUR_HUB_NAME your_mission.py
```

---

## Robot hardware (physical setup)

These are configured in `BaseRobot.__init__` and should match how the robot is actually built.

| Component | Port | Notes |
|-----------|------|-------|
| Left drive motor | A | `Direction.COUNTERCLOCKWISE` = forward |
| Right drive motor | E | Default direction = forward |
| Left attachment motor | B | Used by `moveLeftAttachmentMotorForMillis` |
| Right attachment motor | F | Not yet wrapped in a helper |
| Left color sensor | C | Used by `stop_line` / `align_line` |
| Right color sensor | D | Used by `stop_line` / `align_line` |
| Hub gyro | Built into Prime Hub | Used when `gyro=True` on drive/turn/line functions |

If motors or sensors are plugged into different ports, update `base_robot.py` — do not change ports in every mission file.

---

## Global constants

These live at the top of `base_robot.py`. Tune them once for your robot, then all functions inherit the defaults.

### `TIRE_DIAMETER` (mm)

**Physical meaning:** The diameter of one drive wheel, measured in millimeters.

**Why it matters:** Pybricks converts motor rotation into distance traveled. If this number is wrong, the robot will consistently drive too far or not far enough.

**How to measure:** Measure the wheel across its center (including tire). Default: `56` mm.

---

### `AXLE_TRACK` (mm)

**Physical meaning:** The distance between the two drive wheels, measured at the point where they touch the ground.

**Why it matters:** Used for accurate turns. Wrong axle track → turns overshoot or undershoot.

**How to measure:** Measure center-to-center of the left and right wheel contact patches. Default: `113` mm.

---

### `STRAIGHT_ACCEL` (mm/s²)

**Physical meaning:** How quickly the robot **increases** forward/backward speed when starting a straight move.

**Example:** `200` means speed can rise by up to 200 mm/s every second (0 → 200 mm/s in ~1 s).

**Lower** = gentler start, less wheel slip. **Higher** = snappier start.

---

### `STRAIGHT_DECEL` (mm/s²)

**Physical meaning:** How quickly the robot **decreases** forward/backward speed when stopping a straight move.

**Example:** `600` means speed can drop by up to 600 mm/s every second.

**Higher** = harder braking, less overshoot past the target. **Too high** can cause skid on the FLL mat.

---

### `TURN_ACCEL` (deg/s²)

**Physical meaning:** How quickly the robot **increases** its spin rate when starting a turn.

**Example:** `200` means turn rate can rise by 200 degrees per second, per second.

---

### `TURN_DECEL` (deg/s²)

**Physical meaning:** How quickly the robot **decreases** its spin rate when finishing a turn.

**Higher** = stops rotation closer to the target angle, less angular overshoot.

---

## Shared concepts

### Sign conventions

| Parameter type | Positive | Negative |
|----------------|----------|----------|
| Drive `speed` / `distance` | Forward | Backward |
| Turn `angle` / turn rate | Clockwise (right) | Counterclockwise (left) |
| Attachment motor `speed` | One direction | Opposite direction |

### `then` (Stop behavior)

What the motors do **after** a move completes:

| Value | Physical behavior |
|-------|-------------------|
| `Stop.BRAKE` (default) | Motors passively brake — robot stops and stays put |
| `Stop.HOLD` | Motors actively hold position — resists being pushed |
| `Stop.COAST` | Motors freewheel — robot may roll slightly |

### `gyro` (True / False)

| Value | Physical behavior |
|-------|-------------------|
| `True` (default) | Hub gyro corrects drift while driving straight or turning |
| `False` | Uses only wheel encoders — less accurate but sometimes needed |

Always use `gyro=True` unless you have a specific reason not to.

### Color sensor `reflection()` (0–100%)

**Physical meaning:** How much light bounces back to the sensor.

| Typical surface | Approx. reflection |
|-----------------|-------------------|
| Black line / dark tile | 5–20% |
| Gray | 30–50% |
| White FLL mat | 70–90% |

Calibrate on **your** mat before relying on line functions. Write a quick test program that prints `br.colorSensorLeft.reflection()` while you move the sensor over the line.

---

## Functions

---

### `moveLeftAttachmentMotorForMillis(millis, speed)`

**What it does:** Runs the **left attachment motor** (Port B) for a fixed time, then stops.

**Parameters:**

| Parameter | Unit | Physical meaning |
|-----------|------|------------------|
| `millis` | milliseconds | How long the motor runs (1000 ms = 1 second) |
| `speed` | deg/s | How fast the motor spins; sign = direction |

**Example:**

```python
br.moveLeftAttachmentMotorForMillis(500, 250)   # run 0.5 s at 250 deg/s
br.moveLeftAttachmentMotorForMillis(1000, -200) # run 1 s in reverse
```

**When to use:** Raising/lowering an arm, flipping an attachment, or any timed mechanism move.

---

### `driveForDistance(distance, speed, then=Stop.BRAKE, gyro=True, accel=STRAIGHT_ACCEL, decel=STRAIGHT_DECEL)`

**What it does:** Drives straight a specific distance with automatic acceleration and deceleration. This is the **most accurate** way to move the robot.

**Parameters:**

| Parameter | Unit | Physical meaning |
|-----------|------|------------------|
| `distance` | mm | How far to travel; positive = forward, negative = backward |
| `speed` | mm/s | Top speed during the move |
| `then` | Stop | Motor behavior after stopping (see above) |
| `gyro` | bool | Use hub gyro for straight-line correction |
| `accel` | mm/s² | How fast speed ramps **up** at the start |
| `decel` | mm/s² | How fast speed ramps **down** near the target |

**Examples:**

```python
br.driveForDistance(500, speed=250)                          # forward 500 mm
br.driveForDistance(-300, speed=200)                       # backward 300 mm
br.driveForDistance(800, speed=300, decel=800)               # fast run, hard stop
br.driveForDistance(100, speed=120, accel=100, decel=300)    # slow precise approach
```

**Tuning tips:**

- Robot drives past target → increase `decel` or lower `speed`
- Wheels spin at start → decrease `accel` or lower `speed`
- Long moves: use high `speed`; final approach: short move with low `speed`

---

### `driveForTime(millis, speed, then=Stop.BRAKE, gyro=True)`

**What it does:** Drives at a constant speed for a fixed time, then stops abruptly.

**Parameters:**

| Parameter | Unit | Physical meaning |
|-----------|------|------------------|
| `millis` | milliseconds | How long to drive |
| `speed` | mm/s | Drive speed; positive = forward, negative = backward |
| `then` | Stop | Motor behavior after stopping |
| `gyro` | bool | Gyro correction while driving (helps stay straight) |

**Example:**

```python
br.driveForTime(2000, speed=200)   # drive forward for 2 seconds
br.driveForTime(500, speed=-150)   # drive backward for 0.5 seconds
```

**Caution:** Less precise than `driveForDistance` — no built-in deceleration profile, stops suddenly. Prefer `driveForDistance` when accuracy matters.

---

### `turnForAngle(angle, speed, then=Stop.BRAKE, gyro=True, accel=TURN_ACCEL, decel=TURN_DECEL)`

**What it does:** Rotates the robot in place by a given angle with automatic spin-up and spin-down.

**Parameters:**

| Parameter | Unit | Physical meaning |
|-----------|------|------------------|
| `angle` | degrees | How much to turn; positive = right (clockwise), negative = left |
| `speed` | deg/s | Maximum turn rate during the maneuver |
| `then` | Stop | Motor behavior after stopping |
| `gyro` | bool | Use hub gyro for accurate heading |
| `accel` | deg/s² | How fast turn rate ramps **up** |
| `decel` | deg/s² | How fast turn rate ramps **down** |

**Examples:**

```python
br.turnForAngle(90, speed=100)                    # turn right 90°
br.turnForAngle(-45, speed=80)                   # turn left 45°
br.turnForAngle(180, speed=120, decel=500)       # fast half-turn, firm stop
```

**Tuning tips:**

- Turn overshoots → increase `decel` or lower `speed`
- Turn feels sluggish → increase `speed` or `accel`

---

### `stop_line(speed, reflectivity, sensor=Side.LEFT, tolerance=3, stop_below=True, gyro=True, then=Stop.BRAKE)`

**What it does:** Drives until a **single color sensor** reads a target reflectivity, then stops. Used to find a line or color boundary on the mat.

**Parameters:**

| Parameter | Unit | Physical meaning |
|-----------|------|------------------|
| `speed` | mm/s | Drive speed while searching; sign = direction |
| `reflectivity` | % (0–100) | Target reflection value to stop at |
| `sensor` | Side | `Side.LEFT` or `Side.RIGHT` — which color sensor to watch |
| `tolerance` | % | Allowed slack around the target (default ±3) |
| `stop_below` | bool | `True` = stop when reflection ≤ target; `False` = stop when ≥ target |
| `gyro` | bool | Keep driving straight while searching |
| `then` | Stop | Motor behavior after stopping |

**How `stop_below` works:**

| `stop_below` | Stops when… | Typical use |
|--------------|-------------|-------------|
| `True` (default) | Sensor sees **dark** (reflection drops to target) | Finding a black line from white mat |
| `False` | Sensor sees **bright** (reflection rises to target) | Leaving a dark area onto white |

**Examples:**

```python
# Roll forward until left sensor hits black line (~15% on most FLL mats)
br.stop_line(speed=150, reflectivity=15, sensor=Side.LEFT)

# Back up until right sensor sees white mat again
br.stop_line(speed=-100, reflectivity=70, sensor=Side.RIGHT, stop_below=False)
```

**Calibration:** Run a test that prints sensor values over the line and white mat, then pick `reflectivity` between those readings.

---

### `align_line(reflectivity, tolerance=3, forward_speed=0, max_turn_rate=40, kp=0.4, gyro=True, then=Stop.BRAKE)`

**What it does:** Uses **both** color sensors in a feedback loop to rotate (and optionally creep forward) until left and right sensors both read the target reflectivity. Designed to center the robot on a line without overshooting one side.

**Parameters:**

| Parameter | Unit | Physical meaning |
|-----------|------|------------------|
| `reflectivity` | % (0–100) | Target reflection both sensors should reach |
| `tolerance` | % | How close each sensor must be to target to count as "aligned" |
| `forward_speed` | mm/s | Optional creep forward while aligning (`0` = pivot in place) |
| `max_turn_rate` | deg/s | Caps how fast the robot spins during correction |
| `kp` | unitless gain | How aggressively the robot corrects left/right imbalance |
| `gyro` | bool | Gyro assist during alignment drive |
| `then` | Stop | Motor behavior after aligned |

**How the feedback loop works:**

1. Read left and right reflection.
2. If both are within `tolerance` of `reflectivity` → done.
3. Compute `turn_error = left_refl - right_refl`.
   - If left reads brighter than right → robot turns to balance them.
4. Turn rate is scaled down when close to target (reduces overshoot).
5. If turn direction flips (sign change), turn rate is damped to 25% (prevents oscillating past the line).

**Examples:**

```python
# Pivot in place until both sensors are on the black line
br.align_line(reflectivity=15)

# Creep forward slowly while aligning on the line
br.align_line(reflectivity=15, forward_speed=50, tolerance=5)

# Gentler correction (less wobble)
br.align_line(reflectivity=15, kp=0.25, max_turn_rate=25)
```

**Tuning tips:**

| Problem | Try |
|---------|-----|
| Robot wiggles back and forth | Lower `kp` or `max_turn_rate` |
| Takes too long to align | Raise `kp` slightly |
| One side overshoots repeatedly | Lower `max_turn_rate`; widen `tolerance` slightly |
| Need to align while approaching line | Set small `forward_speed` (e.g. 30–50) |

---

## Typical mission sequences

### Drive to a line and stop

```python
def Run(br: BaseRobot):
    br.driveForDistance(400, speed=250)
    br.stop_line(speed=80, reflectivity=15, sensor=Side.LEFT)
    br.align_line(reflectivity=15)
```

### Turn and drive with tuned deceleration

```python
def Run(br: BaseRobot):
    br.turnForAngle(90, speed=100)
    br.driveForDistance(600, speed=300, decel=800)
    br.driveForDistance(80, speed=100, decel=400)  # slow final approach
```

### Attachment + drive

```python
def Run(br: BaseRobot):
    br.moveLeftAttachmentMotorForMillis(800, 300)
    br.driveForDistance(500, speed=250)
    br.moveLeftAttachmentMotorForMillis(500, -300)
```

---

## Quick reference table

| Function | Primary use | Key units |
|----------|-------------|-----------|
| `moveLeftAttachmentMotorForMillis` | Timed attachment move | ms, deg/s |
| `driveForDistance` | Precise straight travel | mm, mm/s, mm/s² |
| `driveForTime` | Timed straight travel (less precise) | ms, mm/s |
| `turnForAngle` | Precise rotation | deg, deg/s, deg/s² |
| `stop_line` | Find line with one sensor | mm/s, reflection % |
| `align_line` | Center on line with both sensors | reflection %, deg/s |

---

## Further reading

- [Pybricks API docs](https://docs.pybricks.com/en/latest/index.html)
- [Team FLL Pybricks VS Code tutorial](https://github.com/MrGibbage/fll-pybricks-vscode-tutorial)
- [Pybricks DriveBase tuning](https://docs.pybricks.com/en/latest/robotics.html)
