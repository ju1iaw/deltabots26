from DeltaBots_Base import DeltaBots

def Run():
    bot = DeltaBots()
    bot.Reset_Gyro()
    bot.Gyro_Move(distance=220, velocity=800)
    bot.Gyro_Turn(-61, velocity=100)
    bot.Gyro_Move(distance=260, velocity=500)
    bot.Attachment_Time(1, 520, velocity=-550)
    bot.Gyro_Move(distance=-69, velocity=200)
    bot.Gyro_Turn(-60, velocity=100)
    bot.Gyro_Move(distance=185, velocity=500)
    bot.Gyro_Turn(67, velocity=100)
    bot.Attachment_Time(1, 160, velocity=-250)
    bot.Gyro_Move(distance=65, velocity=300)
    bot.Attachment_Time(1, 590, velocity=400)
    bot.Gyro_Turn(-35, velocity=40)
    bot.Gyro_Move(distance=160, velocity=400)
    bot.Gyro_Turn(54, velocity=90)
    bot.Gyro_Move(distance=30, velocity=400)
    bot.Gyro_Turn(-80, velocity=100)



	
	


   


if __name__ == "__main__":
    Run()
                                            