# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
Python rpc remote runner handlers
"""
__author__ = 'dhubbard'
import base64


script_stdin = """import os
os.popen(\"{command}\".decode('base64').decode('{compressor}'),'w').write(\"\"\"{input}\"\"\".decode('base64').decode('{compressor}'))
"""

script_sudo = """import os
command = \"{command}\".decode('base64').decode('{compressor}')
fh = os.popen(\"sudo -S \" + command,'w')
fh.write(\"{password}\\n\")
fh.write(\"\"\"{input}\"\"\".decode('base64').decode('{compressor}'))
"""

def get_runner(command, input, password='', runner_script=None,
               compressor='bz2'):
    if not runner_script:
        runner_script = script_stdin

    if compressor not in ['bz2', 'zlilb']:
        compressor = 'bz2'

    base64_command = base64.b64encode(command.encode('bz2'))
    base64_input = base64.b64encode(input.encode('bz2'))

    return runner_script.format(
        command=base64_command,
        input=base64_input,
        compressor=compressor,
        password=password
    )
