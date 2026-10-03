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
        velocity=300,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )

    bot.Wait(1000)


def mission4_5(bot: DeltaBots):
    """
    bot.moveLeftAttachmentMotorForMillis(3000, -200)
    bot.driveForDistance(698.5, 200)
    bot.turnForAngle(-38, 200)
    bot.driveForDistance(110, 200)
    bot.moveLeftAttachmentMotorForMillis(1000, 200)
    bot.turnForAngle(38, 200)
    bot.moveRightAttachmentMotorForMillis(1000, 200)

    bot.Reset_Gyro(0)
    bot.Attachment_Time(side=-1, millis=3000, velocity=-200)

    )
    """
    bot.Reset_Gyro(0)
    bot.Attachment_Time(1, 2000, velocity=200, stop=Stop.HOLD, wait=False)
    bot.Move_Straight(
        distance=790,
        velocity=1000,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    """
    bot.Gyro_Turn(
        angle=-38, velocity=200, acceleration=200, stop=Stop.BRAKE, wait=True
    )
    
    bot.Gyro_Move(
        distance=110,
        velocity=200,
        acceleration=200,
        stop=Stop.BRAKE,
        wait=True,
    )
    
    bot.Move_Straight(
        distance=110,
        velocity=200,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    bot.Attachment_Time(side=-1, millis=1000, velocity=200)
    """

    bot.Gyro_Turn(
        angle=25,
        pivot=0,
        velocity=200,
        acceleration=200,
        stop=Stop.BRAKE,
        wait=True,
    )

    bot.Move_Straight(
        distance=-40,
        velocity=200,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    # bot.Attachment_Time(1, 1000, velocity=-1000, stop=Stop.HOLD, wait=True)
    bot.Attachment_Angle(side=1, angle=-150, velocity=200, stop=Stop.HOLD, wait=True)
    bot.Move_Straight(
        distance=200,
        velocity=200,
        acceleration=200,
        deceleration=400,
        stop=Stop.BRAKE,
        wait=True,
    )
    # bot.Move_Straight(distance=40, velocity=200, acceleration=200, deceleration=400, stop=Stop.BRAKE, wait=True)
    # bot.Move_Straight(distance=40, velocity=200, acceleration=200, deceleration=400, stop=Stop.BRAKE, wait=True)


if __name__ == "__main__":
    bot = DeltaBots()
    mission4_5(bot)
