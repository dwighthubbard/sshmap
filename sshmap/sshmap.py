#!/usr/bin/env python
""" Python based ssh multiplexer optimized for map operations """

"""
 Copyright (c) 2010 Yahoo! Inc. All rights reserved.
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
import urllib
import urllib2
import getpass
import socket
import types
import base64
import time
import re
import random
import signal
from optparse import OptionParser
import multiprocessing
import subprocess
import traceback

# Imports from external python extension modules
import paramiko

# Imports from other sshmap modules
import hostlists

# Defaults
JOB_MAX=65
try:
  for line in open('/proc/%d/limits'%os.getpid(),'r').readlines():
    if line.startswith('Max processes'):
 	JOB_MAX=int(line.strip().split()[2])/3
except:
  pass

# Return code values
RUN_OK=0
RUN_FAIL_AUTH=1
RUN_FAIL_TIMEOUT=2
RUN_FAIL_CONNECT=3
RUN_FAIL_SSH=4
RUN_SUDO_PROMPT=5
RUN_FAIL_UNKNOWN=6

# Text return codes
RUN_CODES=['Ok','Authentication Error','Timeout','SSH Connection Failed','SSH Failure','Sudo did not send a password prompt','Connection refused']

# Configuration file field descriptions
conf_desc={
        "username":"IRC Server username",
        "password":"IRC Server password",
        "channel":"sshmap",
}

# Configuration file defaults 
conf_defaults={
        "address":"chat.freenode.net",
        "port":"6667",
        "use_ssl":False,
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
  def __init__(self,out=[],err=[],host=None,retcode=0,ssh_ret=0,parm=None):
    self.out=out
    self.err=err
    self.retcode=retcode
    self.ssh_retcode=ssh_ret
    self.parm=parm
    self.host=host
  def out_string(self):
    """ Return the output as a string """
    return ''.join(self.out)
  def err_string(self):
    """ Return the err as a string """
    return ''.join(self.err)
  def setting(self,key):
    """ Get a setting from the parm dict or return None if it doesn't exist """
    return get_parm_val(self.parm,key)
  def ssh_error_message(self):
    """ Return the ssh_error_message for the error code """
    return RUN_CODES[self.ssh_retcode]
  def dump(self):
    """ Print all our public values """
    print self.host,self.out_string().replace('\n',''),self.err_string().replace('\n',''),self.retcode,self.ssh_retcode,self.parm
  def print_output(self):
    """ Print output from the commands """
    for line in self.out:
      print '%s:'%self.host,line.strip()
    for line in self.err:
      print '%s:' %self.host,line.strip()

class ssh_results(list):
  """
  ssh_results class, provides 2 things, an iterator to iterate over ssh_result objects
  and a single variable parm which contains the parm parameter after the completion of 
  all the result objects (the parm variable contains the global variables used and
  provided by the callbacks)
  """
  parm=None
  def dump(self):
    """ Dump all the result objects """
    for item in self.__iter__():
      item.dump()
  def print_output(self):
    """ Print all the objects """
    for item in self.__iter__():
      item.print_output()

class fastSSHClient(paramiko.SSHClient):
  """ Paramiko SSHClient class extended with timeout support """
  def exec_command(self, command, bufsize=-1, timeout=None):
    chan = self._transport.open_session()
    chan.settimeout(timeout)
    chan.exec_command(command)
    stdin = chan.makefile('wb', bufsize)
    stdout = chan.makefile('rb', bufsize)
    stderr = chan.makefile_stderr('rb', bufsize)
    return stdin, stdout, stderr, chan

def run_command(host,command="uname -a",username=None,password=None,sudo=False,script=None,timeout=None,parms=None,client=None,bufsize=-1,cwd='/tmp',logging=False):
  """ 
  Run a command or script on a remote node via ssh 
  """
  # Guess any parameters not passed that can be
  if isinstance(host,types.TupleType):
    host,command,username,password,sudo,script,timeout,parms,client=host
  if timeout == 0:
    timeout=None
  if not username:
    username=getpass.getuser()
  if bufsize==-1 and script:
    bufsize=os.path.getsize(script)+1024

  # Get a result object to put our output in
  result=ssh_result(host=host,parm=parms)

  if logging:
    paramiko.util.log_to_file('paramiko.log')

  close_client=False
  if not client:
    client=fastSSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # load_system_host_keys slows things way down
    #client.load_system_host_keys()
    close_client=True
  try:
    client.connect(host, username=username,  password=password,timeout=timeout)
  except paramiko.AuthenticationException:
    result.ssh_retcode=RUN_FAIL_AUTH
    return result
  except paramiko.SSHException:
    result.ssh_retcode=RUN_FAIL_CONNECT
    return result
  except AttributeError:
    result.ssh_retcode=RUN_FAIL_SSH
    return result
  except socket.error:
    result.ssh_retcode=RUN_FAIL_CONNECT
    return result
  except:
    result.ssh_retcode=RUN_FAIL_UNKNOWN
    return result
  try:
      # Force a sudo -k first or we can't reliably know we'll be prompted for our password
    if sudo:
      stdin,  stdout,  stderr, chan = client.exec_command('sudo -k;sudo "%s"' % command,timeout=timeout,bufsize=bufsize)
    else:
      stdin,  stdout,  stderr,chan = client.exec_command(command,timeout=timeout,bufsize=bufsize)
  except paramiko.SSHException, paramiko.transport.SSHException:
      result.ssh_retcode=RUN_FAIL_SSH
      return result
  if sudo:
    stdin.write(password+'\r')
    stdin.flush()
    prompt =stderr.readline()
    if prompt.lower().find('password') == -1:
      result.err=[prompt.strip()]
      result.out=[]
      result.ssh_retcode=RUN_SUDO_PROMPT
      return result
  if script:
    # Pass the script over stdin and close the channel so the receving end gets an EOF
    stdin.write(open(script,'r').read())
    stdin.flush()
    stdin.channel.shutdown_write()
  try:
    # Read the output from stdout,stderr and close the connection
    result.out=stdout.readlines()
    result.err=stderr.readlines()
    result.retcode=chan.recv_exit_status()
    if close_client:
      client.close()
  except socket.timeout:
    result.ssh_retcode=RUN_FAIL_TIMEOUT
    return result
  result.ssh_retcode=RUN_OK
  return result

""" Handy utility functions """
def get_parm_val(parm=None,key=None):
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

def status_info(callbacks,text):
  """ 
  Update the display line at the cursor 
  """
  if isinstance(callbacks,types.ListType) and callback_status_count in callbacks:
    print >> sys.stderr,'\x1b[0G\x1b[0%s'%text,
    sys.stderr.flush()

def status_clear():
  """ 
  Clear the status line (current line) 
  """
  sys.stderr.write('\x1b[0G\x1b[0K')
  sys.stderr.flush()

def read_conf(key=None,prompt=True):
    """ Read settings from the config file """
    try:
        conf=json.load(open(os.path.expanduser('~/.fastssh2.conf'),'r'))
    except IOError:
        conf=conf_defaults
    if key:
        try:
            return conf[key].encode('ascii')
        except KeyError:
            pass
    else:
        return conf
    if key and prompt:
        conf[key]=raw_input(conf_desc[key]+': ')
        fh=open(os.path.expanduser('~/.fastssh2.conf'),'w')
	os.fchmod(fh.fileno(),stat.S_IRUSR|stat.S_IWUSR)
        json.dump(conf,fh)
	fh.close()
        return conf[key]
    else:
        return None

""" Filter callback handlers """
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
  failures=result.setting('failures')
  if not failures:
    result.parm['failures']=[]
    failures=[]
  if result.ssh_retcode:
    failures.append(result.host)
    result.parm['failures']=failures
  return result

def callback_exec_command(result):
  """ 
  Builtin Callback, pass the results to a command/script 
  """
  script=result.setting("callback_script")
  if not script:
    return result
  status_clear()
  result_out,result_err=subprocess.Popen(script + " "+result.host, shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate(result.out_string()+result.err_string())
  result.out=[result_out]
  result.err=[result_err]
  print result.out_string()
  return result

def callback_filter_match(result):
  """
  Builtin Callback, remove all output if the string is not found in the output
  similar to grep
  """
  if result.out_string().find(result.setting('match')) == -1 and result.err_string().find(result.setting('match')) == -1:
    result.out=''
    result.err=''
  return result

def callback_filter_json(result):
  """ 
  Builtin Callback, change stdout to json

  >>> result=callback_filter_json(ssh_result(["output"], ["error"],"foo", 0))
  >>> result.dump()
  foo [["output"], ["error"], 0] error 0 0 None
  """
  result.out=[json.dumps((result.out,result.err,result.retcode))]
  return result

def callback_filter_base64(result):
  """ 
  Builtin Callback, base64 encode the info in out and err streams 
  """
  result.out=[base64.b64encode(result.out_string)]
  result.err=[base64.b64encode(result.err_string)]
  return result

""" Status callback handlers """
def callback_status_count(result):
  """ 
  Builtin Callback, show the count complete/remaining 
    """
  # The master process inserts the status into the
  # total_host_count and completed_host_count variables
  sys.stderr.write('\x1b[0G\x1b[0K%s/%s'%(result.setting('completed_host_count'),result.setting('total_host_count')))
  sys.stderr.flush()
  return result

""" Output callback handlers """
def callback_output_prefix_host(result):
  """ 
  Builtin Callback, print the output with the hostname: prefixed to each line 

  >>> result=callback_output_prefix_host(ssh_result(['out'],['err'], 'hostname', 0))
  hostname: out
  >>> result.dump()
  hostname hostname: out hostname: Error: err 0 0 None
  """
  output=[]
  error=[]
  status_clear()
  # If summarize_failures option is set don't print ssh errors inline
  if result.setting('summarize_failed') and result.ssh_retcode:
    return result
  if result.setting('print_rc'):
    rc=' SSH_Returncode: %d\tCommand_Returncode: %d' % (result.ssh_retcode,result.retcode)
  else:
    rc=''
  if result.ssh_retcode:
    print >> sys.stderr, '%s: %s' % (result.host,result.ssh_error_message())
    error=['%s: %s' % (result.host,result.ssh_error_message())]
  if len(result.out_string()):
    for line in result.out:
      if line:
        print '%s:%s %s' % (result.host,rc,line.strip())
        output.append('%s:%s %s\n' % (result.host,rc,line.strip()))
  if len(result.err_string()):
    for line in result.err:
      if line:
        print >> sys.stderr, '%s:%s %s' % (result.host,rc,line.strip())
        error.append('%s:%s Error: %s\n' % (result.host,rc,line.strip()))
  if result.setting('output'):
    if not len(result.out_string()) and not len(result.err_string()) and not result.setting('only_output') and result.setting('print_rc'):
        print '%s:%s' % (result.host,rc) 
    sys.stdout.flush()
    sys.stderr.flush()
  result.out=output
  result.err=error
  return result

def init_worker():
  """ Set up the signal handler for new worker threads """
  signal.signal(signal.SIGINT, signal.SIG_IGN)

def run(range,command,username=None,password=None,sudo=False,script=None,timeout=None,sort=False,bufsize=-1,cwd='/tmp',jobs=None,output_callback=callback_summarize_failures,parms=None,shuffle=False):
  """ 
  Run a command on a hostlists range of hosts   
  >>> res=run_command_on_range(range='localhost',command="echo ok")
  >>> print res[0].dump()
  localhost ok  0 0 {'failures': [], 'total_host_count': 1, 'completed_host_count': 1}
  None
  """
  status_info(output_callback,' \bLooking up hosts')
  hosts=hostlists.expandrange(range,compress=False).split(',')
  if shuffle:
    random.shuffle(hosts)
  status_clear()
  results=ssh_results()
  if parms:
    results.parm=parms
  else:
    results.parm={}
  if jobs < 1:
    jobs=1
  if jobs > JOB_MAX:
    jobs=JOB_MAX

  # Set up our ssh client
  #status_info(output_callback,' \bSetting up the SSH client')
  client=fastSSHClient()
  client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  # load_system_host_keys slows things way down
  #client.load_system_host_keys()

  results.parm['total_host_count']=len(hosts)
  results.parm['completed_host_count']=0
  if isinstance(output_callback,types.ListType) and callback_status_count in output_callback:
      callback_status_count(ssh_result(parm=results.parm))
  pool=multiprocessing.Pool(processes=jobs,initializer=init_worker)
  if sort:
    map_command=pool.imap
  else:
    map_command=pool.imap_unordered

  # Create a process pool and pass the parameters to it
  #status_info(output_callback,' \bSpawning processes')
  try:
    for result in map_command(run_command,[(host,command,username,password,sudo,script,timeout,results.parm,client) for host in hosts]):
      #status_info(output_callback,' \bLoop start')
      results.parm['completed_host_count']=results.parm['completed_host_count']+1
      result.parm=results.parm
      if isinstance(output_callback,types.ListType):
        for callback in output_callback:
          #print 'callback',callback,len(multiprocessing.active_children())
          result=callback(result)
      else:
        result=output_callback(result)
      results.parm=result.parm
      results.append(result)
  except KeyboardInterrupt:
    #print 'ctrl-c pressed'
    pool.terminate()
  except:
    #print 'unknown error encountered'
    pass
  pool.terminate()
  if isinstance(output_callback,types.ListType) and callback_status_count in output_callback:
    status_clear()
  return results

if __name__=="__main__":
  parser = OptionParser()
  #parser.add_option("--html", dest="html", default=False,action="store_true", help="Use HTML for formatting")
  parser.add_option("--output_json", dest="output_json", default=False,action="store_true", help="Output in JSON format")
  parser.add_option("--output_base64",dest="output_base64",default=False,action="store_true",help="Output in base64 format")
  parser.add_option("--summarize_failed", dest="summarize_failed", default=False,action="store_true", help="Print a list of hosts that failed at the end")
  parser.add_option("--only_output",dest="only_output", default=False,action="store_true",help="Only print lines for hosts that return output")
  parser.add_option("--jobs","-j",dest="jobs",default=65,type="int",help="Number of parallel commands to execute")
  parser.add_option("--timeout",dest="timeout",type="int",default=0, help="Timeout, or 0 for no timeout")
  parser.add_option("--sort",dest="sort",default=False,action="store_true",help="Print output sorted in the order listed")
  parser.add_option("--shuffle",dest="shuffle",default=False,action="store_true",help="Shuffle (randomize) the order of hosts")
  parser.add_option("--print_rc",dest="print_rc",default=False,action="store_true",help="Print the return code value")
  parser.add_option("--match",dest="match",default=None,help="Only show host output if the string is found in the output")
  parser.add_option("--runscript","--run_script",dest="runscript",default=None,help="Run a script on all hosts.  The command value is the shell to pass the script to on the remote host.")
  parser.add_option("--callback_script",dest="callback_script",default=None,help="Script to process the output of each host.  The hostname will be passed as the first argument and the stdin/stderr from the host will be passed as stdin/stderr of the script") 
  parser.add_option("--no_status",dest="show_status",default=True,action="store_false",help="Don't show a status count as the command progresses")
  parser.add_option("--sudo",dest="sudo",default=False,action="store_true",help="Use sudo to run the command as root")
  parser.add_option("--password",dest="password",default=None,action="store_true",help="Prompt for a password")
  
  (options, args) = parser.parse_args()

  if len(args) == 1 and options.runscript:
    firstline=open(options.runscript).readline().strip()
    if firstline.startswith('#!'):
      command=firstline[2:]
      args.append(command)

  # Default option values
  options.password=None
  options.username=getpass.getuser()
  options.output=True

  # Create our callback pipeline based on the options passed
  callback=[callback_summarize_failures]
  if options.match:
    callback.append(callback_filter_match)
  if options.output_base64:
    callback.append(callback_filter_base64)
  if options.output_json:
    callback.append(callback_filter_json)
  if options.callback_script:
    callback.append(callback_exec_command)
  else:
    callback.append(callback_output_prefix_host)
  if options.show_status:
    callback.append(callback_status_count)

  # Get the password if the options passed indicate it might be needed
  if options.sudo:
    # Prompt for password
    options.password=getpass.getpass('Enter sudo password for user '+getpass.getuser()+': ')
  elif options.password:
    # Prompt for password
    options.password=getpass.getpass('Enter password for user '+getpass.getuser()+': ')


  command=' '.join(args[1:])
  range=args[0]

  results=run(args[0],command,username=options.username,password=options.password,sudo=options.sudo,timeout=options.timeout,script=options.runscript,jobs=options.jobs,sort=options.sort,shuffle=options.shuffle,output_callback=callback,parms=vars(options))

  # Print the failure summary if it was requested and there are failures
  if options.summarize_failed and 'failures' in results.parm.keys() and len(results.parm['failures']):
    print 'SSH Failed to: %s' % hostlists.compress(results.parm['failures'])
