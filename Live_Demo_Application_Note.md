# DeltaBots Live Demo – Application Note

## 1. Purpose

`Live_Demo.py` is the interactive control program for the DeltaBots LEGO SPIKE Prime mower demonstration.

The program supports up to three SPIKE Prime Medium Angular Motors and provides three operating modes for demonstrating different insect-protection attachments.

The program is designed so that motors may be added or removed without changing the software. If a motor is not connected, the program ignores that motor and continues running.

---

## 2. Hardware Configuration

| Port | Motor Function | Used In |
|---|---|---|
| B | Swing-stick attachment | Mode 1 |
| D | Fan / airflow attachment | Mode 2 |
| F | Simulated mower blade | Modes 0, 1, and 2 |

All motors are SPIKE Prime Medium Angular Motors.

No additional sensors are required.

---

## 3. User Controls

The SPIKE Prime Hub buttons are used to control the demonstration.

| Button | Function |
|---|---|
| LEFT | Select previous mode |
| RIGHT | Select next mode |
| CENTER | Start / stop selected mode |
| LEFT + RIGHT | Stop all motors and exit program |

The three modes cycle continuously.

**RIGHT:**  
`Mode 0 → Mode 1 → Mode 2 → Mode 0`

**LEFT:**  
`Mode 0 → Mode 2 → Mode 1 → Mode 0`

Whenever the mode is changed, all motors are stopped automatically before entering the new mode.

---

## 4. Hub Display

The selected mode is displayed on the SPIKE Prime Hub LED matrix.

Large custom 3 × 5 digits are used for improved visibility:

- `0` = Blade only
- `1` = Blade + swing-stick attachment
- `2` = Blade + fan attachment

Selecting a mode does not automatically start the motors. The system remains in standby until the CENTER button is pressed.

---

## 5. Mode 0 – Blade Demonstration

### Function

Mode 0 operates only the simulated mower blade.

### Motor Operation

- Motor F: ON
- Motor B: OFF
- Motor D: OFF

Press CENTER once to start the blade.

Press CENTER again to stop all motors.

### Default Setting

```python
BLADE_SPEED = -1000
```

The speed is specified in degrees per second.

The sign determines the rotation direction.

---

## 6. Mode 1 – Blade + Swing-Stick Demonstration

### Function

Mode 1 demonstrates the powered soft-stick attachment intended to disturb insects before the mower reaches them.

When Mode 1 starts:

1. Motor B is initialized using the mechanical hard stop.
2. Motor B encoder position is reset to 0°.
3. Motor F starts the simulated mower blade.
4. Motor B continuously swings between 0° and the configured swing angle.

### Motor Operation

- Motor F: Blade
- Motor B: Swing mechanism
- Motor D: OFF

### Default Settings

```python
BLADE_SPEED = -1000
SWING_SPEED = 1000
SWING_ANGLE = 160
```

Motor B swings approximately:

`0° ↔ 160° ↔ 0° ↔ 160° ...`

### Motor B Initialization

The swing mechanism uses a mechanical hard stop as its reference position.

The first time Mode 1 is started after running the program, Motor B moves slowly toward the hard stop using:

```python
HOMING_SPEED = -180
HOMING_DUTY_LIMIT = 30
```

When the motor detects that it has stalled against the hard stop, the encoder is reset:

```python
motor_B.motor.reset_angle(0)
```

This establishes a known reference for the 160° swing.

Motor B is initialized only once during each execution of `Live_Demo.py`.

### Changing the Homing Direction

If Motor B moves away from the hard stop during initialization, reverse:

```python
HOMING_SPEED = -180
```

to:

```python
HOMING_SPEED = 180
```

The software automatically adjusts the normal swing direction based on the sign of `HOMING_SPEED`.

---

## 7. Mode 2 – Blade + Fan Demonstration

### Function

Mode 2 demonstrates the airflow attachment.

### Motor Operation

- Motor F: Blade
- Motor D: Fan
- Motor B: OFF

Press CENTER once to start both motors.

Press CENTER again to stop all motors.

### Default Settings

```python
BLADE_SPEED = -1000
FAN_SPEED = 1000
```

The sign of `FAN_SPEED` can be reversed if the airflow direction is incorrect.

---

## 8. Default Configuration

The main adjustable parameters are located near the beginning of `Live_Demo.py`.

```python
# Blade
BLADE_SPEED = -1000

# Fan
FAN_SPEED = 1000

# Swing attachment
SWING_ANGLE = 160
SWING_SPEED = 1000

# Swing motor initialization
HOMING_SPEED = -180
HOMING_DUTY_LIMIT = 30
```

These values can be changed without modifying the remainder of the program.

---

## 9. Missing Motor Handling

The program is designed for incremental hardware development.

Examples:

- F only connected → Mode 0 works normally.
- B and F connected → Modes 0 and 1 work normally.
- B, D, and F connected → all three modes operate normally.

If a motor is not detected, the software prints a message such as:

```text
Motor not connected: Port.D
```

The program continues instead of terminating.

---

## 10. Normal Startup Procedure

1. Make sure the mower mechanisms can move freely.
2. Confirm the swing attachment has its mechanical hard stop installed.
3. Connect the required motors.
4. Turn on the SPIKE Prime Hub.
5. Run `Live_Demo.py`.
6. The Hub displays `0`.
7. Use LEFT or RIGHT to select the desired mode.
8. Press CENTER to start the demonstration.
9. Press CENTER again to stop the demonstration.
10. Press LEFT + RIGHT together to exit the program.

---

## 11. Important Mode 1 Setup

Before starting Mode 1 for the first time, make sure Motor B is not physically trapped on the wrong side of its mechanism.

During initialization, Motor B intentionally moves toward the mechanical hard stop.

The motion is intentionally slower and power-limited during calibration:

```python
HOMING_SPEED = -180
HOMING_DUTY_LIMIT = 30
```

The normal high-speed swing begins only after initialization is complete.

---

## 12. Safety and Mechanical Considerations

The blade in the LEGO mower should remain a simulated blade and stay completely inside the protective circular blade opening.

The 160° swing motion can reverse rapidly. Before running Mode 1 at full speed:

- Check that Technic pins and axles are fully inserted.
- Make sure the soft stick cannot contact the wheels, blade, chassis, or cables.
- Keep hands away from the moving swing attachment.
- Verify that the mechanical hard stop is strong enough for repeated initialization.
- Stop the program immediately if the mechanism binds.

LEFT + RIGHT provides a convenient program-level stop command.

---

## 13. Program Summary

`Live_Demo.py` provides one common program for all three DeltaBots mower demonstrations:

- **Mode 0 – Blade:** Motor F demonstrates the basic mower operation.
- **Mode 1 – Blade + Soft Stick:** Motor F operates the blade while Motor B continuously swings the insect-disturbance stick through a 160° range.
- **Mode 2 – Blade + Airflow:** Motor F operates the blade while Motor D drives the fan attachment.

The program provides a simple judge-friendly interface using only the SPIKE Prime Hub buttons and display, allowing each attachment to be demonstrated without reconnecting or reprogramming the Hub.
