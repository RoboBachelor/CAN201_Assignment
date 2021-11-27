import os, sys, shutil, socket, struct, hashlib, math, tqdm, numpy, threading
import multiprocessing, gzip, zlib, zipfile, time, argparse, json

ignore = [".can201", ".downloading"]
header_size = 1024
chunk_size = 1024 * 1024

num_attribute = 4
KEY, MTIME, STATE, VER = tuple(range(num_attribute))
PRINT_DEBUG = True

def scan_file(file_dict:dict, root, current):
    for file_or_dir in os.listdir(os.path.join(root, current)):
        access_path = os.path.join(root, current, file_or_dir)
        key_path = os.path.normpath(os.path.join(current, file_or_dir))
        if os.path.isfile(access_path):
            if os.path.splitext(file_or_dir)[-1] in ignore:
                continue
            # Find a file
            cur_mtime = int(os.path.getmtime(access_path) * 1000)
            if key_path in file_dict:
                # This file is in local file dict
                if cur_mtime > int(file_dict[key_path][MTIME]):
                    file_dict[key_path][STATE] = "local"
                    file_dict[key_path][VER] = int(file_dict[key_path][VER]) + 1
                    file_dict[key_path][MTIME] = cur_mtime
            else:
                # New file which is not in local file dict
                file_dict[key_path] = list(range(num_attribute))
                file_dict[key_path][KEY] = key_path
                file_dict[key_path][MTIME] = cur_mtime
                file_dict[key_path][STATE] = "local"
                file_dict[key_path][VER] = 1
        if os.path.isdir(access_path):
            scan_file(file_dict, root, key_path)

def handle_remote_dict(local_dict, remote_dict:dict):
    for remote_key, remote_record in remote_dict.items():
        if remote_key in local_dict:
            # The remote file is in local dict
            if remote_record[VER] > local_dict[remote_key][VER]:
                # Remote has new version of file
                local_dict[remote_key][STATE] = "remote"
                local_dict[remote_key][VER] = remote_record[VER]
                local_dict[remote_key][MTIME] = remote_record[MTIME]
            elif remote_record[VER] == local_dict[remote_key][VER]:
                # Acknowledge the sync status
                if local_dict[remote_key][STATE] == "local" and remote_record[STATE] == 'local':
                    local_dict[remote_key][STATE] = "sync"
                if remote_record[STATE] == "sync":
                    local_dict[remote_key][STATE] = "sync"
        else:
            # New record is insert to our local dict
            local_dict[remote_key] = list(range(num_attribute))
            local_dict[remote_key][KEY] = remote_key
            local_dict[remote_key][MTIME] = remote_record[MTIME]
            local_dict[remote_key][STATE] = "remote"
            local_dict[remote_key][VER] = remote_record[VER]

def dict_to_str(dict_in:dict):
    ret_str = str()
    for record in dict_in.values():
        ret_str += '|'.join(str(attribute) for attribute in record) + '\n'
    return ret_str

def str_to_dict(in_str:str):
    ret_dict = dict()
    for record_str in in_str.splitlines():
        record_list = record_str.split('|')
        record_list[VER] = int(record_list[VER])
        record_list[MTIME] = int(record_list[MTIME])
        ret_dict[os.path.normpath(record_list[0])] = record_list
    return ret_dict


def recv_file(sock: socket, access_path, file_size):
    received_len = 0
    if not os.path.exists(os.path.split(access_path)[0]):
        os.makedirs(os.path.split(access_path)[0])
    with open(access_path + ".downloading", "wb") as f:
        while received_len < file_size:
            chunk = sock.recv(min(file_size - received_len, chunk_size))
            if len(chunk) == 0:
                raise ConnectionError("Received length is zero while receiving file %s" % access_path)
            received_len += len(chunk)
            f.write(chunk)
    if os.path.exists(access_path):
        os.remove(access_path)
    os.rename(access_path + ".downloading", access_path)


def send_file(sock: socket, access_path, file_size):
    sent_size = 0
    with open(access_path, 'rb') as file:
        while sent_size < file_size:
            chunk = file.read(min(file_size - sent_size, chunk_size))
            sock.sendall(chunk)
            sent_size += len(chunk)


def save_repository(share_root, role, file_dict):
    with open(os.path.join(share_root, ".repository.can201"), 'w', encoding="utf-8") as f:
        f.write(role + '\n')
        f.write(dict_to_str(file_dict))


def recv_dict(sock: socket, content_len):
    dict_msg = b''
    received_len = 0
    while received_len < content_len:
        chunk = sock.recv(min(content_len - received_len, chunk_size))
        if len(chunk) == 0:
            raise ConnectionError("Received length is zero while receiving remote file list.")
        dict_msg += chunk
        received_len += len(chunk)
    return str_to_dict(dict_msg.decode())

'''
def get_file_md5(fname):
    m = hashlib.md5()   #创建md5对象
    with open(fname,'rb') as fobj:
        while True:
            data = fobj.read(4096)
            if not data:
                break
            m.update(data)  #更新md5对象
    return m.hexdigest()    #返回md5对象
'''
