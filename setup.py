#!/usr/bin/env python
# Copyright (c) 2010-2015, Yahoo Inc.
# Copyrights licensed under the Apache 2.0 License
# See the accompanying LICENSE.txt file for terms.
"""
sshmap package configuration
"""
import json
import os
from setuptools import setup


METADATA_FILENAME = 'sshmap/package_metadata.json'


def readme():
    with open('README.rst') as f:
        return f.read()


version_list = ['1','0','0']
if 'TRAVIS_BUILD_NUMBER' in os.environ.keys():
    version_list[-1] = os.environ['TRAVIS_BUILD_NUMBER']
else:
    revision = len(os.popen('git rev-list HEAD 2>/dev/null').readlines())
    if revision > 0:
        version_list[-1] = '{}'.format(revision)
version = '.'.join(version_list)


class Git(object):
    version_list = ['1', '0', '0']

    def __init__(self, version=None):
        if version:
            self.version_list = version.split('.')

    @property
    def version(self):
        """
        Generate a Unique version value from the git information
        :return:
        """
        git_rev = len(os.popen('git rev-list HEAD').readlines())
        if git_rev != 0:
            self.version_list[-1] = '%d' % git_rev
        version = '.'.join(self.version_list)
        return version

    @property
    def branch(self):
        """
        Get the current git branch
        :return:
        """
        return os.popen('git rev-parse --abbrev-ref HEAD').read().strip()

    @property
    def hash(self):
        """
        Return the git hash for the current build
        :return:
        """
        return os.popen('git rev-parse HEAD').read().strip()

    @property
    def origin(self):
        """
        Return the fetch url for the git origin
        :return:
        """
        for item in os.popen('git remote -v'):
            split_item = item.strip().split()
            if split_item[0] == 'origin' and split_item[-1] == '(push)':
                return split_item[1]


def get_and_update_metadata():
    """
    Get the package metadata or generate it if missing
    :return:
    """
    global METADATA_FILENAME
    global REDIS_SERVER_METADATA

    if not os.path.exists('.git') and os.path.exists(METADATA_FILENAME):
        with open(METADATA_FILENAME) as fh:
            metadata = json.load(fh)
    else:
        git = Git(version=setup_arguments['version'])
        metadata = {
            'git_version': git.version,
            'git_origin': git.origin,
            'git_branch': git.branch,
            'git_hash': git.hash,
            'version': git.version,
        }
        with open(METADATA_FILENAME, 'w') as fh:
            json.dump(metadata, fh, indent=4)
    return metadata


setup_arguments = dict(
    name="sshmap",
    version=version,
    author="Dwight Hubbard",
    author_email="dhubbard@yahoo-inc.com",
    url="https://github.com/yahoo/sshmap",
    license="LICENSE.txt",
    packages=["sshmap"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],
    description="A SSH Multiplexer designed to use ssh to perform map/reduce operations",
    requires=[
        'paramiko',
        'hostlists'
    ],
    extras_require={
        'test': ['nose', 'serviceping'],
        'django_template': ['django'],
        'all': ['django'],
    },
    install_requires=[
        'paramiko>=1.13.0',
        'hostlists>=0.6.9'
    ],
    package_data={
        'sshmap': ['package_metadata.json'],
    },
    include_package_data=True,
)
if os.path.isdir('scripts'):
    setup_arguments['scripts'] = [
        os.path.join('scripts', f) for f in os.listdir('scripts')
    ]


if __name__ == '__main__':
    metadata = get_and_update_metadata()
    setup_arguments['version'] = metadata['version']

    setup(**setup_arguments)