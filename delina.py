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


def align(br: BaseRobot):
    br.driveForDistance(650, 200)
    br.stop_line(200, 20, tolerance=5)
    br.align_line(
        100, 25, tolerance=5, forward_speed=30, max_turn_rate=40, kp=0.9
    )


def Run2(br: BaseRobot):
    br.driveForDistance(650, 200)
    br.turnForAngle(-100, 200)
    br.driveForDistance(100, 200)
    br.turnForAngle(-40, 200)
    br.moveRightAttachmentMotorForMillis(1000, 200)
    br.driveForDistance(-200, 200)
    br.turnForAngle(100, 200)
    br.driveForDistance(600, -200)


def test(br: BaseRobot):
    for i in range(100):
        print(br.colorSensorLeft.reflection())


def rock(br: BaseRobot):
    if br.colorSensorLeft.reflection() < 25:
        br.moveRightAttachmentMotorForMillis(1000, 200)
        br.driveForDistance(-200, 200)
        br.moveRightAttachmentMotorForMillis(1000, -200)
        br.turnForAngle(90, 200)
        br.driveForDistance(75, 200)
        br.turnForAngle(-90, 200)
        br.driveForDistance(200, 200)
    else:
        br.driveForDistance(-200, 200)
        br.turnForAngle(90, 200)
        br.driveForDistance(75, 200)
        br.turnForAngle(-90, 200)
        br.driveForDistance(200, 200)


def therock(br: BaseRobot):
    br.driveForDistance(390, 200)
    for i in range(3):
        rock(br)


def mission3(br: BaseRobot):
    br.driveForDistance(431.8, 200)
    br.driveForDistance(-431.8, 200)
    """
    while Button.LEFT not in pressed:
        pressed = br.hub.buttons.pressed()
    br.turnForAngle(50, 200)
    br.driveForDistance(300, 200)
    br.turnForAngle(-50, 200)
    br.driveForDistance(200, 200)
    """


def mission4_5(br: BaseRobot):
    br.moveLeftAttachmentMotorForMillis(3000, -200)

    br.driveForDistance(698.5, 200)
    br.turnForAngle(-38, 200)
    br.driveForDistance(110, 200)
    br.moveLeftAttachmentMotorForMillis(1000, 200)
    br.turnForAngle(38, 200)
    br.moveRightAttachmentMotorForMillis(1000, 200)


"""   
    while Button.LEFT not in pressed:
        pressed = br.hub.buttons.pressed()
    br.turnForAngle(50, 200)
    br.driveForDistance(300, 200)
    br.turnForAngle(-50, 200)
    br.driveForDistance(200, 200)
    """


if __name__ == "__main__":
    br = BaseRobot()
    mission4_5(br)
    br.stop()
