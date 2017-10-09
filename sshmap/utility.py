# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
sshmap utility functions
"""
import subprocess
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
    if not sys.stderr.isatty():
        return

    if isinstance(callbacks, list):
        if 'status_count' in callback_names(callbacks):
            status_clear()
            sys.stderr.write(text)
            sys.stderr.flush()


def status_clear():
    """
    Clear the status line (current line)
    """
    if not sys.stderr.isatty():
        return

    sys.stderr.write('\x1b[0G\x1b[0K')


def get_terminal_size(default_columns=80, default_rows=24):
    """
    Get the terminal rows and columns if we are running on an
    interactive terminal.
    Returns
    -------
    rows : int
        The number of rows on the current terminal.
    columns : int
        The number of columns on the current terminal.
    """
    rows = int(default_rows)
    columns = int(default_columns)

    if not sys.stdout.isatty():
        return rows, columns

    try:
        output = subprocess.check_output(['stty', 'size'])
    except subprocess.CalledProcessError:
        return rows, columns

    try:
        rows, columns = output.split()
    except ValueError:  # pragma: no cover
        return rows, columns

    rows = int(rows)
    columns = int(columns)

    if not rows:
        rows = int(default_rows)
    if not columns:
        columns = int(default_columns)

    return rows, columns
