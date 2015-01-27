#!/usr/bin/env python3
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
        po = os.popen('sshmap/sshmap localhost echo hello')
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
        result = os.popen('sshmap/sshmap localhost --sudo id').read().strip()
        self.assertIn(
            'localhost: uid=0(root)', result
        )

    def test_shell_script_as_user(self):
        # Run a ssh command to localhost and verify it works
        sf = open('testscript.test', 'w')
        sf.write('#!/bin/bash\necho hello\n')
        sf.close()
        po = os.popen(
            'sshmap/sshmap localhost --runscript testscript.test'
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
            'sshmap/sshmap localhost --runscript testscript.test --sudo '
            '--timeout 15'
        ).read().strip()
        self.assertIn(
            'localhost: uid=0(root)', result
        )
        os.remove('testscript.test')


if __name__ == '__main__':
    unittest.main()
