from __future__ import print_function
import sys
import getpass

import hostlists

from .arguments import parse_arguments
from .sshmap import SSHCommand, run
from .utility import get_terminal_size, header, status_clear


def cli():
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
            terse = False
            if options.header_format in ['terse']:
                terse = True
            for md5 in aggregate_hosts.keys():
                hostline = ','.join(hostlists.compress(aggregate_hosts[md5]))
                prefix = ''
                if options.header_format in ['prefixhost']:
                    prefix = hostline + ':'
                else:
                    header(hostline, outfile=sys.stderr, collapse=terse)
                stdout, stderr = collapsed_output[md5]
                if stdout:
                    sys.stdout.write('\n'.join([prefix + line for line in stdout]))
                    sys.stdout.flush()
                if stderr:
                    sys.stderr.write('\n'.join([prefix + line for line in stderr]))
                sys.stderr.write('\n')
                sys.stderr.flush()
    if options.summarize_failed and 'failures' in results.parm.keys() and len(results.parm['failures']):
        print(
            'SSH Failed to: %s' % hostlists.compress(results.parm['failures'])
        )


if __name__ == "__main__":
    cli()
