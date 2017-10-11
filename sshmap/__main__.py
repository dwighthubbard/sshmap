from __future__ import print_function
import os
import sys
import getpass
import logging


import hostlists
from .arguments import parse_arguments
from .sshmap import SSHCommand
from .utility import get_terminal_size, header, status_clear


if __name__ == "__main__":
    logging.getLogger('sshmap.arguments').setLevel(logging.DEBUG)
    sys.argv[0] = 'sshmap'
    options = parse_arguments()

    if options.sudo and not options.password:
        options.password = getpass.getpass('Enter sudo password for user ' + options.user + ': ')

    command = ' '.join(options.command)
    hostrange = ','.join(options.hostrange)
    command = SSHCommand(
        hostrange, command, username=options.username,
        password=options.password, sudo=options.sudo,
        timeout=options.timeout, script=options.runscript, jobs=options.jobs,
        sort=options.sort, shuffle=options.shuffle,
        output_callback=options.callbacks, parms=vars(options)
    )
    results = command.run()
    if options.aggregate_output:
        aggregate_hosts = results.setting('aggregate_hosts')
        collapsed_output = results.setting('collapsed_output')
        status_clear()
        if aggregate_hosts and collapsed_output:
            rows, columns = get_terminal_size()
            for md5 in aggregate_hosts.keys():
                header(','.join(hostlists.compress(aggregate_hosts[md5])), outfile=sys.stderr, collapse=options.output_terse_headers)
                stdout, stderr = collapsed_output[md5]
                if stdout:
                    print(''.join(stdout))
                if stderr:
                    print('\n'.join(stderr), file=sys.stderr)
    if options.summarize_failed and 'failures' in results.parm.keys() and len(results.parm['failures']):
        print(
            'SSH Failed to: %s' % hostlists.compress(results.parm['failures'])
        )
