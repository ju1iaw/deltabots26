from base_robot import *

def mission1(br: BaseRobot):
    br.moveRightAttachmentMotorForMillis(1000, -900)
    br.driveForDistance(825, 400)
    br.turnForAngle(-45, 60)
    br.moveRightAttachmentMotorForMillis(3000, 1000)
    #br.moveRightAttachmentMotorForMillis(1000, -300)
    br.driveForDistance(-100, 200)

if __name__ == "__main__":
    br = BaseRobot()
    mission1(br)
