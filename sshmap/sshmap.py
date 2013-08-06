#!/usr/bin/env python
#Copyright (c) 2012 Yahoo! Inc. All rights reserved.
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License. See accompanying LICENSE file.
"""
 Python based ssh multiplexer optimized for map operations
"""
# Pull in the python3 print function for python3 compatibility
from __future__ import print_function

#disable deprecated warning messages that occur during some of the imports
import warnings
warnings.filterwarnings("ignore")

# Python Standard Library imports
import os
import sys
import getpass
import socket
import types
import random
import signal
import multiprocessing
import logging

# Imports from external python extension modules
import ssh

# Imports from other sshmap modules
import hostlists
import utility
import callback
import defaults
import runner

# Fix to make ctrl-c correctly terminate child processes
# spawned by the multiprocessing module
from multiprocessing.pool import IMapIterator


def wrapper(func):
    """
    Simple timeout wrapper for multiprocessing
    :param func:
    """
    def wrap(self, timeout=None):
        """
        The wrapper method
        :param timeout:
        """
        return func(self, timeout=timeout if timeout is not None else 1e100)

    return wrap


IMapIterator.next = wrapper(IMapIterator.next)


class ssh_result(object):
    """
    ssh_result class, that holds the output from the ssh_call.  This is passed
    to all the callback functions.
    """

    def __init__(self, out=None, err=None, host=None, retcode=0, ssh_ret=0,
                 parm=None):
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
        """
        Get a setting from the parm dict or return None if it doesn't exist
        :param key:
        """
        return utility.get_parm_val(self.parm, key)

    def ssh_error_message(self):
        """ Return the ssh_error_message for the error code """
        return defaults.RUN_CODES[self.ssh_retcode]

    def dump(self, return_parm=True, return_retcode=True):
        """ Print all our public values
        :param return_parm:
        :param return_retcode:
        """
        sys.stdout.write(self.host+' ')
        sys.stdout.write(self.out_string().replace('\n', '')+' ')
        sys.stderr.write(self.err_string().replace('\n', '')+' ')
        if return_retcode:
            sys.stdout.write(self.retcode+' ')
        if return_parm:
            sys.stdout.write(self.ssh_retcode+' '+self.parm)
        else:
            sys.stdout.write('\n')

    def print_output(self):
        """ Print output from the commands """
        for line in self.out:
            print('%s: %s' % (self.host, line.strip()))
        for line in self.err:
            print('%s: %s' % (self.host, line.strip()))


class ssh_results(list):
    """
    ssh_results class, provides 2 things, an iterator to iterate over
    ssh_result objects and a single variable parm which contains the parm
    parameter after the completion of all the result objects (the parm
    variable contains the global variables used and provided by the callbacks)
    """
    parm = None

    def dump(self):
        """ Dump all the result objects """
        for item in self.__iter__():
            item.dump(return_parm=False, return_retcode=False)
        print(self.parm)

    def print_output(self, summarize_failures=False):
        """ Print all the objects
        :param summarize_failures:
        """
        for item in self.__iter__():
            item.print_output()
        if summarize_failures:
            if len(self.parm['failures']):
                print(
                    'SSH Failures: %s' % ','.join(
                        self.parm['failures']).strip(',')
                )

    def setting(self, key):
        """
        Get a setting from the parm dict or return None if it doesn't exist
        :param key:
        """
        return utility.get_parm_val(self.parm, key)


def agent_auth(transport, username):
    """
    Attempt to authenticate to the given transport using any of the private
    keys available from an SSH agent or from a local private RSA key file
    (assumes no pass phrase).
    :param transport:
    :param username:
    """

    agent = ssh.Agent()
    agent_keys = agent.get_keys()
    if len(agent_keys) == 0:
        return

    for key in agent_keys:
        logging.info(
            'Trying ssh-agent key %s' % key.get_fingerprint().encode('hex'))
        try:
            transport.auth_publickey(username, key)
            logging.debug('agent_auth success!')
            return
        except ssh.SSHException as e:
            logging.debug('agent_auth failed! %s', e)


# A version of the ssh.SSHClient that supports timeout
class fastSSHClient(ssh.SSHClient):
    """ ssh SSHClient class extended with timeout support """

    def exec_command(self, command, bufsize=-1, timeout=None, pty=False):
        """
        Execute a command
        :param command:
        :param bufsize:
        :param timeout:
        :param pty:
        :return:
        """
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
    char = handle.read(1)
    buf = ""
    try:
        while char:
            buf += char
            if char in ['\r', '\n']:
                return buf
            char = handle.read(1)
    except Exception as message:
        print('%s %s' % (Exception, message))
    return buf


def run_command(host, command="uname -a", username=None, password=None,
                sudo=False, script=None, timeout=None, parms=None, client=None,
                bufsize=-1, logging=False):
    """
    Run a command or script on a remote node via ssh
    :param host:
    :param command:
    :param username:
    :param password:
    :param sudo:
    :param script:
    :param timeout:
    :param parms:
    :param client:
    :param bufsize:
    :param logging:
    """
    # Guess any parameters not passed that can be
    if isinstance(host, types.TupleType):
        host, command, username, password, sudo, script, timeout, parms, \
            client = host
    if timeout == 0:
        timeout = None
    if not username:
        username = getpass.getuser()
    if bufsize == -1 and script and os.path.exists(script):
        bufsize = os.path.getsize(script) + 1024

    script_parameters = None
    if script:
        temp = command.split()
        if len(temp) > 1:
            command = temp[0]
            script_parameters = temp

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
            result.ssh_retcode = defaults.RUN_FAIL_UNKNOWN
            return result
        client.set_missing_host_key_policy(ssh.AutoAddPolicy())
        # load_system_host_keys slows things way down
        #client.load_system_host_keys()
        close_client = True
        # noinspection PyBroadException
    try:
        client.connect(host, username=username, password=password,
                       timeout=timeout)
    except ssh.AuthenticationException:
        result.ssh_retcode = defaults.RUN_FAIL_AUTH
        return result
    except ssh.SSHException:
        result.ssh_retcode = defaults.RUN_FAIL_CONNECT
        return result
    except AttributeError:
        result.ssh_retcode = defaults.RUN_FAIL_SSH
        return result
    except socket.error:
        result.ssh_retcode = defaults.RUN_FAIL_CONNECT
        return result
    except Exception as message:
        logging.debug('Got unknown exception %s', message)
        result.ssh_retcode = defaults.RUN_FAIL_UNKNOWN
        return result
    try:
    # We have to force a sudo -k first or we can't reliably know we'll be
    # prompted for our password
        if sudo:
            stdin, stdout, stderr, chan = client.exec_command(
                'sudo -k -S %s' % command,
                timeout=timeout, bufsize=bufsize, pty=False
            )
            if not chan:
                result.ssh_retcode = defaults.RUN_FAIL_CONNECT
                return result
        else:
            stdin, stdout, stderr, chan = client.exec_command(
                command, timeout=timeout, bufsize=bufsize)
            if not chan:
                result.ssh_retcode = defaults.RUN_FAIL_CONNECT
                result.err = ["WTF, this shouldn't happen\n"]
                return result

    except (ssh.SSHException, ssh.transport.SSHException):
        result.ssh_retcode = defaults.RUN_FAIL_SSH
        return result
    if sudo:
        try:
            # Send the password
            stdin.write(password + '\r')
            stdin.flush()
        except socket.timeout:
            result.err = ['Timeout during sudo connect, likely bad password']
            result.ssh_retcode = defaults.RUN_FAIL_TIMEOUT
            return result
    if script:
        # Pass the script over stdin and close the channel so the receiving end
        # gets an EOF process it as a django template with the arguments passed
        # noinspection PyBroadException
        try:
            import django.template
            import django.template.loader
            import django.conf

            django.conf.settings.configure()
            if os.path.exists(script):
                template = open(script, 'r').read()
            else:
                template = script
            if script_parameters:
                c = django.template.Context({'argv': script_parameters})
            else:
                c = django.template.Context({})
            stdin.write(django.template.Template(template).render(c))
        except:
            if os.path.exists(script):
                stdin.write(open(script, 'r').read())
            else:
                stdin.write(script)
        stdin.flush()
        stdin.channel.shutdown_write()
    try:
        # Read the output from stdout,stderr and close the connection
        result.out = stdout.readlines()
        result.err = stderr.readlines()
        if sudo:
            # Remove any passwords or prompts from the start of the stderr
            # output
            err = []
            check_prompt = True
            skip = False
            for el in result.err:
                if check_prompt:
                    if password in el or 'assword:' in el or \
                            '[sudo] password' in el or el.strip() == '' or \
                            el.strip() in defaults.sudo_message or \
                            el.strip().startswith('sudo:'):
                        skip = True
                    else:
                        check_prompt = False
                if not skip:
                    err.append(el)
                skip = False
            result.err = err

        result.retcode = chan.recv_exit_status()
        if close_client:
            client.close()
    except socket.timeout:
        result.ssh_retcode = defaults.RUN_FAIL_TIMEOUT
        return result
    result.ssh_retcode = defaults.RUN_OK
    return result


def init_worker():
    """ Set up the signal handler for new worker threads """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def run_with_runner(*args, **kwargs):
    """
    Run a command with a python runner script
    :param args:
    :param kwargs:
    """
    if 'runner' in kwargs.keys() and isinstance(
        kwargs['runner'], type.FunctionType):
        kwargs['script'] = runner.get_runner(
            command=args[1],
            input="",
            password=kwargs['password'],
            runner_script=kwargs['runner'],
            compressor='bz2'
        )
        del kwargs['runner']
    return run(*args, **kwargs)


def run(host_range, command, username=None, password=None, sudo=False,
        script=None, timeout=None, sort=False,
        jobs=None, output_callback=[callback.summarize_failures],
        parms=None, shuffle=False, chunksize=None, exit_on_error=False):
    """
    Run a command on a hostlists host_range of hosts
    :param host_range:
    :param command:
    :param username:
    :param password:
    :param sudo:
    :param script:
    :param timeout:
    :param sort:
    :param jobs:
    :param output_callback:
    :param parms:
    :param shuffle:
    :param chunksize:
    :param exit_on_error: Exit as soon as one result comes back with a non 0
                          return code.

    >>> res=run(host_range='localhost',command="echo ok")
    >>> print(res[0].dump())
    localhost ok  0 0 {'failures': [], 'total_host_count': 1,
    'completed_host_count': 1}
    """
    utility.status_info(output_callback, 'Looking up hosts')

    # Expand the host range if we were passed a string host list
    if isinstance(host_range, (unicode, str)):
        hosts = hostlists.expand(hostlists.range_split(host_range))
    else:
        hosts = host_range

    if shuffle:
        random.shuffle(hosts)
    utility.status_clear()
    results = ssh_results()
        
    if parms:
        results.parm = parms
    else:
        results.parm = {}

    if sudo and not password:
        for host in hosts:
            result = ssh_result()
            result.host = host
            result.err = 'Sudo password required'
            result.retcode = defaults.RUN_FAIL_NOPASSWORD
            results.append(result)
        results.parm['total_host_count'] = len(hosts)
        results.parm['completed_host_count'] = 0
        results.parm['failures'] = hosts
        return results    

    if jobs < 1:
        jobs = 1
    if jobs > defaults.JOB_MAX:
        jobs = defaults.JOB_MAX

    # Set up our ssh client
    #status_info(output_callback,'Setting up the SSH client')
    client = fastSSHClient()
    client.set_missing_host_key_policy(ssh.AutoAddPolicy())
    # load_system_host_keys slows things way down
    #client.load_system_host_keys()

    results.parm['total_host_count'] = len(hosts)
    results.parm['completed_host_count'] = 0

    utility.status_clear()
    utility.status_info(output_callback, 'Spawning processes')

    if jobs > len(hosts):
        jobs = len(hosts)

    pool = multiprocessing.Pool(processes=jobs, initializer=init_worker)
    if not chunksize:
        if jobs == 1 or jobs >= len(hosts):
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

    if isinstance(output_callback, types.ListType) and \
            callback.status_count in output_callback:
        callback.status_count(ssh_result(parm=results.parm))

    # Create a process pool and pass the parameters to it

    utility.status_clear()
    utility.status_info(
        output_callback, 'Sending %d commands to each process' % chunksize)
    if callback.status_count in output_callback:
        callback.status_count(ssh_result(parm=results.parm))
        
    try:
        for result in map_command(
            run_command,
            [
                (
                    host, command, username, password, sudo, script, timeout,
                    results.parm, client
                ) for host in hosts
            ],
            chunksize
        ):
            results.parm['completed_host_count'] += 1
            result.parm = results.parm
            if isinstance(output_callback, types.ListType):
                for cb in output_callback:
                    result = cb(result)
            else:
                result = output_callback(result)
            results.parm = result.parm
            results.append(result)
            if exit_on_error and result.retcode != 0:
                break
        pool.close()
    except KeyboardInterrupt:
        print('ctrl-c pressed')
        pool.terminate()
        #except Exception as e:
    #  print 'unknown error encountered',Exception,e
    #  pass
    pool.terminate()
    if isinstance(output_callback, types.ListType) and \
            callback.status_count in output_callback:
        utility.status_clear()
    return results


if __name__ == "__main__":
    # The contents that where formerly here have been moved to the sshmap 
    # command line utility.  
    pass