# Program 3
# Owner: Richard
# Missions, in execution order: Mission 9, Mission 8

from DeltaBots_Base import *

def Run(bot=None):
    if bot is None:
        bot = DeltaBots()   
    bot.Reset_Gyro(0)
    bot.Attachment_Time(1,400,-500, wait=True)
    bot.Attachment_Time(1,680,500, wait=False)
    bot.Gyro_Move(30,670,250)
    bot.Gyro_Move(40,60,250)
    bot.Gyro_Turn(-40,0,300)
    bot.Gyro_Move(0,90,150)
    #_____________________________ do not delete
    bot.Attachment_Angle(1,-225,300)
    bot.Attachment_Angle(1,80,300)
    bot.Gyro_Move(20,-130,300)
    bot.Attachment_Angle(1,-325,300)
    bot.Gyro_Move(0 ,115,200)
    bot.Attachment_Angle(-1, -1600 ,600)
    print('attachment -1900 done')
    # bot.Gyro_Move(0,100,3000)
    bot.Gyro_Move(30,-600,700)

if __name__ == "__main__":
    Run()

