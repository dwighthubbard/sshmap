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
Python rpc remote runner handlers
"""
__author__ = 'dhubbard'
import os
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
