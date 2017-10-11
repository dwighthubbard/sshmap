from IPython.core.magic import Magics, magics_class, line_magic, cell_magic, line_cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from .sshmap import SSHCommand


_loaded = False


@magics_class
class SSHMapMagic(Magics):

    @magic_arguments()
    @argument(
        'host_range', nargs=1,
        help='Host range to run the command on',
    )
    @argument(
        'command', nargs='*',
        help='Host range to run the command on',
    )
    @argument(
        '-m', '--collapse', default=False, action='store_true',
        help='Collapse (Merge) output that is the same from multiple hosts'
    )
    @argument(
        '-s', '--sort', default=False, action='store_true',
        help='Sort the results by hostname'
    )
    @argument(
        '--shell', default='/bin/bash', help='Shell command parser to run the code'
    )
    @line_cell_magic
    def sshmap(self, line='', cell=None):
        args = parse_argstring(self.sshmap, line)
        command = ' '.join(args.command)
        script = None
        if cell:
            command = args.shell
            script = cell
        return SSHCommand(host_range=','.join(args.host_range), command=command, collapse=args.collapse, sort=args.sort, script=script)


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(SSHMapMagic)
        _loaded = True
