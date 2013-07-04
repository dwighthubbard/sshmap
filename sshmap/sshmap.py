#!/usr/bin/env python
"""
 Python based ssh multiplexer optimized for map operations

 Copyright (c) 2012 Yahoo! Inc. All rights reserved.
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,   
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License. See accompanying LICENSE file.
"""
#disable deprecated warning messages
import warnings

warnings.filterwarnings("ignore")

# Python Standard Library imports
import sys
import os
import stat
import getpass
import socket
import types
import base64
import random
import signal
import hashlib
import json
import multiprocessing
import subprocess

# Imports from external python extension modules
import ssh

# Imports from other sshmap modules
import hostlists

# Defaults
JOB_MAX = 100
# noinspection PyBroadException
try:
    for line in open('/proc/%d/limits' % os.getpid(), 'r').readlines():
        if line.startswith('Max processes'):
            JOB_MAX = int(line.strip().split()[2]) / 4
except:
    pass

# Return code values
RUN_OK = 0
RUN_FAIL_AUTH = 1
RUN_FAIL_TIMEOUT = 2
RUN_FAIL_CONNECT = 3
RUN_FAIL_SSH = 4
RUN_SUDO_PROMPT = 5
RUN_FAIL_UNKNOWN = 6
RUN_FAIL_NOPASSWORD = 7
RUN_FAIL_BADPASSWORD = 8

# Text return codes
RUN_CODES = ['Ok', 'Authentication Error', 'Timeout', 'SSH Connection Failed', 'SSH Failure',
             'Sudo did not send a password prompt', 'Connection refused', 'Sudo password required',
             'Invalid sudo password']

# Configuration file field descriptions
conf_desc = {
    "username": "IRC Server username",
    "password": "IRC Server password",
    "channel": "sshmap",
}

# Configuration file defaults 
conf_defaults = {
    "address": "chat.freenode.net",
    "port": "6667",
    "use_ssl": False,
}

# Fix to make ctrl-c correctly terminate child processes
# spawned by the multiprocessing module
from multiprocessing.pool import IMapIterator


def wrapper(func):
    def wrap(self, timeout=None):
        return func(self, timeout=timeout if timeout is not None else 1e100)

    return wrap


IMapIterator.next = wrapper(IMapIterator.next)


class ssh_result:
    """
    ssh_result class, that holds the output from the ssh_call.  This is passed
    to all the callback functions.
    """

    def __init__(self, out=None, err=None, host=None, retcode=0, ssh_ret=0, parm=None):
        if not err:
            err = []
        if not out:
            out = []
        self.out = out
        self.err = err
        self.retcode = retcode
        self.ssh_retcode = ssh_ret
        self.parm = parm
        self.host = host

    def out_string(self):
        """ Return the output as a string """
        return ''.join(self.out)

    def err_string(self):
        """ Return the err as a string """
        return ''.join(self.err)

    def setting(self, key):
        """ Get a setting from the parm dict or return None if it doesn't exist """
        return get_parm_val(self.parm, key)

    def ssh_error_message(self):
        """ Return the ssh_error_message for the error code """
        return RUN_CODES[self.ssh_retcode]

    def dump(self, return_parm=True, return_retcode=True):
        """ Print all our public values """
        print self.host, self.out_string().replace('\n', ''), self.err_string().replace('\n', ''),
        if return_retcode:
            print self.retcode,
        if return_parm:
            print self.ssh_retcode, self.parm
        else:
            print

    def print_output(self):
        """ Print output from the commands """
        for line in self.out:
            print '%s:' % self.host, line.strip()
        for line in self.err:
            print '%s:' % self.host, line.strip()


class ssh_results(list):
    """
    ssh_results class, provides 2 things, an iterator to iterate over ssh_result objects
    and a single variable parm which contains the parm parameter after the completion of
    all the result objects (the parm variable contains the global variables used and
    provided by the callbacks)
    """
    parm = None

    def dump(self):
        """ Dump all the result objects """
        for item in self.__iter__():
            item.dump(return_parm=False, return_retcode=False)
        print self.parm

    def print_output(self, summarize_failures=False):
        """ Print all the objects """
        for item in self.__iter__():
            item.print_output()
        if summarize_failures:
            if len(self.parm['failures']):
                print 'SSH Failures:', ','.join(self.parm['failures']).strip(',')

    def setting(self, key):
        """ Get a setting from the parm dict or return None if it doesn't exist """
        return get_parm_val(self.parm, key)


# A version of the ssh.SSHClient that supports timeout
class fastSSHClient(ssh.SSHClient):
    """ ssh SSHClient class extended with timeout support """

    def exec_command(self, command, bufsize=-1, timeout=None, pty=False):
        chan = self._transport.open_session()
        chan.settimeout(timeout)
        if pty:
            chan.get_pty()
        chan.exec_command(command)
        stdin = chan.makefile('wb', bufsize)
        stdout = chan.makefile('rb', bufsize)
        stderr = chan.makefile_stderr('rb', bufsize)
        return stdin, stdout, stderr, chan


def _term_readline(handle):
    #print '_iterm_readline'
    #print type(handle)
    char = handle.read(1)
    #print '%s' % (char), type(char)
    buf = ""
    #print '_iterm_readline: starting loop'
    try:
        while char:
            #print '_item_readline: appending',type(buf),type(char)
            buf += char
            if char in ['\r', '\n']:
                #print '_iterm_readline - Found line', len(buf), char, buf
                return buf
            char = handle.read(1)
    except Exception, message:
        print Exception, message
    #print '_item_readline - Exit', buf
    return buf


def run_command(host, command="uname -a", username=None, password=None, sudo=False, script=None, timeout=None,
                parms=None, client=None, bufsize=-1, cwd='/tmp', logging=False):
    """
    Run a command or script on a remote node via ssh
    """
    # Guess any parameters not passed that can be
    if isinstance(host, types.TupleType):
        host, command, username, password, sudo, script, timeout, parms, client = host
    if timeout == 0:
        timeout = None
    if not username:
        username = getpass.getuser()
    if bufsize == -1 and script:
        bufsize = os.path.getsize(script) + 1024

    if script:
        temp = command.split()
        if len(temp) > 1:
            command = temp[0]
            script_parameters = temp
        else:
            script_parameters = None

    # Get a result object to put our output in
    result = ssh_result(host=host, parm=parms)

    if logging:
        ssh.util.log_to_file('ssh.log')

    close_client = False
    if not client:
        # noinspection PyBroadException
        try:
            client = fastSSHClient()
        except:
            result.err = ['Error creating client']
            result.ssh_retcode = RUN_FAIL_UNKNOWN
            return result
        client.set_missing_host_key_policy(ssh.AutoAddPolicy())
        # load_system_host_keys slows things way down
        #client.load_system_host_keys()
        close_client = True
        # noinspection PyBroadException
    try:
        client.connect(host, username=username, password=password, timeout=timeout)
    except ssh.AuthenticationException:
        result.ssh_retcode = RUN_FAIL_AUTH
        return result
    except ssh.SSHException:
        result.ssh_retcode = RUN_FAIL_CONNECT
        return result
    except AttributeError:
        result.ssh_retcode = RUN_FAIL_SSH
        return result
    except socket.error:
        result.ssh_retcode = RUN_FAIL_CONNECT
        return result
    except Exception, message:
        result.ssh_retcode = RUN_FAIL_UNKNOWN
        return result
    try:
    # We have to force a sudo -k first or we can't reliably know we'll be prompted for our password
        if sudo:
            stdin, stdout, stderr, chan = client.exec_command('sudo -k %s' % command, timeout=timeout, bufsize=bufsize,
                                                              pty=True)
            if not chan:
                result.ssh_retcode = RUN_FAIL_CONNECT
                return result
        else:
            stdin, stdout, stderr, chan = client.exec_command(command, timeout=timeout, bufsize=bufsize)
            if not chan:
                result.ssh_retcode = RUN_FAIL_CONNECT
                result.err = ["WTF, this shouldn't happen\n"]
                return result

    except ssh.SSHException, ssh.transport.SSHException:
        result.ssh_retcode = RUN_FAIL_SSH
        return result
    if sudo:
        try:
            # Send the password
            stdin.write(password + '\r')
            stdin.flush()
            
            # Remove the password prompt and password from the output
            prompt = _term_readline(stdout)
            seen_password = False
            seen_password_prompt = False
            #print 'READ:',prompt
            while 'assword:' in prompt or password in prompt or 'try again' in prompt or len(prompt.strip()) == 0:
                if 'try again' in prompt:
                    result.ssh_retcode = RUN_FAIL_BADPASSWORD
                    return result
                prompt_new = _term_readline(stdout)
                if 'assword:' in prompt:
                    seen_password_prompt = True
                if password in prompt:
                    seen_password = True
                if seen_password_prompt and seen_password:
                    break
                prompt = prompt_new
        except socket.timeout:
            result.err = ['Timeout during sudo connect, likely bad password']
            result.ssh_retcode = RUN_FAIL_TIMEOUT
            return result
    if script:
        # Pass the script over stdin and close the channel so the receving end gets an EOF
        # process it as a django template with the arguments passed
        # noinspection PyBroadException
        try:
            import django.template
            import django.template.loader
            import django.conf

            django.conf.settings.configure()
            template = open(script, 'r').read()
            if script_parameters:
                c = django.template.Context({ 'argv': script_parameters })
            else:
                c = django.template.Context({ })
            stdin.write(django.template.Template(template).render(c))
        except Exception, e:
            stdin.write(open(script, 'r').read())
        stdin.flush()
        stdin.channel.shutdown_write()
    try:
        # Read the output from stdout,stderr and close the connection
        result.out = stdout.readlines()
        result.err = stderr.readlines()
        result.retcode = chan.recv_exit_status()
        if close_client:
            client.close()
    except socket.timeout:
        result.ssh_retcode = RUN_FAIL_TIMEOUT
        return result
    result.ssh_retcode = RUN_OK
    return result


# Handy utility functions
def get_parm_val(parm=None, key=None):
    """
    Return the value of a key

    >>> get_parm_val(parm={'test':'val'},key='test')
    'val'
    >>> get_parm_val(parm={'test':'val'},key='foo')
    >>>
    """
    if parm and key in parm.keys():
        return parm[key]
    else:
        return None


def status_info(callbacks, text):
    """
    Update the display line at the cursor
    """
    #print callbacks,text
    #return
    if isinstance(callbacks, list) and callback_status_count in callbacks:
        status_clear()
        sys.stderr.write(text)
        sys.stderr.flush()


def status_clear():
    """
    Clear the status line (current line)
    """
    sys.stderr.write('\x1b[0G\x1b[0K')
    #sys.stderr.flush()


# Built in callbacks
# Filter callback handlers
def callback_flowthrough(result):
    """
    Builtin Callback, return the raw data passed

    >>> result=callback_flowthrough(ssh_result(["output"], ["error"],"foo", 0))
    >>> result.dump()
    foo output error 0 0 None
    """
    return result


def callback_summarize_failures(result):
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


def callback_exec_command(result):
    """
    Builtin Callback, pass the results to a command/script
    :param result:
    """
    script = result.setting("callback_script")
    if not script:
        return result
    status_clear()
    result_out, result_err = subprocess.Popen(script + " " + result.host, shell = True, stdin = subprocess.PIPE,
                                              stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate(
        result.out_string() + result.err_string())
    result.out = [result_out]
    result.err = [result_err]
    print result.out_string()
    return result


def callback_aggregate_output(result):
    """ Builtin Callback, Aggregate identical results """
    aggregate_hosts = result.setting('aggregate_hosts')
    if not aggregate_hosts:
        aggregate_hosts = {}
    collapsed_output = result.setting('collapsed_output')
    if not collapsed_output:
        collapsed_output = {}
    h = hashlib.md5()
    h.update(result.out_string())
    h.update(result.err_string())
    if result.ssh_retcode:
        h.update(result.ssh_error_message())
    digest = h.hexdigest()
    if digest in aggregate_hosts.keys():
        aggregate_hosts[digest].append(result.host)
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


def callback_filter_match(result):
    """
    Builtin Callback, remove all output if the string is not found in the output
    similar to grep
    """
    if result.out_string().find(result.setting('match')) == -1 and result.err_string().find(
            result.setting('match')) == -1:
        result.out = ''
        result.err = ''
    return result


def callback_filter_json(result):
    """
    Builtin Callback, change stdout to json

    >>> result=callback_filter_json(ssh_result(["output"], ["error"],"foo", 0))
    >>> result.dump()
    foo [["output"], ["error"], 0] error 0 0 None
    """
    result.out = [json.dumps((result.out, result.err, result.retcode))]
    return result


def callback_filter_base64(result):
    """
    Builtin Callback, base64 encode the info in out and err streams
    """
    result.out = [base64.b64encode(result.out_string)]
    result.err = [base64.b64encode(result.err_string)]
    return result


#Status callback handlers
def callback_status_count(result):
    """
    Builtin Callback, show the count complete/remaining
    :param result:
      """
    # The master process inserts the status into the
    # total_host_count and completed_host_count variables
    sys.stderr.write('\x1b[0G\x1b[0K%s/%s' % (
        result.setting('completed_host_count'), result.setting('total_host_count')))
    sys.stderr.flush()
    return result


#Output callback handlers
def callback_output_prefix_host(result):
    """
    Builtin Callback, print the output with the hostname: prefixed to each line
    :param result:

    >>> result=callback_output_prefix_host(ssh_result(['out'],['err'], 'hostname', 0))
    hostname: out
    >>> result.dump()
    hostname hostname: out hostname: Error: err 0 0 None
    """
    output = []
    error = []
    status_clear()
    # If summarize_failures option is set don't print ssh errors inline
    if result.setting('summarize_failed') and result.ssh_retcode:
        return result
    if result.setting('print_rc'):
        rc = ' SSH_Returncode: %d\tCommand_Returncode: %d' % (result.ssh_retcode, result.retcode)
    else:
        rc = ''
    if result.ssh_retcode:
        print >> sys.stderr, '%s: %s' % (result.host, result.ssh_error_message())
        error = ['%s: %s' % (result.host, result.ssh_error_message())]
    if len(result.out_string()):
        for line in result.out:
            if line:
                print '%s:%s %s' % (result.host, rc, line.strip())
                output.append('%s:%s %s\n' % (result.host, rc, line.strip()))
    if len(result.err_string()):
        for line in result.err:
            if line:
                print >> sys.stderr, '%s:%s %s' % (result.host, rc, line.strip())
                error.append('%s:%s Error: %s\n' % (result.host, rc, line.strip()))
    if result.setting('output'):
        if not len(result.out_string()) and not len(result.err_string()) and not result.setting(
                'only_output') and result.setting('print_rc'):
            print '%s:%s' % (result.host, rc)
        sys.stdout.flush()
        sys.stderr.flush()
    result.out = output
    result.err = error
    return result


def read_conf(key=None, prompt=True):
    """ Read settings from the config file """
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


def init_worker():
    """ Set up the signal handler for new worker threads """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run(host_range, command, username=None, password=None, sudo=False, script=None, timeout=None, sort=False,
        bufsize=-1, cwd='/tmp', jobs=None, output_callback=callback_summarize_failures, parms=None, shuffle=False,
        chunksize=None):
    """
    Run a command on a hostlists host_range of hosts
    >>> res=run(host_range='localhost',command="echo ok")
    >>> print res[0].dump()
    localhost ok  0 0 {'failures': [], 'total_host_count': 1, 'completed_host_count': 1}
    None
    """
    status_info(output_callback, 'Looking up hosts')
    hosts = hostlists.expand(hostlists.range_split(host_range))
    if shuffle:
        random.shuffle(hosts)
    status_clear()
    results = ssh_results()
        
    if parms:
        results.parm = parms
    else:
        results.parm = { }

    if sudo and not password:
        for host in hosts:
            result=ssh_result()
            result.err='Sudo password required'
            result.retcode = RUN_FAIL_NOPASSWORD
            results.append(result)
        results.parm['total_host_count'] = len(hosts)
        results.parm['completed_host_count'] = 0
        results.parm['failures'] = hosts
        return results    

    if jobs < 1:
        jobs = 1
    if jobs > JOB_MAX:
        jobs = JOB_MAX

    # Set up our ssh client
    #status_info(output_callback,'Setting up the SSH client')
    client = fastSSHClient()
    client.set_missing_host_key_policy(ssh.AutoAddPolicy())
    # load_system_host_keys slows things way down
    #client.load_system_host_keys()

    results.parm['total_host_count'] = len(hosts)
    results.parm['completed_host_count'] = 0

    status_clear()
    status_info(output_callback, 'Spawning processes')

    if jobs > len(hosts):
        jobs = len(hosts)

    pool = multiprocessing.Pool(processes = jobs, initializer = init_worker)
    if not chunksize:
        chunksize = 1
        if jobs >= len(hosts):
            chunksize = 1
        else:
            chunksize = int(len(hosts) / jobs) - 1
        if chunksize < 1:
            chunksize = 1

        if chunksize > 10:
            chunksize = 10

    results.parm['chunksize'] = chunksize
    if sort:
        map_command = pool.imap
    else:
        map_command = pool.imap_unordered

    if isinstance(output_callback, types.ListType) and callback_status_count in output_callback:
        callback_status_count(ssh_result(parm=results.parm))

    # Create a process pool and pass the parameters to it

    status_clear()
    status_info(output_callback, 'Sending %d commands to each process' % chunksize)
    if callback_status_count in output_callback:
        callback_status_count(ssh_result(parm = results.parm))
        
    try:
        for result in map_command(run_command,
                                  [(host, command, username, password, sudo, script, timeout, results.parm, client) for
                                   host in hosts], chunksize):
            #results.parm['active_processes']=len(multiprocessing.active_children())
            results.parm['completed_host_count'] += 1
            result.parm = results.parm
            if isinstance(output_callback, types.ListType):
                for callback in output_callback:
                    result = callback(result)
            else:
                result = output_callback(result)
            results.parm = result.parm
            results.append(result)
        pool.close()
    except KeyboardInterrupt:
        print 'ctrl-c pressed'
        pool.terminate()
        #except Exception,e:
    #  print 'unknown error encountered',Exception,e
    #  pass
    pool.terminate()
    if isinstance(output_callback, types.ListType) and callback_status_count in output_callback:
        status_clear()
    return results

# TODO Distributed ssh execution
# Method:
#   1. Parse config for regular expressions to map hostnames to admin host
#   2. For each adminhost
#   2.1 ssh to addmin host sshmap --output_base64 --output_json hosts command
#   2.2 As data comes back, parse it and insert data into the out,err,rc dictionaries

if __name__ == "__main__":
    # The contents that where formerly here have been moved to the sshmap 
    # command line utility.  
    pass