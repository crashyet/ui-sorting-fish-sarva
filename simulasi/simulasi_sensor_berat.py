import random
import time

def baca_berat(min_berat=0.5, max_berat=10.0):
    berat = round(random.uniform(min_berat, max_berat), 2)
    return berat

if __name__ == "__main__":
    print("=== Simulasi Berat Barang (Tekan Ctrl+C untuk berhenti) ===\n")
    
    while True:
        berat = baca_berat()
        print(f"Berat barang: {berat} kg")
        time.sleep(0.2)  # jeda 2 detik