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

def Run2(br: BaseRobot):
    br.driveForDistance(700, 300)
    br.stop_line(speed = 100, reflectivity = 10, tolerance = 5)
    br.align_line(reflectivity = 50, tolerance = 10)


def Run3(br: BaseRobot):
    br.moveRightAttachmentMotorForMillis(400, 200)
    #br.driveForDistance(200, 300)
    #br.moveRightAttachmentMotorForMillis(-50, 300)
    #br.driveForDistance(-200, 300)

"""

def colorsensorthingy(br: BaseRobot):
    x = 0
    if br.colorSensorRight.reflection() <= 27:
        x = 1
        br.moveRightAttachmentMotorForMillis(1000, -200)
    br.driveForDistance(-200, 200)
    if x == 1:
        br.moveRightAttachmentMotorForMillis(700, 200)
    br.turnForAngle(89, 200)
    br.driveForDistance(87, 200)
    br.turnForAngle(-90, 200)
    br.driveForDistance(205, 200)

def Run4(br: BaseRobot):
    br.driveForDistance(375, 300)
    for i in range(3):
        colorsensorthingy(br)



    
if __name__ == "__main__":
    br = BaseRobot()
    Run4(br)


