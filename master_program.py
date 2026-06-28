from base_robot import *

# Import missions
import sample_mission1, sample_mission2


br = BaseRobot()

pressed = br.hub.buttons.pressed()

while Button.LEFT not in pressed:
    pressed = br.hub.buttons.pressed()

sample_mission1.Run(br)

while Button.LEFT not in pressed:
    pressed = br.hub.buttons.pressed()

sample_mission2.Run(br)
