# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
sshmap utility functions
"""
import sys


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


def callback_names(callbacks):
    """"
    Return the name of the callback functions passed
    """
    names = []
    for item in callbacks:
        names.append(item.__name__)
    return names


def status_info(callbacks, text):
    """
    Update the display line at the cursor
    """
    #print callbacks,text
    #return
    if isinstance(callbacks, list):
        if 'status_count' in callback_names(callbacks):
            status_clear()
            sys.stderr.write(text)
            sys.stderr.flush()


def status_clear():
    """
    Clear the status line (current line)
    """
    sys.stderr.write('\x1b[0G\x1b[0K')
    #sys.stderr.flush()