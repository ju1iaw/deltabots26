"""DeltaBots movement demonstration and robot self-inspection.

Run this file directly, or call Robot_Self_Instpection(bot) from the master.
The requested spelling Instpection is retained; Robot_Self_Inspection is an alias.

Master Program 9:
    def Program_9(bot):
        from Robot_Self_Inspection import Robot_Self_Instpection
        Robot_Self_Instpection(bot)

Use a clear area for a 500 mm square PLUS the robot/pivot sweep. Attachment
motors must be free to rotate at least two revolutions in either direction;
remove restricted-travel mechanisms for this demonstration. No line is needed.
The nominal path returns the AXLE CENTER and orientation to the start. Wheel
slip, IMU error, and physical tolerances can cause real return-position error;
this script has no external position sensor to certify an exact return.

API keywords are case-sensitive: velocity (lowercase), wait, stop,
acceleration, direction, and distance are written explicitly in examples.
Gyro_Turn angle is RELATIVE unless absolute=True; positive is clockwise.
+180 and -180 describe the same compass orientation. To demonstrate a full
circle between them, use two 180-degree calls (each call is limited to 355).
Attachment_Target velocity must be positive. Its target selects direction.
"""
from DeltaBots_Base import DeltaBots, Stop


def Robot_Self_Instpection(bot=None):
    """Run the test; reuse the supplied robot, or create one for standalone use.

    Returns True if all commands finish. Errors are printed and re-raised so
    the master can report failure and return to its menu. Always stops motors.
    Completion messages confirm command completion, not physical calibration.
    """
    if bot is None:
        bot = DeltaBots()
    step = 'initialization'

    def completed(message):
        print(message, '- completed; yaw:', bot.Get_YAW_Angle(), 'deg')

    try:
        print('Robot self-inspection starting. No line test.')
        step = 'Reset_Gyro'
        bot.Reset_Gyro(0)
        completed('Reset gyro to 0 deg')

        step = 'forward 500 mm at 0 deg'
        bot.Gyro_Move(direction=0, distance=500, velocity=150,
                      acceleration=200, stop=Stop.BRAKE, wait=True)
        completed('Move forward 50 cm, direction 0 deg')

        step = 'center turn to 90 deg'
        bot.Gyro_Turn(90, pivot=0, velocity=90, acceleration=200,
                      stop=Stop.BRAKE, wait=True)
        completed('Center turn clockwise 90 deg')

        step = 'reverse 500 mm at 90 deg'
        bot.Gyro_Move(direction=90, distance=-500, velocity=150,
                      acceleration=200, stop=Stop.BRAKE, wait=True)
        completed('Move backward 50 cm, direction 90 deg')

        # A one-wheel 90-degree pivot shifts the axle center. Undo that pivot
        # around the SAME wheel before continuing the square route.
        step = 'left-wheel pivot to 180 deg'
        bot.Gyro_Turn(90, pivot=-1, velocity=90, acceleration=200,
                      stop=Stop.BRAKE, wait=True)
        completed('Left-wheel pivot clockwise to 180 deg')
        step = 'undo left-wheel pivot'
        bot.Gyro_Turn(-90, pivot=-1, velocity=90, acceleration=200,
                      stop=Stop.BRAKE, wait=True)
        completed('Left-wheel pivot counterclockwise back to 90 deg')
        step = 'center turn to 180 deg'
        bot.Gyro_Turn(90, pivot=0, velocity=90, acceleration=200,
                      stop=Stop.BRAKE, wait=True)
        completed('Center turn clockwise to 180 deg')

        # Each full circle returns the axle center to the same nominal point.
        for part in (1, 2):
            step = 'right-wheel clockwise circle, part ' + str(part)
            bot.Gyro_Turn(180, pivot=1, velocity=90, acceleration=200,
                          stop=Stop.BRAKE, wait=True)
            completed('Right-wheel clockwise 180 deg, part ' + str(part))
        completed('Full clockwise circle: heading equivalent to -180 deg')

        for part in (1, 2):
            step = 'left-wheel counterclockwise circle, part ' + str(part)
            bot.Gyro_Turn(-180, pivot=-1, velocity=90, acceleration=200,
                          stop=Stop.BRAKE, wait=True)
            completed('Left-wheel counterclockwise 180 deg, part ' + str(part))
        completed('Full counterclockwise circle: heading equivalent to 180 deg')

        step = 'reflectance readings'
        bot.Print_Reflectance()
        completed('Print left/right reflectance')

        step = 'both attachments forward for 1000 ms'
        left = bot.Attachment_Time(-1, 1000, velocity=300,
                                   stop=Stop.HOLD, wait=False)
        print('Left attachment +300 deg/s, 1000 ms - started')
        right = bot.Attachment_Time(1, 1000, velocity=300,
                                    stop=Stop.HOLD, wait=False)
        print('Right attachment +300 deg/s, 1000 ms - started')
        bot.Wait_For(left)
        completed('Left attachment +300 deg/s, 1000 ms')
        bot.Wait_For(right)
        completed('Right attachment +300 deg/s, 1000 ms')

        # Join the first pair before reversing: a resource cannot own two jobs.
        step = 'both attachments reverse for 1000 ms'
        left = bot.Attachment_Time(-1, 1000, velocity=-300,
                                   stop=Stop.HOLD, wait=False)
        print('Left attachment -300 deg/s, 1000 ms - started')
        right = bot.Attachment_Time(1, 1000, velocity=-300,
                                    stop=Stop.HOLD, wait=False)
        print('Right attachment -300 deg/s, 1000 ms - started')
        bot.Wait_For(left)
        completed('Left attachment -300 deg/s, 1000 ms')
        bot.Wait_For(right)
        completed('Right attachment -300 deg/s, 1000 ms')

        step = 'wait 1500 ms'
        bot.Wait(1500)
        completed('Wait 1500 ms')

        # Absolute targets relative to the CURRENT encoder readings. This
        # preserves the existing references instead of resetting encoders.
        left_target = bot.leftAttachmentMotor.angle() - 720
        right_target = bot.rightAttachmentMotor.angle() + 720
        step = 'attachment targets and forward drive together'
        left = bot.Attachment_Target(-1, left_target, velocity=300,
                                     stop=Stop.HOLD, wait=False)
        print('Left attachment target:', left_target, 'deg (-720 deg travel) - started')
        right = bot.Attachment_Target(1, right_target, velocity=300,
                                      stop=Stop.HOLD, wait=False)
        print('Right attachment target:', right_target, 'deg (+720 deg travel) - started')
        bot.Gyro_Move(direction=180, distance=500, velocity=150,
                      acceleration=200, stop=Stop.BRAKE, wait=True)
        completed('Move forward 50 cm, direction 180 deg')
        bot.Wait_For(left)
        completed('Left attachment -720 deg travel; absolute target reached')
        bot.Wait_For(right)
        completed('Right attachment +720 deg travel; absolute target reached')

        # From 180, +90 clockwise reaches 270 (wrapped yaw -90).
        # A relative -90 turn here would instead face +90 and break the route.
        step = 'center turn to heading -90 deg'
        bot.Gyro_Turn(90, pivot=0, velocity=90, acceleration=200,
                      stop=Stop.BRAKE, wait=True)
        completed('Center turn to heading -90 deg')

        step = 'reverse 500 mm at -90 deg'
        bot.Gyro_Move(direction=-90, distance=-500, velocity=150,
                      acceleration=200, stop=Stop.BRAKE, wait=True)
        completed('Move backward 50 cm, direction -90 deg')

        step = 'center turn to heading 0 deg'
        bot.Gyro_Turn(90, pivot=0, velocity=90, acceleration=200,
                      stop=Stop.BRAKE, wait=True)
        completed('Center turn to heading 0 deg')
        bot.Wait_All()
        print('Self-inspection commands completed. Check physical return position.')
        print('Final wrapped yaw:', bot.Get_YAW_Angle(), 'deg')
        return True
    except Exception as error:
        print('Self-inspection FAILED during:', step)
        print(type(error).__name__, str(error))
        raise
    finally:
        bot.Stop_All(stop=Stop.BRAKE)
        print('All motors stopped.')


# Correct-spelling alias; both names call the same function.
Robot_Self_Inspection = Robot_Self_Instpection

if __name__ == '__main__':
    Robot_Self_Instpection()
