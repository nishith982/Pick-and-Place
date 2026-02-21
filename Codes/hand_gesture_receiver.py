import socket
import time
from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD
# ---------------- ROBOT SETUP ----------------
mc = MyCobot(PI_PORT, PI_BAUD)
time.sleep(1)
mc.power_on()
time.sleep(1)

# Store current joint angles
angles = [0, 0, 0, 0, 0, 0]

SPEED = 20   # smooth, safe speed

# ---------------- SOCKET SETUP ----------------
HOST = ""        # Listen on all network interfaces
PORT = 9999      # Same port must be used on Windows

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(1)

print(" Robot receiver started")
print("Waiting for connection on port", PORT)

conn, addr = server.accept()
print("Connected from:", addr)

# ---------------- MAIN LOOP ----------------
try:
    while True:
        data = conn.recv(1024).decode().strip()
        if not data:
            break

        print("Received:", data)

        # ---- HOME COMMAND ----
        if data == "HOME":
            angles = [0, 0, 0, 0, 0, 0]
            mc.send_angles(angles, SPEED)
            print("\Moving to HOME")

        # ---- STOP COMMAND ----
        elif data == "STOP":
            print("⏸ STOP command received (holding position)")
            # No movement needed

        # ---- JOINT MOVE COMMAND ----
        else:
            try:
                joint, step = data.split(",")
                joint_index = int(joint[1]) - 1
                step = int(step)

                if 0 <= joint_index < 6:
                    angles[joint_index] += step
                    mc.send_angles(angles, SPEED)
                    print(f"J{joint_index+1} moved by {step}°")
                else:
                    print("Invalid joint number")

            except Exception as e:
                print("Invalid command format:", e)

except KeyboardInterrupt:
    print("\nReceiver stopped by user")

finally:4
    conn.close()
    server.close()
    print("🔌 Connection closed")
