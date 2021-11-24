import os, sys, shutil, socket, struct, hashlib, math, tqdm, numpy, threading
import multiprocessing, gzip, zlib, zipfile, time, argparse, json

ignore = [".can201", ".downloading"]
header_size = 1024
chunk_size = 1024 * 1024

num_attribute = 4
KEY, MTIME, STATE, VER = tuple(range(num_attribute))
PRINT_DEBUG = False

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
