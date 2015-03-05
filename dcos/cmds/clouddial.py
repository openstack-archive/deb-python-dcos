import os

def start():
    os.execvp("/opt/demo/cloud-dial/controller.py", ["/opt/demo/cloud-dial/controller.py", "start"]) 

def stop():
    os.execvp("/opt/demo/cloud-dial/controller.py", ["/opt/demo/cloud-dial/controller.py", "stop"])

