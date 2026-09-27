from pybricks.tools import wait
from DeltaBots_Base import *
bot=DeltaBots

def mission8_9(Bot: DeltaBots):
#_____________________________________
    Bot.Attachment_Time(1,400,-500)
    # Bot.Attachment_Time(-1,2300, -7000)
    # Bot.Attachment_Time(-1,2300, 7000)
    Bot.Attachment_Time(1,700,500)
    Bot.Gyro_Move(30,670,150)
    Bot.Gyro_Move(40,60,250)
    Bot.Gyro_Turn(-40,0,300)
    Bot.Gyro_Move(0,90,150)
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
    Bot.Attachment_Angle(1,-225,300)
    Bot.Attachment_Angle(1,80,300)
    Bot.Gyro_Move(18,-160,200)
    Bot.Attachment_Angle(1,-325,300)
    Bot.Gyro_Move(0,200,200)
    Bot.Attachment_Angle(-1, -1630 ,300)
    print('attachment -1900 done')
    # Bot.Gyro_Move(0,-50,150)
    # Bot.Attachment_Angle(-1, 1500 ,300)
    # Bot.Gyro_Turn(30,0,200)
    # Bot.Attachment_Angle(1, 500 ,3000)
    # Bot.Gyro_Move(0,200,3300)
    Bot.Gyro_Move(30,-600,700)

if __name__ == "__main__":
    bot= DeltaBots() 
    mission8_9(bot)

