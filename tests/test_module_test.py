#!/usr/bin/env python3
# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
Unit tests of sshmap
"""
import logging
import os
import unittest
import sshmap
from serviceping import scan


NO_LOCAL_SSH = False


class TestSshmapModule(unittest.TestCase):
    """
    sshmap command line unit tests
    """

    def __init__(self, *args, **kwargs):
        global NO_LOCAL_SSH

        if scan('localhost').get('state', 'closed'):
            NO_LOCAL_SSH = True
        self.logger = logging.getLogger('module_test')
        super(TestSshmapModule, self).__init__(*args, **kwargs)

    @unittest.skipIf(NO_LOCAL_SSH, "No ssh server running on localhost")
    def test__run__as_user(self):
        """Run a ssh command to localhost and verify it works """
        result = sshmap.run('localhost', 'echo hello')
        if result[0].ssh_retcode == 3:
            self.logger.warning('Could not connect to localhost')
            return
        self.assertEqual('hello\n', result[0].out_string())

    @unittest.skipIf(NO_LOCAL_SSH, "No ssh server running on localhost")
    def test__run_shell_script_as_user(self):
        # Run a ssh command to localhost and verify it works
        sf = open('testscript.test', 'w')
        sf.write('#!/bin/bash\necho hello\n')
        sf.close()

        result = sshmap.run(
            'localhost',
            '/bin/bash',
            script='testscript.test'
        )
        if result[0].ssh_retcode == 3:
            self.logger.warning('Could not connect to localhost')
            return
        self.assertEqual('hello\n', result[0].out_string())
        os.remove('testscript.test')


if __name__ == '__main__':
    unittest.main()
