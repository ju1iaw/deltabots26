# Program 8
# Owner: Michael
# Missions, in execution order: Mission6, 7, 12

from DeltaBots_Base import *

def Run(bot=None):
    if bot is None:
            bot = DeltaBots()  
    '''
    bot.Reset_Gyro(0)
    bot.Attachment_Angle(-1, 180, velocity=300,stop=Stop.HOLD, wait=False)
    bot.Move_Straight(distance=630, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, 180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Gyro_Turn(15, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, -180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Attachment_Angle(1, 180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Move_Straight(distance=-110, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, -180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Move_Straight(distance=100, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(-20, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Time(-1, 1000, velocity=-300,stop=Stop.HOLD, wait=True)
    bot.Gyro_Turn(-90, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=370, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(133, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=600, velocity=150,acceleration=200, stop=Stop.BRAKE, wait=True) 
    bot.Move_Straight(distance=-100, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(-82, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=-1000, velocity=600,acceleration=200, deceleration=400,stop=Stop.BRAKE, wait=True)  
    '''
    bot.Reset_Gyro(0)
    bot.Attachment_Angle(-1, 180, velocity=300,stop=Stop.HOLD, wait=False)
    bot.Move_Straight(distance=630, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, 180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Gyro_Turn(15, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, -180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Attachment_Angle(1, 180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Move_Straight(distance=-110, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, -180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Move_Straight(distance=100, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(-20, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Time(-1, 1000, velocity=-300,stop=Stop.HOLD, wait=True)
    bot.Gyro_Turn(-90, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=370, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(133, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)

    bot.Move_Straight(distance=600, velocity=100,acceleration=200, stop=Stop.BRAKE, wait=True) 

    bot.Stop_Line(sensor=-1, velocity=-60, reflectance=40,stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(-87, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=-1000, velocity=600,acceleration=200, deceleration=400,stop=Stop.BRAKE, wait=True)  



if __name__ == "__main__":
    Run()


