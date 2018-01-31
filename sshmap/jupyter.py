import argparse
import shlex
from IPython.core.magic import register_line_magic, register_cell_magic, register_line_cell_magic, Magics
from .sshmap import SSHCommand, ssh_results


class JupyterSSHCommand(SSHCommand):
    _ansi_repr = True
    ansi = True


@register_line_cell_magic
def sshmap(line, cell=None):
    shlex.split(line)
    if not cell:
        cell = shlex.split(line)[-1]
        line = ' '.join(shlex.split(line)[:-1])
    parser = argparse.ArgumentParser()
    parser.add_argument('host_range', nargs='+')
    parser.add_argument('-collapse', action='store_true', default=False)
    parser.add_argument('-sort', action='store_true', default=False)
    parser.add_argument('-shell', default='/bin/bash')
    args = parser.parse_args(shlex.split(line))

    # Hack to allow jupyter qtconsole to give reasonable output
    ssh_results.__repr__ = ssh_results._repr_text_
    command = JupyterSSHCommand(
        host_range=','.join(args.host_range), script=cell, command=args.shell, collapse=args.collapse, sort=args.sort
    )
    return command
