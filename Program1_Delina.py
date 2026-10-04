# Program 1
# Owner: Delina
# Mission 3

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


if __name__ == "__main__":
    bot = DeltaBots()
    mission3(bot)
