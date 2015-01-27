#!/usr/bin/python
#Copyright (c) 2012-2014 Yahoo! Inc. All rights reserved.
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License. See accompanying LICENSE file.
"""
sshmap package configuration
"""
import os
from setuptools import setup


version_list = ['0','7','0']
if 'TRAVIS_BUILD_NUMBER' in os.environ.keys():
    version_list[-1] = os.environ['TRAVIS_BUILD_NUMBER']
else:
    revision = len(os.popen('git rev-list HEAD 2>/dev/null').readlines())
    if revision > 0:
        version_list[-1] = '{}'.format(revision)
version = '.'.join(version_list)


setup(
    name="sshmap",
    version=version,
    author="Dwight Hubbard",
    author_email="dhubbard@yahoo-inc.com",
    url="https://github.com/yahoo/sshmap",
    license="LICENSE.txt",
    packages=["sshmap"],
    scripts=["sshmap/sshmap"],
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
    description="A SSH Multiplexer designed to use ssh to perform map/reduce "
                "operations",
    requires=['paramiko', 'hostlists'],
    install_requires=['paramiko>=1.13.0', 'hostlists>=0.6.9']
)

