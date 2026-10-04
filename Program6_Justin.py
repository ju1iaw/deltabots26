# Program 6
# Owner: Justin
# Mission 15
from DeltaBots_Base import DeltaBots

def Run(bot=None):
	if bot is None:
		bot = DeltaBots()
	bot.Reset_Gyro()
	bot.Gyro_Move(distance=322, velocity=200)
	bot.Attachment_Time(-1, 600, -550)
	bot.Gyro_Move(distance=-300, velocity=300)
	bot.Wait_All()
	
    

    



	
	


   


if __name__ == "__main__":
    Run()
                                            