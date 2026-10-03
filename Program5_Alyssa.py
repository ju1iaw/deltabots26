# Program 5
# Owner: Alyssa
# Missions, in execution order: Mission 2

from DeltaBots_Base import *

def Run(bot=None):
    Start_angle = -36
    if bot is None:
            bot = DeltaBots()   
            
    bot.Reset_Gyro(0)
    bot.Attachment_Time(-1, 1500, velocity=300,stop=Stop.COAST, wait=False)
    bot.Gyro_Turn(angle=Start_angle, pivot=-1, time_ms=2000, velocity=400)
    bot.Gyro_Move(direction=Start_angle, distance=550, time_ms=3000,velocity=400, wait=True)
#    bot.Wait(1500)
    bot.Attachment_Reset(-1, 0)
    bot.Wait(200)
    bot.Attachment_Angle(-1, -40, velocity=300,stop=Stop.HOLD, wait=True)
    bot.leftDriveMotor.reset_angle(0)
    bot.rightDriveMotor.reset_angle(0)
    bot.Wait(100)
    
    bot.Gyro_Move(direction=Start_angle, distance=-30, velocity=200,time_ms=3000, wait=True)
    bot.Attachment_Angle(-1, -40, velocity=300,stop=Stop.HOLD, wait=False)
    bot.Wait(300)
    bot.Gyro_Move(direction=Start_angle, distance=-60, velocity=200,time_ms=3000, wait=True)
    bot.Attachment_Angle(-1, -40, velocity=300,stop=Stop.HOLD, wait=False)
    bot.Wait(300)
    bot.Gyro_Move(direction=Start_angle, distance=-220, velocity=200,time_ms=3000, wait=True)
    bot.Attachment_Angle(-1, 100, velocity=300,stop=Stop.HOLD, wait=False)
    bot.Gyro_Move(direction=-13, distance=900, velocity=800, wait=True)
    bot.Attachment_Angle(-1, -150, velocity=300,stop=Stop.HOLD, wait=False)
    bot.Wait(500)
    bot.Gyro_Move(direction=30, distance=500, velocity=700, wait=True)
        
           
        
        


        

'''
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
    
    br.moveLeftAttachmentMotorForMillis(700, 400)
    br.driveForDistance(450, 800)
    br.moveLeftAttachmentMotorForMillis(900, -200)
    br.driveForDistance(-500, 800)
'''

if __name__ == "__main__":
    Run()