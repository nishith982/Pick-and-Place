import cv2
import mediapipe as mp
import socket
import time

# ---------------- NETWORK ----------------
PI_IP = "10.111.195.199"
PORT = 9999

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((PI_IP, PORT))
print("✅ Connected to Raspberry Pi")

# ---------------- MEDIAPIPE ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
draw = mp.solutions.drawing_utils

# ---------------- PARAMETERS ----------------
STEP = 4
COMMAND_DELAY = 0.3   # seconds

last_action = 0
last_command = None
status = "WAITING"

# ---------------- HELPERS ----------------
def fingers_state(lm):
    """
    Returns [thumb, index, middle, ring, little]
    """
    fingers = []

    # Thumb (x-axis check)
    fingers.append(lm.landmark[4].x < lm.landmark[3].x)

    # Other fingers (y-axis check)
    for tip in [8, 12, 16, 20]:
        fingers.append(lm.landmark[tip].y < lm.landmark[tip - 2].y)

    return fingers

# ---------------- CAMERA ----------------
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (0, 0),fx=2, fy=2)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    now = time.time()

    if res.multi_hand_landmarks:
        lm = res.multi_hand_landmarks[0]
        draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

        thumb, index, middle, ring, little = fingers_state(lm)

        # -------- HOME --------
        if not any([thumb, index, middle, ring, little]):
            if last_command != "HOME":
                sock.send(b"HOME")
                last_command = "HOME"
            status = "HOME"

        # -------- STOP --------
        elif all([thumb, index, middle, ring, little]):
            if last_command != "STOP":
                sock.send(b"STOP")
                last_command = "STOP"
            status = "STOP"

        # -------- J1 --------
        elif index and middle and not thumb and not ring:
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J1,{STEP}".encode())
                last_action = now
                status = "J1 CW"

        elif index and little and not thumb and not ring:
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J1,-{STEP}".encode())
                last_action = now
                status = "J1 CCW"

        # -------- J2 --------
        elif thumb and index and not middle and not ring:
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J2,{STEP}".encode())
                last_action = now
                status = "J2 CW"

        elif thumb and little and not index and not middle:
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J2,-{STEP}".encode())
                last_action = now
                status = "J2 CCW"

        # -------- J3 --------
        elif index and not any([thumb, middle, ring, little]):
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J3,{STEP}".encode())
                last_action = now
                status = "J3 CW"

        elif thumb and not any([index, middle, ring, little]):
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J3,-{STEP}".encode())
                last_action = now
                status = "J3 CCW"

        # -------- J4 --------
        elif little and not any([thumb, index, middle, ring]):
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J4,{STEP}".encode())
                last_action = now
                status = "J4 CW"

        elif ring and little and not any([thumb, index, middle]):
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J4,-{STEP}".encode())
                last_action = now
                status = "J4 CCW"

        # -------- J5 --------
        elif middle and ring and little and not thumb and not index:
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J5,{STEP}".encode())
                last_action = now
                status = "J5 CW"

        elif index and middle and ring and not thumb and not little:
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J5,-{STEP}".encode())
                last_action = now
                status = "J5 CCW"

        # -------- J6 --------
        elif index and middle and ring and little and not thumb:
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J6,{STEP}".encode())
                last_action = now
                status = "J6 CW"

        elif thumb and index and middle and not ring and not little:
            if now - last_action > COMMAND_DELAY:
                sock.send(f"J6,-{STEP}".encode())
                last_action = now
                status = "J6 CCW"

    else:
        status = "NO HAND"

    # ---------------- UI ----------------
    cv2.putText(frame, f"STATUS: {status}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2)

    cv2.imshow("Gesture Control J1–J6", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
sock.close()
cv2.destroyAllWindows()
