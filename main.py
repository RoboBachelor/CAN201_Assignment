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

    if os.path.exists(os.path.join(share_root, ".filelist.can201")):
        # Filelist exists.
        with open(os.path.join(share_root, ".filelist.can201"), encoding="utf-8") as f:
            role = f.readline().strip()
            file_dict_str = f.read()
        file_dict = str_to_dict(file_dict_str)
        print("Who am I:", role)
    else:
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

        print("Who am I: Creating new repository.")
        scan_file(file_dict, share_root, '.')
        with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
            f.write(role + '\n')
            f.write(dict_to_str(file_dict))

    if role == "client":
        client_app(ip_port, file_dict, share_root)
    elif role == "server":
        server_app(file_dict, share_root)

