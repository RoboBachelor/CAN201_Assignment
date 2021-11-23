from client import *
from server import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=str, help="Shared dir")
    args = parser.parse_args()
    share_root = args.root

    remote_ip = "127.0.0.1"
    ip_port = (remote_ip, 20080)
    file_dict = dict()

    if os.path.exists(os.path.join(share_root, ".filelist.can201")):
        # Filelist exists.
        with open(os.path.join(share_root, ".filelist.can201"), encoding="utf-8") as f:
            role = f.readline().strip()
            file_dict_str = f.read()
        file_dict = str_to_dict(file_dict_str)
        print("Who am I:", role)
    else:
        print("Who am I: Checking.")
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

        print("Who am I: Creating new repository.")
        scan_file(file_dict, share_root, '.')
        with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
            f.write(role + '\n')
            f.write(dict_to_str(file_dict))

    if role == "client":
        client_app(ip_port, file_dict, share_root)
    elif role == "server":
        server_app(file_dict, share_root)

