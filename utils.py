import os, sys, shutil, socket, struct, hashlib, math, tqdm, numpy, threading
import multiprocessing, gzip, zlib, zipfile, time, argparse, json

ignore = [".can201", ".downloading"]
header_len = 1024
chunk_len = 4096

def get_file_md5(fname):
    m = hashlib.md5()   #创建md5对象
    with open(fname,'rb') as fobj:
        while True:
            data = fobj.read(4096)
            if not data:
                break
            m.update(data)  #更新md5对象
    return m.hexdigest()    #返回md5对象


def scan_file(file_dict:dict, root, current):
    for file_or_dir in os.listdir(os.path.join(root, current)):
        access_path = os.path.join(root, current, file_or_dir)
        key_path = os.path.normpath(os.path.join(current, file_or_dir))
        if os.path.isfile(access_path):
            if os.path.splitext(file_or_dir)[-1] in ignore:
                continue
            # Find a file
            md5_str = get_file_md5(access_path)
            if key_path in file_dict:
                if md5_str != file_dict[key_path][1]:
                    file_dict[key_path][2] = "local"
                    file_dict[key_path][3] = int(file_dict[key_path][3]) + 1
            else:
                file_dict[key_path] = [key_path, md5_str, "local", 1]
        if os.path.isdir(access_path):
            scan_file(file_dict, root, key_path)

def handle_remote_dict(local_dict, remote_dict:dict):
    for remote_key, remote_record in remote_dict.items():
        if remote_key in local_dict:
            # Different MD5
            if remote_record[1] != local_dict[remote_key][1]:
                local_dict[remote_key][2] = "remote"
                local_dict[remote_key][3] = remote_record[3]
            # Same MD5
            else:
                if local_dict[remote_key][2] == "local" and remote_record[2] == 'local':
                    local_dict[remote_key][2] = "sync"
                if remote_record[2] == "sync":
                    local_dict[remote_key][2] = "sync"
                local_dict[remote_key][3] = remote_record[3]
        else:
            local_dict[remote_key] = [remote_key, remote_record[1], "remote", remote_record[3]]

def dict_to_str(dict_in:dict):
    ret_str = str()
    for record in dict_in.values():
        ret_str += '|'.join(str(attribute) for attribute in record) + '\n'
    return ret_str

def str_to_dict(in_str:str):
    ret_dict = dict()
    for record_str in in_str.splitlines():
        record_list = record_str.split('|')
        ret_dict[os.path.normpath(record_list[0])] = record_list
    return ret_dict

'''

def str_to_list(in_str:str):
    out_list = []
    for row in in_str.splitlines():
        out_list.append(row.split())
    return out_list

def list_to_str(list_in):
    str = ''
    for row in list_in:
        str += " ".join(attribute for attribute in row) + '\n'
    return str

'''