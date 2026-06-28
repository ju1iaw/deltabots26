from base_robot import *



def Run(br: BaseRobot):
    br.moveLeftAttachmentMotorForMillis(millis=1000, speed= 300)
    br.turnForAngle(90, speed = 300)
    br.driveForDistance(100, 300)
if __name__ == "__main__":
    br = BaseRobot()
    Run(br)


