from utils import *

role = "server"
share_root = "unknown"
file_dict = dict()

def server_SYNC_handler(conn:socket, client_header:list):
    # Receive message
    client_msg_len = int(client_header[1])
    client_msg = b''
    received_len = 0
    while received_len < client_msg_len:
        chunk = conn.recv(min(client_msg_len - received_len, chunk_size))
        if len(chunk) == 0:
            raise ConnectionError("Received length is zero while receiving remote file list.")
        client_msg += chunk
        received_len += len(chunk)
    client_dict = str_to_dict(client_msg.decode())
    # print("Server: The client sent the following massages with length %d:\n%s" % (client_msg_len, client_msg.decode()))

    # Handle request
    scan_file(file_dict, share_root, '.')
    handle_remote_dict(file_dict, client_dict)
    file_dict_str = dict_to_str(file_dict)
    save_file_dict(share_root, role, file_dict)

    # Response to client
    response_bin = file_dict_str.encode()
    response_header_str = "SYNC-RE|%d\n" % (len(response_bin))
    response_header_bin = response_header_str.encode()
    response_header_bin += b'\x00' * (header_size - len(response_header_bin))
    conn.send(response_header_bin)
    conn.sendall(response_bin)

def server_POST_handler(conn:socket, client_header:list):
    file_key = os.path.normpath(client_header[1])
    access_path = os.path.join(share_root, client_header[1])
    file_size = int(client_header[2])

    recv_file(conn, access_path, file_size)
    print("Server: Successfully received file %s with size %d bytes." % (access_path, file_size))
    file_dict[file_key][STATE] = "sync"
    file_dict[file_key][MTIME] = int(os.path.getmtime(access_path) * 1000)
    save_file_dict(share_root, role, file_dict)

    # Response to client
    response_str = "POST-RE|%s|%s\n" % (client_header[1], "OK")
    response_bin = response_str.encode()
    response_bin += b'\x00' * (header_size - len(response_bin))
    conn.send(response_bin)

def server_GET_handler(conn:socket, client_header:list):
    file_key = os.path.normpath(client_header[1])
    access_path = os.path.join(share_root, client_header[1])
    file_size = os.path.getsize(access_path)
    sent_size = 0

    # Request header and content
    response_header_str = "GET-RE|%s|%d\n" % (client_header[1], file_size)
    response_header_bin = response_header_str.encode()
    response_header_bin += b'\x00' * (header_size - len(response_header_bin))
    conn.send(response_header_bin)
    with open(access_path, 'rb') as file:
        while sent_size < file_size:
            chunk = file.read(min(file_size - sent_size, chunk_size))
            conn.send(chunk)
            sent_size += len(chunk)
            if file_size != os.path.getsize(os.path.join(share_root, file_key)):
                print("Server: File size changed while sending!")

def server_app(dict_in:dict, share:str):
    global file_dict, share_root
    file_dict = dict_in
    share_root = share

    if not PRINT_DEBUG:
        sys.stdout = open(os.path.join(share_root, ".log.can201"), "w")

    listening_socket = ("0.0.0.0", 20080)
    sk = socket.socket()            # Create the socket
    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sk.bind(listening_socket)      # Bind the IP and port
    sk.listen(5)                    # Listening for connections

    while True:
        print('Server: Waiting for the client...')
        conn, address = sk.accept()  # 等待连接，此处自动阻塞
        print("Server: Client %s connected." % str(address))
        try:
            while True:     # 一个死循环，直到客户端发送‘exit’的信号，才关闭连接

                client_header_bin = conn.recv(header_size)
                if len(client_header_bin) == 0:
                    print("Server: Received length from client %s is zero." % str(address))
                    break
                client_header = client_header_bin.decode().splitlines()[0].split('|')
                print("Server: Client %s requests with header: %s" % (address, str(client_header)))

                if client_header[0] == "SYNC":
                    server_SYNC_handler(conn, client_header)

                elif client_header[0] == 'POST':
                    server_POST_handler(conn, client_header)

                elif client_header[0] == 'GET':
                    server_GET_handler(conn, client_header)

        except Exception as e:
            print("Server:", repr(e))
        conn.close()    # 关闭连接

if __name__ == '__main__':
    server_app()