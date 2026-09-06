from base_robot import *

def mission2(br: BaseRobot):
    br.moveLeftAttachmentMotorForMillis(700, 400)
    br.driveForDistance(450, 800)
    br.moveLeftAttachmentMotorForMillis(900, -200)
    br.driveForDistance(-500, 800)

if __name__ == "__main__":
    br = BaseRobot()
    mission2(br)
