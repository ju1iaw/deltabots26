from base_robot import *

# Import mission files that actually exist in this project.
# Update this list to point to the mission you want to run.
import delina
# import michael
# import justin_capy
# import alyssa

br = BaseRobot()

pressed = br.hub.buttons.pressed()

while Button.LEFT not in pressed:
    pressed = br.hub.buttons.pressed()

# Run the selected mission.
delina.Run(br)

# If you want to run another mission afterward, add it here.
# while Button.LEFT not in pressed:
#     pressed = br.hub.buttons.pressed()
# michael.Run(br)
