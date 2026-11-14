# DeltaBots Changelog

## 2026-11-13 — Speed improvements (branch `DeltaBots_Post_Qualifier`)

Three changes to `DeltaBots_Base.py` make every program faster. The programs
themselves were not edited; they pick up the new behavior automatically.

| # | Change | Saved per run | Saved for all 8 runs |
|---|---|---|---|
| 1 | `Reset_Gyro()`: no pause at program start | ~1.2 s | **~10 s** |
| 2 | `Gyro_Move()`: higher speed cap, faster acceleration, creep fix | 0–2.9 s | **~8.5 s now, up to ~13 s** (see 2b) |
| 3 | `Gyro_Turn()`: tuned `kp` and new brake-early `lead_ms`, creep fix | 0–1.5 s | **~4.3 s** |
| | **Total** | | **~23 s now, up to ~27 s** |

Savings were estimated by running each program's commands through a robot
simulation with the old and the new code. The simulation was checked against
the real robot tests below (straight moves within 0.01 s, turn savings at 30°
and 90° within 0.01 s). Real savings on the mat may differ a little.

### Quick reference: what changed

| Function | Setting | Before | Now |
|---|---|---|---|
| `DeltaBots()` | `max_motor_speed` (drive speed cap) | 800 deg/s (≈391 mm/s) | **1000 deg/s (≈489 mm/s)** |
| `Reset_Gyro()` | waits for 1 s of stillness | always | **no** (`wait_still=True` to wait) |
| `Gyro_Move()` | `acceleration` | 200 mm/s² | **400 mm/s²** |
| `Gyro_Move()` | `deceleration` | 400 mm/s² | 400 mm/s² (unchanged) |
| `Gyro_Move()` | `min_speed` (creep fix) | — | **40 mm/s** |
| `Move_Straight()` | `acceleration` | 200 mm/s² | **400 mm/s²** |
| `Gyro_Turn()` | `kp` | 3 | **16** |
| `Gyro_Turn()` | `lead_ms` (brake early) | — | **40 ms** |
| `Gyro_Turn()` | `min_rate` (creep fix) | — | **20 deg/s** |
| `Gyro_Turn()` | velocity / acceleration / deceleration | 90 / 200 / 300 | unchanged |

---

### 1. `Reset_Gyro()` — no more pause at program start (~1.2 s per run, ~10 s total)

**Problem.** After pressing CENTER, the robot always waited 1–2 seconds before
moving. Every program starts with `bot.Reset_Gyro(0)`, which waited until the
hub reported "stationary". Pybricks only reports that after the hub has been
completely still for a full second, and pressing the button shakes the hub.

**Change.** The heading is now reset right away. It still waits if the gyro is
not calibrated yet (right after power-on, or if the robot has not sat still for
a few seconds in the last 10 minutes), which is rare. Calibration itself is not
affected: Pybricks recalibrates automatically whenever the robot sits still,
for example in the menu between runs.

- Old behavior when needed: `bot.Reset_Gyro(0, wait_still=True)`.
  `Robot_Self_Inspection.py` uses this.
- **Operators: take your hand off the robot before pressing CENTER.**

---

### 2. `Gyro_Move()` — faster driving (~8.5 s now, up to ~13 s total)

#### 2a. Higher speed cap: 800 → 1000 deg/s

The software capped driving at 800 deg/s (≈391 mm/s), so `velocity=1000` drove
no faster than `velocity=400`. The cap is now 1000 deg/s (≈489 mm/s, +25%).
It is also limited automatically to the motors' own firmware limit.

Measured with `Coach_Test.py`: the motors top out at **about 1100 deg/s
(≈540 mm/s)**, close to LEGO's 185 rpm rating. 1100 is possible but only at
full motor power, leaving nothing for steering corrections or a weaker battery,
so 1000 is the recommended cap.

#### 2b. Faster default acceleration: 200 → 400 mm/s²

With 200 mm/s², short moves never reached top speed. The default for
`Gyro_Move()` and `Move_Straight()` is now 400 mm/s². Deceleration stays 400.

| Straight move | Before (cap 800, accel 200) | Now (cap 1000, accel 400) |
|---|---|---|
| 300 mm | 2.1 s | 1.7 s |
| 600 mm | 3.0 s | 2.4 s |
| 1000 mm | 4.0 s | 3.3 s |

Wheel slip test (`Coach_Test.py`, robot without attachments): **no slip at
1200 mm/s², slip at 1600 mm/s²**. 400 is well inside the safe range; up to about
800 is reasonable (keep margin for attachments, dust and worn tires). When the
wheels slip, distances are wrong because the encoders count wheel spin as travel.

**Why "up to ~13 s":** Programs 1, 2 and 8 pass `acceleration=200` in their own
code, so they keep the old slow acceleration. Changing those to 400 (or
removing them to use the default) would save about 0.75 s (Program 1), 2.2 s
(Program 2) and 2.4 s (Program 8) more, about 5 s in total. Those routes must
then be re-tested.

#### 2c. Creep fix: `min_speed=40`

Near the target, `Gyro_Move` set its speed to 4 × the distance left
(`distance_kp=4`): 40 mm/s at 10 mm, 20 mm/s at 5 mm, 12 mm/s at 3 mm. The robot
crawled over the last millimeters. With higher deceleration this took about
0.5 s per move. Now it never goes slower than 40 mm/s until it is within the
2 mm stopping window, then brakes. Accuracy is unchanged. `min_speed=0` restores
the old behavior. With the default deceleration of 400 the effect is small
(about 0.1 s per move); it matters most if deceleration is raised later.

---

### 3. `Gyro_Turn()` — faster turns without overshoot (~4.3 s total)

**Problem.** `kp=3` was chosen to prevent overshoot. It works, but the turn
speed was capped at 3 × the degrees left, so the robot slowed down for most of
every turn. In the simulation a 90° turn took about the same time at
`velocity` 100, 200 or 400, so higher velocity settings bought almost nothing.

**Why higher `kp` alone does not work.** The gyro and motors react a few
hundredths of a second late, so the robot keeps turning briefly after the code
says stop. On the robot, every `kp` above 3 overshot by 1.0–1.9°, more than the
1° tolerance, so the robot had to turn back.

**Change.**

- **`lead_ms=40` (new, "brake early"):** the slowdown is planned as if the robot
  keeps turning for 40 ms after each command. This makes up for the delay.
- **`kp=16`:** with brake-early on, a much higher `kp` no longer overshoots.
- **`min_rate=20` (creep fix):** the last few degrees are approached at a steady
  20 deg/s instead of crawling slower and slower.

**How the values were chosen** (`Turn_Tuner.py`, velocity 200, turns of 30°,
90° and 180° there and back; pass = overshoot ≤ 0.5° and final error ≤ 1°):

- Round 1 (floor), `kp` 3/5/8/12 × `lead_ms` 0/40/80/120: no brake-early →
  overshoot; 40 ms → no overshoot; 80–120 ms → slower than before.
- Round 2 (game mat), `kp` 8/12/16 × `lead_ms` 20/30/40/50: 20 ms overshoots on
  the mat; 30 ms passes with little margin; **40 ms gives 0.0° overshoot**, and
  so do its neighbors (`kp=16, lead_ms=50` and `kp=12, lead_ms=40`).

Result on the game mat:

| Turn | Before (`kp=3`) | Now (`kp=16, lead_ms=40`) | Change |
|---|---|---|---|
| 30° | 1.03 s | **0.73 s** | −29% |
| 90° | 1.71 s | **1.39 s** | −19% |
| 180° | 1.76 s | 1.90 s | +8% |
| Overshoot | 0.0° | **0.0°** | same |
| Final error | ≤0.7° | ≤0.7° | same (tolerance 1°) |

Large turns (≈135° and more) are slightly slower because braking 40 ms early
from high speed starts about 8° early. Most of the team's turns are 90° or less.

- Old behavior for one turn: `bot.Gyro_Turn(..., kp=3, lead_ms=0)`.
- If a turn overshoots: `bot.Gyro_Turn(..., kp=12, lead_ms=40)` (0.0° overshoot
  on both floor and mat).
- Re-run `Turn_Tuner.py` if the robot's weight, wheels or mat change.

---

### Estimated savings per program

| Program | Owner | Run time before | 1. Start pause | 2. Moves (now) | 2. Moves (potential) | 3. Turns | Total now |
|---|---|---|---|---|---|---|---|
| 1 | Delina | 4.3 s | 1.2 s | 0.0 s | 0.75 s | — | **1.2 s** |
| 2 | Delina | 19.4 s | 1.2 s | 0.3 s | 2.5 s | 0.5 s | **2.0 s** |
| 3 | Richard | 19.2 s | 1.2 s | 2.2 s | 2.2 s | 0.5 s | **4.0 s** |
| 4 | Alyssa | 13.2 s | 1.2 s | 1.0 s | 1.0 s | 1.1 s | **3.3 s** |
| 5 | Alyssa | 16.5 s | 1.2 s | 2.9 s | 2.9 s | 0.5 s | **4.6 s** |
| 6 | Justin | 5.8 s | 1.2 s | 0.6 s | 0.6 s | — | **1.8 s** |
| 7 | Justin | 10.3 s | 1.2 s | 1.4 s | 1.4 s | 0.5 s | **3.1 s** |
| 8 | Michael | 31.4 s | 1.2 s | 0.1 s | 2.5 s | 1.0–1.5 s | **2.3–2.8 s** |
| **All** | | | **~10 s** | **~8.5 s** | **~13 s** | **~4.3 s** | **~23 s** |

"Potential" = after Programs 1, 2 and 8 change `acceleration=200` to 400.
Time-limited moves (for example Program 4's wall push with `time_ms`) take the
same time as before and are not counted.

### Who needs to re-test (on the game mat)

Every program, because the robot now starts sooner, drives faster and turns
faster. Distances and angles are unchanged, but anything that depends on time
can line up differently: `time_ms` limits, `bot.Wait(ms)` between moves, and
attachments started with `wait=False` while driving (the robot may arrive
before the attachment finishes).

| Program | Owner | Check especially |
|---|---|---|
| 1 | Delina | Starts sooner; moves unchanged (`acceleration=200` in code). |
| 2 | Delina | Right attachment lowers with `wait=False` while driving; 25° turn. |
| 3 | Richard | `velocity=700` moves now ≈489 mm/s; attachments with `wait=False`; −40° turn. |
| 4 | Alyssa | **Pivot turns** (`pivot=-1`, `0.3`, `-5`) with `time_ms`; the turn tuning used center turns, so watch for overshoot. Last move `velocity=1000` faster. |
| 5 | Alyssa | **Pivot turn** (`pivot=-1`); `velocity=900` moves faster; timed moves. |
| 6 | Justin | Faster acceleration on all moves. |
| 7 | Justin | 600 mm/s return move now ≈489 mm/s; 29° turn. |
| 8 | Michael | Two ≈135° turns (slightly slower) and three shorter turns (faster); last move `velocity=250000` now ≈489 mm/s. |
| 9 | Self-inspection | Uses `Reset_Gyro(0, wait_still=True)`; turns use the new defaults. |

### New test programs

Both run directly, not from the master:
`.venv/bin/pybricksdev run ble --name "Alyssa" <file>.py`

- **`Coach_Test.py`** — test bench. LEFT/RIGHT choose a test (number on the
  display), CENTER runs it, LEFT+RIGHT quits. "Move" tests drive 1.5 m forward
  and back and print top speed, cruise speed, acceleration, deceleration, time
  to within 10 mm and total time. "Turn" tests turn 90° and back. Tests 1–8
  compare the creep fix off and on. It raises the motors' firmware limits only
  while it runs. Needs about 2 m of clear space in front and behind.
- **`Turn_Tuner.py`** — automatic turn tuning. Runs the old setting first, then
  every `kp` × `lead_ms` combination on 30°, 90° and 180° turns, and prints the
  top 3 settings without overshoot. About 4–5 minutes, turns in place.

### Other changes

- `DeltaBots_Base_Application_Notes.md` updated for all of the above (also fixed:
  `heading_kd` default is 0.6, not 0.5).
- `.idea/` (PyCharm settings) is no longer tracked by git and is in `.gitignore`.

### Ideas for later

- Re-run the `Coach_Test.py` slip test on the game mat (the slip results above
  were measured on the floor).
- Change `acceleration=200` to 400 in Programs 1, 2 and 8 (about 5 s more).
- Raise the `Gyro_Move` default acceleration and deceleration to 800 after
  testing on the mat; the creep fix makes higher deceleration worthwhile.
- Optional acceleration cap (about 1200 mm/s²) so no program can ask for a value
  that makes the wheels slip.
