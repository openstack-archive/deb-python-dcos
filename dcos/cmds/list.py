
from __future__ import absolute_import, print_function

import blessings
import prettytable

from mesos.cli.master import CURRENT as MASTER

from .. import cli


@cli.init()
def main(args):
    term = blessings.Terminal()

    tb = prettytable.PrettyTable(
        ["Name", "Version"],
        border=False,
        max_table_width=term.width,
        hrules=prettytable.NONE,
        vrules=prettytable.NONE,
        left_padding_width=0,
        right_padding_width=1
    )

    tb.align["Name"] = "l"
    tb.align["Version"] = "l"

    for fw in MASTER.frameworks(active_only=True):
        if '-' in fw["name"]:
            tb.add_row(fw["name"].split('-',1))
        else:
            tb.add_row([fw["name"],"0.0.1"])

#    for fw in MASTER.frameworks(active_only=True):
#        tb.add_row(fw["name"].split('-', 1))

    print(tb)
