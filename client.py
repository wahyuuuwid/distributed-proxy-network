from socket import *
import time, csv, argparse, statistics

# ── Konfigurasi ──────────────────────────
PROXY_HOST  = 'localhost'
PROXY_PORT  = 8080
SERVER_HOST = 'localhost'
UDP_PORT    = 9000
FILE_PATH   = '/index.html'
UDP_COUNT   = 10
BUFFER_SIZE = 4096

# ── Argumen ──────────────────────────────
parser = argparse.ArgumentParser(description='Client HTTP/UDP QoS')
parser.add_argument('--mode', choices=['tcp', 'udp'], default='tcp')
args = parser.parse_args()

# ── Helpers ──────────────────────────────
def save_csv(rows, filename="hasil_metrik.csv"):
    with open(filename, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Mode", "Metrik", "Nilai", "Satuan"])
        w.writerows(rows)
    print(f"[INFO] Hasil disimpan ke {filename}")

def print_metrics(mode, rows):
    print(f"\n{'='*45}")
    print(f"  {'HASIL PENGUKURAN QoS':^41}")
    print(f"  Mode: {mode.upper():<36}")
    print(f"{'─'*45}")
    for _, metrik, nilai, satuan in rows:
        print(f"  {metrik:<20}: {nilai:>8} {satuan}")
    print(f"{'='*45}")

# ─────────────────────────────────────────
# MODE TCP — HTTP via Proxy
# ─────────────────────────────────────────
def run_tcp():
    print(f"[TCP] Menghubungi proxy {PROXY_HOST}:{PROXY_PORT} ...")

    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.connect((PROXY_HOST, PROXY_PORT))
    except ConnectionRefusedError:
        print("[ERROR] Proxy tidak dapat dijangkau.")
        exit(1)

    t_start = time.time()
    s.send(f"GET {FILE_PATH} HTTP/1.1\r\nHost: {PROXY_HOST}\r\nConnection: close\r\n\r\n".encode())

    response, chunk_times = b"", []
    while True:
        t0   = time.time()
        data = s.recv(BUFFER_SIZE)
        if not data: break
        chunk_times.append(time.time() - t0)
        response += data
    t_total = time.time() - t_start
    s.close()

    latency    = chunk_times[0] * 1000 if chunk_times else 0
    throughput = (len(response) * 8) / t_total / 1000 if t_total > 0 else 0
    jitter     = statistics.stdev([t * 1000 for t in chunk_times]) if len(chunk_times) > 1 else 0
    pkt_loss   = sum(1 for t in chunk_times if t > 0.5) / max(len(chunk_times), 1) * 100

    rows = [
        ["TCP", "Throughput",  round(throughput, 2), "Kbps"],
        ["TCP", "Latency",     round(latency, 2),    "ms"],
        ["TCP", "Packet Loss", round(pkt_loss, 2),   "%"],
        ["TCP", "Jitter",      round(jitter, 2),     "ms"],
    ]
    print_metrics("tcp", rows)
    save_csv(rows)

    try:
        sep = response.index(b"\r\n\r\n")
        print("\n--- RESPONSE HEADER ---")
        print(response[:sep].decode())
        print("\n--- RESPONSE BODY ---")
        print(response[sep+4:].decode(errors='replace'))
    except ValueError:
        print(response.decode(errors='replace'))

# ─────────────────────────────────────────
# MODE UDP — QoS Pinger ke Web Server
# ─────────────────────────────────────────
def run_udp():
    print(f"[UDP] Mengirim {UDP_COUNT} paket ke {SERVER_HOST}:{UDP_PORT}\n")

    s = socket(AF_INET, SOCK_DGRAM)
    s.settimeout(1)

    rtts, sent, lost = [], 0, 0
    t_start = time.time()
    payload = b""

    for seq in range(1, UDP_COUNT + 1):
        payload = f"Ping {seq} {time.time():.6f}".encode()
        t_send  = time.time()
        s.sendto(payload, (SERVER_HOST, UDP_PORT))
        sent += 1
        try:
            data, _ = s.recvfrom(BUFFER_SIZE)
            rtt = (time.time() - t_send) * 1000
            rtts.append(rtt)
            print(f"  [{seq:>2}] RTT = {rtt:.2f} ms  |  {data.decode()}")
        except (timeout, ConnectionResetError):
            lost += 1
            print(f"  [{seq:>2}] Request timed out")
        time.sleep(0.1)

    t_total = time.time() - t_start
    s.close()

    pkt_loss   = lost / sent * 100
    rtt_min    = min(rtts) if rtts else 0
    rtt_avg    = sum(rtts) / len(rtts) if rtts else 0
    rtt_max    = max(rtts) if rtts else 0
    jitter     = statistics.stdev(rtts) if len(rtts) > 1 else 0
    throughput = (sent * len(payload) * 8) / t_total / 1000 if t_total > 0 else 0

    rows = [
        ["UDP", "RTT Min",     round(rtt_min, 2),    "ms"],
        ["UDP", "RTT Avg",     round(rtt_avg, 2),    "ms"],
        ["UDP", "RTT Max",     round(rtt_max, 2),    "ms"],
        ["UDP", "Jitter",      round(jitter, 2),     "ms"],
        ["UDP", "Packet Loss", round(pkt_loss, 2),   "%"],
        ["UDP", "Throughput",  round(throughput, 2), "Kbps"],
    ]
    print_metrics("udp", rows)
    save_csv(rows)

# ── Entry Point ──────────────────────────
if args.mode == 'tcp':
    run_tcp()
else:
    run_udp()