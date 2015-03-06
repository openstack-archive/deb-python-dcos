
from __future__ import absolute_import, print_function

import argparse
import os
import sys

from ... import cli
from ... import fake
from ... import service

parser = cli.parser(
    description="move a workload"
)

parser.add_argument(
    "workload"
)

parser.add_argument(
    '--location'
)

# I would like to apologize for this code. It is horrible and anyone seeing this
# is welcome to give me a hard time about it. Yes, I'm lazy, I accept this fact.
@cli.init(parser)
def main(args):

    if args.workload == "all" and args.location == "azure":
        os.system(
            "dcos marathon update rails-app demo/rails-cloud.json > /dev/null")
        os.system(
            "dcos chronos stop 5 && dcos chronos run demo/batch-cloud.json > /dev/null")

    if args.workload == "all" and args.location == "local":
        os.system("dcos marathon update rails-app demo/rails-return.json > /dev/null")
        os.system(
            "dcos chronos stop 5 && dcos chronos run demo/batch-local.json > /dev/null")

    print("moving workload!")
