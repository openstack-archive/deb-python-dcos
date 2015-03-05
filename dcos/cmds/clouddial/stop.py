import os

def main():
    os.execvp(
        "/opt/demo/cloud-dial/controller.py",
        ["/opt/demo/cloud-dial/controller.py", "stop"])
