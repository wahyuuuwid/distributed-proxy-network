import socket
import sys
import time

# Konfigurasi Client
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8080

# Default langsung tanpa argumen
serverName = '127.0.0.1'  # Ganti dengan IP server jika tidak di localhost
serverPort = 8080
filePath = '/index.html'

    for i in range(num_requests):
        try:
            # Connect ke proxy
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"\n[REQUEST {i+1}] Connecting to proxy {PROXY_HOST}:{PROXY_PORT}")

            client_socket.connect((PROXY_HOST, PROXY_PORT))

            # Create HTTP request
            http_request = f"GET {path} HTTP/1.1\r\nHost: {PROXY_HOST}\r\nConnection: close\r\n\r\n"

            print(f"[REQUEST {i+1}] Sending: GET {path} HTTP/1.1")
            start_time = time.time()

            # Send request
            client_socket.sendall(http_request.encode('utf-8'))

            # Receive response
            response = b''
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                response += data

            elapsed_time = time.time() - start_time

            # Parse response
            response_str = response.decode('utf-8', errors='ignore')
            response_lines = response_str.split('\n')
            status_line = response_lines[0]

            # Extract Content-Length
            content_length = 0
            for line in response_lines[1:]:
                if line.startswith('Content-Length'):
                    content_length = int(line.split(':')[1].strip())
                    break

            print(f"[RESPONSE {i+1}] {status_line}")
            print(f"[RESPONSE {i+1}] Content-Length: {content_length} bytes")
            print(f"[RESPONSE {i+1}] Time: {elapsed_time:.4f}s")

            # Show cache status (first request slower, subsequent faster if cached)
            if i == 0:
                print(f"[CACHE] First request (no cache yet)")
            else:
                print(f"[CACHE] Subsequent request (should be faster if cached)")

            client_socket.close()

            # Delay between requests
            if i < num_requests - 1:
                time.sleep(1)

        except ConnectionRefusedError:
            print(f"[ERROR {i+1}] Cannot connect to proxy at {PROXY_HOST}:{PROXY_PORT}")
            print("[ERROR] Make sure proxy is running!")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR {i+1}] {e}")

    print("\n" + "=" * 60)
    print("[CLIENT] Test completed!")

def main():
    print("[INFO] HTTP Forward Caching Proxy Client Test")
    print("[INFO] This client sends multiple requests to test caching\n")

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "/"

    # Send 3 requests: 1st uncached, 2nd+3rd should be cached
    send_request(path=path, num_requests=3)

if __name__ == '__main__':
    main()
