import socket
import os
import threading

# Konfigurasi Network Server
HOST = '127.0.0.1'  # Localhost
PORT = 8000        # Port sesuai di halaman Config UI

def handle_client(client_socket, client_address):
    print(f"[CONNECT] Koneksi diterima dari IP Client: {client_address[0]}:{client_address[1]}")
    
    try:
        # Menerima request dari browser (max buffer 4096 bytes)
        request = client_socket.recv(4096).decode('utf-8')
        if not request:
            client_socket.close()
            return

        # Parsing baris pertama request untuk mengambil file yang diminta
        first_line = request.split('\n')[0]
        requested_file = first_line.split(' ')[1]
        
        # Jika client mengakses akar (/) atau localhost:8080, arahkan ke index.html
        if requested_file == '/' or requested_file == '/index.html':
            filename = 'index.html'
        else:
            filename = requested_file.lstrip('/')

        print(f"[REQUEST] Client meminta asset: /{filename}")

        # Mengecek apakah file yang diminta ada di dalam folder
        if os.path.exists(filename) and os.path.isfile(filename):
            with open(filename, 'rb') as f:
                content = f.read()
            
            # Membuat HTTP Response Header Sukses (200 OK)
            response_header = "HTTP/1.1 200 OK\r\n"
            response_header += "Content-Type: text/html; charset=utf-8\r\n"
            response_header += f"Content-Length: {len(content)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + content)
            print(f"[SUCCESS] HTTP/1.1 200 OK Served - /{filename} ({len(content)} bytes)")
        else:
            # Jika file tidak ditemukan, kirim Response HTTP 404 Not Found
            not_found_msg = "<h1>404 Not Found</h1><p>File yang kamu cari tidak ada di Web Server ini.</p>"
            response_header = "HTTP/1.1 404 Not Found\r\n"
            response_header += "Content-Type: text/html\r\n"
            response_header += f"Content-Length: {len(not_found_msg)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + not_found_msg.encode('utf-8'))
            print(f"[ERROR] HTTP/1.1 404 Not Found - /{filename}")

    except Exception as e:
        print(f"[EXCEPTION] Terjadi kesalahan data: {e}")
    finally:
        client_socket.close()
        print(f"[DISCONNECT] Koneksi dengan {client_address[0]} selesai.\n")

def main():
    # Membuat socket TCP/IP untuk Web Server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Membuat socket TCP/IP
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        
        # Cek Ctrl+C 
        server_socket.settimeout(1.0) 
        
        print(f"[INFO] Web Server berhasil dijalankan di http://{HOST}:{PORT}")
        print("[INFO] Menunggu request masuk dari client browser (Tekan Ctrl+C untuk matiin)...\n")
        
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_thread.start()
            except socket.timeout:
                # Mengabaikan timeout internal 1 detik agar loop terus berjalan mencari Ctrl+C
                continue
                
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Mematikan sistem Web Server. Sampai jumpa!")
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()