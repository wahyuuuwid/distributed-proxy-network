from socket import *
import time, csv, argparse, statistics

BUFFER_SIZE = 4096
PROXY_HOST  = 'localhost'
PROXY_PORT  = 8080
SERVER_HOST = 'localhost'  # untuk UDP langsung ke webserver
UDP_PORT    = 9000
FILE_PATH   = '/index.html'
UDP_COUNT   = 10

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['tcp', 'udp'], default='tcp')
args = parser.parse_args()

# ─────────────────────────────────────────
# MODE TCP — HTTP via Proxy
# ─────────────────────────────────────────
if args.mode == 'tcp':
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.connect((PROXY_HOST, PROXY_PORT))
    except ConnectionRefusedError:
        print(f"[ERROR] Tidak bisa konek ke proxy {PROXY_HOST}:{PROXY_PORT}")
        exit(1)

    t_start = time.time()
    s.send(f"GET {FILE_PATH} HTTP/1.1\r\nHost: {PROXY_HOST}\r\nConnection: close\r\n\r\n".encode())

    response = b""
    chunk_times = []
    while True:
        t0 = time.time()
        data = s.recv(BUFFER_SIZE)
        if not data: break
        chunk_times.append(time.time() - t0)
        response += data

    t_total = time.time() - t_start
    s.close()

    # Hitung metrik
    latency    = chunk_times[0] * 1000 if chunk_times else 0
    throughput = (len(response) * 8) / t_total / 1000 if t_total > 0 else 0
    jitter     = statistics.stdev([t * 1000 for t in chunk_times]) if len(chunk_times) > 1 else 0
    pkt_loss   = sum(1 for t in chunk_times if t > 0.5) / max(len(chunk_times), 1) * 100

    print(f"\n[Mode: TCP]")
    print(f"{'='*40}")
    print(f"  Throughput : {throughput:.2f} Kbps")
    print(f"  Latency    : {latency:.2f} ms")
    print(f"  Packet Loss: {pkt_loss:.2f} %")
    print(f"  Jitter     : {jitter:.2f} ms")
    print(f"  Total Data : {len(response)} bytes | {t_total:.4f}s")
    print(f"{'='*40}")

    # Simpan CSV
    with open("hasil_metrik.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Mode", "Metrik", "Nilai", "Satuan"])
        w.writerow(["TCP", "Throughput",  round(throughput, 2), "Kbps"])
        w.writerow(["TCP", "Latency",     round(latency, 2),    "ms"])
        w.writerow(["TCP", "Packet Loss", round(pkt_loss, 2),   "%"])
        w.writerow(["TCP", "Jitter",      round(jitter, 2),     "ms"])
    print("[INFO] Hasil disimpan ke hasil_metrik.csv\n")

    # Tampilkan response
    try:
        sep = response.index(b"\r\n\r\n")
        print("--- RESPONSE HEADER ---")
        print(response[:sep].decode())
        print("\n--- RESPONSE BODY ---")
        print(response[sep+4:].decode(errors='replace'))
    except ValueError:
        print(response.decode(errors='replace'))

# ─────────────────────────────────────────
# MODE UDP — QoS Pinger ke Webserver
# ─────────────────────────────────────────
else:
    s = socket(AF_INET, SOCK_DGRAM)
    s.settimeout(1)

    rtts       = []
    sent       = 0
    lost       = 0
    t_test_start = time.time()

    print(f"\n[Mode: UDP] Mengirim {UDP_COUNT} paket ke {SERVER_HOST}:{UDP_PORT}\n")

    for seq in range(1, UDP_COUNT + 1):
        payload = f"Ping {seq} {time.time():.6f}".encode()
        t_send  = time.time()
        s.sendto(payload, (SERVER_HOST, UDP_PORT))
        sent += 1
        try:
            data, _ = s.recvfrom(BUFFER_SIZE)
            rtt = (time.time() - t_send) * 1000
            rtts.append(rtt)
            print(f"  Paket {seq}: RTT = {rtt:.2f} ms | {data.decode()}")
        except (timeout, ConnectionResetError):
            lost += 1
            print(f"  Paket {seq}: Request timed out")
        time.sleep(0.1)

    t_test_total = time.time() - t_test_start
    s.close()

    # Hitung statistik
    pkt_loss   = lost / sent * 100
    rtt_min    = min(rtts) if rtts else 0
    rtt_avg    = sum(rtts) / len(rtts) if rtts else 0
    rtt_max    = max(rtts) if rtts else 0
    jitter     = statistics.stdev(rtts) if len(rtts) > 1 else 0
    total_payload = sent * BUFFER_SIZE  # estimasi
    throughput = (total_payload * 8) / t_test_total / 1000 if t_test_total > 0 else 0

    print(f"\n{'='*40}")
    print(f"  Paket dikirim : {sent}")
    print(f"  Paket hilang  : {lost}")
    print(f"  Packet Loss   : {pkt_loss:.2f} %")
    print(f"  RTT Min/Avg/Max: {rtt_min:.2f}/{rtt_avg:.2f}/{rtt_max:.2f} ms")
    print(f"  Jitter        : {jitter:.2f} ms")
    print(f"  Throughput    : {throughput:.2f} Kbps")
    print(f"{'='*40}")

    # Simpan CSV
    with open("hasil_metrik.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Mode", "Metrik", "Nilai", "Satuan"])
        w.writerow(["UDP", "RTT Min",      round(rtt_min, 2),   "ms"])
        w.writerow(["UDP", "RTT Avg",      round(rtt_avg, 2),   "ms"])
        w.writerow(["UDP", "RTT Max",      round(rtt_max, 2),   "ms"])
        w.writerow(["UDP", "Packet Loss",  round(pkt_loss, 2),  "%"])
        w.writerow(["UDP", "Jitter",       round(jitter, 2),    "ms"])
        w.writerow(["UDP", "Throughput",   round(throughput, 2),"Kbps"])
    print("[INFO] Hasil disimpan ke hasil_metrik.csv")