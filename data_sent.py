# socket_client_pc.py
import socket
import json

HOST = '192.168.30.185'
# HOST = '10.153.128.204'
PORT = 65432

data = {
    "jenis": "Ikan B",
    "berat": 5,
    "koordinat": [2, 5],
    "status": "OFF"
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(json.dumps(data).encode())
    print("✅ JSON terkirim:", data)