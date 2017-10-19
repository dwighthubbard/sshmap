"""
SSHMap Command Line Utility Argument Parsing Module
"""
from argparse import ArgumentParser
from getpass import getuser
import logging
import os
import sys
from .callback import aggregate_output, exec_command, filter_match, filter_base64, filter_json, output_prefix_host, output_print_result, \
    status_count, summarize_failures


LOG = logging.getLogger(__name__)


def parse_arguments():
    parser = ArgumentParser()

    job_args = parser.add_argument_group('Job Settings')
    job_args.add_argument("--jobs", "-j", dest="jobs", default=65, type=int, help="Number of parallel commands to execute")
    job_args.add_argument("--timeout", dest="timeout", type=int, default=0, help="Timeout, or 0 for no timeout")
    job_args.add_argument("--sort", dest="sort", default=False, action="store_true", help="Print output sorted in the order listed")
    job_args.add_argument("--shuffle", dest="shuffle", default=False, action="store_true", help="Shuffle (randomize) the order of hosts")

    format_args = parser.add_argument_group('Output Formats')
    format_args.add_argument("--header_format", default='prefixhost', choices=['prefixhost', 'terse', 'full'], help="Format for the hostname headers")
    format_args.add_argument("--output_json", dest="output_json", default=False, action="store_true", help="Output in JSON format")
    format_args.add_argument("--output_base64", dest="output_base64", default=False, action="store_true", help="Output in base64 format")

    output_args = parser.add_argument_group('Output Options')
    output_args.add_argument("--summarize_failed", dest="summarize_failed", default=False, action="store_true", help="Print a list of hosts that failed at the end")
    output_args.add_argument("--aggregate_output", "--collapse", dest="aggregate_output", default=False, action="store_true", help="Aggregate identical list")
    output_args.add_argument("--only_output", dest="only_output", default=False, action="store_true", help="Only print lines for hosts that return output")
    output_args.add_argument("--print_rc", dest="print_rc", default=False, action="store_true", help="Print the return code value")
    output_args.add_argument("--match", dest="match", default=None, help="Only show host output if the string is found in the output")
    output_args.add_argument("--no_status", dest="show_status", default=True, action="store_false", help="Don't show a status count as the command progresses")

    exec_args = parser.add_argument_group('Execution Options')
    exec_args.add_argument("--runscript", "--run_script", dest="runscript", default=None, help="Run a script on all hosts.  The command value is the shell to pass the script to on the remote host.")
    exec_args.add_argument("--callback_script", dest="callback_script", default=None, help="Script to process the output of each host.  The hostname will be passed as the first argument and the stdin/stderr from the host will be passed as stdin/stderr of the script")
    exec_args.add_argument("--sudo", dest="sudo", default=False, action="store_true", help="Use sudo to run the command as root")
    exec_args.add_argument("--username", dest="username", default=getuser(), action="store_true", help="Prompt for a password")
    exec_args.add_argument("--password", dest="password", default=False, action="store_true", help="Prompt for a password")

    parser.add_argument('hostrange', nargs=1, type=str, help='Hostlists hostrange of hosts to operate on')
    parser.add_argument('command', nargs='*', type=str, help='Command to run on the remote system')

    options = parser.parse_args()

    if options.runscript and not options.command:
        firstline = open(options.runscript).readline().strip()
        if firstline.startswith('#!'):
            command = firstline[2:]
            options.command = [command]
    
    # Default option values
    options.output = True
    # Create our callback pipeline based on the options passed
    options.callbacks = [summarize_failures]
    if options.match:
        options.callbacks.append(filter_match)
    if options.output_base64:
        options.callbacks.append(filter_base64)
    if options.output_json:
        options.callbacks.append(filter_json)
    if options.callback_script:
        options.callbacks.append(exec_command)
    else:
        if options.aggregate_output:
            options.callbacks.append(aggregate_output)
        else:
            options.callbacks.append(output_print_result)
    if options.show_status:
        if sys.stdout.isatty():
            options.callbacks.append(status_count)
        else:
            LOG.debug('Current terminal is not a tty, disabling status output')
    if not options.password:
        options.password = os.environ.get('SSHMAP_SUDO_PASSWORD', None)

    return options
