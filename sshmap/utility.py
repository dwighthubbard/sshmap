# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
sshmap utility functions
"""
from __future__ import print_function
import os
import subprocess
import sys
import textwrap


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
    sys.stderr.flush()


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


def header(text='', width=None, separator=None, outfile=None, collapse=False):
    """
    Display a textual header message.
    Parameters
    ----------
    text : str
        The text to print/display
    width : int, optional
        The width (text wrap) of the header message.
        This will be the current terminal width as determined
        by the 'stty size' shell command if not specified.
    separator : str, optional
        The character or string to use as a horizontal
        separator.  Will use '=' if one is not specified.
    outfile : File, optional
        The File object to print the header text to.
        This will use sys.stdout if not specified.
    :return:
    """
    if not outfile:
        outfile = sys.stdout
    width = width or get_terminal_size()[1]
    separator = separator or '='
    # Screwdriver buffers stdout and stderr separately.  This can
    # cause output from previous operations to show after our
    # header text.  So we flush the output streams to ensure
    # all existing output is sent/displayed before printing our
    # header.
    sys.stderr.flush()
    outfile.flush()

    if collapse:
        for line in textwrap.wrap(text, width=width-4):
            header_line = separator + ' ' + line + ' ' + \
                separator * (width - 4 - len(line))
            print(header_line, file=outfile)
    else:
        # Print the header text
        horiz = separator * width
        print(horiz, file=outfile)
        print(
            os.linesep.join(textwrap.wrap(text, width=width)),
            file=outfile
        )
        print(horiz, file=outfile)

    # Once again flush our header to the output stream so things
    # show up in the correct order.
    sys.stderr.flush()
    outfile.flush()
