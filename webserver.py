import socket
import os
import threading

# Konfigurasi Network Server
HOST = '127.0.0.1'  # Localhost
PORT = 8080        # Port akses

# Fungsi untuk mendeteksi tipe file (MIME Type) berdasarkan eksternsinya
def get_content_type(filepath):
    if filepath.endswith('.html') or filepath.endswith('.htm'):
        return "text/html; charset=utf-8"
    elif filepath.endswith('.css'):
        return "text/css"
    elif filepath.endswith('.png'):
        return "image/png"
    elif filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
        return "image/jpeg"
    elif filepath.endswith('.mp4'):
        return "video/mp4"
    else:
        return "application/octet-stream"

def handle_client(client_socket, client_address):
    print(f"[CONNECT] Koneksi diterima dari IP Client: {client_address[0]}:{client_address[1]}")
    
    try:
        request = client_socket.recv(4096).decode('utf-8')
        if not request:
            client_socket.close()
            return

        # Parsing file yang diminta oleh browser
        first_line = request.split('\n')[0]
        requested_file = first_line.split(' ')[1]
        
        # Atur routing utama ke dalam folder HTML
        if requested_file == '/' or requested_file == '/index.html':
            filepath = os.path.join('HTML', 'index.html')
        else:
            # Mengamankan path dan mengarahkannya ke dalam subfolder 'HTML'
            clean_path = requested_file.lstrip('/')
            filepath = os.path.join('HTML', clean_path)

        print(f"[REQUEST] Client meminta path file: {filepath}")

        # Mengecek apakah file beneran ada di folder HTML
        if os.path.exists(filepath) and os.path.isfile(filepath):
            # Tentukan tipe konten (HTML/CSS/Gambar/Video)
            content_type = get_content_type(filepath)
            
            # Membaca konten file secara biner (rb) agar support gambar/video
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Membuat HTTP Response Header yang sesuai dengan spek browser
            response_header = "HTTP/1.1 200 OK\r\n"
            response_header += f"Content-Type: {content_type}\r\n"
            response_header += f"Content-Length: {len(content)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            # Kirim header beserta data binernya
            client_socket.sendall(response_header.encode('utf-8') + content)
            print(f"[SUCCESS] 200 OK Sent - {filepath} ({content_type})")
        else:
            # Respons 404 jika file tidak ditemukan
            not_found_msg = "<h1>404 Not Found</h1><p>File tugas jarkom tidak ditemukan di folder HTML.</p>"
            response_header = "HTTP/1.1 404 Not Found\r\n"
            response_header += "Content-Type: text/html\r\n"
            response_header += f"Content-Length: {len(not_found_msg)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + not_found_msg.encode('utf-8'))
            print(f"[ERROR] 404 Not Found - {filepath}")

    except Exception as e:
        print(f"[EXCEPTION] Terjadi kesalahan data: {e}")
    finally:
        client_socket.close()
        print(f"[DISCONNECT] Koneksi dengan {client_address[0]} selesai.\n")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        server_socket.settimeout(1.0) 
        
        print(f"[INFO] Web Server Jarkom berjalan di http://{HOST}:{PORT}")
        print("[INFO] Menunggu request dari browser... (Tekan Ctrl+C untuk mematikan)\n")
        
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_thread.start()
            except socket.timeout:
                continue
                
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Mematikan sistem Web Server. Semangat tubesnya!")
    finally:
        server_socket.close()

if __name__ == '__main__':
    main()