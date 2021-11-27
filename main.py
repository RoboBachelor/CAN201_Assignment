from client import *
from server import *

def _argparse():
    parser = argparse.ArgumentParser(description="Please specify the remote IP addr and local share root.")
    parser.add_argument('--ip', action='store', required=False, default="127.0.0.1",
                        dest='ip', help='Specify the remote IP address, default: 127.0.0.1')
    parser.add_argument('--root', action='store', required=False, default="./share",
                        dest='root', help='Specify the share dir, default: ./share')
    return parser.parse_args()

if __name__ == '__main__':
    args = _argparse()
    share_root = args.root
    remote_ip = args.ip
    ip_port = (remote_ip, 20080)
    file_dict = dict()

    # Check if the local repository exists.
    if os.path.exists(os.path.join(share_root, ".repository.can201"))\
            and os.path.getsize(os.path.join(share_root, ".repository.can201")) > 0:
        # Local repository exists and has non-zero size.
        # Get the role (client or server) and load the file dict to memory.
        with open(os.path.join(share_root, ".repository.can201"), encoding="utf-8") as f:
            role = f.readline().strip()
            file_dict_str = f.read()
        file_dict = str_to_dict(file_dict_str)
        print("Who am I:", role)

    else:
        # The app is first run in this share dir.
        # Decide who am I by trying to connect the remote server.
        print("Who am I: Test connect to %s" % str(ip_port))
        try:
            test_sock = socket.socket()
            test_sock.connect(ip_port)
            print("Who am I: Client.")
            role = "client"
            test_sock.close()

        except Exception as e:
            print("Who am I:", repr(e))
            print("Who am I: Server.")
            role = "server"

        # Create a new local repository.
        print("Who am I: Creating new repository.")
        scan_file(file_dict, share_root, '.')
        save_repository(share_root, role, file_dict)

    # Start the corresponding APP according the role.
    if role == "client":
        client_app(ip_port, file_dict, share_root)
    elif role == "server":
        server_app(file_dict, share_root)
