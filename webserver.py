import socket
import os
import threading

# Konfigurasi Network Server
HOST = '0.0.0.0'  # Listen di semua interface aktif agar tidak validcontext error
PORT = 8000       # Port akses sesuai topologi kelompok

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

# ==================== [ HANDLER PROTOKOL TCP ] ====================

def handle_tcp_client(client_socket, client_address):
    print(f"[TCP-CONNECT] Koneksi masuk dari Client: {client_address[0]}:{client_address[1]}")
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

        print(f"[TCP-REQUEST] Meminta file: {filepath}")

        if os.path.exists(filepath) and os.path.isfile(filepath):
            content_type = get_content_type(filepath)
            with open(filepath, 'rb') as f:
                content = f.read()
            
            response_header = "HTTP/1.1 200 OK\r\n"
            response_header += f"Content-Type: {content_type}\r\n"
            response_header += f"Content-Length: {len(content)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + content)
            print(f"[TCP-SUCCESS] Berhasil mengirim {filepath}")
        else:
            not_found_msg = "<h1>404 Not Found</h1><p>File tidak ditemukan (TCP Mode).</p>"
            response_header = "HTTP/1.1 404 Not Found\r\n"
            response_header += "Content-Type: text/html\r\n"
            response_header += f"Content-Length: {len(not_found_msg)}\r\n"
            response_header += "Connection: close\r\n\r\n"
            
            client_socket.sendall(response_header.encode('utf-8') + not_found_msg.encode('utf-8'))
            print(f"[TCP-ERROR] 404 Not Found: {filepath}")

    except Exception as e:
        print(f"[TCP-EXCEPTION] Error terjadi: {e}")
    finally:
        client_socket.close()

def listen_tcp(stop_event):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((HOST, PORT))
    tcp_socket.listen(5)
    tcp_socket.settimeout(1.0)
    
    while not stop_event.is_set():
        try:
            client_socket, client_address = tcp_socket.accept()
            tcp_thread = threading.Thread(target=handle_tcp_client, args=(client_socket, client_address))
            tcp_thread.start()
        except socket.timeout:
            continue
    tcp_socket.close()

# ==================== [ HANDLER PROTOKOL UDP ] ====================

def listen_udp(stop_event):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind((HOST, PORT))
    udp_socket.settimeout(1.0)
    
    while not stop_event.is_set():
        try:
            data, client_address = udp_socket.recvfrom(4096)
            request = data.decode('utf-8', errors='ignore').strip()
            if not request:
                continue
                
            print(f"[UDP-CONNECT] Paket QoS masuk dari Client: {client_address[0]}:{client_address[1]}")
            print(f"[UDP-DATA-RAW] Isi request: {request}")
            
            # Pengaman parsing: Jika client mengirim request mentah atau custom flag dari client.py
            # Kita deteksi apakah ada keyword path file di dalamnya
            filepath = os.path.join('HTML', 'index.html') # default fallback
            
            try:
                if 'GET' in request:
                    parts = request.split('\n')[0].split(' ')
                    if len(parts) >= 2 and parts[1] != '/':
                        filepath = os.path.join('HTML', parts[1].lstrip('/'))
                elif '/' in request:
                    # Jika client hanya mengirim path seperti "/index.html" atau "osi.html"
                    filepath = os.path.join('HTML', request.lstrip('/'))
            except Exception:
                pass

            print(f"[UDP-REQUEST] Menghitung estimasi throughput untuk file: {filepath}")

            if os.path.exists(filepath) and os.path.isfile(filepath):
                content_type = get_content_type(filepath)
                with open(filepath, 'rb') as f:
                    content = f.read()
                
                response_header = "HTTP/1.1 200 OK\r\n"
                response_header += f"Content-Type: {content_type}\r\n"
                response_header += f"Content-Length: {len(content)}\r\n\r\n"
                
                # Kirim data balik via Datagram UDP
                udp_socket.sendto(response_header.encode('utf-8') + content, client_address)
                print(f"[UDP-SUCCESS] Paket file berhasil ditembak balik ke client!")
            else:
                not_found_msg = "HTTP/1.1 404 Not Found\r\n\r\n<h1>404 File Not Found (UDP Mode)</h1>"
                udp_socket.sendto(not_found_msg.encode('utf-8'), client_address)
                print(f"[UDP-ERROR] File {filepath} tidak ditemukan")
                
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[UDP-EXCEPTION] Error: {e}")
            
    udp_socket.close()

# ==================== [ MAIN ] ====================

def main():
    stop_event = threading.Event()
    tcp_thread = threading.Thread(target=listen_tcp, args=(stop_event,))
    udp_thread = threading.Thread(target=listen_udp, args=(stop_event,))
    
    try:
        tcp_thread.start()
        udp_thread.start()
        print(f"[SYSTEM] Dual Web Server Aktif di Port {PORT} (Mendukung Multi-mode Client)")
        print("[SYSTEM] Siap menerima pengujian '--mode tcp' dan '--mode udp'\n")
        
        while True:
            tcp_thread.join(timeout=1.0)
            udp_thread.join(timeout=1.0)
            if not tcp_thread.is_alive() and not udp_thread.is_alive():
                break
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Mematikan server secara bersih...")
        stop_event.set()
        tcp_thread.join()
        udp_thread.join()
        print("[SHUTDOWN] Selesai.")

if __name__ == '__main__':
    main()