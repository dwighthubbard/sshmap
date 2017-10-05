# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.

import json
import os

from .callback import summarize_failures as callback_summarize_failures
from .callback import aggregate_output as callback_aggregate_output
from .callback import exec_command as callback_exec_command
from .callback import filter_match as callback_filter_match
from .callback import status_count as callback_status_count

from .sshmap import run, run_command, run_with_runner


_metadata_file = os.path.join(
    os.path.dirname(__file__),
    'package_metadata.json'
)


if os.path.exists(_metadata_file):  # pragma: no cover
    with open(_metadata_file) as fh:
        _package_metadata = json.load(fh)
        __version__ = str(_package_metadata.get('version', '0.0.0'))
        __git_version__ = str(_package_metadata.get('git_version', ''))
        __git_origin__ = str(_package_metadata.get('git_origin', ''))
        __git_branch__ = str(_package_metadata.get('git_branch', ''))
        __git_hash__ = str(_package_metadata.get('git_hash', ''))
        __git_base_url__ = 'https://github.com/yahoo/sshmap'
        if __git_origin__.endswith('.git'):  # pragma: no cover
            __git_base_url__ = __git_origin__[:-4].strip('/')
        __source_url__ = __git_base_url__ + '/tree/' + __git_hash__


__all__ = ['callback', 'defaults', 'runner', 'sshmap', 'utility']