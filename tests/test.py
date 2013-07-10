#!/usr/bin/env python
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
__author__ = 'dhubbard'
import sshmap
import os
import unittest

class TestSSH(unittest.TestCase):
    """
    sshmap unit tests
    """
    def set_up(self):
        pass

    def test_shell_command_as_user(self):
        # Run a ssh command to localhost and verify it works
        result = os.popen('sshmap/sshmap localhost echo hello').read().strip()
        self.assertEqual('localhost: hello', result)

    def test_shell_command_sudo(self):
        # Run a ssh command to localhost and verify it works
        result = os.popen('sshmap/sshmap localhost --sudo id').read().split('\n')[-1].strip()
        self.assertIn(result, 'localhost: uid=0(root) gid=0(root) groups=0(root)')

    def test_shell_script_as_user(self):
        # Run a ssh command to localhost and verify it works
        open('testscript.test', 'w').write('#!/bin/bash\necho hello\n')
        result = os.popen('sshmap/sshmap localhost --runscript testscript.test').read().strip()
        self.assertEqual('localhost: hello', result)
        os.remove('testscript.test')


if __name__ == '__main__':
    unittest.main()