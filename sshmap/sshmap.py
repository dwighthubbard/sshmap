# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
 Python based ssh multiplexer optimized for map operations
"""
from __future__ import print_function
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
from collections import Iterable

# Imports from external python extension modules
import paramiko

# Imports from other sshmap modules
import hostlists

# from . import callback
# from . import defaults
# from . import runner

try:
    import sshmap.callback as callback
    import sshmap.defaults as defaults
    import sshmap.runner as runner
except ImportError:
    import callback
    import defaults
    import runner

from .utility import status_clear, status_info


# Fix to make ctrl-c correctly terminate child processes
# spawned by the multiprocessing module
from multiprocessing.pool import IMapIterator


LOG = logging.getLogger(__name__)


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


class SSHResult(object):
    """
    ssh_result class, that holds the output from the ssh_call.  This is passed
    to all the callback functions.
    """
    bootstrap = True
    bootstrap_show_retcodes = False

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

    @property
    def stdout(self):
        return self.sequence_to_bytes(self.out)

    @property
    def stderr(self):
        return self.sequence_to_bytes(self.err)

    @property
    def output(self):
        result = self.stdout + self.stderr
        if isinstance(result, bytes):
            return result.decode(errors='ignore')
        return result

    def __str__(self):
        output = self.stdout if self.stdout else ''
        output += self.stderr if self.stderr else ''
        return output.decode(errors='ignore')

    def __repr__(self):
        return 'sshmap.ssh_result({0}, {1}, {2}, {3})'.format(
            repr(self.out_string()),
            repr(self.err_string()),
            self.host,
            self.ssh_retcode
        )

    def _repr_html__plain_(self):
        """
        __repr__ in an html table format
        """
        output = '<table width="100%"><tr><th>{host}</th></tr>'.format(host=self.host)
        output += '<tr><td><pre style="max-width:100%;">{0}</pre></td></tr>'.format(self.__str__())
        output += '</table>'
        return output

    def _repr_html__bootstrap_(self):
        panel_context = 'panel-success'
        if self.ssh_retcode > 0:
            panel_context = 'panel-warning'
        if self.retcode > 0:
            panel_context = 'panel-danger'
        panel_start = '<div class="panel {panelcontext}">'.format(panelcontext=panel_context)
        panel_header = '<div class="panel-heading"><strong>{host}</strong></div>'.format(host=self.host)
        if self.bootstrap_show_retcodes:
            panel_header = '<div class="panel-heading"><strong>{host}</strong> SSH Response Code: {sshretcode} Return Code {retcode}</div>'.format(host=self.host, retcode=self.retcode, sshretcode=self.ssh_retcode)
        panel_body = '<div class="panel-body"><pre style="max-width:100%;">{output}</pre></div>'.format(output=self.output)
        panel_footer = ''
        panel_end = '</div>'
        return panel_start + panel_header + panel_body + panel_footer + panel_end

    def _repr_html_(self):
        if self.bootstrap:
            return self._repr_html__bootstrap_()
        return self._repr_html__plain_()

    def sequence_to_bytes(self, sequence):
        output = b''
        for line in sequence:
            if isinstance(line, bytes):
                output += line
            else:
                output += line.encode()
        return output

    def sequence_to_str(self, sequence):
        return self.sequence_to_bytes(sequence).decode(errors='ignore')

    def out_string(self):
        """ Return the output as a string """
        return self.sequence_to_str(self.out)

    def err_string(self):
        """ Return the err as a string """
        return self.sequence_to_str(self.err)

    def setting(self, key):
        """
        Get a setting from the parm dict or return None if it doesn't exist
        :param key:
        """
        return self.parm.get(key, None)

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
            sys.stdout.write('%d ' % self.retcode)
        if return_parm:
            sys.stdout.write('%d %s' % (self.ssh_retcode, self.parm))
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
    _executed = True
    parm = None
    bootstrap = True
    _ansi_repr = False
    ansi = False
    collapse = False

    def run(self):
        pass

    def __repr__(self):
        if self._ansi_repr:
            return self._repr_text_()

        if not self._executed:
            self.run()
        output = []
        for item in self.__iter__():
            output.append(item)
        return repr(output)

    def __str__(self):
        if not self._executed:
            self.run()
        output = ''
        for item in self.__iter__():
            output += item.host + os.linesep
            output += item.output + os.linesep
        return output

    def _repr_text_(self):
        if not self._executed:
            self.run()
        output = ''
        aggregate_hosts = self.setting('aggregate_hosts')
        collapsed_output = self.setting('collapsed_output')
        if self.collapse and aggregate_hosts and collapsed_output:
            for md5, hosts in aggregate_hosts.items():
                if self.ansi:
                    output += '\033[1m'
                output += ','.join(hostlists.compress(hosts))
                if self.ansi:
                    output += '\033[0m'
                output += os.linesep
                out, err = collapsed_output[md5]
                output += ''.join(out)
                output += ''.join(err)
                output += os.linesep
        else:
            for item in self.__iter__():
                if self.ansi:
                    output += '\033[1m'
                output += item.host
                if self.ansi:
                    output += '\033[0m'
                output += os.linesep
                output += item.output + os.linesep
        if output.endswith(os.linesep):
            return output[:-1]
        return output

    def _repr_html__plain_(self):
        """
        __repr__ in an html table format
        """
        if not self._executed:
            self.run()
        output = '<table width="100%">'
        for item in self.__iter__():
            output += '<tr><th>{0}</th></tr>'.format(item.host)
            output += '<tr><td><pre>{0}</pre></td></tr>'.format(item.output)
        output += '</table>'
        return output

    def _repr_html__bootstrap_(self):
        if not self._executed:
            self.run()
        aggregate_hosts = self.setting('aggregate_hosts')
        collapsed_output = self.setting('collapsed_output')
        output = '<row>'
        if self.collapse and aggregate_hosts and collapsed_output:
            for md5, hosts in aggregate_hosts.items():
                panel_start = '<div class="panel">'
                panel_header = '<div class="panel-heading"><strong>{host}</strong></div>'.format(host=','.join(hostlists.compress(hosts)))
                out, err = collapsed_output[md5]
                out = ''.join(out)
                err = ''.join(err)

                panel_body = '<div class="panel-body"><pre style="max-width:100%;">{0}{1}</pre></div>'.format(out, err)
                panel_footer = ''
                panel_end = '</div>'
                output += panel_start + panel_header + panel_body + panel_footer + panel_end
        else:
            for item in self.__iter__():
                output += item._repr_html__bootstrap_()
        output += '</row>'
        return output

    def _repr_html_(self):
        if self.bootstrap:
            return self._repr_html__bootstrap_()
        return self._repr_html__plain_()

    @property
    def output(self):
        if not self._executed:
            self.run()
        out = ''
        for item in self.__iter__():
            out += item.output
        return out

    def dump(self):
        """ Dump all the result objects """
        if not self._executed:
            self.run()
        for item in self.__iter__():
            item.dump(return_parm=False, return_retcode=False)
        print(self.parm)

    def print_output(self, summarize_failures=False):
        """ Print all the objects
        :param summarize_failures:
        """
        if not self._executed:
            self.run()
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
        if not self.parm:
            return
        return self.parm.get(key, None)


def agent_auth(transport, username):
    """
    Attempt to authenticate to the given transport using any of the private
    keys available from an SSH agent or from a local private RSA key file
    (assumes no pass phrase).
    :param transport:
    :param username:
    """

    agent = paramiko.Agent()
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
        except paramiko.SSHException as e:
            logging.debug('agent_auth failed! %s', e)


# A version of the paramiko.SSHClient that supports timeout
class fastSSHClient(paramiko.SSHClient):
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
        paramiko.agent.AgentRequestHandler(chan)
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
                bufsize=-1, log_to_file=False):
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
    :param log_to_file:
    """
    # Guess any parameters not passed that can be
    if isinstance(host, tuple):
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

    if log_to_file:
        paramiko.util.log_to_file('ssh.log')

    close_client = False
    if not client:
        # noinspection PyBroadException
        try:
            client = fastSSHClient()
        except:
            result.err = ['Error creating client']
            result.ssh_retcode = defaults.RUN_FAIL_UNKNOWN
            return result
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # load_system_host_keys slows things way down
        #client.load_system_host_keys()
        close_client = True
        # noinspection PyBroadException
    try:
        client.connect(host, username=username, password=password,
                       timeout=timeout)
    except paramiko.AuthenticationException:
        result.ssh_retcode = defaults.RUN_FAIL_AUTH
        return result
    except paramiko.SSHException:
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

    except (paramiko.SSHException, paramiko.transport.SSHException):
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
                t = open(script, 'r')
                template = t.read()
                t.close()
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
        # Read the output from stdout, stderr and close the connection
        result.out = stdout.readlines()
        result.err = stderr.readlines()
        if result.out and len(result.out) and isinstance(result.out[0], bytes):
            result.out = [r.decode('utf-8') for r in result.out]
        if result.err and len(result.err) and isinstance(result.err[0], bytes):
            result.err = [r.decode('utf-8') for r in result.err]
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
        kwargs['runner'],
        types.FunctionType
    ):
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
        script=None, timeout=None, sort=False, jobs=0, output_callback=None,
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

    if not output_callback:
        output_callback = [callback.summarize_failures]

    status_info(output_callback, 'Looking up hosts')

    # Expand the host range if we were passed a string host list
    if 'basestring' not in dir(__builtins__):
        # basestring is not in python3.x
        basestring = str

    if isinstance(host_range, basestring):
        hosts = hostlists.expand(hostlists.range_split(host_range))
    else:
        hosts = host_range

    if shuffle:
        random.shuffle(hosts)
    status_clear()
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
    client = fastSSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # load_system_host_keys slows things way down
    #client.load_system_host_keys()

    results.parm['total_host_count'] = len(hosts)
    results.parm['completed_host_count'] = 0

    status_clear()
    status_info(output_callback, 'Spawning processes')

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

    if isinstance(output_callback, list) and \
            callback.status_count in output_callback:
        callback.status_count(ssh_result(parm=results.parm))

    # Create a process pool and pass the parameters to it

    status_clear()
    status_info(
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
            if isinstance(output_callback, list):
                for cb in output_callback:
                    result = cb(result)
            else:
                # noinspection PyCallingNonCallable
                result = output_callback(result)
            results.parm = result.parm
            results.append(result)
            if exit_on_error and result.retcode != 0:
                break
        pool.close()
    except KeyboardInterrupt:
        print('ctrl-c pressed')
        pool.terminate()
    pool.terminate()
    if isinstance(output_callback, list) and \
            callback.status_count in output_callback:
        status_clear()
    return results


class SSHCommand(ssh_results):
    _jobs = defaults.JOB_MAX
    _executed = False
    output_callback = [callback.summarize_failures]
    parm = {}

    def __init__(
            self, host_range, command, username=None, password=None, sudo=False,
            script=None, timeout=None, sort=False, jobs=None, output_callback=None,
            parms=None, shuffle=False, chunksize=None, exit_on_error=False, collapse=False
    ):
        """
        A generic ssh command object class

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
        """
        self.host_range = host_range
        self.command = command
        self.username = username
        self.password = password
        self.sudo = sudo
        self.script = script
        self.timeout = timeout
        self.sort = sort
        self.collapse = collapse
        if collapse:
            self.output_callback.append(callback.aggregate_output)
        if jobs:
            self._jobs = int(jobs)
        if output_callback:
            self.output_callback = output_callback
        if parms:
            self.parm = parms

        self.shuffle = shuffle
        self._chunksize = chunksize
        self.exit_on_error = exit_on_error
        self.init_client()

    @property
    def hosts(self):
        # Expand the host range if we were passed a string host list
        if sys.version_info.major > 2:
            basestring = str

        host_list = self.host_range
        if isinstance(self.host_range, basestring):
            host_list = hostlists.expand(hostlists.range_split(self.host_range))
        if self.shuffle:
            random.shuffle(host_list)
        return host_list

    @property
    def jobs(self):
        if self._jobs > len(self.hosts):
            return len(self.hosts)
        return self._jobs

    @property
    def chunksize(self):
        if self._chunksize:
            if self._chunksize < 1:
                return 1
            if self._chunksize > 10:
                return 10

        if self.jobs == 1 or self.jobs >= len(self.hosts):
            return 1
        return int(len(self.hosts) / self.jobs) - 1

    def fail_all(self, retcode=defaults.RUN_FAIL_NOPASSWORD):
        for host in self.hosts:
            result = ssh_result(host=host, parm=self.parm)
            result.err = 'Sudo password required'
            result.retcode = defaults.RUN_FAIL_NOPASSWORD
            yield result
        self.parm['total_host_count'] = len(self.hosts)
        self.parm['completed_host_count'] = 0
        self.parm['failures'] = self.hosts

    def init_client(self):
        self.client = fastSSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def reset_parm(self):
        self.parm = dict(
            total_host_count=len(self.hosts),
            completed_host_count=0,
            chunksize=self.chunksize
        )

    def status_count(self):
        if not isinstance(self.output_callback, Iterable):
            return
        if callback.status_count not in list(self.output_callback):
            return
        callback.status_count(ssh_result(parm=self.parm))

    def run_iterate(self):
        """
        Run the ssh command
        """
        status_info(self.output_callback, 'Looking up hosts')
        self.reset_parm()

        status_clear()

        if not self.hosts:
            # No hosts to ssh to
            return

        if self.sudo and not self.password:
            for result in self.fail_all(defaults.RUN_FAIL_NOPASSWORD):
                yield result
            return

        status_info(self.output_callback, 'Spawning processes')
        pool = multiprocessing.Pool(processes=self.jobs, initializer=init_worker)
        map_command = pool.imap_unordered
        if self.sort:
            map_command = pool.imap

        # self.status_count()

        status_clear()
        status_info(self.output_callback, 'Sending %d commands to each process' % self.chunksize)
        self.status_count()

        try:
            for result in map_command(
                    run_command,
                    [
                        (
                                host, self.command, self.username, self.password, self.sudo, self.script, self.timeout,
                                self.parm, self.client
                        ) for host in self.hosts
                    ],
                    self.chunksize
            ):
                self._executed = True
                self.parm['completed_host_count'] += 1
                result.parm = self.parm
                if isinstance(self.output_callback, Iterable):
                    for cb in self.output_callback:
                        result = cb(result)
                else:
                    result = self.output_callback(result)
                self.parm = result.parm
                yield result
                if self.exit_on_error and result.retcode != 0:
                    break
            pool.close()
        except KeyboardInterrupt:
            print('ctrl-c pressed')
            pool.terminate()
        pool.terminate()
        if isinstance(self.output_callback, Iterable) and callback.status_count in self.output_callback:
            status_clear()

    def run(self):
        self.clear()
        for result in self.run_iterate():
            self.append(result)
        return self


# Old class names for backwards compatibility
class ssh_result(SSHResult):
    pass


if __name__ == "__main__":
    # The contents that where formerly here have been moved to the sshmap 
    # command line utility.  
    pass
