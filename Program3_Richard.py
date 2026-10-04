# Program 3
# Owner: Richard
# Missions, in execution order: Mission 9, Mission 8

from pybricks.tools import wait
from DeltaBots_Base import *
bot=DeltaBots


def Run(bot=None):
    if bot is None:
            bot = DeltaBots()   
#_____________________________________
    bot.Attachment_Time(1,400,-500, wait=True)
    # Bot.Attachment_Time(-1,2300, -7000)
    # Bot.Attachment_Time(-1,2300, 7000)
    bot.Attachment_Time(1,680,500, wait=False)
    bot.Gyro_Move(30,670,250)
    bot.Gyro_Move(40,60,250)
    bot.Gyro_Turn(-40,0,300)
    bot.Gyro_Move(0,90,150)
    # Bot.Move_Straight(-40,200)
    # Bot.Attachment_Angle(1,-67,300)
    # Bot.Gyro_Move(0,40,200)
    # Bot.Gyro_Move(0, 80, 150)
    # Bot.Attachment_Angle(1,-120,200)
        # Bot.Gyro_Move(0,-120,400)
    # Bot.Attachment_Time(1,700,-500)
    # Bot.Gyro_Move(0,120,300)
    # Bot.Attachment_Angle(-1,-1200,600)
#_________________________________________ do not delete
    bot.Attachment_Angle(1,-225,300)
    bot.Attachment_Angle(1,80,300)
    bot.Gyro_Move(20,-130,300)
    bot.Attachment_Angle(1,-325,300)
    bot.Gyro_Move(0 ,120,200)
    bot.Attachment_Angle(-1, -1650 ,600)
    print('attachment -1900 done')
    # Bot.Gyro_Turn(20,0,300)
    # Bot.Gyro_Turn(-20,0,300)
    # Bot.Gyro_Move(0,-50,150)
    # Bot.Attachment_Angle(-1, 1500 ,300)
    # Bot.Gyro_Turn(30,0,200)
    # Bot.Attachment_Angle(1, 500 ,3000)
    # Bot.Gyro_Move(0,200,3300)
    bot.Gyro_Move(30,-600,700)

if __name__ == "__main__":
    Run()

