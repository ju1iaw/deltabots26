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

    
#    br.moveLeftAttachmentMotorForMillis(millis=1000, speed=250)
    
#    br.driveForDistance(610, 200)
    
#    br.moveLeftAttachmentMotorForMillis(millis=1000, speed=-250)

#    br.turnForAngle(angle=30, speed=200, then=Stop.BRAKE, gyro=True, accel=TURN_ACCEL, decel=TURN_DECEL,)

#    br.driveForDistance(50, 200)
    
#    br.turnForAngle(angle=-30, speed=200, then=Stop.BRAKE, gyro=True, accel=TURN_ACCEL, decel=TURN_DECEL,)

#    br.driveForDistance(-610, 200)

    '''
    br.stop_line(
        speed=200,
        reflectivity=20,
        sensor=Side.LEFT,
        tolerance=3,
        stop_below=True,
        gyro=True,
        then=Stop.BRAKE,
    )
    #'''
    

    br.align_line(
        reflectivity=20,
        tolerance=3,
        forward_speed=30,
        max_turn_rate=40,
        kp=0.9,
        gyro=True,
        then=Stop.BRAKE,
    )
    
    hub = PrimeHub()



if __name__ == "__main__":
    br = BaseRobot()
    OutputReflectivity(br)
    # Run(br)



