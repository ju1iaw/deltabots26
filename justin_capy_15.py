from DeltaBots_Base import DeltaBots

def Run():
	bot = DeltaBots()
	bot.Reset_Gyro()
	bot.Gyro_Move(distance=322, velocity=200)
	bot.Attachment_Time(-1, 600, -550)
	bot.Gyro_Move(distance=-300, velocity=300)
	
    

    



	
	


   


if __name__ == "__main__":
    Run()
                                            