from base_robot import *
"""
def Run(br: BaseRobot):

   br.driveForDistance(325, 300)
    br.turnForAngle(92, 600)
    br.driveForDistance(700, 300)
    br.turnForAngle(92, 600)
    br.driveForDistance(250, 300)
    br.moveRightAttachmentMotorForMillis(500, 300)
    br.driveForDistance(-200, 500)
    br.turnForAngle(-120, 600)
    br.driveForDistance(-900, 500)
"""

def Run2(br: BaseRobot):
    br.driveForDistance(700, 300)
    br.stop_line(speed = 100, reflectivity = 10, tolerance = 5)
    br.align_line(reflectivity = 10, tolerance = 5)

if __name__ == "__main__":
    br = BaseRobot()
    Run2(br)


