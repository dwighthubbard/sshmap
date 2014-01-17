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
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name="sshmap",
    version="0.5.62",
    author="Dwight Hubbard",
    author_email="dhubbard@yahoo-inc.com",
    url="https://github.com/yahoo/sshmap",
    license="LICENSE.txt",
    packages=["sshmap"],
    scripts=["sshmap/sshmap"],
    long_description=open('README.txt').read(),
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
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],
    description="A SSH Multiplexer designed to use ssh to perform map/reduce"
                " operations",
    requires=['ssh', 'hostlists', 'django'],
    install_requires=['ssh', 'hostlists', 'django'],
)
