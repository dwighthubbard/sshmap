Description
sshmap is a python scriptable ssh multiplexer optimized for performing 
parallel map operations via ssh.

sshmap provides 3 python modules in order to operate:
  sshmap - This module provides the multiprocessing ssh functionality

The other two modules have been moved to a seperate package named hostlists
  hostlists - This module handles hostlist expansion
  hostlists_plugins - This module contains plugins that can be used
                      by the hostlists plugin to obtain lists of hosts. 

Dependencies
sshmap uses one open source library.

This file summarizes the tools used, their purpose, and the licenses under
which they're released.

* paramiko 1.7.7.2 (LGPL license)

This is a library for making SSH2 connections (client or server). Emphasis
is on using SSH2 as an alternative to SSL for making secure connections
between python scripts. All major ciphers and hash methods are supported.
SFTP client and server mode are both supported too.

[http://www.lag.net/paramiko/]

--------
Changelog
