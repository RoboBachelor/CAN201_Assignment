import os, sys, shutil, socket, struct, hashlib, math, tqdm, numpy, threading
import multiprocessing, gzip, zlib, zipfile, time, argparse, json

if __name__ =="__main__":
    #1.创建套接字
    tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    #2.获取服务器的ip,port
    dest_ip = "127.0.0.1"
    dest_port = 20080

    #3.链接服务器
    tcp_socket.connect((dest_ip,dest_port))

    while True:

        #4.获取下载的文件名字
        download_file_name=input("请输入要下载的文件名字：")

        #5.将文件名字发送到服务器
        tcp_socket.sendall(download_file_name.encode("utf-8"))

        #6.接收文件中的数据:1M
        recv_data = tcp_socket.recv(1024*1024)

        #7.保存接收的数据到一个文件中
        #用with的前提是open能够打开
        if recv_data:
            print(recv_data)
            # with open(download_file_name,"wb") as f:
            #     f.write(recv_data)

    #8.关闭套接字
    tcp_socket.close()
