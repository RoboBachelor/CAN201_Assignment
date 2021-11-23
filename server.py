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
        chunk = conn.recv(min(client_msg_len - received_len, chunk_len))
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
    with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
        f.write(role + '\n')
        f.write(file_dict_str)

    # Response to client
    response_bin = file_dict_str.encode()
    response_header_str = "SYNC-RE|%d\n" % (len(response_bin))
    response_header_bin = response_header_str.encode()
    response_header_bin += b'\x00' * (header_len - len(response_header_bin))
    conn.send(response_header_bin)
    conn.sendall(response_bin)

def server_POST_handler(conn:socket, client_header:list):
    file_key = os.path.normpath(client_header[1])
    access_path = os.path.join(share_root, client_header[1])
    file_size = int(client_header[2])

    received_len = 0
    if not os.path.exists(os.path.split(access_path)[0]):
        os.makedirs(os.path.split(access_path)[0])
    with open(access_path + ".downloading", "wb") as f:
        while received_len < file_size:
            chunk = conn.recv(min(file_size - received_len, chunk_len))
            if len(chunk) == 0:
                raise ConnectionError("Received length is zero while receiving file %s" % file_key)
            received_len += len(chunk)
            f.write(chunk)
    print("Server: Successfully received file %s with size %d bytes." % (access_path, file_size))
    if os.path.exists(access_path):
        os.remove(access_path)
    os.rename(access_path + ".downloading", access_path)
    file_dict[file_key][INDEX_STATE] = "sync"
    file_dict[file_key][INDEX_MTIME] = int(os.path.getmtime(access_path) * 1000)
    with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
        f.write(role + '\n')
        f.write(dict_to_str(file_dict))

    # Response to client
    response_str = "POST-RE|%s|%s\n" % (client_header[1], "OK")
    response_bin = response_str.encode()
    response_bin += b'\x00' * (header_len - len(response_bin))
    conn.send(response_bin)

def server_GET_handler(conn:socket, client_header:list):
    file_key = os.path.normpath(client_header[1])
    access_path = os.path.join(share_root, client_header[1])
    file_size = os.path.getsize(access_path)
    sent_size = 0

    # Request header and content
    response_header_str = "GET-RE|%s|%d\n" % (client_header[1], file_size)
    response_header_bin = response_header_str.encode()
    response_header_bin += b'\x00' * (header_len - len(response_header_bin))
    conn.send(response_header_bin)
    with open(access_path, 'rb') as file:
        while sent_size < file_size:
            chunk = file.read(min(file_size - sent_size, chunk_len))
            conn.send(chunk)
            sent_size += len(chunk)
            if file_size != os.path.getsize(os.path.join(share_root, file_key)):
                print("Server: File size changed while sending!")

def server_app(dict_in:dict, share:str):
    global file_dict, share_root
    file_dict = dict_in
    share_root = share

    listening_socket = ('127.0.0.1', 20080)
    sk = socket.socket()            # Create the socket
    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sk.bind(listening_socket)      # Bind the IP and port
    sk.listen(5)                    # Listening for connections
    print('Server: Waiting for the client...')

    while True:
        conn, address = sk.accept()  # 等待连接，此处自动阻塞
        print("Server: Client %s connected." % str(address))
        try:
            while True:     # 一个死循环，直到客户端发送‘exit’的信号，才关闭连接

                client_header_bin = conn.recv(header_len)
                if len(client_header_bin) == 0:
                    print("Server: Received length from client %s is zero." % str(address))
                    break
                client_header = client_header_bin.decode().splitlines()[0].split('|')
                print("Server: Client %s requests with header：%s" % (address, str(client_header)))

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