import os

def main():
    os.system("parallel-ssh -h local-hosts -i sudo start mesos-slave > /dev/null")
    print "maintenance has been finished!"
