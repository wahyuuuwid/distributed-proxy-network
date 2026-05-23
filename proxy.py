import socket
import threading
import time

# Proxy Configuration
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8080

# Backend Server (WebServer)
BACKEND_HOST = '127.0.0.1'
BACKEND_PORT = 8000

# Cache Configuration
CACHE_TTL = 300  # 5 minutes

class CachingForwardProxy:
    def __init__(self):
        self.cache = {}  # {request_path: (response_bytes, timestamp)}
        self.lock = threading.Lock()

    def extract_path(self, request_line):
        """Extract request path dari HTTP request line"""
        try:
            parts = request_line.split(' ')
            return parts[1]  # GET /path HTTP/1.1 -> /path
        except:
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
            with self.lock:
                if path and path in self.cache:
                    cached_response, cache_time = self.cache[path]
                    if self.is_cache_valid(cache_time):
                        print(f"[CACHE HIT] {path}")
                        client_socket.sendall(cached_response)
                        client_socket.close()
                        print(f"[DISCONNECT] {client_address[0]}\n")
                        return
                    else:
                        del self.cache[path]

            # Forward to backend
            print(f"[FORWARD] To {BACKEND_HOST}:{BACKEND_PORT}")
            backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                backend_socket.connect((BACKEND_HOST, BACKEND_PORT))
                backend_socket.sendall(request)

                # Receive response from backend
                response = b''
                while True:
                    data = backend_socket.recv(4096)
                    if not data:
                        break
                    response += data
                backend_socket.close()

                # Cache response
                if path:
                    with self.lock:
                        self.cache[path] = (response, time.time())
                    print(f"[CACHED] {path} ({len(response)} bytes)")

                # Send to client
                client_socket.sendall(response)
                print(f"[SUCCESS] {len(response)} bytes sent")

            except ConnectionRefusedError:
                print(f"[ERROR] Backend unreachable at {BACKEND_HOST}:{BACKEND_PORT}")
                error = b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n"
                client_socket.sendall(error)
            except Exception as e:
                print(f"[ERROR] {e}")

        except Exception as e:
            print(f"[EXCEPTION] {e}")
        finally:
            client_socket.close()
            print(f"[DISCONNECT] {client_address[0]}\n")

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((PROXY_HOST, PROXY_PORT))
            server_socket.listen(5)
            server_socket.settimeout(1.0)

            print(f"[INFO] Forward Caching Proxy at {PROXY_HOST}:{PROXY_PORT}")
            print(f"[INFO] Backend: {BACKEND_HOST}:{BACKEND_PORT}")
            print(f"[INFO] Cache TTL: {CACHE_TTL}s")
            print("[INFO] Waiting for requests (Ctrl+C to stop)\n")

            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    thread.start()
                except socket.timeout:
                    continue

        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Proxy stopped")
        finally:
            server_socket.close()

if __name__ == '__main__':
    proxy = CachingForwardProxy()
    proxy.start()
