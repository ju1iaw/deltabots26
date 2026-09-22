
from DeltaBots_Base import *


def mission1(bot=DeltaBots()):
    bot.Reset_Gyro(0)
    bot.Attachment_Angle(1, -360, 1000, wait=False)
    bot.Gyro_Move(direction= 0, distance=15,velocity=100,wait=True)
    bot.Gyro_Move(direction=0, distance=400, velocity=900, wait=True)
    bot.Gyro_Move(direction=0, distance=450, velocity=300, wait=True)
    bot.Gyro_Turn(angle=-45, velocity=60)
    bot.Attachment_Angle(1, 3000, 1000)
    #bot.Attachment_Angle(1, 1000, -300)
    bot.Gyro_Move(direction=-45, distance=-100, velocity=200, wait=True)

if __name__ == "__main__":

    mission1()

