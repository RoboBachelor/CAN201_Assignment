from utils import *

role = "server"
share_root = "unknown"
file_dict = dict()


def server_SYNC_handler(conn: socket, client_header: list):
    """
    Handler for "SYNC" request from client, i.e., exchange and synchronize the file list between client and server.
    :param conn: Connected socket object.
    :param client_header: Request header from client.
    :return: None
    """

    # Receive the message: the full list of the file in client.
    client_msg_len = int(client_header[1])
    client_dict = recv_dict(conn, client_msg_len)

    # Handle request
    scan_file(file_dict, share_root, '.')
    handle_remote_dict(file_dict, client_dict)
    file_dict_str = dict_to_str(file_dict)
    save_repository(share_root, role, file_dict)

    # Response to client
    response_bin = file_dict_str.encode()
    response_header_str = "SYNC-RE|%d\n" % (len(response_bin))
    response_header_bin = response_header_str.encode()
    response_header_bin += b'\x00' * (header_size - len(response_header_bin))
    conn.send(response_header_bin)
    conn.sendall(response_bin)


def server_POST_handler(conn:socket, client_header:list):
    """
    Handler for "POST" request from client. Receive a single file from client.
    :param conn: socket object.
    :param client_header: contains filename and size.
    :return: None
    """
    file_key = os.path.normpath(client_header[1])
    access_path = os.path.join(share_root, client_header[1])
    file_size = int(client_header[2])

    recv_file(conn, access_path, file_size)
    print("Server: Successfully received file %s with size %d bytes." % (access_path, file_size))
    file_dict[file_key][STATE] = "sync"
    file_dict[file_key][MTIME] = int(os.path.getmtime(access_path) * 1000)
    save_repository(share_root, role, file_dict)

    # Response to client
    response_str = "POST-RE|%s|%s\n" % (client_header[1], "OK")
    response_bin = response_str.encode()
    response_bin += b'\x00' * (header_size - len(response_bin))
    conn.send(response_bin)


def server_GET_handler(conn:socket, client_header:list):
    """
    Handler for "GET" request from client. Send a requested file.
    :param conn: socket object.
    :param client_header: file path
    :return: None
    """
    file_key = os.path.normpath(client_header[1])
    access_path = os.path.join(share_root, client_header[1])
    file_size = os.path.getsize(access_path)

    # Response header
    response_header_str = "GET-RE|%s|%d\n" % (client_header[1], file_size)
    response_header_bin = response_header_str.encode()
    response_header_bin += b'\x00' * (header_size - len(response_header_bin))
    conn.send(response_header_bin)

    # Send the requested file
    send_file(conn, access_path, file_size)
    if file_size != os.path.getsize(os.path.join(share_root, file_key)):
        print("Server: File size changed while sending!")


def server_app(dict_in:dict, share:str):
    """
    This is the entrance of the server app. The server listens and responses the requests from client passively.
    This function runs infinitely and will not return unless killed.

    :param dict_in: Initialized file dictionary in main function
    :param share: Root of shared dir
    :return: None
    """
    # Init the global variables.
    global file_dict, share_root
    file_dict = dict_in
    share_root = share

    if not PRINT_DEBUG:
        # Save the printed message to file to improve the performance a little bit.
        sys.stdout = open(os.path.join(share_root, ".log.can201"), "w")

    listening_socket = ("0.0.0.0", 20080)
    sk = socket.socket()            # Create the socket
    sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sk.bind(listening_socket)       # Bind the IP and port
    sk.listen(5)                    # Listening for connections

    # Accept for infinite number of times, since the client may terminated.
    while True:
        print('Server: Waiting for the client...')
        conn, address = sk.accept() # Waiting for a client, and blocking here.
        print("Server: Client %s connected." % str(address))
        try:
            # Response the infinite number of requests from the client.
            # Once the connection is established, it is keep-alive.
            while True:
                # First, receive the application layer header from the client.
                client_header_bin = conn.recv(header_size)
                if len(client_header_bin) == 0:
                    print("Server: Received length from client %s is zero." % str(address))
                    break
                client_header = client_header_bin.decode().splitlines()[0].split('|')
                print("Server: Client %s requests with header: %s" % (address, str(client_header)))

                # Then call the corresponding request handler.
                if client_header[0] == "SYNC":
                    server_SYNC_handler(conn, client_header)

                elif client_header[0] == 'POST':
                    server_POST_handler(conn, client_header)

                elif client_header[0] == 'GET':
                    server_GET_handler(conn, client_header)

        # Close the current connection and re-accept a client if any error occurs.
        except Exception as e:
            print("Server:", repr(e))
        conn.close()
        # After close(), the server will block in accept() and wait for the client connects again.
