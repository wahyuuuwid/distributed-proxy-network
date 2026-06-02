import socket
import os
import threading

# Konfigurasi Network Server
HOST = '0.0.0.0'  # IP kamu
PORT = 8000             # Port akses (bisa diakses lewat TCP maupun UDP)

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

# ==================== [ BAGIAN PROTOKOL TCP ] ====================

def handle_tcp_client(client_socket, client_address):
    print(f"[TCP-CONNECT] Koneksi diterima dari IP Client: {client_address[0]}:{client_address[1]}")
    try:
        request = client_socket.recv(4096).decode('utf-8')
        if not request:
            client_socket.close()
            return

        first_line = request.split('\n')[0]
        requested_file = first_line.split(' ')[1]
        
        if requested_file == '/' or requested_file == '/index.html':
            filepath = os.path.join('HTML', 'index.html')
        else:
            clean_path = requested_file.lstrip('/')
            filepath = os.path.join('HTML', clean_path)

        print(f"[TCP-REQUEST] Client meminta path file: {filepath}")

        if os.path.exists(filepath) and os.path.isfile(filepath):
            content_type = get_content_type(filepath)
            with open(filepath, 'rb') as f:
                content = f.read()
            
            response_header = "HTTP/1.1 200 OK\r\n"
            response_header += f"Content-Type: {content_type}\r\n"
            response_header += f"Content-Length: {len(content)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + content)
            print(f"[TCP-SUCCESS] 200 OK Sent - {filepath}")
        else:
            not_found_msg = "<h1>404 Not Found</h1><p>File tidak ditemukan (TCP).</p>"
            response_header = "HTTP/1.1 404 Not Found\r\n"
            response_header += "Content-Type: text/html\r\n"
            response_header += f"Content-Length: {len(not_found_msg)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + not_found_msg.encode('utf-8'))
            print(f"[TCP-ERROR] 404 Not Found - {filepath}")

    except Exception as e:
        print(f"[TCP-EXCEPTION] Kesalahan: {e}")
    finally:
        client_socket.close()
        print(f"[TCP-DISCONNECT] Koneksi dengan {client_address[0]} selesai.\n")


def listen_tcp(stop_event):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((HOST, PORT))
    tcp_socket.listen(5)
    tcp_socket.settimeout(1.0)
    
    print(f"[INFO] TCP Listener aktif di port {PORT}")
    
    while not stop_event.is_set():
        try:
            client_socket, client_address = tcp_socket.accept()
            tcp_thread = threading.Thread(target=handle_tcp_client, args=(client_socket, client_address))
            tcp_thread.start()
        except socket.timeout:
            continue
    tcp_socket.close()

# ==================== [ BAGIAN PROTOKOL UDP ] ====================

def listen_udp(stop_event):
    # SOCK_DGRAM menandakan penggunaan protokol UDP
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind((HOST, PORT))
    udp_socket.settimeout(1.0)
    
    print(f"[INFO] UDP Listener aktif di port {PORT}")
    
    while not stop_event.is_set():
        try:
            # Menerima data dan alamat IP pengirim secara connectionless
            data, client_address = udp_socket.recvfrom(4096)
            request = data.decode('utf-8', errors='ignore')
            if not request:
                continue
                
            print(f"[UDP-CONNECT] Paket masuk dari IP Client: {client_address[0]}:{client_address[1]}")
            
            # Parsing request HTTP sederhana via UDP
            try:
                first_line = request.split('\n')[0]
                requested_file = first_line.split(' ')[1]
                
                if requested_file == '/' or requested_file == '/index.html':
                    filepath = os.path.join('HTML', 'index.html')
                else:
                    filepath = os.path.join('HTML', requested_file.lstrip('/'))
            except IndexError:
                filepath = os.path.join('HTML', 'index.html')

            print(f"[UDP-REQUEST] Client meminta path file: {filepath}")

            if os.path.exists(filepath) and os.path.isfile(filepath):
                content_type = get_content_type(filepath)
                with open(filepath, 'rb') as f:
                    content = f.read()
                
                response_header = "HTTP/1.1 200 OK\r\n"
                response_header += f"Content-Type: {content_type}\r\n"
                response_header += f"Content-Length: {len(content)}\r\n\r\n"
                
                # Mengirim response balik menggunakan sendto karena UDP tidak memiliki session lock
                udp_socket.sendto(response_header.encode('utf-8') + content, client_address)
                print(f"[UDP-SUCCESS] 200 OK Sent via UDP - {filepath}")
            else:
                not_found_msg = "<h1>404 Not Found</h1><p>File tidak ditemukan (UDP).</p>"
                response_header = "HTTP/1.1 404 Not Found\r\n"
                response_header += f"Content-Length: {len(not_found_msg)}\r\n\r\n"
                
                udp_socket.sendto(response_header.encode('utf-8') + not_found_msg.encode('utf-8'), client_address)
                print(f"[UDP-ERROR] 404 Not Found via UDP - {filepath}")
                
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[UDP-EXCEPTION] Kesalahan: {e}")
            
    udp_socket.close()

# ==================== [ MAIN FUNCTION ] ====================

def main():
    stop_event = threading.Event()
    
    # Menjalankan listener TCP dan UDP di thread terpisah agar bisa berjalan berbarengan
    tcp_thread = threading.Thread(target=listen_tcp, args=(stop_event,))
    udp_thread = threading.Thread(target=listen_udp, args=(stop_event,))
    
    try:
        tcp_thread.start()
        udp_thread.start()
        
        print(f"[SYSTEM] Dual Web Server berjalan di IP {HOST} Port {PORT}")
        print("[SYSTEM] Menunggu request... (Tekan Ctrl+C untuk mematikan secara bersih)\n")
        
        # Loop utama agar thread utama tetap hidup menunggu instruksi mati (Ctrl+C)
        while True:
            tcp_thread.join(timeout=1.0)
            udp_thread.join(timeout=1.0)
            if not tcp_thread.is_alive() and not udp_thread.is_alive():
                break
                
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Menerima instruksi penutupan server...")
        stop_event.set()  # Menginstruksikan kedua thread untuk berhenti dari loop tracking
        
        # Menunggu thread menyelesaikan tugas terakhirnya dengan rapi
        tcp_thread.join()
        udp_thread.join()
        print("[SHUTDOWN] Server TCP & UDP berhasil dimatikan secara bersih. Sukses tubesnya!")

if __name__ == '__main__':
    main()