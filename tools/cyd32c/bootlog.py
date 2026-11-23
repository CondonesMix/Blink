"""Reset the board and save its serial console for N seconds to boot.log.
   python3 bootlog.py /dev/cu.usbserial-XXXX [seconds]   (needs pyserial)"""
import sys, time, serial
port = sys.argv[1]; secs = float(sys.argv[2]) if len(sys.argv) > 2 else 15
s = serial.Serial(port, 115200, timeout=0.2)
s.dtr = False; s.rts = True; time.sleep(0.15); s.rts = False
end = time.time() + secs
with open("boot.log", "wb") as f:
    while time.time() < end:
        d = s.read(4096)
        if d:
            f.write(d); f.flush()
s.close()
