# Program 1
# Owner: Delina
# Mission 3

from DeltaBots_Base import *


def Run(bot: DeltaBots):
    bot.Reset_Gyro(0)
    # move forward the finish and align with mission 3
    bot.Move_Straight(
        distance=300,
        velocity=1000,
        acceleration=400,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    # Move out of Mission 3
    bot.Move_Straight(
        distance=-70,
        velocity=1000,
        acceleration=400,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    # turn to move away from mission 3
    bot.Gyro_Turn(
        angle=60,
        pivot=0,
        velocity=200,
        acceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    # move forward to adjust position to move to mission 5
    bot.Move_Straight(
        distance=195,
        velocity=1000,
        acceleration=400,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    # turn to align to mission 5
    bot.Gyro_Turn(
        angle=-60,
        pivot=0,
        velocity=200,
        acceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    # lower down right attachment
    bot.Attachment_Time(1, 2000, velocity=200, stop=Stop.HOLD, wait=False)

    # drive to mission 5
    bot.Move_Straight(
        distance=390,
        velocity=1000,
        acceleration=400,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    # move right attachemt under mission 5
    bot.Gyro_Turn(
        angle=25,
        pivot=0,
        velocity=200,
        acceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    # pull mission 5 down
    bot.Move_Straight(
        distance=-40,
        velocity=200,
        acceleration=400,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    # lift mission 5 up with right attachment
    bot.Attachment_Angle(side=1, angle=-150, velocity=200, stop=Stop.HOLD, wait=True)

    # push mission 5 forward to unfold position
    bot.Move_Straight(
        distance=150,
        velocity=1000,
        acceleration=400,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    # back up robot to point to mission 4
    bot.Gyro_Move(direction=-45, distance=-220, velocity=150, acceleration=400, stop=Stop.BRAKE, wait=True)

    # lower down left attachment
    bot.Attachment_Time(-1, 1000, velocity=-1000, stop=Stop.HOLD, wait=True)

    # drive to mission 4
    bot.Move_Straight(
        distance=140,
        velocity=200,
        acceleration=400,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    # lift up left attachment to grab mission 4
    bot.Attachment_Time(-1, 1000, velocity=200, stop=Stop.HOLD, wait=True)

    # back up robot to point to home zone
    bot.Gyro_Move(direction=0, distance=-200, velocity=150, acceleration=400, stop=Stop.BRAKE, wait=True)

    # Lift up right attachment arm
    bot.Attachment_Time(1, 1000, velocity=200, stop=Stop.HOLD, wait=False)

    # move back to home zone
    bot.Move_Straight(
        distance=-650,
        velocity=1000,
        acceleration=400,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )


if __name__ == "__main__":
    bot = DeltaBots()
    Run(bot)
