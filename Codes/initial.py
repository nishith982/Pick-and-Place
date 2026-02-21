from pymycobot.mycobot import MyCobot
from pymycobot.genre import Angle
from pymycobot import PI_PORT, PI_BAUD
import time


# Initialize MyCobot (Raspberry Pi)
mc = MyCobot("/dev/ttyAMA0", 1000000)
# Number of swings
num = [0, 0, 0, 0, -60, 47]
time.sleep(1)
mc.send_angles(num, 40)