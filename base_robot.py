from pybricks.pupdevices import Motor, ColorSensor

from pybricks.parameters import (
    Port,
    Direction,
    Axis,
    Side,
    Stop,
    Color,
    Button,
    Icon,
)
from pybricks.robotics import DriveBase
from pybricks.hubs import PrimeHub
from pybricks.tools import wait
from pybricks import version

# All default constant percentages will be defined here
TIRE_DIAMETER = 56  # mm
AXLE_TRACK = 113  # distance between the wheels, mm
STRAIGHT_ACCEL = 200  # mm/s²
STRAIGHT_DECEL = 600  # mm/s²
TURN_ACCEL = 200  # deg/s²
TURN_DECEL = 400  # deg/s²


# Check the pybricks API documentation to see how these parameters are set
# and used. Add other parameters that your robot needs.
class BaseRobot:
    """
    A collection of methods and Spike Prime for FLL Team 24277. \
    Uses pybricks for most functionality.

    Example:

    >>> from base_robot import *
    >>> br = BaseRobot()
    """

    def __init__(self):
        self.hub = PrimeHub(top_side=Axis.Z, front_side=Axis.X)
        self.leftDriveMotor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
        self.rightDriveMotor = Motor(Port.E)
        self.robot = DriveBase(
            self.leftDriveMotor,
            self.rightDriveMotor,
            TIRE_DIAMETER,
            AXLE_TRACK,
        )

        self.leftAttachmentMotor = Motor(Port.B)
        self.rightAttachmentMotor = Motor(Port.F)

        self.colorSensorLeft = ColorSensor(Port.C)
        self.colorSensorRight = ColorSensor (Port.D)


# Write all of the functions that your robot will need to do.

    def moveLeftAttachmentMotorForMillis(self, millis, speed,):
        self.leftAttachmentMotor.run_time(speed, millis)

    def driveForDistance(self, distance, speed, then=Stop.BRAKE, gyro=True, accel=STRAIGHT_ACCEL, decel=STRAIGHT_DECEL, ):
       
        self.robot.use_gyro(gyro)
        self.robot.settings(speed, (accel, decel), 100, 100)
        self.robot.straight(distance, then, wait)

    def driveForTime(self, millis, speed, then=Stop.BRAKE, gyro=True):
        self.robot.use_gyro(gyro)
        self.robot.drive(speed, 0)
        wait(millis)
        if then == Stop.BRAKE:
            self.robot.brake()
        elif then == Stop.HOLD:
            self.robot.hold()
        else:
            self.robot.stop()

    def turnForAngle(self, angle, speed, then=Stop.BRAKE, gyro=True, accel=TURN_ACCEL, decel=TURN_DECEL,):
        '''accel/decel = mm/s increase in speed; for instance 100mm/s accel vs 200mm/s accel'''
        self.robot.use_gyro(gyro)
        self.robot.settings(100, 100, speed, (accel, decel))
        self.robot.turn(angle, then, wait)

    def stop_line(self, speed, reflectivity, sensor=Side.LEFT, tolerance=3, stop_below=True, gyro=True, then=Stop.BRAKE,):
        self.robot.use_gyro(gyro)
        color_sensor = self.colorSensorLeft if sensor in (Side.LEFT, "left") else self.colorSensorRight
        self.robot.drive(speed, 0)
        while True:
            if stop_below and color_sensor.reflection() <= reflectivity + tolerance:
                break
            if not stop_below and color_sensor.reflection() >= reflectivity - tolerance:
                break
            wait(10)
        if then == Stop.BRAKE:
            self.robot.brake()
        elif then == Stop.HOLD:
            self.robot.hold()
        else:
            self.robot.stop()

    def align_line(self, reflectivity, tolerance=3, forward_speed=0, max_turn_rate=40, kp=0.4, gyro=True, then=Stop.BRAKE,):
        self.robot.use_gyro(gyro)
        prev_turn_error = 0
        while True:
            left_refl = self.colorSensorLeft.reflection()
            right_refl = self.colorSensorRight.reflection()
            if abs(left_refl - reflectivity) <= tolerance and abs(right_refl - reflectivity) <= tolerance:
                break
            turn_error = left_refl - right_refl
            if prev_turn_error != 0 and (turn_error > 0) != (prev_turn_error > 0):
                turn_rate = turn_error * kp * 0.25
            else:
                closeness = min(abs(left_refl - reflectivity), abs(right_refl - reflectivity))
                scale = min(1.0, closeness / max(tolerance * 3, 1))
                turn_rate = turn_error * kp * max(scale, 0.15)
            turn_rate = max(-max_turn_rate, min(max_turn_rate, turn_rate))
            self.robot.drive(forward_speed, turn_rate)
            prev_turn_error = turn_error
            wait(10)
        if then == Stop.BRAKE:
            self.robot.brake()
        elif then == Stop.HOLD:
            self.robot.hold()
        else:
            self.robot.stop()



if __name__ == "__main__":
    print("Don't run the BaseRobot class file. Nothing to do here.")
    print("You probably meant to run one of the mission files.")
