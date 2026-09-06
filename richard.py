from base_robot import *



def Run(br: BaseRobot):
    
    br.driveForDistance(600,600)
    br.moveLeftAttachmentMotorForMillis(960,-100)
    br.turnForAngle(45,300)
    br.driveForDistance(100,600)
    br.turnForAngle(-45,300)
    br.driveForDistance(-600,-200)
def Run2(br: BaseRobot):   
    br.driveForDistance(500,150)
    br.turnForAngle(-50,-100)
    br.driveForDistance(380,100)
    br.turnForAngle(12,100)
    br.driveForDistance(-200,-100)
 


if __name__ == "__main__":
    br = BaseRobot()
    Run2(br)
