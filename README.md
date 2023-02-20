# mNas - Minimal NAS
### Open source minimal network attached storage

# Installation
- get latest version from [releases](https://github.com/cpy-dev/mnas/releases)
- or clone this repo


    $ git clone https://github.com/cpy-dev/mnasn

- extract files from archive


    $ tar -xf mnas_1.0.0-linux-any.tar.gz


- run "setup.sh", which will 
  - create a folder under /etc named "mnas"
  - copy there the conf.json file
- this action is required only on the device which will be server
    

    $ sudo ./setup.sh

- then install the requirements for mNas GUI


    $ pip install -r requirements.txt


- you are good to go

# Server Usage
- before starting the server for the first time, you should setup few settings:
  - set allowed ip addresses, which will be the only able to connect to mNas server

        $ python3 mnas-server.py --add-ip 192.168.1.100 

  - if you want the server to be available for any device on the network, add the ip "x.x.x.x" 

        $ python3 mnas-server.py --add-ip x.x.x.x

- set up the first user

      $ python3 mnas-server.py --add-user 

  - you will be prompted to provide username and password for the user

- default location for mNas storage is "/etc/mnas/storage", if you wish to change it run the following command providing the new location

      $ python3 mnas-server.py --set-storage-dir /new/path/to/storage/

- once done configuring, just run mnas-server.py with no arguments and server will start itself

      $ python3 mnas-server.py

- it is a good practice to have a log file, to have a trace of any activity involving mNas server

      $ python3 mnas-server.py &>> /etc/mnas/mnas.log

# Client GUI application usage
- just run the "mnas-client-gui.py" script (after installing requirements) and you're good to go

      $ python3 mnas-client-gui.py