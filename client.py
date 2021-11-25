from utils import *

role = "client"
share_root = "unknown"
file_dict = dict()


def client_sync(sock: socket):
    """
    Synchronize the file list between local and server.
    :param sock: socket object.
    :return: None
    """

    # First, re-scan the local shared dir.
    scan_file(file_dict, share_root, '.')
    save_repository(share_root, role, file_dict)

    # Request to the server.
    msg_bin = dict_to_str(file_dict).encode()
    msg_len = len(msg_bin)

    request_str = "SYNC|%d\n" % (msg_len)
    request_bin = request_str.encode()
    request_bin += b'\x00' * (header_size - len(request_bin))
    sock.send(request_bin)
    sock.sendall(msg_bin)

    # Get response from server.
    server_header = sock.recv(header_size).decode().splitlines()[0].split('|')
    if len(server_header) == 0:
        return
    if server_header[0] == "SYNC-RE":
        server_msg_len = int(server_header[1])
        server_dict = recv_dict(sock, server_msg_len)
        print("Client: Response header for SYNC from the server is: %s" % (str(server_header)))

        # Handle Response
        handle_remote_dict(file_dict, server_dict)
        save_repository(share_root, role, file_dict)


def client_sendall(sock: socket):
    """
    Send all of the files which exists in local but does not exist in remote.
    :param sock: socket object.
    :return: None
    """
    for file_key, file_record in file_dict.items():
        if file_record[STATE] == "local":
            # For each file, create a "POST" request to the server.
            access_path = os.path.join(share_root, file_key)
            file_size = os.path.getsize(access_path)

            request_str = "POST|%s|%d\n" % (file_record[KEY], file_size)
            request_bin = request_str.encode()
            request_bin += b'\x00' * (header_size - len(request_bin))
            sock.send(request_bin)

            send_file(sock, access_path, file_size)
            # We can detect whether we sent a file which is still writing to the local shared dir.
            if file_size != os.path.getsize(os.path.join(share_root, file_key)):
                print("Client: File size changed while sending!")

            # Response form the server.
            server_header = sock.recv(header_size).decode().splitlines()[0].split('|')
            if server_header[2] == 'OK':
                print("Client: File %s has been successfully sent." % (server_header[1]))
                file_dict[file_key][STATE] = "sync"
                save_repository(share_root, role, file_dict)


def client_getall(sock:socket):
    """
    Download all of the files which exists in remote but does not exist locally.
    :param sock: socket object.
    :return: None.
    """
    for file_key, file_record in file_dict.items():
        if file_record[STATE] == "remote":
            access_path = os.path.join(share_root, file_key)
            # Request header
            request_str = "GET|%s\n" % (file_record[KEY])
            request_bin = request_str.encode()
            request_bin += b'\x00' * (header_size - len(request_bin))
            sock.send(request_bin)

            # Response header
            server_header = sock.recv(header_size).decode().splitlines()[0].split('|')
            if len(server_header) == 0:
                return
            file_size = int(server_header[2])

            # Response message
            recv_file(sock, access_path, file_size)
            print("Client: Successfully received file %s with size %d bytes." % (access_path, file_size))
            file_dict[file_key][STATE] = "sync"
            file_dict[file_key][MTIME] = int(os.path.getmtime(access_path) * 1000)
            save_repository(share_root, role, file_dict)


def client_app(server_ip_port, dict_in:dict, share:str):
    """
    This is the entrance of the client app. The client app will run infinitely.
    :param server_ip_port: Server IP and listening port
    :param dict_in: Initialized file dict.
    :param share: Root of shared dir.
    :return: None.
    """
    global file_dict, share_root
    file_dict = dict_in
    share_root = share

    if not PRINT_DEBUG:
        sys.stdout = open(os.path.join(share_root, ".log.can201"), "w")

    # Infinite loop to connect the server, unless the client is killed.
    while True:
        try:
            sock = socket.socket()          # Create socket
            sock.connect(server_ip_port)    # Connect to the server
            print("Client: Connected to the server.")

            # Infinite loop: scan local file and sync with the server.
            # If error occurred during the following steps, close the socket and connect again.
            while True:
                client_sync(sock)
                client_sendall(sock)
                client_getall(sock)
                time.sleep(0.1)
            sock.close()

        except Exception as e:
            sock.close()
            print("Client:", repr(e))
            print("Client: Something Error. Waiting for 1 sec and connect again.")
            time.sleep(0.1)
