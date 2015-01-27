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


class TestSshmapModule(unittest.TestCase):
    """
    sshmap command line unit tests
    """
    def test__run__as_user(self):
        """Run a ssh command to localhost and verify it works """
        result = sshmap.run('localhost', 'echo hello')
        self.assertEqual('hello\n', result[0].out_string())

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
        self.assertEqual('hello\n', result[0].out_string())
        os.remove('testscript.test')


if __name__ == '__main__':
    unittest.main()
