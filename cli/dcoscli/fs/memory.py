from fuse import Operations, LoggingMixIn, FuseOSError
from collections import defaultdict
import time
from stat import S_IFDIR, S_IFLNK, S_IFREG
from errno import ENOENT
from dcos import mesos, util, http, marathon
import os
import posixpath
from six.moves import urllib
import subprocess
import json


logger = util.get_logger(__name__)

# class FileEntry:
#     def __init__(self, stat, file_):
#         self.stat = stat
#         self.file_ = file_

class File(object):
    """Models a normal file or a directory in the DCOS FS"""
    def __init__(self):
        now = time.time()
        self._stat = create_stat(st_ctime=now,
                                 st_mtime=now,
                                 st_atime=now,
                                 st_nlink=1)

    def stat(self):
        return self._stat


class Dir(File):
    """Models a directory in the DCOS FS"""
    def __init__(self):
        super(Dir, self).__init__()
        self._stat['st_mode'] = (S_IFDIR | 0755)
        self._stat['st_size'] = 0

        self._files = {}

    def add_file(self, name, file_):
        """Add file `file_` with name `name` to this directory"""

        if name in self._files:
            raise Exception('File {} already exists'.format(name))
        else:
            self._files[name] = file_

    def files(self):
        """ Returns the filenames in this directory.  Called by `readdir`.

        :rtype: [str]
        """

        return self._files.keys()

    def resolve(self, path):
        """Returns the file in this directory at relative path `path`

        :rtype: File | None
        """

        if path == '':
            return self

        parts = path.split('/', 1)

        if len(parts) == 1:
            if path in self.files():
                return self._file(path)
            else:
                return None
        else:
            base, rest = parts
            if base in self.files():
                next_dir = self._file(base)
                return next_dir.resolve(rest)
            else:
                return None

    def _file(self, name):
        """ Returns the file in this directory with name `name`

        :rtype: File
        """

        if name in self._files:
            return self._files[name]
        else:
            raise ValueError('File {} does not exist'.format(name))

class FrameworksDir(Dir):
    """ /frameworks """
    def _update(self):
        self._files = {}

        master = MASTER_STATE.get_master()
        for framework in master.frameworks():
            logger.info("Framework: {}".format(framework['name']))
            self._files[framework['name']] = FrameworkDir(framework['id'])

    def files(self):
        self._update()
        return super(FrameworksDir, self).files()

class FrameworkDir(Dir):
    """ /frameworks/<framework> """
    def __init__(self, id_):
        self._id = id_
        super(FrameworkDir, self).__init__()

    def _update(self):
        self._files = {}

        master = MASTER_STATE.get_master()
        framework = master.framework(self._id)
        self._files['state.json'] = _json_file(framework.dict())

        logger.info("Framework: {}: Num Tasks: {}".format(framework['name'], len(framework.tasks())))

        tasks_dir = Dir()
        for task in framework.tasks():
            tasks_dir.add_file(task['id'], TaskDir(task['id']))

        self._files['tasks'] = tasks_dir

    def files(self):
        self._update()
        return super(FrameworkDir, self).files()


class TaskDir(Dir):
    """ /frameworks/<framework>/tasks/<task> """
    def __init__(self, id_):
        self._id = id_
        super(TaskDir, self).__init__()

    def _update(self):
        self._files = {}

        master = MASTER_STATE.get_master()
        task = master.task(self._id)
        self._files['state.json'] = _json_file(task.dict())
        self._files['sandbox'] = SandboxDir(task, '')

    def files(self):
        self._update()
        return super(TaskDir, self).files()


class SandboxDir(Dir):
    """Models a DCOS FS directory backed by a task's sandbox directory

    /frameworks/<framework>/tasks/<task>/sandbox
    """

    def __init__(self, task, path):
        """
        :param path: sandbox relative path (e.g. downloads/)
        :type path: str
        """

        super(SandboxDir, self).__init__()
        self.task = task
        self.path = path
        self._files_update = 0

    def files(self):
        if time.time() - self._files_update < 10:
            return self._files.keys()

        self._files = {}

        files = browse(self.task.slave(), self._full_path())
        for file_ in files:
            abs_path = file_['path']
            type_ = file_['mode'][0]

            basename = os.path.basename(abs_path)
            sandbox_path = posixpath.join(self.path, basename)

            f = None
            if type_ == '-':
                f = DCOSMesosFile(mesos.MesosFile(sandbox_path, self.task), file_['size'])
            elif type_ == 'd':
                f = SandboxDir(self.task, sandbox_path)
            else:
                raise Exception

            self.add_file(basename, f)

        self._files_update = time.time()

        return self._files.keys()

    def _full_path(self):
        return posixpath.join(self.task.directory(), self.path)

    # def _resolve(self, path):

    #     rel_path = posixpath.join(self.path, path)
    #     full_path = posixpath.join(self.task.directory(), rel_path)
    #     dir_name = os.path.dirname(full_path)

    #     contents = browse(self.task.slave(), dir_name)

    #     type_ = None
    #     for file_ in contents:
    #         if file_['path'] == full_path:
    #             type_ = file_['mode'][0]
    #             break
    #     if type_ is None:
    #         raise Exception

    #     if type_ == '-':
    #         return DCOSMesosFile(mesos.MesosFile(rel_path, self.task))
    #     elif type_ == 'd':
    #         return SandboxDir(self.task, rel_path)
    #     else:
    #         raise Exception


class Symlink(File):
    def __init__(self, dst):
        super(Symlink, self).__init__()
        self._dst = dst
        self._stat['st_mode'] = (S_IFLNK | 0755)
        self._stat['st_size'] = len(self._dst)


class NormalFile(File):
    def read(self, offset, length):
        pass

class DCOSMesosFile(NormalFile):
    """ A normal file read via /files/read.json """
    def __init__(self, mesos_file, size=None):
        super(DCOSMesosFile, self).__init__()

        self._mesos_file = mesos_file

        self._size = size or self._mesos_file.size()
        self._size_update = time.time()

        self._stat['st_mode'] = (S_IFREG | 0755)
        self._stat['st_size'] = self._size

    def read(self, offset, length):
        self._mesos_file.seek(offset)
        return str(self._mesos_file.read(length))

    def stat(self):
        if time.time() - self._size_update > 10:
            self._size = self._mesos_file.size()
            self._size_update= time.time()

        if self._size != self._stat['st_size']:
            self._stat['st_size'] = self._size
            self._stat['st_mtime'] = time.time()

        return self._stat


class StrFile(NormalFile):
    """ A normal file with static string contents """

    def __init__(self, contents):
        super(StrFile, self).__init__()
        self._contents = contents
        self._stat['st_size'] = len(self._contents)

    def read(self, offset, length):
        return self._contents[offset:offset+length]

class AppsDir(Dir):
    """ /marathon/apps """

    def _update(self):
        self._files = {}

        apps = MARATHON_CLIENT.get_apps()
        logger.info(apps)

        for app in apps:
            app_dir = AppDir(app['id'])
            app_filename = app['id'].replace('/', '_')
            self._files[app_filename] = app_dir

    def files(self):
        self._update()
        return super(AppsDir, self).files()


class AppDir(Dir):
    """ /marathon/apps/<app> """

    def __init__(self, app_id):
        self.app_id = app_id
        super(AppDir, self).__init__()

    def _update(self):
        self._files = {}

        app = MARATHON_CLIENT.get_app(self.app_id)
        self._files['state.json'] = _json_file(app)

        tasks_dir = Dir()
        self._files['tasks'] = tasks_dir

        for task in MARATHON_CLIENT.get_tasks(app['id']):
            task_dir = Dir()
            tasks_dir.add_file(task['id'], task_dir)

            state = _json_file(task)
            task_dir.add_file('state.json', state)

            sandbox = Symlink(os.path.join(MOUNT_POINT, 'frameworks/marathon/tasks/{}/sandbox'.format(task['id'])))
            task_dir.add_file('sandbox', sandbox)


    def files(self):
        self._update()
        return super(AppDir, self).files()


MOUNT_POINT = None
MARATHON_CLIENT = marathon.create_client()
class DCOSFilesystem(LoggingMixIn, Operations):
    """Example memory filesystem. Supports only one level of files."""

    def __init__(self, mount_point):
        MASTER_STATE.start()
        self.mount_point = mount_point
        global MOUNT_POINT
        MOUNT_POINT = mount_point
        self.master = mesos.get_master()
        self.root = Dir()
        self.fd = 0
        self._init_fs()

    def _init_fs(self):
        self._init_frameworks_fs()
        self._init_marathon_fs()

    def _init_marathon_fs(self):
        marathon_dir = Dir()
        self.root.add_file('marathon', marathon_dir)

        apps_dir = AppsDir()
        marathon_dir.add_file('apps', apps_dir)

    def _init_frameworks_fs(self):
        frameworks = FrameworksDir()
        self.root.add_file('frameworks', frameworks)

    def init_nodes_fs(self):
        nodes = Dir()
        self.root.add_file('nodes', nodes)

        master = Dir()
        nodes.add_file('master', master)

        master_log = DCOSMesosFile(mesos.MesosFile('/master/log', host=self.master))
        master.add_file('log', master_log)

        #master_fs = Dir()
        #master.add_file('fs', master_fs)

        # master_ip = get_master_ip()
        # master_mount_point = os.path.join(self.mount_point, 'nodes', 'master', 'fs')
        # cmd = 'sshfs core@{}:/ {}'.format(master_ip, master_mount_point)
        # subprocess.call(cmd, shell=True)

        # cmd = 'ssh -D 9000 core@{} -N'.format(master_ip)
        # socks_proc = subprocess.Popen(cmd, shell=True)
        # time.sleep(3)  # wait for listening port

        slaves = Dir()
        nodes.add_file('slaves', slaves)

        for slave in self.master.slaves():
            slave_dir = Dir()
            slaves.add_file(slave['id'], slave_dir)

            slave_log = DCOSMesosFile(mesos.MesosFile('/slave/log',  host=slave))
            slave_dir.add_file('log', slave_log)

            # slave_fs = Dir()
            # slave_dir.add_file('fs', slave_fs)

            # slave_ip = pid_to_ip(slave['pid'])
            # slave_mount_point = os.path.join(self.mount_point, 'nodes', 'slaves', slave['id'], 'fs')
            # cmd = "sshfs core@{}:/ {} -o ProxyCommand='nc -x localhost:9000 %h %p' -o StrictHostKeyChecking=no".format(
            #     slave_ip, slave_mount_point)
            # subprocess.call(cmd, shell=True)

    def readlink(self, path):
        """ Resolve symlink at `path` into its target directory

        :rtype: str
        """

        file_ = self.root.resolve(path[1:])
        return file_._dst

    def getattr(self, path, fh=None):
        """ Returns a dict with struct stat properties

        :rtype: dict
        """

        file_ = self.root.resolve(path[1:])

        if not file_:
            raise FuseOSError(ENOENT)

        return file_.stat()

    def readdir(self, path, fh):
        """ Returns a list of filenames in `path`

        :rtype: [str]
        """

        dir_ = self.root.resolve(path[1:])
        if not dir_:
            raise FuseOSError(ENOENT)

        return ['.', '..'] + dir_.files()

    def open(self, path, flags):
        """ Returns a file descriptor

        :rtype: int
        """
        self.fd += 1
        return self.fd - 1


    def read(self, path, size, offset, fh):
        """ Return a chunk of the file at `path`

        :rtype: str
        """

        file_ = self.root.resolve(path[1:])

        return file_.read(offset, size)


class Memory(LoggingMixIn, Operations):
    'Example memory filesystem. Supports only one level of files.'

    def __init__(self):
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time.time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=2)

    def chmod(self, path, mode):
        self.files[path]['st_mode'] &= 0770000
        self.files[path]['st_mode'] |= mode
        return 0

    def chown(self, path, uid, gid):
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid

    def create(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                                st_size=0, st_ctime=time(), st_mtime=time(),
                                st_atime=time())

        self.fd += 1
        return self.fd

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        return self.files[path]

    def getxattr(self, path, name, position=0):
        attrs = self.files[path].get('attrs', {})

        try:
            return attrs[name]
        except KeyError:
            return ''       # Should return ENOATTR

    def listxattr(self, path):
        attrs = self.files[path].get('attrs', {})
        return attrs.keys()

    def mkdir(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFDIR | mode), st_nlink=2,
                                st_size=0, st_ctime=time(), st_mtime=time(),
                                st_atime=time.time())

        self.files['/']['st_nlink'] += 1

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        return self.data[path][offset:offset + size]

    def readdir(self, path, fh):
        return ['.', '..'] + [x[1:] for x in self.files if x != '/']

    def readlink(self, path):
        return self.data[path]

    def removexattr(self, path, name):
        attrs = self.files[path].get('attrs', {})

        try:
            del attrs[name]
        except KeyError:
            pass        # Should return ENOATTR

    def rename(self, old, new):
        self.files[new] = self.files.pop(old)

    def rmdir(self, path):
        self.files.pop(path)
        self.files['/']['st_nlink'] -= 1

    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        attrs = self.files[path].setdefault('attrs', {})
        attrs[name] = value

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        self.files[target] = dict(st_mode=(S_IFLNK | 0777), st_nlink=1,
                                  st_size=len(source))

        self.data[target] = source

    def truncate(self, path, length, fh=None):
        self.data[path] = self.data[path][:length]
        self.files[path]['st_size'] = length

    def unlink(self, path):
        self.files.pop(path)

    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime

    def write(self, path, data, offset, fh):
        self.data[path] = self.data[path][:offset] + data
        self.files[path]['st_size'] = len(self.data[path])
        return len(data)


def browse(slave, path):
    """
    Request

    /files/browse.json
      path=...  # path to run ls on


    Response

    [
      {path:  # full path to file
       nlink:
       size:
       mtime:
       mode:
       uid:
       gid:
      }
    ]

    """

    url = mesos.MesosClient().slave_url(slave['id'], 'files/browse.json')
    return http.get(url, params={'path': path}).json()


def create_stat(st_ctime=0,
                st_mtime=0,
                st_atime=0,
                st_nlink=1,
                st_mode=(S_IFREG | 0755),
                st_size=0):
    """
        st_ctime  # time of last status change
        st_mtime  # time of last modification
        st_atime  # time of last access
        st_nlink  # number of hard links
        st_mode   # protection
        st_size   # total size, in bytes
    """
    return dict(st_ctime=st_ctime,
                st_mtime=st_mtime,
                st_atime=st_atime,
                st_nlink=st_nlink,
                st_mode=st_mode,
                st_size=st_size)


def get_master_ip():
    config = util.get_config()
    dcos_url = util.get_config_vals(config, ['core.dcos_url'])[0]
    metadata = http.get(urllib.parse.urljoin(dcos_url, 'metadata')).json()
    master_ip = metadata["PUBLIC_IPV4"]
    return master_ip

def pid_to_ip(pid):
    return pid.split('@')[1].split(':')[0]


def _json_file(dict_):
    return StrFile(json.dumps(dict_, indent=4))

class CachedProperty(object):
    def __init__(self, ttl=300):
        self.ttl = ttl

    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        try:
            value, last_update = inst._cache[self.__name__]
            if self.ttl > 0 and time() - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = (value, time())
        return value

import threading
class MasterStateThread(threading.Thread):
    def run(self):
        self._master = mesos.get_master()
        self._lock = threading.Lock()
        while True:
            time.sleep(5)
            new_master = mesos.get_master()
            with self._lock:
                self._master = new_master

    def get_master(self):
        with self._lock:
            return self._master
MASTER_STATE = MasterStateThread()
