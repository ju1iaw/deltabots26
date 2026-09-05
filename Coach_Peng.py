from DeltaBots_Base import *
from pybricks.tools import wait

bot = DeltaBots()
bot.Reset_Gyro(0)


bot.Gyro_Move(direction=0,distance=100, velocity=6, acceleration=400,wait=False, stop=Stop.BRAKE)
bot.Wait(1000)
bot.Attachment_Time(1, 2000, velocity=600, wait=False, stop=Stop.HOLD)
bot.Attachment_Time(-1, 2000, velocity=600, stop=Stop.HOLD)

bot.Print_Reflectance()
#def Run2(bot):
#    while True:
#    left, right = bot.Read_Reflectance()
#    print("Left:", left, "Right:", right)
#    wait(200)


#if __name__ == "__main__":
#    bot = DeltaBots()
#    Run2(bot)
