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
        self.hub = PrimeHub(top_side=Axis.Z, front_side=-Axis.Y)
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


# Write all of the "things" that your robot will need to do.
# These methods will then be available for team members to program the robot
# their mission
#
# Here, we have two examples to get you started.
    def moveLeftAttachmentMotorForMillis(self, millis, speed,):
        """
        Moves the left attachment motor for a set amount of time

        Example:

        >>> moveLeftAttachmentMotorForMillis(millis=500, speedPct=50)

        Args:

        millis (REQUIRED integer, > 0): how many miliseconds the left \
        attachment motor will turn for. A millisecond is 0.001 of a second, \
        so 5000 is 5 seconds.

        speed (REQUIRED integer): Controls how fast \
        the motor/motors will move. Positive numbers move the motor right, \
        negative numbers turn it to the left.
        """
        self.leftAttachmentMotor.run_time(speed, millis)


    def driveForDistance(self, distance, speed, then=Stop.BRAKE, gyro=True, accel=STRAIGHT_ACCEL, decel=STRAIGHT_DECEL, ):
       
        self.robot.use_gyro(gyro)
        self.robot.settings(
            straight_speed=speed,
            straight_acceleration=(accel, decel),
        )
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

    def turnForAngle(
        self,
        angle,
        speed,
        then=Stop.BRAKE,
        gyro=True,
        accel=TURN_ACCEL,
        decel=TURN_DECEL,
    ):
        self.robot.use_gyro(gyro)
        self.robot.settings(
            turn_rate=speed,
            turn_acceleration=(accel, decel),
        )
        self.robot.turn(angle, then, wait)

# write stop_line etc.
# This BaseRobot class file is not meant to be run like the mission files.
# But if someone does try (accidentally probably) to run it, show this
# error message.
if __name__ == "__main__":
    print("Don't run the BaseRobot class file. Nothing to do here.")
    print("You probably meant to run one of the mission files.")
