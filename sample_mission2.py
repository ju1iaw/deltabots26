from base_robot import *

def Run(br: BaseRobot):
    br.driveForDistance(2000, speed = 400)
    br.driveForDistance(-2000, speed= 400)
    br.driveForDistance(2000, speed = 400)
    br.driveForDistance(-2000, speed=400)

if __name__ == "__main__":
    br = BaseRobot()
    Run(br)
