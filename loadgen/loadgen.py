import os
import time
import threading
import requests

TARGET_URL = os.getenv("TARGET_URL", "http://localhost:8080/reco?user_id=42")
RPS = float(os.getenv("RPS", "20"))

lock = threading.Lock()
ok = 0
fail = 0

def worker():
    global ok, fail
    while True:
        t0 = time.time()
        try:
            r = requests.get(TARGET_URL, timeout=2)
            with lock:
                if r.status_code == 200:
                    ok += 1
                else:
                    fail += 1
        except Exception:
            with lock:
                fail += 1
        dt = time.time() - t0
        time.sleep(max(0.0, (1.0 / RPS) - dt))

def reporter():
    global ok, fail
    last_ok = 0
    last_fail = 0
    while True:
        time.sleep(2)
        with lock:
            d_ok = ok - last_ok
            d_fail = fail - last_fail
            last_ok, last_fail = ok, fail
        print(f"[loadgen] last 2s ok={d_ok} fail={d_fail} total_ok={ok} total_fail={fail}")

if __name__ == "__main__":
    threads = []
    for _ in range(4):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)
    reporter()
