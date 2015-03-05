import os

def main():
    os.system("parallel-ssh -h local-hosts -i sudo stop mesos-slave > /dev/null")
    print "beginning maintenance..."
