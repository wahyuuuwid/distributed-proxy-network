import socket, threading, os

CACHE = "cache"
os.makedirs(CACHE, exist_ok=True)

lock = threading.Lock()  # mencegah race condition

def handle(client, addr):
    print(f"[CONNECT] {addr}")

    try:
        req = client.recv(4096)
        path = req.decode(errors="ignore").split(" ")[1]
        file = CACHE + "/" + path.replace("/", "_")

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
                server.connect(("127.0.0.1", 8000))
                server.sendall(req)

                response = b""
                while data := server.recv(4096):
                    response += data

                with lock:
                    with open(file, "wb") as f:
                        f.write(response)

                client.sendall(response)
                server.close()

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
