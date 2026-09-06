#from turtle import speed

from base_robot import *



def OutputReflectivity(br: BaseRobot):
    """Temporarily output reflectivity values from both sensors"""
    print("Reading reflectivity values for 10 seconds...")
    for i in range(100):
        left_refl = br.colorSensorLeft.reflection()
        right_refl = br.colorSensorRight.reflection()
        print(f"Left: {left_refl}, Right: {right_refl}")
        wait(100)
    print("Done.")


def Run(br: BaseRobot):
    '''
    br.moveLeftAttachmentMotorForMillis(775, 200)
    br.moveRightAttachmentMotorForMillis(1200, 200)
    br.driveForDistance(422,200)
    #br.moveLeftAttachmentMotorForMillis(2050, -100)
    br.moveRightAttachmentMotorForMillis(370, -200)
    br.driveForDistance(-130, 200)
    #br.moveLeftAttachmentMotorForMillis(2050, 100)
    br.moveRightAttachmentMotorForMillis(500, 200)    
    #br.driveForDistance(-455,150)
    br.moveRightAttachmentMotorForMillis(1300, -200)
    br.driveForDistance(50, 200)
    br.turnForAngle(-40, 200)
    #br.driveForDistance(600, 200)
    br.moveLeftAttachmentMotorForMillis(775, -200)
    br.turnForAngle(50, 200)
    br.driveForDistance(-30, 200)
    br.moveLeftAttachmentMotorForMillis(1550, 100)
    '''
    #br.moveLeftAttachmentMotorForMillis(1550,200)
    br.driveForDistance(630, 200) 
    br.moveRightAttachmentMotorForMillis(900, 200)
    br.turnForAngle(20, 200)
    br.moveRightAttachmentMotorForMillis(800, -200)    
    br.moveRightAttachmentMotorForMillis(950, 200)
    br.driveForDistance(-100, 200)
    br.driveForDistance(50, 200)
    br.turnForAngle(-20, 200)
    br.moveRightAttachmentMotorForMillis(1200, -200)
    br.moveLeftAttachmentMotorForMillis(1550, -200)
    br.turnForAngle(-90, 200)
    br.driveForDistance(450, 200)
    br.turnForAngle(135, 200)     
    br.driveForDistance(600, 100)

hub = PrimeHub()


if __name__ == "__main__":
    br = BaseRobot()
    #OutputReflectivity(br)
    Run(br)



