from pymycobot.mycobot import MyCobot
from pymycobot.genre import Angle
from pymycobot import PI_PORT, PI_BAUD
import time
mc = MyCobot(PI_PORT, PI_BAUD)
time.sleep(2)

positions = []

for i in range(5):
    print("teach position ",i+1)
    mc.release_all_servos()
    time.sleep(10)
    mc.power_on()
    time.sleep(2)
    recorded_pos = mc.get_angles()
    print("recorded angles:", recorded_pos)
    if recorded_pos is None:
        print("failed")
        mc.send_angles([0, 0, 0, 0, 0, 0], 50)
        exit()
    positions.append(recorded_pos)
    mc.send_angles(recorded_pos, 20)
    time.sleep(2)

print("all position is taught successfully")
print("playback started")
mc.power_on()
time.sleep(2)
mc.set_fresh_mode(0)
for i, recorded_pos in enumerate(positions):
    print("moving position ", i+1)
    time.sleep(5)
    mc.send_angles(recorded_pos, 40)
    time.sleep(5)
    tag = mc.get_angles()
    print("angles:", tag)
print("playback successfull")    
mc.send_angles([0, 0, 0, 0, 0, 0], 40)