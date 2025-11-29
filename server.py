import socket
import os

HOST = "0.0.0.0"
PORT = 65432
BUFFER_SIZE = 1024
SERVER_DIR = "./server_files"

os.makedirs(SERVER_DIR, exist_ok=True)

def send(conn, msg):
    conn.sendall(msg.encode('utf-8'))

def recv_line(conn):
    """Receive a line ending with \n."""
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(1)
        if not chunk:
            break
        data += chunk
    return data.decode().strip()

def handle_put(conn, parts):
    if len(parts) < 3:
        send(conn, "ERROR Missing filename or filesize\n")
        return

    filename = parts[1]
    filesize = int(parts[2])
    save_path = os.path.join(SERVER_DIR, filename)

    send(conn, "OK")

    with open(save_path, "wb") as f:
        remaining = filesize
        while remaining > 0:
            chunk = conn.recv(min(BUFFER_SIZE, remaining))
            if not chunk:
                break
            f.write(chunk)
            remaining -= len(chunk)

    print(f"[SERVER] Received file: {filename}")
    send(conn, "Upload complete\n")

def handle_get(conn, parts):
    if len(parts) < 2:
        send(conn, "ERROR Missing filename\n")
        return

    filename = parts[1]
    file_path = os.path.join(SERVER_DIR, filename)

    if not os.path.isfile(file_path):
        send(conn, "ERROR File not found\n")
        return

    filesize = os.path.getsize(file_path)
    send(conn, f"OK {filesize}")

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            conn.sendall(chunk)

def main():
    print(f"[SERVER] Starting on {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(1)
        print("[SERVER] Waiting for connection...")

        conn, addr = server.accept()
        with conn:
            print(f"[SERVER] Client connected: {addr}")

            while True:
                data = recv_line(conn)
                if not data:
                    print("[SERVER] Client disconnected")
                    break

                parts = data.split()
                command = parts[0].lower()
                print(f"[SERVER] Command received: {data}")

                if command in ["quit", "bye"]:
                    send(conn, "Goodbye\n")
                    break

                elif command == "ls":
                    files = "\n".join(os.listdir(SERVER_DIR))
                    send(conn, files + "\n")

                elif command == "delete":
                    if len(parts) < 2:
                        send(conn, "ERROR Missing filename\n")
                        continue
                    target = os.path.join(SERVER_DIR, parts[1])
                    if os.path.isfile(target):
                        os.remove(target)
                        send(conn, "File deleted\n")
                    else:
                        send(conn, "ERROR File not found\n")

                elif command == "rename":
                    if len(parts) < 3:
                        send(conn, "ERROR Missing filenames\n")
                        continue
                    old = os.path.join(SERVER_DIR, parts[1])
                    new = os.path.join(SERVER_DIR, parts[2])
                    if os.path.isfile(old):
                        os.rename(old, new)
                        send(conn, "File renamed\n")
                    else:
                        send(conn, "ERROR File not found\n")

                elif command == "put":
                    handle_put(conn, parts)

                elif command == "get":
                    handle_get(conn, parts)

                else:
                    send(conn, "ERROR Unknown command\n")

    print("[SERVER] Shutdown")

if __name__ == "__main__":
    main()
