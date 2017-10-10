import sys
import unittest
import sshmap.utility
try:
    from unittest.mock import MagicMock
    from unittest.mock import patch
except ImportError:
    MagicMock = None



class TestUtility(unittest.TestCase):

    @unittest.skipUnless(MagicMock, "MagicMock is required")
    def test__get_terminal_size__no_tty(self):
        with patch.object(sys.stdout, 'isatty', return_value=False):
            result = sshmap.utility.get_terminal_size()
        self.assertEqual(result, (24, 80,))
