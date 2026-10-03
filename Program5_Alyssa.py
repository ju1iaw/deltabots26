# Program 5
# Owner: Alyssa
# Missions, in execution order: Mission 2

from DeltaBots_Base import *

def Run(bot=None):
    if bot is None:
            bot = DeltaBots()   
            
    bot.Reset_Gyro(0)
            
    
'''def mission2(br: BaseRobot):
    br.moveLeftAttachmentMotorForMillis(700, 400)
    br.driveForDistance(450, 800)
    br.moveLeftAttachmentMotorForMillis(900, -200)
    br.driveForDistance(-500, 800)
'''
if __name__ == "__main__":
    Run()