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
from serviceping import scan
import sshmap


NO_LOCAL_SSH = False


class TestSshmapCLI(unittest.TestCase):
    """
    sshmap command line unit tests
    """

    def __init__(self, *args, **kwargs):
        global NO_LOCAL_SSH

        if scan('localhost').get('state', 'closed'):
            NO_LOCAL_SSH = True
        self.logger = logging.getLogger('module_test')
        super(TestSshmapCLI, self).__init__(*args, **kwargs)

    @unittest.skipIf(NO_LOCAL_SSH, "No ssh server running on localhost")
    def test_shell_command_as_user(self):
        """Run a ssh command to localhost and verify it works """
        if NO_LOCAL_SSH:
            return
        po = os.popen('sshmap localhost echo hello')
        result = po.read().strip()
        po.close()
        self.assertEqual('localhost: hello', result)

    @unittest.skip('Sudo does not work in CI pipelines')
    def disable_test_shell_command_sudo(self):
        """Run a ssh command to localhost using sudo and verify it works"""
        result = os.popen('sshmap localhost --sudo id').read().strip()
        self.assertIn(
            'localhost: uid=0(root)', result
        )

    @unittest.skipIf(NO_LOCAL_SSH, "No ssh server running on localhost")
    def test_shell_script_as_user(self):
        if NO_LOCAL_SSH:
            return
        # Run a ssh command to localhost and verify it works
        sf = open('testscript.test', 'w')
        sf.write('#!/bin/bash\necho hello\n')
        sf.close()
        po = os.popen(
            'sshmap localhost --runscript testscript.test'
        )
        result = po.read().strip()
        po.close()
        self.assertEqual('localhost: hello', result)
        os.remove('testscript.test')

    @unittest.skip('Cannot mock sudo')
    def test_shell_script_sudo(self):
        """Run a ssh command to localhost and verify it works """
        open('testscript.test', 'w').write('#!/bin/bash\nid\n')
        result = os.popen(
            'sshmap localhost --runscript testscript.test --sudo '
            '--timeout 15'
        ).read().strip()
        self.assertIn(
            'localhost: uid=0(root)', result
        )
        os.remove('testscript.test')


if __name__ == '__main__':
    unittest.main()
