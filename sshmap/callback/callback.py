#!/usr/bin/env python
""" Python based ssh multiplexer optimized for map operations """

"""
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

""" Filter callback handlers """
def flowthrough(result):
  """ 
  Builtin Callback, return the raw data passed
  
  >>> result=callback_flowthrough(ssh_result(["output"], ["error"],"foo", 0))
  >>> result.dump()
  foo output error 0 0 None
  """
  return result

def summarize_failures(result):
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

def exec_command(result):
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

def filter_match(result):
  """
  Builtin Callback, remove all output if the string is not found in the output
  similar to grep
  """
  if result.out_string().find(result.setting('match')) == -1 and result.err_string().find(result.setting('match')) == -1:
    result.out=''
    result.err=''
  return result

def filter_json(result):
  """ 
  Builtin Callback, change stdout to json

  >>> result=callback_filter_json(ssh_result(["output"], ["error"],"foo", 0))
  >>> result.dump()
  foo [["output"], ["error"], 0] error 0 0 None
  """
  result.out=[json.dumps((result.out,result.err,result.retcode))]
  return result

def filter_base64(result):
  """ 
  Builtin Callback, base64 encode the info in out and err streams 
  """
  result.out=[base64.b64encode(result.out_string)]
  result.err=[base64.b64encode(result.err_string)]
  return result

""" Status callback handlers """
def status_count(result):
  """ 
  Builtin Callback, show the count complete/remaining 
    """
  # The master process inserts the status into the
  # total_host_count and completed_host_count variables
  sys.stderr.write('\x1b[0G\x1b[0K%s/%s'%(result.setting('completed_host_count'),result.setting('total_host_count')))
  sys.stderr.flush()
  return result

""" Output callback handlers """
def output_prefix_host(result):
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
          