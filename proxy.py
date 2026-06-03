import socket
import time

# Proxy Configuration
PROXY_HOST = '0.0.0.0'
PROXY_PORT = 8080

# Backend Server (WebServer)
BACKEND_HOST = '10.101.48.84'
BACKEND_PORT = 8000

# Cache Configuration
CACHE_TTL = 300  # 5 minutes


class CachingForwardProxy:
    def __init__(self):
        # {path: (response_bytes, timestamp)}
        self.cache = {}

    def extract_path(self, request_line):
        """Extract request path dari HTTP request line"""
        try:
            parts = request_line.split(' ')
            return parts[1]
        except Exception:
            return None

    def is_cache_valid(self, cache_time):
        """Check cache TTL validity"""
        return (time.time() - cache_time) < CACHE_TTL

    def handle_client(self, client_socket, client_address):
        print(f"[CONNECT] Client: {client_address[0]}:{client_address[1]}")

        try:
            # Receive request from client
            request = client_socket.recv(4096)

            if not request:
                return

            request_str = request.decode('utf-8', errors='ignore')
            request_line = request_str.split('\n')[0]
            path = self.extract_path(request_line)

            print(f"[REQUEST] {request_line}")

            # Check cache
            if path and path in self.cache:
                cached_response, cache_time = self.cache[path]

                if self.is_cache_valid(cache_time):
                    print(f"[CACHE HIT] {path}")
                    client_socket.sendall(cached_response)
                    print(f"[SUCCESS] Cached response sent")
                    return
                else:
                    print(f"[CACHE EXPIRED] {path}")
                    del self.cache[path]

            # Forward request to backend server
            print(f"[FORWARD] To {BACKEND_HOST}:{BACKEND_PORT}")

            backend_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            try:
                backend_socket.connect(
                    (BACKEND_HOST, BACKEND_PORT)
                )

                backend_socket.sendall(request)

                # Receive full response from backend
                response = b''

                while True:
                    data = backend_socket.recv(4096)

                    if not data:
                        break

                    response += data

                backend_socket.close()

                # Store in cache
                if path:
                    self.cache[path] = (
                        response,
                        time.time()
                    )

                    print(
                        f"[CACHED] {path} "
                        f"({len(response)} bytes)"
                    )

                # Send response to client
                client_socket.sendall(response)

                print(
                    f"[SUCCESS] "
                    f"{len(response)} bytes sent"
                )

            except ConnectionRefusedError:
                print(
                    f"[ERROR] Backend unreachable at "
                    f"{BACKEND_HOST}:{BACKEND_PORT}"
                )

                error_response = (
                    b"HTTP/1.1 502 Bad Gateway\r\n"
                    b"Content-Length: 0\r\n"
                    b"\r\n"
                )

                client_socket.sendall(error_response)

            except Exception as e:
                print(f"[ERROR] {e}")

        except Exception as e:
            print(f"[EXCEPTION] {e}")

        finally:
            client_socket.close()
            print(f"[DISCONNECT] {client_address[0]}\n")

    def start(self):
        server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        try:
            server_socket.bind(
                (PROXY_HOST, PROXY_PORT)
            )

            server_socket.listen(5)
            server_socket.settimeout(1.0)

            print(
                f"[INFO] Forward Caching Proxy at "
                f"{PROXY_HOST}:{PROXY_PORT}"
            )

            print(
                f"[INFO] Backend: "
                f"{BACKEND_HOST}:{BACKEND_PORT}"
            )

            print(
                f"[INFO] Cache TTL: "
                f"{CACHE_TTL}s"
            )

            print(
                "[INFO] Waiting for requests "
                "(Ctrl+C to stop)\n"
            )

            while True:
                try:
                    client_socket, client_address = (
                        server_socket.accept()
                    )

                    self.handle_client(
                        client_socket,
                        client_address
                    )

                except socket.timeout:
                    continue

        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Proxy stopped")

        finally:
            server_socket.close()


if __name__ == '__main__':
    proxy = CachingForwardProxy()
    proxy.start()