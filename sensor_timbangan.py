import serial

ser = serial.Serial('COM7', 9600, timeout=1)

while True:
    try:
        line = ser.readline().decode().strip()
        if line:
            print(f"Berat: {line}")
    except KeyboardInterrupt:
        break   