
from DeltaBots_Base import *


def Mission1(bot=None):
    if bot is None:
            bot = DeltaBots()   
            
    bot.Reset_Gyro(0)
    #bot.Attachment_Time(1, 2000, velocity=-100, stop=Stop.HOLD, wait=False) #Resetting the right attachment to the initial position
    #bot.Attachment_Time(-1, 2000, velocity=100, stop=Stop.HOLD, wait=False) #Resetting the left attachment to the initial position

    #bot.Gyro_Move(direction= 0, distance=1500,velocity=10,wait=True)
        
    bot.Gyro_Move(direction= 1, distance = 1200, time_ms=3500, velocity=300, wait=True, stop=Stop.BRAKE)
    bot.Wait(100)
    bot.leftDriveMotor.reset_angle(0)
    bot.rightDriveMotor.reset_angle(0)
    bot.Wait(100)
    bot.Gyro_Move(direction= 0, distance=-15,velocity=20,wait=True)
    bot.Gyro_Turn(angle=-90, pivot=-1, time_ms=2000, velocity=400)
    bot.Gyro_Turn(angle=-15, pivot=0.3, absolute=True,time_ms=2000, velocity=200)
    bot.Gyro_Turn(angle = -10, pivot = -5, absolute = True, time_ms=3000, velocity = 200)
    bot.Gyro_Move(direction= -8, distance=-180, velocity=200, wait=True)
    bot.Gyro_Move(direction= 3, distance=-800, velocity=1000, wait=True)
    #bot.Gyro_Move(direction = 355, distance=70, velocity=200, wait=True)
    #bot.Gyro_Move(direction = 0, distance=-150, velocity=200, wait=True)
    """bot.Gyro_Move(direction= -15, distance=-95,velocity=200,wait=True)
    bot.Gyro_Turn(angle=-60, pivot=-1.5, absolute=True,time_ms=1000, velocity=200)
    bot.Gyro_Turn(angle=5, pivot=1, absolute=True,time_ms=1000, velocity=200)
    bot.Gyro_Move(direction=2, distance=-800,velocity=600,wait=True)"""
'''    bot.Reset_Gyro(0)
    bot.Attachment_Angle(1, -360, 1000, wait=False)
    bot.Gyro_Move(direction= 0, distance=15,velocity=100,wait=True)
    bot.Gyro_Move(direction=0, distance=400, velocity=900, wait=True)
    bot.Gyro_Move(direction=0, distance=450, velocity=300, wait=True)
    bot.Gyro_Turn(angle=-45, velocity=60)
    bot.Attachment_Angle(1, 3000, 1000)
    #bot.Attachment_Angle(1, 1000, -300)
    bot.Gyro_Move(direction=-45, distance=-100, velocity=200, wait=True)
'''

if __name__ == "__main__":

    Mission1()

