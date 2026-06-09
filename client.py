from socket import *

BUFFER_SIZE = 4096

# Default langsung tanpa argumen
serverName = '127.0.0.1'  # Ganti dengan IP server jika tidak di localhost
serverPort = 8080
filePath = '/index.html'

clientSocket = socket(AF_INET, SOCK_STREAM)

# Koneksi ke server
try:
    print(f"Connecting to {serverName}:{serverPort}...")
    clientSocket.connect((serverName, serverPort))
except ConnectionRefusedError:
    print(f"[ERROR] Tidak bisa konek ke {serverName}:{serverPort}. Pastikan server sudah berjalan.")
    exit(1)

# Kirim HTTP Request
requestMessage = f"GET {filePath} HTTP/1.1\r\nHost: {serverName}\r\nConnection: close\r\n\r\n"
clientSocket.send(requestMessage.encode())

# Terima response
response = b""
while True:
    data = clientSocket.recv(BUFFER_SIZE)
    if not data:
        break
    response += data

clientSocket.close()

# Pisahkan header dan body
print("\nResponse from server:\n")
try:
    header_end = response.index(b"\r\n\r\n")
    header = response[:header_end].decode()
    body = response[header_end + 4:].decode(errors='replace')

    print("--- RESPONSE HEADER ---")
    print(header)
    print("\n--- RESPONSE BODY ---")
    print(body)
except ValueError:
    print(response.decode(errors='replace'))