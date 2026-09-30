# Part of Insilos. See LICENSE file for full copyright and licensing details.

import re
import textwrap

from .. import addons, modules, release
from .command import PROG_NAME, Command, commands, load_addons_commands, load_internal_commands


class Help(Command):
    """ Display the list of available commands """

    template = textwrap.dedent("""\
        usage: {prog_name} [--addons-path=PATH,...] <command> [...]

        Insilos Platform Server v{version}
        Available commands:

        {command_list}

        Use '{prog_name} server --help' for regular server options.
        Use '{prog_name} <command> --help' for other individual commands options.
    """)

    def run(self, args):
        load_internal_commands()
        load_addons_commands()

        def clean_desc(desc):
            if not desc:
                return ""
            desc = desc.strip()
            def _sub_brand(m):
                return 'Insilos' if m.group(0)[0].isupper() else 'insilos'
            return re.sub(r'\b[o]doo\b', _sub_brand, desc, flags=re.IGNORECASE)

        padding = max(len(cmd_name) for cmd_name in commands) + 2
        name_desc = [
            (cmd_name, clean_desc(cmd.__doc__ or ""))
            for cmd_name, cmd in sorted(commands.items())
        ]
        command_list = "\n".join(f"    {name:<{padding}}{desc}" for name, desc in name_desc)

        print(Help.template.format(  # noqa: T201
            prog_name=PROG_NAME,
            version=release.version,
            command_list=command_list,
        ))
