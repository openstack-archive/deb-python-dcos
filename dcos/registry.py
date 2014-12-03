
from __future__ import absolute_import, print_function

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from .cfg import CURRENT as CFG

# XXX - This command is used for every completion right now. It should
# take a very short time to complete.
def list():
    return [
        OrderedDict([
            ("name", "spark"),
            ("version", "1.1.0")
        ]),
        OrderedDict([
            ("name", "cassandra"),
            ("version", "2.1.2")
        ]),
        OrderedDict([
            ("name", "kafka"),
            ("version", "0.8.2-beta")
        ]),
        OrderedDict([
            ("name", "kubernetes"),
            ("version", "0.5")
        ]),
        OrderedDict([
            ("name", "chronos"),
            ("version", "2.1.0")
        ]),
        OrderedDict([
            ("name", "jenkins"),
            ("version", "1.588")
        ]),
        OrderedDict([
            ("name", "hdfs"),
            ("version", "2.6.0")
        ]),
        OrderedDict([
            ("name", "deis"),
            ("version", "1.0.2")
        ]),
        OrderedDict([
            ("name", "hadoop"),
            ("version", "0.23.11")
        ]),
        OrderedDict([
            ("name", "yarn"),
            ("version", "2.6.0")
        ]),
        OrderedDict([
            ("name", "accumulo"),
            ("version", "1.6.1")
        ]),
        OrderedDict([
            ("name", "elasticsearch"),
            ("version", "1.4.1")
        ]),
        OrderedDict([
            ("name", "aurora"),
            ("version", "0.6.0")
        ]),
        OrderedDict([
            ("name", "storm"),
            ("version", "0.9.3")
        ])
    ]

def names():
    return map(lambda x: x["name"], list())

def installed():
    return CFG["installed"]
