import socket
import os
import threading

# Konfigurasi Port Jaringan Sesuai Spesifikasi Modul
HOST = '0.0.0.0'
TCP_PORT = 8000  # Port untuk Web Server & valid file request via Proxy
UDP_PORT = 9000  # Port untuk pengujian UDP Echo

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

# ==================== [ HANDLER PROTOKOL TCP (PORT 8000) ] ====================

def handle_tcp_client(client_socket, client_address):
    # Poin 5: Menampilkan pembuatan thread baru untuk tiap koneksi secara eksplisit di log
    current_thread_name = threading.current_thread().name
    print(f"[THREAD-CREATE] {current_thread_name} dialokasikan untuk melayani Client: {client_address[0]}:{client_address[1]}")
    
    try:
        request = client_socket.recv(4096).decode('utf-8')
        if not request:
            return

        # Parsing request HTTP
        first_line = request.split('\n')[0]
        parts = first_line.split(' ')
        
        if len(parts) >= 2:
            requested_file = parts[1]
        else:
            requested_file = '/'
        
        if requested_file == '/' or requested_file == '/index.html':
            filepath = os.path.join('HTML', 'index.html')
        else:
            filepath = os.path.join('HTML', requested_file.lstrip('/'))

        # Mencatat log aktivitas IP Proxy / Client
        print(f"[{current_thread_name}-REQUEST] Menerima permintaan berkas: {filepath} dari IP: {client_address[0]}")

        # Permintaan Berkas Valid (200 OK)
        if os.path.exists(filepath) and os.path.isfile(filepath):
            content_type = get_content_type(filepath)
            with open(filepath, 'rb') as f:
                content = f.read()
            
            response_header = "HTTP/1.1 200 OK\r\n"
            response_header += f"Content-Type: {content_type}\r\n"
            response_header += f"Content-Length: {len(content)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + content)
            print(f"[{current_thread_name}-SUCCESS] Response 200 OK + konten dikirim ke {client_address[0]}")
        
        # Permintaan Berkas Tidak Ditemukan (404 Not Found)
        else:
            not_found_msg = "<h1>404 Not Found</h1><p>File tidak ditemukan di Web Server.</p>"
            response_header = "HTTP/1.1 404 Not Found\r\n"
            response_header += "Content-Type: text/html\r\n"
            response_header += f"Content-Length: {len(not_found_msg)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + not_found_msg.encode('utf-8'))
            print(f"[{current_thread_name}-GALAT] Response 404 Not Found dicatat untuk file: {filepath}")

    except Exception as e:
        print(f"[{current_thread_name}-EXCEPTION] Galat internal: {e}")
    finally:
        client_socket.close()
        print(f"[THREAD-TERMINATE] {current_thread_name} selesai bertugas.\n")

def listen_tcp(stop_event):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((HOST, TCP_PORT))
    tcp_socket.listen(10)
    tcp_socket.settimeout(1.0)
    
    thread_counter = 1
    while not stop_event.is_set():
        try:
            client_socket, client_address = tcp_socket.accept()
            # Membuat nama thread dinamis untuk mempermudah penilaian konkurensi di log
            t_name = f"ThreadClient-{thread_counter}"
            tcp_thread = threading.Thread(target=handle_tcp_client, args=(client_socket, client_address), name=t_name)
            tcp_thread.start()
            thread_counter += 1
        except socket.timeout:
            continue
    tcp_socket.close()

# ==================== [ HANDLER PROTOKOL UDP ECHO (PORT 9000) ] ====================

def listen_udp(stop_event):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind((HOST, UDP_PORT))
    udp_socket.settimeout(1.0)
    
    while not stop_event.is_set():
        try:
            # Pengujian UDP Echo
            data, client_address = udp_socket.recvfrom(4096)
            if not data:
                continue
                
            print(f"[UDP-ECHO] Menerima paket dari {client_address[0]}:{client_address[1]}")
            print(f"[UDP-PAYLOAD] Data: {data}")
            
            # Memantulkan kembali data/payload yang identik 100% tanpa modifikasi (Echo)
            udp_socket.sendto(data, client_address)
            print(f"[UDP-SUCCESS] Memantulkan kembali payload identik (echo) ke client.\n")
                
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[UDP-EXCEPTION] Galat: {e}")
            
    udp_socket.close()

# ==================== [ MAIN ENGINE ] ====================

def main():
    stop_event = threading.Event()
    tcp_thread = threading.Thread(target=listen_tcp, args=(stop_event,), name="TCPListener")
    udp_thread = threading.Thread(target=listen_udp, args=(stop_event,), name="UDPListener")
    
    try:
        tcp_thread.start()
        udp_thread.start()
        
        # Poin 1: Output log awal wajib sesuai format instruksi praktikum
        print(f'Log: "Server running on port {TCP_PORT}/{UDP_PORT}", thread pool siap')
        print("[SYSTEM] Tekan Ctrl+C untuk mematikan secara bersih...\n")
        
        while True:
            tcp_thread.join(timeout=1.0)
            udp_thread.join(timeout=1.0)
            if not tcp_thread.is_alive() and not udp_thread.is_alive():
                break
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Menutup semua socket dan mematikan server...")
        stop_event.set()
        tcp_thread.join()
        udp_thread.join()
        print("[SHUTDOWN] Server mati dengan bersih.")

if __name__ == '__main__':
    main()