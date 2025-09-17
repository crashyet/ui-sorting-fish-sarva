import serial

def baca_berat():   
    ser = serial.Serial('COM7', 9600, timeout=1)

    while True:
        try:
            line = ser.readline().decode().strip()
            if line:
                print(f"Berat: {line}")
                return line
        except KeyboardInterrupt:
            break
        
    return 0.0