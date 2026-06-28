from base_robot import *



def Run(br: BaseRobot):
    br.moveLeftAttachmentMotorForMillis(millis=500, speed=250)
    br.driveForDistance(600, 200)
    br.turnForAngle(90, speed=100)
    



if __name__ == "__main__":
    br = BaseRobot()
    Run(br)
