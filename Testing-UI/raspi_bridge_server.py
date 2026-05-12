import json
import socketserver
from datetime import datetime
from pathlib import Path


HOST = "0.0.0.0"
PORT = 65432
LOG_PATH = Path(__file__).with_name("raspi_bridge.log")


def write_log(message):
    line = f"{datetime.now().isoformat(timespec='seconds')} {message}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="")


def handle_command(payload):
    command = payload.get("command")
    if command == "system_start":
        return apply_system_start(payload)
    if command == "system_stop":
        return apply_system_stop(payload)
    if command == "system_reset":
        return apply_system_reset(payload)
    if command == "set_conveyor_speed":
        return apply_conveyor_speed(payload)
    if command == "reset_box":
        return apply_reset_box(payload)
    if command == "reset_reject_bin":
        return apply_reset_reject_bin(payload)
    return {"ok": False, "error": f"unknown command: {command}"}


def apply_system_start(payload):
    # Enable machine relay, GPIO safety chain, or motor controller here.
    write_log(f"START {json.dumps(payload, ensure_ascii=False)}")
    return {"ok": True, "command": "system_start"}


def apply_system_stop(payload):
    # Stop motor relay, VFD, and actuator outputs here.
    write_log(f"STOP {json.dumps(payload, ensure_ascii=False)}")
    return {"ok": True, "command": "system_stop"}


def apply_system_reset(payload):
    # Clear controller counters or local machine state here.
    write_log(f"RESET {json.dumps(payload, ensure_ascii=False)}")
    return {"ok": True, "command": "system_reset"}


def apply_conveyor_speed(payload):
    key = payload.get("conveyor_key")
    speed_ms = float(payload.get("speed_ms", 0))
    raw_value = int(payload.get("raw_value", round(speed_ms * 10)))
    # Send raw_value to COM, GPIO, VFD, or PLC from the Raspberry Pi here.
    write_log(f"CONVEYOR {key} speed={speed_ms:.1f}m/s raw={raw_value}")
    return {"ok": True, "command": "set_conveyor_speed", "conveyor_key": key, "speed_ms": speed_ms}


def apply_reset_box(payload):
    write_log(f"RESET_BOX {payload.get('box')}")
    return {"ok": True, "command": "reset_box", "box": payload.get("box")}


def apply_reset_reject_bin(payload):
    write_log("RESET_REJECT_BIN")
    return {"ok": True, "command": "reset_reject_bin"}


class CommandHandler(socketserver.BaseRequestHandler):
    def handle(self):
        raw = self.request.recv(65535)
        try:
            payload = json.loads(raw.decode("utf-8"))
            response = handle_command(payload)
        except Exception as exc:
            response = {"ok": False, "error": str(exc)}
            write_log(f"ERROR {exc}")
        self.request.sendall(json.dumps(response).encode("utf-8"))


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ReusableTCPServer((HOST, PORT), CommandHandler) as server:
        write_log(f"Raspi bridge listening on {HOST}:{PORT}")
        server.serve_forever()
