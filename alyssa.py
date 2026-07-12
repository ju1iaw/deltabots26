from base_robot import *



def Run(br: BaseRobot):
    br.driveForDistance(325, 200)
    br.turnForAngle(92, 200)
    br.driveForDistance(700, 200)
    br.turnForAngle(92, 200)
    br.driveForDistance(250, 200)
    br.moveRightAttachmentMotorForMillis(500, 200)
    br.driveForDistance(-200, 200)
    br.turnForAngle(-92, 200)
    br.driveForDistance(-700, 200)
    br.turnForAngle(-92, 200)

if __name__ == "__main__":
    br = BaseRobot()
    Run(br)


