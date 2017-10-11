import os
import sys
from unittest import TestCase, main
from sshmap.arguments import parse_arguments
from sshmap.callback import aggregate_output, exec_command, filter_match, filter_base64, filter_json, output_prefix_host, status_count, \
    summarize_failures


class TestArguments(TestCase):
    _argv = None
    _stdout_isatty = None
    _stderr_isatty = None

    @staticmethod
    def _return_true():
        return True

    @staticmethod
    def _return_false():
        return False

    def setUp(self):
        self._argv = sys.argv
        self._stdout_isatty = sys.stdout.isatty
        self._stderr_isatty = sys.stderr.isatty
        sys.stdout.isatty = self._return_true
        sys.stderr.isatty = self._return_true

    def tearDown(self):
        if self._argv:
            sys.argv = self._argv
            self._argv = None
        if self._stdout_isatty:
            sys.stdout.isatty = self._stdout_isatty
        if self._stderr_isatty:
            sys.stderr.isatty = self._stderr_isatty

    def test__parse_arguments__none(self):
        sys.argv = ['sshmap']
        with self.assertRaises(SystemExit):
            result = parse_arguments()

    def test__parse_arguments__defaults(self):
        sys.argv = ['sshmap', 'testhost', 'id']
        result = parse_arguments()
        self.assertListEqual(result.command, ['id'])
        self.assertListEqual(result.hostrange, ['testhost'])
        self.assertFalse(result.aggregate_output, "aggregate_output is not False")
        self.assertListEqual(result.callbacks, [summarize_failures, output_prefix_host, status_count])

    def test__parse_arguments__collapse(self):
        sys.argv = ['sshmap', '--collapse', 'testhost', 'id']
        result = parse_arguments()
        self.assertListEqual(result.command, ['id'])
        self.assertListEqual(result.hostrange, ['testhost'])
        self.assertTrue(result.aggregate_output, "aggregate_output is not False")
        print(result.callbacks)
        self.assertListEqual(result.callbacks, [summarize_failures, aggregate_output, status_count])
