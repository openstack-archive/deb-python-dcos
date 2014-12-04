
from __future__ import absolute_import, print_function

import copy
import sys
import time

from .. import cli
from .. import fake
from .. import service

parser = cli.parser(
    description="chaos on your cluster"
)

parser.add_argument(
    "number", type=int, help="number of nodes to add"
)

NODE_CONFIG = {
    "mem": 1,
    "cpus": 0.01
}

@cli.init(parser)
def main(args):
    cfg = copy.copy(NODE_CONFIG)
    cfg["num"] = args.number
    print(fake.start_tasks("http://{0}:8081".format("10.8.148.49"), cfg))
