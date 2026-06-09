import socket
import threading
import os

PROXY_PORT = 8080
SERVER_ADDR = ("127.0.0.1", 8000)

CACHE = "cache"
os.makedirs(CACHE, exist_ok=True)
lock = threading.Lock()

def handle(client, addr):
    print(f"[CONNECT] {addr}")

    try:
        req = client.recv(4096)
        # request kosong
        if not req:
            return

        parts = req.decode(errors="ignore").split()

        # request tidak valid
        if len(parts) < 2:
            print("[ERROR] Invalid HTTP request")
            client.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Length:0\r\n\r\n")
            return

        path = parts[1]
        file = os.path.join(CACHE, path.replace("/", "_"))

        with lock:
            cache_exist = os.path.exists(file)

        if cache_exist:
            print(f"[CACHE HIT] {path}")

            with open(file, "rb") as f:
                client.sendall(f.read())

        else:
            print(f"[CACHE MISS] {path}")
            print(f"[FORWARD] {path} -> 127.0.0.1:8000")

            try:
                server = socket.socket()
                server.settimeout(5)
                server.connect(SERVER_ADDR)
                server.sendall(req)

                response = b""
                while True:
                    data = server.recv(4096)
                    if not data:
                        break
                    response += data

                server.close()

                with lock:
                    with open(file, "wb") as f:
                        f.write(response)

                client.sendall(response)

            except ConnectionRefusedError:
                print("[ERROR 502] Backend unreachable")
                client.sendall(
                    b"HTTP/1.1 502 Bad Gateway\r\nContent-Length:0\r\n\r\n"
                )

            except socket.timeout:
                print("[ERROR 504] Gateway Timeout")
                client.sendall(
                    b"HTTP/1.1 504 Gateway Timeout\r\nContent-Length:0\r\n\r\n"
                )

    except Exception as e:
        print("[ERROR]", e)

    finally:
        client.close()
        print(f"[DISCONNECT] {addr}")


proxy = socket.socket()
proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

proxy.bind(("127.0.0.1", 8080))
proxy.listen()
print("Proxy listening on port 8080")

while True:
    client, addr = proxy.accept()
    threading.Thread(
        target=handle,
        args=(client, addr),
        daemon=True
    ).start()