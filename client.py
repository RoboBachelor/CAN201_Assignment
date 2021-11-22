import os

from utils import *

def client_app(ip_port):

    role = "client"
    share_root = ".\share_client"

    file_dict = dict()
    if os.path.exists(os.path.join(share_root, ".filelist.can201")):
        with open(os.path.join(share_root, ".filelist.can201"), encoding="utf-8") as f:
            role = f.readline().strip()
            file_dict_str = f.read()
        file_dict = str_to_dict(file_dict_str)
    else:
        print("Client: New Repository.")

    scan_file(file_dict, share_root, '.')
    with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
        f.write(role + '\n')
        f.write(dict_to_str(file_dict))

    # Infinite loop to connect the server
    while True:

        try:
            sock = socket.socket()     # 创建套接字
            sock.connect(ip_port)      # 连接服务器

            print("Client: Connected to the server.")

            while True:     # 通过一个死循环不断接收用户输入，并发送给服务器
                cmd = input("请输入要发送的信息： ").strip()
                if not cmd:     # 防止输入空信息，导致异常退出
                    continue

                if cmd == "list":

                    # Request
                    scan_file(file_dict, share_root, '.')
                    with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
                        f.write(role + '\n')
                        f.write(dict_to_str(file_dict))

                    msg_bin = dict_to_str(file_dict).encode()
                    msg_len = len(msg_bin)

                    request_str = "SYNC|%d\n" % (msg_len)
                    request_bin = request_str.encode()
                    request_bin += b'\x00' * (header_len - len(request_bin))
                    sock.send(request_bin)
                    sock.sendall(msg_bin)

                    # Response
                    server_header = sock.recv(header_len).decode().splitlines()[0].split('|')
                    server_msg = b''
                    if server_header[0] == "SYNC-RE":
                        server_msg_len = int(server_header[1])
                        received_len = 0
                        while received_len < server_msg_len:
                            chunk = sock.recv(min(server_msg_len - received_len, chunk_len))
                            server_msg += chunk
                            received_len += len(chunk)
                            if len(chunk) == 0:
                                print("Client: Error: Received length is zero!")
                        server_dict = str_to_dict(server_msg.decode())
                        print("服务器的响应头为：%s" % (str(server_header)))
                        print("消息长度：%d, 消息数据：\n%s" % (server_msg_len, str(server_dict)))

                        # Handle Response
                        handle_remote_dict(file_dict, server_dict)
                        with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
                            f.write(role + '\n')
                            f.write(dict_to_str(file_dict))
                        print("本地数据：\n%s" % (str(file_dict)))

                elif cmd == "send":
                    for file_key, file_record in file_dict.items():
                        if file_record[INDEX_STATE] == "local":
                            # Request header and content
                            request_str = "POST|%s|%d\n" % (file_record[INDEX_KEY], os.path.getsize(os.path.join(share_root, file_key)))
                            request_bin = request_str.encode()
                            request_bin += b'\x00' * (header_len - len(request_bin))
                            sock.send(request_bin)
                            with open(os.path.join(share_root, file_key), 'rb') as file:
                                sock.sendall(file.read())

                            # Response
                            server_header = sock.recv(header_len).decode().splitlines()[0].split('|')
                            if server_header[2] == 'OK':
                                print("文件 %s 发送成功" % (server_header[1]))
                                file_dict[file_key][INDEX_STATE] = "sync"
                                with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
                                    f.write(role + '\n')
                                    f.write(dict_to_str(file_dict))
                            if server_header[2] == 'FAIL':
                                print("文件 %s 发送失败" % (server_header[1]))

                elif cmd == "get":
                    for file_key, file_record in file_dict.items():
                        if file_record[INDEX_STATE] == "remote":
                            access_path = os.path.join(share_root, file_key)
                            # Request header
                            request_str = "GET|%s\n" % (file_record[INDEX_KEY])
                            request_bin = request_str.encode()
                            request_bin += b'\x00' * (header_len - len(request_bin))
                            sock.send(request_bin)

                            # Response header
                            server_header = sock.recv(header_len).decode().splitlines()[0].split('|')
                            file_size = int(server_header[2])

                            # Response message
                            received_len = 0
                            if not os.path.exists(os.path.split(access_path)[0]):
                                os.makedirs(os.path.split(access_path)[0])
                            with open(access_path + ".downloading", "wb") as f:
                                while received_len < file_size:
                                    chunk = sock.recv(min(file_size - received_len, chunk_len))
                                    received_len += len(chunk)
                                    f.write(chunk)
                                    if len(chunk) == 0:
                                        print("Client: Error: Received length is zero!")
                            print("Client: Successfully received file %s with size %d bytes." % (access_path, file_size))
                            if os.path.exists(access_path):
                                os.remove(access_path)
                            os.rename(access_path + ".downloading", access_path)
                            file_dict[file_key][INDEX_STATE] = "sync"
                            file_dict[file_key][INDEX_MTIME] = int(os.path.getmtime(access_path) * 1000)
                            with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
                                f.write(role + '\n')
                                f.write(dict_to_str(file_dict))

                else:
                    sock.send(cmd.encode())
                    server_reply = sock.recv(4096)
                    print(server_reply.decode())

            sock.close()
        except Exception as e:
            print("Client:", repr(e))
            print("Client: Something Error. Waiting for 1 sec and connect again.")
            time.sleep(1)


if __name__ == '__main__':
    ip_port = ('127.0.0.1', 9999)
    client_app(ip_port)