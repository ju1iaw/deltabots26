# Program 4
# Owner: Alyssa
# Missions, in execution order: Mission 1, Mission 15

from DeltaBots_Base import *

def Run(bot=None):
    if bot is None:
            bot = DeltaBots()   
            
    bot.Reset_Gyro(0)
            
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

    bot.Wait_All()    

if __name__ == "__main__":

    Run()
