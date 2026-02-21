import cv2
import numpy as np
import time
import RPi.GPIO as GPIO
from pymycobot.mycobot import MyCobot

# ================= ROBOT PARAMETERS =================
ROBOT_PORT = '/dev/ttyAMA0'
ROBOT_BAUD = 1000000
TABLE_Z = 95
PRE_PICK_Z = 95
MIN_AREA = 2000

# ================= SERVO (GRIPPER) SETUP =================
SERVO_PIN = 19

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_angle(angle):
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)

def gripper_open():
    set_angle(90)

def gripper_close():
    set_angle(180)

# ================= COLOR-BASED GOAL POSITIONS =================
GOAL_ANGLES = {
    "red": [-46.66, -93.6, 54.31, -41.13, -2.37, 73.47],
    "blue": [-63.63, -97.38, 75.32, -66.62, -1.49, 64.68],
    "green": [-80.5, -96.24, 59.15, -54.4, -3.07, 44.82]
}

# ================= HSV COLOR RANGES =================
COLOR_RANGES = {
    "blue": ([np.array([75,150,0]), np.array([130,255,255])]),
    "green": ([np.array([35,100,100]), np.array([85,255,255])]),
    "yellow": ([np.array([20,100,100]), np.array([30,255,255])]),
    "red1": ([np.array([0,120,70]), np.array([10,255,255])]),
    "red2": ([np.array([170,120,70]), np.array([180,255,255])]),
}

# ================= HOMOGRAPHY =================
pixels = np.array([
    [419, 75],
    [198, 86],
    [175, 393],
    [350, 400],
], dtype=float)

world_coords = np.array([
    [140, -100],
    [255, -87],
    [255, 90],
    [155, 90],
], dtype=float)

H, _ = cv2.findHomography(pixels, world_coords)

# ================= ROBOT INIT =================
mc = MyCobot(ROBOT_PORT, ROBOT_BAUD)
time.sleep(1)

current_angles = mc.get_angles()
fixed_j6 = current_angles[5]

# ================= CAMERA INIT =================
vs = cv2.VideoCapture(0)
vs.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ================= TIMING =================
last_pick_time = 0
cooldown_time = 5

# ================= FUNCTIONS =================
def pixel_to_table(uv, H, table_z=TABLE_Z):
    uv_h = np.array([uv[0], uv[1], 1.0])
    XY_h = H @ uv_h
    XY_h /= XY_h[2]
    return np.array([XY_h[0], XY_h[1], table_z])

def move_to_goal(color):
    if color in GOAL_ANGLES:
        print(f"🎯 Placing in {color.upper()} basket")
        mc.send_angles(GOAL_ANGLES[color], 20)
        time.sleep(8)
        gripper_open()
        time.sleep(1)
        mc.send_angles([0, 0, 0, 0, -67, 47], 20)
        time.sleep(2)

def move_to_position(target_xyz, color):
    gripper_open()

    mc.send_coords([target_xyz[0], target_xyz[1], PRE_PICK_Z,
                    -180.0, 0, fixed_j6], 20, 0)
    time.sleep(1)

    mc.send_coords([target_xyz[0], target_xyz[1], target_xyz[2],
                    -180.0, 0, fixed_j6], 20, 0)
    time.sleep(4)

    gripper_close()

    mc.send_coords([target_xyz[0], target_xyz[1], PRE_PICK_Z,
                    -180.0, 0, fixed_j6], 20, 0)
    time.sleep(1)

    mc.send_angles([0, 0, 0, 0, -67, 47], 20)
    time.sleep(1)

    move_to_goal(color)

# ================= MAIN LOOP =================
while True:
    ret, frame = vs.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    detected_color = None
    largest_area = 0
    best_cnt = None
    best_box = None

    for color, bounds in COLOR_RANGES.items():
        if color in ("red1", "red2"):
            continue
        mask = cv2.inRange(hsv, bounds[0], bounds[1])
        contours,_ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > MIN_AREA and area > largest_area:
                largest_area = area
                best_cnt = cnt
                best_box = cv2.boundingRect(cnt)
                detected_color = color

    mask_red = cv2.inRange(hsv, COLOR_RANGES["red1"][0], COLOR_RANGES["red1"][1]) | \
               cv2.inRange(hsv, COLOR_RANGES["red2"][0], COLOR_RANGES["red2"][1])
    contours,_ = cv2.findContours(mask_red, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > MIN_AREA and area > largest_area:
            largest_area = area
            best_cnt = cnt
            best_box = cv2.boundingRect(cnt)
            detected_color = "red"

    if detected_color and best_cnt is not None:
        M = cv2.moments(best_cnt)
        if M["m00"] != 0:

            cx = int(M["m10"]/M["m00"])
            cy = int(M["m01"]/M["m00"])

            x,y,w,h = best_box
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.circle(frame,(cx,cy),5,(255,0,0),-1)

            if time.time() - last_pick_time > cooldown_time:
                target_xyz = pixel_to_table((cx,cy), H)
                print("Moving to:", target_xyz)
                move_to_position(target_xyz, detected_color)

                last_pick_time = time.time()

    cv2.imshow("Detection", frame)
    if cv2.waitKey(1) == 27:
        break

vs.release()
cv2.destroyAllWindows()
pwm.stop()
GPIO.cleanup()