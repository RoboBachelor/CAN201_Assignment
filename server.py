import os

from utils import *

share_root = ".\share_server"
role = "server"
ip_port = ('127.0.0.1', 9999)

file_dict = dict()
if os.path.exists(os.path.join(share_root, ".filelist.can201")):
    with open(os.path.join(share_root, ".filelist.can201"), 'r', encoding="utf-8") as f:
        role = f.readline().strip()
        file_dict_str = f.read()
    file_dict = str_to_dict(file_dict_str)
else:
    print("Server: New Repository.")

scan_file(file_dict, share_root, '.')
file_dict_str = dict_to_str(file_dict)
with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
    f.write(role + '\n')
    f.write(file_dict_str)


sk = socket.socket()            # 创建套接字
sk.bind(ip_port)                # 绑定服务地址
sk.listen(5)                    # 监听连接请求
print('启动socket服务，等待客户端连接...')

while True:
    conn, address = sk.accept()  # 等待连接，此处自动阻塞
    try:
        while True:     # 一个死循环，直到客户端发送‘exit’的信号，才关闭连接

            client_header_bin = conn.recv(header_len)
            client_header = client_header_bin.decode().splitlines()[0].split()
            print("客户端%s的请求头为：%s" % (address, str(client_header)))
            if client_header[0] == "SYNC":
                # Receive message
                client_msg_len = int(client_header[1])
                client_msg = b''
                received_len = 0
                while received_len < client_msg_len:
                    chunk = conn.recv(min(client_msg_len - received_len, chunk_len))
                    client_msg += chunk
                    received_len += len(chunk)
                client_dict = str_to_dict(client_msg.decode())
                print("消息长度：%d, 消息数据：\n%s" % (client_msg_len, client_msg.decode()))

                # Handle request
                scan_file(file_dict, share_root, '.')
                handle_remote_dict(file_dict, client_dict)
                file_dict_str = dict_to_str(file_dict)
                with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
                    f.write(role + '\n')
                    f.write(file_dict_str)

                # Response to client
                response_bin = file_dict_str.encode()
                response_header_str = "SYNC-RE %d\n" % (len(response_bin))
                response_header_bin = response_header_str.encode()
                response_header_bin += b'\x00' * (header_len - len(response_header_bin))
                conn.send(response_header_bin)
                conn.sendall(response_bin)

            elif client_header[0] == 'POST':
                file_key = os.path.normpath(client_header[1])
                access_path = os.path.join(share_root, client_header[1])
                file_size = int(client_header[2])
                status = ''

                received_len = 0
                if not os.path.exists(os.path.split(access_path)[0]):
                    os.makedirs(os.path.split(access_path)[0])
                with open(access_path + ".downloading", "wb") as f:
                    while received_len < file_size:
                        chunk = conn.recv(min(file_size - received_len, chunk_len))
                        received_len += len(chunk)
                        f.write(chunk)
                md5_remote = get_file_md5(access_path + ".downloading")
                if md5_remote == file_dict[file_key][1]:
                    status = 'OK'
                    print("文件 %s 获取成功" % (access_path))
                    os.rename(access_path + ".downloading", access_path)
                    file_dict[file_key][2] = "sync"
                    with open(os.path.join(share_root, ".filelist.can201"), 'w', encoding="utf-8") as f:
                        f.write(role + '\n')
                        f.write(dict_to_str(file_dict))
                else:
                    status = 'FAIL'
                    print("文件 %s MD5对比失败" % (access_path))
                    os.remove(access_path + ".downloading")

                # Response to client
                response_str = "POST-RE %s %s\n" % (client_header[0], status)
                response_bin = response_str.encode()
                response_bin += b'\x00' * (header_len - len(response_bin))
                conn.send(response_bin)

            else:
                conn.send('服务器已经收到你的信息'.encode())    # 回馈信息给客户端
    except Exception as e:
        print(repr(e))
    conn.close()    # 关闭连接