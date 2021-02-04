import os
from vassal.terminal import Terminal
from threading import Thread
import json
import asyncio
import time
import websockets

def start_server():
    shell = Terminal(["python3 /home/andrey/Projects/MicrosController/ServerExamples/server.py"])
    shell.run()

def start_client():
    shell1 = Terminal(["python3 /home/andrey/Projects/MicrosController/ServerExamples/client.py"])
    shell1.run()

# start_server()
# start_client()
threadserver = Thread(target=start_server)
threadclient = Thread(target=start_client)

try:
    threadserver.start()
    time.sleep(1)
    threadclient.start()
except KeyboardInterrupt:
    threadserver.join()
    threadclient.join()
except:
    print("some error")
finally:
    print("clear")
    





# os.system("ssh pi@192.168.42.100")
# os.system("python3 server.py")
# os.system("ls")