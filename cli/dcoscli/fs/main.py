"""Run filesystem

Usage:
    dcos fs <mount_point>
"""

import docopt
import dcoscli

from dcos.errors import DCOSException
from dcos import cmds, util, emitting

from fuse import FUSE
import logging
import memory, loopback, threading
import concurrent.futures


emitter = emitting.FlatEmitter()

def main():
    try:
        return _main()
    except DCOSException as e:
        emitter.publish(e)
        return 1

def _main():
    util.configure_logger_from_environ()

    args = docopt.docopt(
        __doc__,
        version='dcos-package version {}'.format(dcoscli.version))

    return cmds.execute(_cmds(), args)

def _cmds():
    return [
        cmds.Command(
            hierarchy=['fs'],
            arg_keys=['<mount_point>'],
            function=_fs
        )
    ]

def run_fuse(fs, mount_point):
    FUSE(fs, mount_point, allow_other=True, foreground=True)


def _fs(mount_point):
    logging.getLogger().setLevel(logging.DEBUG)
    dcos_fs = memory.DCOSFilesystem(mount_point)

    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        pool.submit(run_fuse, dcos_fs, mount_point)

        import time, os
        while not os.path.isdir(os.path.join(mount_point, 'frameworks')):
            time.sleep(1)

        dcos_fs.init_nodes_fs()
