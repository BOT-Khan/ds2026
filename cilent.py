import socket
import os
import sys

HOST = "127.0.0.1"
PORT = 65432
BUFFER_SIZE = 1024

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((HOST, PORT))
        print(f"[CLIENT] Connected to {HOST}:{PORT}\n")
    except:
        print("Could not connect to server.")
        sys.exit(1)

    while True:
        user_input = input("client> ").strip()
        if not user_input:
            continue

        parts = user_input.split()
        command = parts[0].lower()

        if command in ["quit", "bye"]:
            client.sendall((command + "\n").encode())
            print("Goodbye.")
            break

        elif command == "put":
            if len(parts) < 2:
                print("Usage: put <local_file> [remote_file]")
                continue

            local_path = parts[1]
            remote_name = parts[2] if len(parts) > 2 else os.path.basename(local_path)

            if not os.path.isfile(local_path):
                print("File does not exist.")
                continue

            filesize = os.path.getsize(local_path)

            header = f"put {remote_name} {filesize}\n"
            client.sendall(header.encode())

            response = client.recv(BUFFER_SIZE).decode()
            if response != "OK":
                print("Server rejected upload:", response)
                continue

            print(f"[CLIENT] Uploading {local_path}...")

            with open(local_path, "rb") as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    client.sendall(chunk)

            final = client.recv(BUFFER_SIZE).decode()
            print(final)

        elif command == "get":
            if len(parts) < 2:
                print("Usage: get <remote_file> [local_file]")
                continue

            remote_name = parts[1]
            local_name = parts[2] if len(parts) > 2 else remote_name

            client.sendall(f"get {remote_name}\n".encode())

            response = client.recv(BUFFER_SIZE).decode()

            if response.startswith("ERROR"):
                print(response)
                continue

            _, size = response.split()
            size = int(size)

            print(f"[CLIENT] Downloading {remote_name} ({size} bytes)...")

            received = 0
            with open(local_name, "wb") as f:
                while received < size:
                    chunk = client.recv(min(BUFFER_SIZE, size - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

            print("Download complete.")

        else:
            client.sendall((user_input + "\n").encode())
            response = client.recv(4096).decode()
            print(response)

    client.close()

if __name__ == "__main__":
    main()
