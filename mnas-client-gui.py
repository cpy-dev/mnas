#!/usr/bin/python3

import time
import customtkinter as ctk
from tkinter import filedialog
from _thread import start_new_thread
import socket as sk
import os
import subprocess

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

def mapDirectory(root):
    content = (subprocess.getoutput(f'ls -a "{root}"')).split('\n')

    if '.' in content:
        content.remove('.')

    if '..' in content:
        content.remove('..')

    files = []

    for file in content:
        filePath = f'{root}{file}'

        if os.path.isfile(filePath):
            files.append(filePath)

        else:
            files.extend(mapDirectory(filePath + '/'))

    return files

def removeDirectories(files):
    for index, base in enumerate(files):
        times = 0

        for file in files:
            if base in file:
                times += 1

        if times > 1:
            files.pop(index)

    return files

class Interface():
    def __init__(self):
        self.getFileListPage = False
        self.getFilePage = False
        self.uploadFilePage = False

        self.userName = None
        self.password = None

        self.server = ''
        self.client = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.checkCache()

        self.root = ctk.CTk()
        self.root.title('mNas')

        self.root.geometry('800x600')
        self.root.minsize(800, 600)
        self.root.maxsize(800, 600)
        self.root.resizable(False, False)

        self.font = ('Courier', 20)

        self.centralFrame = ctk.CTkFrame(self.root)
        self.centralFrame.pack(padx=30, pady=30, expand=True, fill='both')

        self.makeLoginPage()
        self.root.mainloop()

    def checkCache(self):
        try:
            with open('/tmp/mnas/mnas.cache', 'r') as  cache:
                self.server = (cache.read()).replace('\n', '')
        except:
            pass

    def makeLoginPage(self):
        self.loginLabel = ctk.CTkLabel(self.centralFrame, font=self.font, text='Waiting for login attempt')
        self.loginLabel.pack(padx=60, pady=40, expand=True, fill='x')

        self.serverIpEntry = ctk.CTkEntry(self.centralFrame, font=self.font, placeholder_text='Server IP address')
        self.serverIpEntry.insert(ctk.END, self.server)
        self.serverIpEntry.pack(padx=60, pady=40, expand=True, fill='x')

        self.userNameEntry = ctk.CTkEntry(self.centralFrame, font=self.font, placeholder_text='Username')
        self.userNameEntry.pack(padx=60, pady=40, expand=True, fill='x')

        self.passwordEntry = ctk.CTkEntry(self.centralFrame, font=self.font, show='*', placeholder_text='Password')
        self.passwordEntry.pack(padx=60, pady=40, expand=True, fill='x')

        self.loginButon = ctk.CTkButton(self.centralFrame, text='Login', font=self.font, command=self.login)
        self.loginButon.pack(padx=60, pady=40)

    def destroyLoginPage(self):
        self.loginLabel.destroy()
        self.serverIpEntry.destroy()
        self.userNameEntry.destroy()
        self.passwordEntry.destroy()
        self.loginButon.destroy()

    def makeHomePage(self):
        self.nordBar = ctk.CTkFrame(self.centralFrame)
        self.nordBar.pack(padx=60, pady=40, expand=True, fill='x', side=ctk.TOP)

        self.getFileListBtn = ctk.CTkButton(self.nordBar, text='Get File List', font=self.font, command=self.makeGetFileListPage)
        self.getFileListBtn.pack(padx=20, expand=True, fill='x', side=ctk.LEFT)

        self.getFileBtn = ctk.CTkButton(self.nordBar, text='Get File', font=self.font, command=self.makeGetFilePage)
        self.getFileBtn.pack(padx=20, expand=True, fill='x', side=ctk.LEFT)

        self.uploadFileBtn = ctk.CTkButton(self.nordBar, text='Upload File', font=self.font, command=self.makeUploadFilePage)
        self.uploadFileBtn.pack(padx=20, expand=True, fill='x', side=ctk.LEFT)

    def makeGetFileListPage(self):
        if not self.getFileListPage:
            self.destroyGetFilePage()
            self.destroyUploadFilePage()

            self.getFileListLabel = ctk.CTkLabel(self.centralFrame, font=self.font, text='Waiting file list from server')
            self.getFileListLabel.pack(padx=20, expand=True, fill='x')

            self.getFileListTextArea = ctk.CTkTextbox(self.centralFrame, font=self.font)
            self.getFileListTextArea.configure(state=ctk.DISABLED)
            self.getFileListTextArea.pack(padx=20, expand=True, fill='both')

            self.threadedGetFileList()

            self.getFileListPage = True

    def destroyGetFileListPage(self):
        if self.getFileListPage:
            self.getFileListLabel.destroy()
            self.getFileListTextArea.destroy()
            self.getFileListPage = False

    def makeGetFilePage(self):
        if not self.getFilePage:
            self.destroyGetFileListPage()
            self.destroyUploadFilePage()

            self.getFileName = ctk.CTkOptionMenu(self.centralFrame, font=self.font, values=['Select a file'])
            self.getFileName.pack(padx=10, pady=10)

            start_new_thread(self.fileList, ())

            self.getFileDest = ctk.CTkLabel(self.centralFrame, font=self.font, text='File destination')
            self.getFileDest.pack(padx=10, pady=10, expand=True, fill='x')

            self.getFileDestBtn = ctk.CTkButton(self.centralFrame, font=self.font, text='Select Destination', command=self.selectDestinationFile)
            self.getFileDestBtn.pack(padx=10, pady=10, expand=True)

            self.getFileStatusLabel = ctk.CTkLabel(self.centralFrame, font=self.font, text='')
            self.getFileStatusLabel.pack(padx=10, pady=10, expand=True, fill='both')

            self.getFileProgressBar = ctk.CTkProgressBar(self.centralFrame)
            self.getFileProgressBar.set(0)
            self.getFileProgressBar.pack(padx=10, pady=10, expand=True, fill='x')

            self.getFileDownloadBtn = ctk.CTkButton(self.centralFrame, font=self.font, text='Download', command=self.threadedGetFile)
            self.getFileDownloadBtn.pack(padx=10, pady=10)

            self.getFilePage = True

    def destroyGetFilePage(self):
        if self.getFilePage:
            self.getFileName.destroy()
            self.getFileDest.destroy()
            self.getFileDestBtn.destroy()
            self.getFileStatusLabel.destroy()
            self.getFileProgressBar.destroy()
            self.getFileDownloadBtn.destroy()

            self.getFilePage = False

    def makeUploadFilePage(self):
        if not self.uploadFilePage:
            self.destroyGetFilePage()
            self.destroyGetFileListPage()

            self.uploadSelection = ctk.CTkOptionMenu(self.centralFrame, font=self.font, values=['Upload a file', 'Upload a directory'])
            self.uploadSelection.pack(padx=10, pady=10)
            
            self.sourceFile = ''
            self.uploadSourceFile = ctk.CTkLabel(self.centralFrame, font=self.font, text='No target')
            self.uploadSourceFile.pack(padx=10, pady=10, expand=True, fill='x')

            self.uploadSelectSourceFile = ctk.CTkButton(self.centralFrame, font=self.font, text='Select target', command=self.selectSourceFile)
            self.uploadSelectSourceFile.pack(padx=10, pady=10)

            self.uploadDestinationFile = ctk.CTkEntry(self.centralFrame, font=self.font, placeholder_text='Destionation path')
            self.uploadDestinationFile.pack(padx=10, pady=10, expand=True, fill='x')

            self.uploadStatusLabel = ctk.CTkLabel(self.centralFrame, font=self.font, text='')
            self.uploadStatusLabel.pack(padx=10, pady=10, expand=True, fill='both')

            self.uploadFileProgressBar = ctk.CTkProgressBar(self.centralFrame)
            self.uploadFileProgressBar.set(0)
            self.uploadFileProgressBar.pack(padx=10, pady=10, expand=True, fill='x')

            self.uploadBtn = ctk.CTkButton(self.centralFrame, font=self.font, text='Upload', command=self.upload)
            self.uploadBtn.pack(padx=10, pady=10)

            self.uploadFilePage = True

    def destroyUploadFilePage(self):
        if self.uploadFilePage:
            self.uploadSelection.destroy()
            self.uploadSourceFile.destroy()
            self.uploadSelectSourceFile.destroy()
            self.uploadDestinationFile.destroy()
            self.uploadStatusLabel.destroy()
            self.uploadFileProgressBar.destroy()
            self.uploadBtn.destroy()

            self.uploadFilePage = False

    def selectSourceFile(self):
        if self.uploadSelection.get() == 'Upload a file':
            target = filedialog.askopenfilename(title='Select file to upload')
        else:
            target = filedialog.askdirectory(title='Select directory to upload')

        if target:
            self.uploadSourceFile.configure(text=target)

    def selectDestinationFile(self):
        fileName = filedialog.asksaveasfilename(title='Select destination file')

        if fileName:
            self.getFileDest.configure(text=fileName)

    def login(self):
        self.server = self.serverIpEntry.get()

        try:
            self.client.connect((self.server, 6432))
        except:
            self.loginLabel.configure(text='Impossible to connect')

        self.client.send((self.userNameEntry.get() + '!-').encode())

        response = ''
        while '!-' not in response:
            response += (self.client.recv(64)).decode()
        response = response[0:-2]

        if not response == '0000':
            self.loginLabel.configure(text='Some error occurred: try again')
            return

        self.client.send((self.passwordEntry.get() + '!-').encode())

        response = ''
        while '!-' not in response:
            response += (self.client.recv(64)).decode()
        response = response[0:-2]

        if not response == '0001':
            self.loginLabel.configure(text='Unrecognized credentials: try again')
            return

        self.client.send(('101!-').encode())
        self.client.close()

        self.userName = self.userNameEntry.get()
        self.password = self.passwordEntry.get()

        with open('/tmp/open-nas/open-nas.cache', 'w') as cache:
            cache.write(self.server)

        self.destroyLoginPage()
        self.makeHomePage()

    def internalLogin(self):
        try:
            self.client = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
            self.client.connect((self.server, 6432))
        except:
            return False

        self.client.send(((self.userName) + '!-').encode())

        response = ''
        while '!-' not in response:
            response += (self.client.recv(64)).decode()
        response = response[0:-2]

        if not response == '0000':
            self.client.close()
            return False

        self.client.send((self.password + '!-').encode())

        response = ''
        while '!-' not in response:
            response += (self.client.recv(64)).decode()
        response = response[0:-2]

        if not response == '0001':
            self.client.close()
            return False

        return True

    def threadedGetFileList(self):
        start_new_thread(self.getFileList, ())

    def getFileList(self):
        try:
            if not self.internalLogin():
                self.getFileListLabel.configure(text='Fatal error occurred')
                self.client.close()
                return

            self.getFileListLabel.configure(text='Waiting list from server')
            self.client.send(('010!-').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response == '0011':
                self.client.close()
                return

            self.client.send(('011!-').encode())

            content = ''
            while '!-' not in content:
                content += (self.client.recv(1024)).decode()
            content = content[0:-2]

            self.getFileListLabel.configure(text='File list received')

            self.getFileListTextArea.configure(state=ctk.NORMAL)
            self.getFileListTextArea.insert(ctk.END, content if content != '0111' else 'Empty file list')
            self.getFileListTextArea.configure(state=ctk.DISABLED)

            self.client.close()
        except:
            self.client.close()

    def fileList(self):
        try:
            if not self.internalLogin():
                pass

            self.client.send(('010!-').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response == '0011':
                self.client.close()
                return

            self.client.send(('011!-').encode())

            content = ''
            while '!-' not in content:
                content += (self.client.recv(1024)).decode()
            content = content[0:-2]

            options = ['Select a file']
            options.extend(content.split('\n'))

            self.getFileName.configure(values=removeDirectories(options))

        except:
            pass

    def threadedGetFile(self):
        start_new_thread(self.getFile, ())

    def getFile(self):
        try:
            if self.getFileName.get() == 'Select a file':
                self.getFileStatusLabel.configure(text='You must select a file first')
                return

            if self.getFileDest.cget('text') == 'File destination':
                self.getFileStatusLabel.configure(text='You must select a destination first')
                return

            self.getFileDownloadBtn.configure(state=ctk.DISABLED)
            if not self.internalLogin():
                self.getFileStatusLabel.configure(text='Fatal error occurred: trye again')
                self.client.close()
                self.getFileDownloadBtn.configure(state=ctk.NORMAL)
                return

            self.getFileStatusLabel.configure(text='Requesting file')
            self.client.send(('000!-').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response == '0011':
                self.getFileStatusLabel.configure(text='Request error')
                self.client.close()
                self.getFileDownloadBtn.configure(state=ctk.NORMAL)
                return

            self.client.send(('011!-').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response == '0100':
                self.getFileStatusLabel.configure(text='Request error')
                self.client.close()
                self.getFileDownloadBtn.configure(state=ctk.NORMAL)
                return

            self.client.send((self.getFileName.get() + '!-').encode())

            fileSize = ''
            while '!-' not in fileSize:
                fileSize += (self.client.recv(64)).decode()
            fileSize = fileSize[0:-2]

            if fileSize == '1000':
                self.getFileStatusLabel.configure(text='File does not exist')
                self.client.close()
                self.getFileDownloadBtn.configure(state=ctk.NORMAL)
                return

            self.client.send(('100!-').encode())

            currentSize = 0
            progress = 0
            fileContent = b''

            while b'!-' not in fileContent:
                self.getFileProgressBar.set(int(progress) if int(progress) < 100 else 100)
                fileContent += (self.client.recv(1024))

                currentSize += 1024
                progress = currentSize * 100 / int(fileSize)

            self.getFileProgressBar.set(100)
            fileContent = fileContent[0:-2]

            with open(self.getFileDest.cget('text'), 'wb') as dest:
                dest.write(fileContent)

            self.getFileStatusLabel.configure(text='Download completed')
            self.client.close()
            self.getFileDownloadBtn.configure(state=ctk.NORMAL)
        except:
            self.getFileDownloadBtn.configure(state=ctk.NORMAL)
            self.client.close()

    def upload(self):
        if self.uploadSelection.get() == 'Upload a file':
            self.threadedUploadFile(self.uploadSourceFile.cget('text'), self.uploadDestinationFile.get())

        else:
            self.threadedUploadDirectory()

    def threadedUploadFile(self, source, dest):
        start_new_thread(self.uploadFile, (source, dest))

    def uploadFile(self, source, destination):
        try:
            self.uploadBtn.configure(state=ctk.DISABLED)
            if not self.internalLogin():

                self.uploadStatusLabel.configure(text='Fatal error occurred: try again')
                self.client.close()

                self.uploadBtn.configure(state=ctk.NORMAL)
                return

            self.uploadStatusLabel.configure(text='Requesting upload')
            self.client.send(('001!-').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response== '0011':
                self.uploadStatusLabel.configure(text='Upload error: please retry')
                self.client.close()

                self.uploadBtn.configure(state=ctk.NORMAL)
                return

            self.uploadStatusLabel.configure(text='Upload request accepted')
            self.client.send(('011!-').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response == '0101':
                self.uploadStatusLabel.configure(text='Upload error: please retry')
                self.client.close()

                self.uploadBtn.configure(state=ctk.NORMAL)
                return

            self.client.send((destination + '!-').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response == '0110':
                self.uploadStatusLabel.configure(text='Upload error: please retry')
                self.client.close()

                self.uploadBtn.configure(state=ctk.NORMAL)
                return

            fileSize = os.path.getsize(source)
            self.client.send((str(fileSize) + '!-').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response == '1010':
                self.uploadStatusLabel.configure(text='Upload error: please retry')
                self.client.close()

                self.uploadBtn.configure(state=ctk.NORMAL)
                return

            with open(source, 'rb') as file:
                self.uploadStatusLabel.configure(text='Uploading' + source)
                sent = 0

                while True:
                    self.uploadFileProgressBar.set(sent if sent < 100 else 100)
                    bufferSize = min(4096, fileSize)
                    chunk = file.read(bufferSize)

                    fileSize -= bufferSize

                    if not chunk: break
                    self.client.sendall(chunk)
                    sent += len(chunk)

                time.sleep(2)
                self.client.send(('<#EOF#>').encode())

            response = ''
            while not '!-' in response:
                response += (self.client.recv(64)).decode()
            response = response[0:-2]

            if not response == '1001':
                self.uploadStatusLabel.configure(text='Upload error: please retry')
                self.client.close()

                self.uploadBtn.configure(state=ctk.NORMAL)
                return

            self.client.close()
            self.uploadStatusLabel.configure(text='File uploaded succesfully')
            self.uploadBtn.configure(state=ctk.NORMAL)

        except:
            self.uploadBtn.configure(state=ctk.NORMAL)
            self.client.close()

    def threadedUploadDirectory(self):
        start_new_thread(self.uploadDirectory, ())

    def uploadDirectory(self):
        files = mapDirectory(self.uploadSourceFile.cget('text') + '/')

        for file in files:
            fileName = file.replace(self.uploadSourceFile.cget('text'), '')
            self.uploadFile(source=file, destination=f'{self.uploadDestinationFile.get()}{fileName}')

if __name__ == '__main__':
    if not os.path.exists('/tmp/mnas'):
        os.system('mkdir /tmp/mnas')
    Interface()