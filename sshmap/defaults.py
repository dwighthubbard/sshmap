# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
Default Values for sshmap
"""
__author__ = 'dhubbard'
import os

# Defaults
JOB_MAX = 100
# noinspection PyBroadException
try:
    for line in open('/proc/%d/limits' % os.getpid(), 'r').readlines():
        if line.startswith('Max processes'):
            JOB_MAX = int(line.strip().split()[2]) / 4
except:
    pass

# Return code values
RUN_OK = 0
RUN_FAIL_AUTH = 1
RUN_FAIL_TIMEOUT = 2
RUN_FAIL_CONNECT = 3
RUN_FAIL_SSH = 4
RUN_SUDO_PROMPT = 5
RUN_FAIL_UNKNOWN = 6
RUN_FAIL_NOPASSWORD = 7
RUN_FAIL_BADPASSWORD = 8

# Text return codes
RUN_CODES = ['Ok', 'Authentication Error', 'Timeout', 'SSH Connection Failed',
             'SSH Failure',
             'Sudo did not send a password prompt', 'Connection refused',
             'Sudo password required',
             'Invalid sudo password']

# Configuration file field descriptions
conf_desc = {
    "username": "IRC Server username",
    "password": "IRC Server password",
    "channel": "sshmap",
}

# Configuration file defaults
conf_defaults = {
    "address": "chat.freenode.net",
    "port": "6667",
    "use_ssl": False,
}

sudo_message = [
    'We trust you have received the usual lecture from the local System',
    'Administrator. It usually boils down to these three things:',
    '#1) Respect the privacy of others.',
    '#2) Think before you type.',
    '#3) With great power comes great responsibility.'
]
