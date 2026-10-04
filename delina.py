# Program 1 and 2
# Owner: Delina
# Missions, in execution order: Mission 3, Mission 4 and 5

from DeltaBots_Base import *


def mission3(bot: DeltaBots):
    bot.Reset_Gyro(0)
    bot.Move_Straight(
        distance=300,
        velocity=1000,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    bot.Move_Straight(
        distance=-240,
        velocity=1000,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    bot.Wait(1000)


def mission4_5(bot: DeltaBots):
    bot.Reset_Gyro(0)
    # lower down right attachment
    bot.Attachment_Time(1, 2000, velocity=200, stop=Stop.HOLD, wait=False)

    # drive to mission 5
    bot.Move_Straight(
        distance=790,
        velocity=1000,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    # move right attachemt under mission 5
    bot.Gyro_Turn(
        angle=25,
        pivot=0,
        velocity=200,
        acceleration=200,
        stop=Stop.BRAKE,
        wait=True,
    )

    # pull mission 5 down
    bot.Move_Straight(
        distance=-40,
        velocity=200,
        acceleration=200,
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
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    # back up robot to point to mission 4
    bot.Gyro_Move(direction=-42, distance=-200, velocity=150, acceleration=200, stop=Stop.BRAKE, wait=True)

    # lower down left attachment
    bot.Attachment_Time(-1, 1000, velocity=-1000, stop=Stop.HOLD, wait=True)

    # drive to mission 4
    bot.Move_Straight(
        distance=140,
        velocity=200,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    # lift up left attachment to grab mission 4
    bot.Attachment_Time(-1, 1000, velocity=200, stop=Stop.HOLD, wait=True)

    # back up robot to point to home zone
    bot.Gyro_Move(direction=0, distance=-200, velocity=150, acceleration=200, stop=Stop.BRAKE, wait=True)

    # move back to home zone
    bot.Move_Straight(
        distance=-690,
        velocity=1000,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )


if __name__ == "__main__":
    bot = DeltaBots()
    mission4_5(bot)
