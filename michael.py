from base_robot import *



def Run(br: BaseRobot):
    br.moveLeftAttachmentMotorForMillis(millis=500, speed=250)
    br.driveForDistance(600, 200)
    

    hub = PrimeHub()

    while True:
        br.drive(120, 0)
        wait(2000)

        br.drive(120, 150)
        wait(2000)

        br.drive(120, -150)
        wait(2000)



if __name__ == "__main__":
    br = BaseRobot()
    Run(br)


