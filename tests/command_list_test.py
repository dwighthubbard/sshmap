#!/usr/bin/env python3
# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
Unit tests of sshmap
"""
__author__ = 'dhubbard'
import sshmap
import os
import unittest


class TestSshmapCLI(unittest.TestCase):
    """
    sshmap command line unit tests
    """

    def test_shell_command_as_user(self):
        """Run a ssh command to localhost and verify it works """
        po = os.popen('sshmap localhost echo hello')
        result = po.read().strip()
        po.close()
        self.assertEqual('localhost: hello', result)

    # Disabled since it won't work when running ci in a virtualenv
    # def test_python3_shell_command_as_user(self):
    #     """Run a ssh command to localhost and verify it works """
    #     po = os.popen('python3 sshmap/sshmap localhost echo hello')
    #     result = po.read().strip()
    #     po.close()
    #     self.assertEqual('localhost: hello', result)

    # Disabled because it prompts for sudo password which isn't compatible with
    # CI
    def disable_test_shell_command_sudo(self):
        """Run a ssh command to localhost using sudo and verify it works"""
        result = os.popen('sshmap localhost --sudo id').read().strip()
        self.assertIn(
            'localhost: uid=0(root)', result
        )

    def test_shell_script_as_user(self):
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

    # Disabled since it won't work with ci in a virutalenv
    # def test_python3_shell_script_as_user(self):
    #     # Run a ssh command to localhost and verify it works
    #     sf = open('testscript.test', 'w')
    #     sf.write('#!/bin/bash\necho hello\n')
    #     sf.close()
    #     po = os.popen(
    #         'python3 sshmap/sshmap localhost --runscript testscript.test'
    #     )
    #     result = po.read().strip()
    #     po.close()
    #     self.assertEqual('localhost: hello', result)
    #     os.remove('testscript.test')

    # Disabled because it prompts for sudo password which isn't compatible with
    # CI
    def disable_test_shell_script_sudo(self):
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
