from DeltaBots_Base import DeltaBots

def Run():
	bot = DeltaBots()
	bot.Reset_Gyro()
	bot.Gyro_Move(distance=170, velocity=200)
	bot.Gyro_Turn(angle=30, velocity=100)
	bot.Gyro_Move(distance=596, velocity=300)
	bot.Attachment_Time(1, 800, -700)
	bot.Gyro_Move(distance=-700, velocity=600)

    

    



	
	


   


if __name__ == "__main__":
    Run()
                                            