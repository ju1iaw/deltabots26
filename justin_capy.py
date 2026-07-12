from base_robot import *



def Run(br: BaseRobot):
    br.driveForDistance(580, 800)
    br.turnForAngle(71, speed=100)
    br.driveForDistance(565, 500)
    br.turnForAngle(-67, speed=100)
    br.moveLeftAttachmentMotorForMillis(millis=265,speed=-290) 
    br.driveForDistance(117, 200)
    br.moveLeftAttachmentMotorForMillis(millis=470, speed=280)
    br.driveForDistance(-40, 300)
    br.turnForAngle(71, speed=100)
    br.driveForDistance(-400, 700)
    br.turnForAngle(-60, speed=100)
    br.driveForDistance(-650, 1000)





if __name__ == "__main__":
    br = BaseRobot()
    Run(br)
