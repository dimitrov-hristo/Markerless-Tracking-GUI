
import time
from pyfirmata import Arduino
from serial.tools import list_ports

def detect_arduino_port():
    for p in list_ports.comports():
        name = (p.description or "") + " " + (p.manufacturer or "")
        if any(s in name for s in ("Arduino", "Genuino", "usbmodem", "wchusbserial", "CH340", "CP2102", "FT232")):
            return p.device
    raise RuntimeError("No Arduino-like port found.")
PIN = 11
port = detect_arduino_port()
board = Arduino(port)
try:
    # let Firmata finish capability query
    time.sleep(0.5)
    repeats = 6
    on_s, off_s = 5.0, 5.0
    t0 = time.perf_counter()
    for i in range(repeats):
        # ON phase
        board.digital[PIN].write(1)
        t_on_end = t0 + (i * (on_s + off_s)) + on_s
        while True:
            now = time.perf_counter()
            dt = t_on_end - now
            if dt <= 0: break
            time.sleep(min(0.05, dt))  # small sleeps, corrected by monotonic clock
        # OFF phase
        board.digital[PIN].write(0)
        t_off_end = t0 + (i * (on_s + off_s)) + on_s + off_s
        while True:
            now = time.perf_counter()
            dt = t_off_end - now
            if dt <= 0: break
            time.sleep(min(0.05, dt))
finally:
    board.exit()