# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
sshmap built in callback handlers
"""
from __future__ import print_function
import os
import sys
import hashlib
import json
import stat
import base64
import subprocess

# import sshmap
# try:
#     import sshmap.utility
# except ImportError:
#     import utility

from .defaults import conf_defaults, conf_desc
from .utility import status_clear


# Filter callback handlers
def flowthrough(result):
    """
    Builtin Callback, return the raw data passed

    >>> result=flowthrough(sshmap.ssh_result(["output"], ["error"],"foo", 0))
    >>> result.dump()
    foo output error 0 0 None
    """
    return result


def summarize_failures(result):
    """
    Builtin Callback, put a summary of failures into parm
    """
    failures = result.setting('failures')
    if not failures:
        result.parm['failures'] = []
        failures = []
    if result.ssh_retcode:
        failures.append(result.host)
        result.parm['failures'] = failures
    return result


def exec_command(result):
    """
    Builtin Callback, pass the results to a command/script
    :param result:
    """
    script = result.setting("callback_script")
    if not script:
        return result
    status_clear()
    result_out, result_err = subprocess.Popen(
        script + " " + result.host,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ).communicate(
        result.out_string() + result.err_string()
    )
    result.out = [result_out]
    result.err = [result_err]
    print(result.out_string())
    return result


def aggregate_output(result):
    """ Builtin Callback, Aggregate identical results """
    aggregate_hosts = result.setting('aggregate_hosts')
    if not aggregate_hosts:
        aggregate_hosts = {}
    collapsed_output = result.setting('collapsed_output')
    if not collapsed_output:
        collapsed_output = {}
    h = hashlib.md5()
    h.update(result.stdout)
    h.update(result.stderr)
    if result.ssh_retcode:
        h.update(result.ssh_error_message().encode())
    digest = h.hexdigest()
    if digest in aggregate_hosts.keys():
        aggregate_hosts[digest].append(result.host)
        aggregate_hosts[digest] = list(set(aggregate_hosts[digest]))
    else:
        aggregate_hosts[digest] = [result.host]
        if result.ssh_retcode:
            error = []
            if result.err:
                error = result.err
            error.append(result.ssh_error_message())
            collapsed_output[digest] = (result.out, error)
        else:
            collapsed_output[digest] = (result.out, result.err)
    result.parm['aggregate_hosts'] = aggregate_hosts
    if collapsed_output:
        result.parm['collapsed_output'] = collapsed_output
    return result


def filter_match(result):
    """
    Builtin Callback, remove all output if the string is not found in the
    output
    similar to grep
    :param result:
    """
    if result.out_string().find(result.setting('match')) == -1 and \
            result.err_string().find(result.setting('match')) == -1:
        result.out = ''
        result.err = ''
    return result


def filter_json(result):
    """
    Builtin Callback, change stdout to json

    >>> result = filter_json(ssh_result(["output"], ["error"], "foo", 0))
    >>> result.dump()
    foo [["output"], ["error"], 0] error 0 0 None
    """
    result.out = [json.dumps((result.out, result.err, result.retcode))]
    return result


def filter_base64(result):
    """
    Builtin Callback, base64 encode the info in out and err streams
    """
    result.out = [base64.b64encode(result.out_string)]
    result.err = [base64.b64encode(result.err_string)]
    return result


#Status callback handlers
def status_count(result):
    """
    Builtin Callback, show the count complete/remaining
    :param result:
      """
    # The master process inserts the status into the
    # total_host_count and completed_host_count variables
    sys.stderr.write('\x1b[0G\x1b[0K%s/%s' % (
        result.setting('completed_host_count'),
        result.setting('total_host_count')))
    sys.stderr.flush()
    return result


#Output callback handlers
def output_prefix_host(result):
    """
    Builtin Callback, print the output with the hostname: prefixed to each line
    :param result:
    hostname: out

    >>> result=sshmap.callback.output_prefix_host(ssh_result(['out'], ['err'], 'hostname', 0))
    >>> result.dump()
    """
    output = []
    error = []
    status_clear()
    # If summarize_failures option is set don't print ssh errors inline
    if result.setting('summarize_failed') and result.ssh_retcode:
        return result
    if result.setting('print_rc'):
        rc = ' SSH_Returncode: %d\tCommand_Returncode: %d' % (
            result.ssh_retcode, result.retcode)
    else:
        rc = ''
    if result.ssh_retcode:
        print(
            '%s: %s' % (result.host, result.ssh_error_message()),
            file=sys.stderr
        )
        error = ['%s: %s' % (result.host, result.ssh_error_message())]
    if len(result.out_string()):
        for line in result.out:
            if line:
                print('%s:%s %s' % (result.host, rc, line.strip()))
                output.append('%s:%s %s\n' % (result.host, rc, line.strip()))
    if len(result.err_string()):
        for line in result.err:
            if line:
                print(
                    '%s:%s %s' % (result.host, rc, line.strip()),
                    file=sys.stderr
                )
                error.append(
                    '%s:%s Error: %s\n' % (result.host, rc, line.strip())
                )
    if result.setting('output'):
        if not len(result.out_string()) and not len(result.err_string()) \
                and not result.setting('only_output') \
                and result.setting('print_rc'):
            print('%s:%s' % (result.host, rc))
        sys.stdout.flush()
        sys.stderr.flush()
    result.out = output
    result.err = error
    return result


# noinspection PyUnboundLocalVariable
def read_conf(key=None, prompt=True):
    """ Read settings from the config file
    :param key:
    :param prompt:
    """
    # Use the right raw_input in python3
    if 'raw_input' not in dir(__builtins__):
        raw_input = input

    try:
        conf = json.load(open(os.path.expanduser('~/.sshmap.conf'), 'r'))
    except IOError:
        conf = conf_defaults
    if key:
        try:
            return conf[key].encode('ascii')
        except KeyError:
            pass
    else:
        return conf
    if key and prompt:
        conf[key] = raw_input(conf_desc[key] + ': ')
        fh = open(os.path.expanduser('~/.sshmap2.conf'), 'w')
        os.fchmod(fh.fileno(), stat.S_IRUSR | stat.S_IWUSR)
        json.dump(conf, fh)
        fh.close()
        return conf[key]
    else:
        return None
