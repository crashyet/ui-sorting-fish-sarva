import os
import json
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "data/log_ikan.json")

def klasifikasi_box(jenis: str, berat: float) -> str:
    jenis = jenis.lower()

    # Mapping kolom ubah sesuai kebutuhanmu
    kolom_map = {
        "mouse": "A",    
        "phone": "B",
        "bawal": "C"
    }

    if jenis not in kolom_map:
        return "TRASH"

    kolom = kolom_map[jenis]

    # Baris berdasarkan berat
    if 0.1 <= berat <= 0.6:
        baris = "1"
    elif 0.6 < berat <= 2.0:
        baris = "2"
    elif berat > 2.0:
        baris = "3"
    else:
        return "TRASH"

    return kolom + baris


def simpan_log_deteksi(jenis, berat):
    box = klasifikasi_box(jenis, berat)
    now = datetime.now().strftime("[%H:%M:%S][%d-%m]")

    log_data = {
        "waktu": now,
        "tipe": "deteksi",
        "jenis": jenis,
        "berat": berat,
        "box": box,
        "pesan": None
    }

    _simpan_log(log_data)
    print(f"✅ Data tersimpan ke box {box}: {jenis}, {berat} Kg")


def log_system_activity(pesan):
    now = datetime.now().strftime("[%H:%M:%S][%d-%m]")
    log_data = {
        "waktu": now,
        "tipe": "sistem",
        "jenis": None,
        "berat": None,
        "box": None,
        "pesan": pesan
    }

    _simpan_log(log_data)
    print(f"📒 Log sistem: {pesan}")


def _simpan_log(log_data):
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data.append(log_data)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def ambil_semua_log(urut_terbaru=False):
    if not os.path.exists(LOG_FILE):
        return []

    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return []

    # Urutkan berdasarkan waktu (desc/asc)
    if urut_terbaru:
        data.sort(key=lambda x: x.get("waktu", ""), reverse=True)
    else:
        data.sort(key=lambda x: x.get("waktu", ""))

    return data