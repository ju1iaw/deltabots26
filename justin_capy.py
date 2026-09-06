from base_robot import BaseRobot
from pybricks.parameters import Port
from pybricks.pupdevices import Motor
br =  BaseRobot()

def Run():
	# br.driveForDistance(580, 800)
	# br.turnForAngle(71, speed=100)
	# br.driveForDistance(565, 500)
	# br.turnForAngle(-67, speed=100)
	# br.moveLeftAttachmentMotorForMillis(millis=265,speed=-290) 
	# br.driveForDistance(117, 200)
	# br.moveLeftAttachmentMotorForMillis(millis=470, speed=280)
	
    
	
	br.driveForDistance(220, 800)
	br.turnForAngle(-61, speed=100)
	br.driveForDistance(260, 500)
	br.moveRightAttachmentMotorForMillis(520, -550)
	br.driveForDistance(-69,200)
	br.turnForAngle(-60, speed=100)
	br.driveForDistance(200, 500)
	br.turnForAngle(67, speed=100)
	br.moveRightAttachmentMotorForMillis(160, -250)
	br.driveForDistance(65, 300)
	br.moveRightAttachmentMotorForMillis(590, 600)
	# br.turnForAngle(-25, 200)
	# br.driveForDistance(200, 500)
	# br.moveRightAttachmentMotorForMillis(650, -400)
	# br.driveForDistance(-60, 200)
	# br.moveRightAttachmentMotorForMillis(600, 400)
	
	


   


if __name__ == "__main__":
    Run()
                                            