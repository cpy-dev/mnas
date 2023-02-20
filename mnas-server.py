#!/usr/bin/python3

import hashlib
import os
import socket as sk
import sys
from _thread import start_new_thread
import subprocess
import json
import argparse

with open('/etc/mnas/conf.json', 'r') as conf:
     configuration = json.loads(conf.read())

def overlinePrint(text):
    sys.stdout.write('\r')
    sys.stdout.write(text)
    sys.stdout.flush()

class Logger:
    def __init__(self):
        self.users = configuration['users']
        self.passwords = configuration['passwords']

    def check(self, username, password):
        userNameHash = hashlib.sha512(username.encode())
        if userNameHash.hexdigest() in self.users:

            index = self.users.index(userNameHash.hexdigest())
            passwordHash = hashlib.sha512(password.encode())

            if self.passwords[index] == passwordHash.hexdigest():
                return True

        return False

class NAS:
    def __init__(self):
        self.logger = Logger()

        self.server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.server.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)

        if sys.platform == 'darwin':
            self.host = subprocess.getoutput("ifconfig -l | xargs -n1 ipconfig getifaddr")
        else:
            self.host = subprocess.getoutput("hostname -I | awk '{ print $1 }'")
        self.port = 6432

    def stop(self):
        self.server.close()
        sys.exit(0)

    def start(self):
        try:
            self.server.bind((self.host, self.port))

            while True:
                self.server.listen(2)
                client, address = self.server.accept()

                if 'x.x.x.x' in configuration['allowedIP'] or address in configuration['allowedIP']:
                    start_new_thread(self.handler, (client,))

                else:
                    client.close()

        except:
            self.server.close()

    def handler(self, client):
        userName = ''
        while '!-' not in userName:
            userName += (client.recv(64)).decode()
        userName = userName[0:-2]

        client.send(('0000!-').encode())

        password = ''
        while '!-' not in password:
            password += (client.recv(64)).decode()
        password = password[0:-2]

        if not self.logger.check(userName, password):
            client.send(('0010!-').encode())
            client.close()
            return

        client.send(('0001!-').encode())
        print('\n[*] User authorized')

        request = ''
        while not '!-' in request:
            request += (client.recv(64)).decode()
        request = request[0:-2]

        if request == '101':
            client.close()
            return

        if request == '101':
            client.send(('0010!-').encode())
            client.close()
            return

        client.send(('0011!-').encode())

        confirm = ''
        while '!-' not in confirm:
            confirm += (client.recv(64)).decode()
        confirm = confirm[0:-2]

        if confirm == '011':
            if request == '000':
                self.sendFile(client)

            elif request == '001':
                self.uploadFile(client)

            elif request == '010':
                self.sendFileList(client)

        client.close()
        print('[*] Connection with client closed')

    def sendFileList(self, client):
        print('[*] Request: Send File List')

        files = subprocess.getoutput(f'cd {configuration["storagedir"]}; find .')
        files = files[2::].replace('./', '')

        if not files:
            files = '0111'
        files += '!-'

        client.send(files.encode())
        print('[*] File list sent')

    def sendFile(self, client):
        print('[*] Request: get file')
        client.send(('0100!-').encode())

        fileName = ''
        while '!-' not in fileName:
            fileName += (client.recv(64)).decode()
        fileName = fileName[0:-2]

        try:
            with open(f'{configuration["storagedir"]}/{fileName}', 'rb') as file:
                content = file.read()
            content += b'!-'

        except:
            client.send(('1000!-').encode())
            return

        size = os.path.getsize(f'{configuration["storagedir "]}/{fileName}')
        client.send((f'{size}!-').encode())

        confirm = ''
        while '!-' not in confirm:
            confirm += (client.recv(64)).decode()
        confirm = confirm[0:-2]

        if not confirm == '100':
            client.close()
            return

        with open(f'{configuration["storagedir"]}/{fileName}', 'rb') as file:
            sent = 0
            fileSize = size

            while True:
                bufferSize = min(4096, size)
                chunk = file.read(bufferSize)

                size -= len(chunk)
                sent += len(chunk)

                overlinePrint(f'[*] Sent: {sent} bytes / {fileSize} bytes')
                if not chunk: break

                client.sendall(chunk)
            client.send(('<#EOF#>').encode())

        print('\n[*] File content sent')

    def uploadFile(self, client):
        print('[*] Request: upload file')
        client.send(('0101!-').encode())

        fileName = ''
        while '!-' not in fileName:
            fileName += (client.recv(64)).decode()
        fileName = fileName[0:-2]

        print('[*] File name received: ', fileName)
        client.send(('0110!-').encode())

        fileSize = ''
        while '!-' not in fileSize:
            fileSize += (client.recv(64)).decode()
        fileSize = int(fileSize[0:-2])

        print('[*] File size received: ', str(fileSize))
        client.send(('1010!-').encode())

        name = fileName
        path = configuration["storagedir"]

        while '/' in name:
            index = name.index('/')
            dir = f'{path}/{name[0:index]}'

            if not os.path.isdir(dir):
                os.system(f'mkdir {dir}')

            path += name[0:index+1]
            name = name[index+1::]

        with open(f'{configuration["storagedir"]}/{fileName}', 'wb') as file:
            size = 0
            originalSize = fileSize

            while True:
                bufferSize = min(fileSize, 4096)
                received = client.recv(bufferSize)

                if size >= originalSize:
                    break
                size += len(received)

                overlinePrint(f'[*] Received {size} bytes / {originalSize} bytes')
                if received == ('<#EOF#>').encode():
                    break

                fileSize -= len(received)
                file.write(received)

        print('\n[*] File content received')
        client.send(('1001!-').encode())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='mNas server'
    )
    parser.add_argument('-au', '--add-user', action='store_true', help='Add authorised user')
    parser.add_argument('-ai', '--add-ip', help='Add authorised IP address')
    parser.add_argument('-std', '--set-storage-dir', help='Change storage base directory')

    args = parser.parse_args()

    if args.add_user:
        username = input('New username: ')
        password = input('New password: ')

        configuration['users'].append(hashlib.sha512(username.encode()).hexdigest())
        configuration['passwords'].append(hashlib.sha512(password.encode()).hexdigest())

        with open('/etc/nas/conf.json', 'w') as conf:
            json.dump(configuration, conf)

    elif args.add_ip:
        configuration['allowedIP'].append(args.add_ip)

        with open('/etc/nas/conf.json', 'w') as conf:
            json.dump(configuration, conf)

    elif args.set_storage_dir:
        dir = args.set_storage_dir

        if dir.endswith('/'):
            dir = dir[0:-1]

        try:
            os.system(f'mv {configuration["storagedir"]} {dir}')

        except:
            print('[*] Error: cannot transfer files from old to new storage diretctory')

        else:
            configuration['storagedir'] = dir
            with open('/etc/mnas/conf.json', 'w') as conf:
                json.dump(configuration, conf)

    else:
        nas = NAS()
        nas.start()
        print('\n[*] Process ended')