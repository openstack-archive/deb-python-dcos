import os
import re
import subprocess
import time

from dcos import mesos
from dcos.errors import DCOSException
from dcoscli.tail.main import _mesos_files, main

import fcntl
from mock import MagicMock, patch

from .common import app, assert_command, assert_mock, exec_command

SLEEP = 'tests/data/marathon/apps/sleep.json'
FOLLOW = 'tests/data/tail/follow.json'
TWO_TASKS = 'tests/data/tail/two_tasks.json'
TWO_TASKS_FOLLOW = 'tests/data/tail/two_tasks_follow.json'


def test_help():
    """ Test `dcos tail --help` output """
    stdout = b"""Output the last part of files in a task's sandbox

Usage:
    dcos tail --info
    dcos tail [--follow --completed --lines=N] <task> [<file>]

Options:
    -h, --help    Show this screen
    --info        Show a short description of this subcommand
    --follow      Output data as the file grows
    --completed   Tail files from completed tasks as well
    --lines=N     Output the last N lines [default: 10]
    --version     Show version

Positional Arguments:

    <task>        Only match tasks whose ID matches <task>.  <task> may be
                  some substring of the ID, or a unix glob pattern.

    <file>        Output this file. [default: stdout]
"""
    assert_command(['dcos', 'tail', '--help'], stdout=stdout)


def test_info():
    """ Test `dcos tail --info` output """
    stdout = b"Output the last part of files in a task's sandbox\n"
    assert_command(['dcos', 'tail', '--info'], stdout=stdout)


def test_no_files():
    """ Tail stdout on nonexistant task """
    assert_command(['dcos', 'tail', 'asdf'],
                   returncode=1,
                   stderr=b'No matching tasks.  Exiting.\n')


def test_single_file():
    """ Tail a single file on a single task """
    with app(SLEEP, 'test-app'):
        returncode, stdout, stderr = exec_command(['dcos', 'tail', 'test-app'])

        assert returncode == 0
        assert stderr == b''
        assert len(stdout.decode('utf-8').split('\n')) == 5


def test_missing_file():
    """ Tail a single file on a single task """
    with app(SLEEP, 'test-app'):
        returncode, stdout, stderr = exec_command(
            ['dcos', 'tail', 'test-app', 'asdf'])

        assert returncode == 1
        assert stdout == b''
        assert stderr == b'No files exist.  Exiting.\n'


def test_lines():
    """ Test --lines """
    with app(SLEEP, 'test-app'):
        returncode, stdout, stderr = exec_command(
            ['dcos', 'tail', 'test-app', '--lines=2'])

        assert returncode == 0
        assert stderr == b''
        assert len(stdout.decode('utf-8').split('\n')) == 3


def test_follow():
    """ Test --follow """
    with app(FOLLOW, 'follow'):
        # verify output
        proc = subprocess.Popen(['dcos', 'tail', 'follow', '--follow'],
                                stdout=subprocess.PIPE)

        # mark stdout as non-blocking, so we can read all available data
        # before EOF
        _mark_non_blocking(proc.stdout)

        # wait for data to be output
        time.sleep(1)

        # assert lines before and after sleep
        assert len(proc.stdout.read().decode('utf-8').split('\n')) == 5
        time.sleep(8)
        assert len(proc.stdout.read().decode('utf-8').split('\n')) == 2

        proc.kill()


def test_two_tasks():
    """ Test tailing a single file on two separate tasks """
    with app(TWO_TASKS, 'two-tasks'):
        returncode, stdout, stderr = exec_command(
            ['dcos', 'tail', 'two-tasks'])

        assert returncode == 0
        assert stderr == b''

        lines = stdout.decode('utf-8').split('\n')
        assert len(lines) == 11
        assert re.match('===>.*<===', lines[0])
        assert re.match('===>.*<===', lines[5])


def test_two_tasks_follow():
    """ Test tailing a single file on two separate tasks with --follow """
    with app(TWO_TASKS_FOLLOW, 'two-tasks-follow'):
        proc = subprocess.Popen(
            ['dcos', 'tail', 'two-tasks-follow', '--follow'],
            stdout=subprocess.PIPE)

        # mark stdout as non-blocking, so we can read all available data
        # before EOF
        _mark_non_blocking(proc.stdout)

        # wait for data to be output
        time.sleep(1)

        # get output before and after the task's sleep
        first_lines = proc.stdout.read().decode('utf-8').split('\n')
        time.sleep(8)
        second_lines = proc.stdout.read().decode('utf-8').split('\n')

        # assert both tasks have printed the expected amount of output
        assert len(first_lines) >= 11
        # assert there is some difference after sleeping
        assert len(second_lines) > 0

        proc.kill()


def test_completed():
    """ Test --completed """
    # create a completed task
    # ensure that tail lists nothing
    # ensure that tail --completed lists a completed task
    with app(SLEEP, 'test-app'):
        pass

    assert_command(['dcos', 'tail', 'test-app'],
                   returncode=1,
                   stderr=b'No matching tasks.  Exiting.\n',
                   stdout=b'')

    returncode, stdout, stderr = exec_command(
        ['dcos', 'tail', '--completed', 'test-app'])
    assert returncode == 0
    assert stderr == b''
    assert len(stdout.decode('utf-8').split('\n')) > 4


def test_master_unavailable():
    """ Test master's state.json being unavailable """
    master = mesos.get_master()
    master.state = _mock_exception()

    with patch('dcos.mesos.get_master', return_value=master):
        args = ['tail', '_']
        assert_mock(main, args, returncode=1, stderr=(b"exception\n"))


def test_slave_unavailable():
    """ Test slave's state.json being unavailable """
    with app(SLEEP, 'test-app'):
        master = mesos.get_master()
        master.slaves()[0].state = _mock_exception()

        with patch('dcos.mesos.get_master', return_value=master):
            args = ['tail', 'test-app']
            stderr = (b"""Error accessing slave: exception\n"""
                      b"""No matching tasks.  Exiting.\n""")
            assert_mock(main, args, returncode=1, stderr=stderr)


def test_file_unavailable():
    """ Test a file's read.json being unavailable """
    with app(SLEEP, 'test-app'):
        files = _mesos_files(False, "", "stdout")
        assert len(files) == 1
        files[0].read = _mock_exception('exception')

        with patch('dcoscli.tail.main._mesos_files', return_value=files):
            args = ['tail', 'test-app']
            stderr = b"No files exist.  Exiting.\n"
            assert_mock(main, args, returncode=1, stderr=stderr)


def _mock_exception(contents='exception'):
    return MagicMock(side_effect=DCOSException(contents))


def _mark_non_blocking(file_):
    fcntl.fcntl(file_.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
