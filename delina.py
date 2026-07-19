from base_robot import *


def Run(br: BaseRobot):
    br.driveForDistance(330, 200)
    br.turnForAngle(90, 200)
    br.driveForDistance(430, 200)
    br.turnForAngle(-75, 200)
    br.driveForDistance(40, 200)
    br.moveRightAttachmentMotorForMillis(300, -200)
    br.turnForAngle(20, 200)
    br.driveForDistance(-300, 200)
    br.turnForAngle(-130, 200)
    br.driveForDistance(400, 200)


if __name__ == "__main__":
    br = BaseRobot()
    Run(br)

    br.stop()
