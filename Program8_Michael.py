# Program 8
# Owner: Michael
# Missions, in execution order: Mission6, 7, 12

from DeltaBots_Base import *

def Run(bot=None):
    if bot is None:
            bot = DeltaBots()  
    '''
    bot.Reset_Gyro(0)
    bot.Attachment_Angle(-1, -180, velocity=300,stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, -180, velocity=300,stop=Stop.BRAKE, wait=False)
    bot.Attachment_Angle(-1, 180, velocity=300,stop=Stop.BRAKE, wait=False)
    bot.Move_Straight(distance=30, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(-1, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=600, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, 180, velocity=300,stop=Stop.HOLD, wait=True)
    bot.Gyro_Turn(14, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)  
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
    bot.Gyro_Turn(-35, absolute=True, pivot=0, velocity=90,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=-1000, velocity=600,acceleration=200, deceleration=400,stop=Stop.BRAKE, wait=True)  
    '''
    bot.Reset_Gyro(0)
    #while True:
        #bot.Print_Reflectance()

    #bot.Attachment_Angle(-1, -100, velocity=250,stop=Stop.BRAKE, wait=False)
    bot.Attachment_Angle(1, 100, velocity=250,stop=Stop.BRAKE, wait=False)
    bot.Move_Straight(distance=630, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(20, pivot=0, velocity=200,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(-1, -160, velocity=250,stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=100, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)  
    bot.Gyro_Turn(20, pivot=0, velocity=900,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=500, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(-1, 160, velocity=1000,stop=Stop.BRAKE, wait=False)
    bot.Attachment_Angle(1, -80, velocity=650,stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, 100, velocity=650,stop=Stop.BRAKE, wait=True)  
    bot.Move_Straight(distance=-200, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Attachment_Angle(1, -100, velocity=650,stop=Stop.BRAKE, wait=False)
    bot.Gyro_Turn(-90, absolute=True, pivot=0, velocity=200,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=400, velocity=250,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(45, absolute=True, pivot=0, velocity=200,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=500, velocity=100,acceleration=200, stop=Stop.BRAKE, wait=True)   
    bot.Stop_Line(sensor=-1, velocity=-60, reflectance=18,stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=-10, velocity=100,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Gyro_Turn(-85, pivot=0, velocity=100,acceleration=200, stop=Stop.BRAKE, wait=True)
    bot.Move_Straight(distance=-1000, velocity=250000,acceleration=200, stop=Stop.BRAKE, wait=True)

     
if __name__ == "__main__":
    Run()


