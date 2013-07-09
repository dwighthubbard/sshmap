#Copyright (c) 2012 Yahoo! Inc. All rights reserved.
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License. See accompanying LICENSE file.
"""
sshmap utility functions
"""
import sys
import callback

__author__ = 'dhubbard'


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
    if isinstance(callbacks, list) and \
            callback.status_count in callbacks:
        status_clear()
        sys.stderr.write(text)
        sys.stderr.flush()


def status_clear():
    """
    Clear the status line (current line)
    """
    sys.stderr.write('\x1b[0G\x1b[0K')
    #sys.stderr.flush()