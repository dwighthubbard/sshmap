sshmap 
******

.. image:: https://travis-ci.org/yahoo/sshmap.svg
    :target: https://travis-ci.org/yahoo/sshmap
    
Description
===========

sshmap is a python scriptable ssh multiplexer optimized for performing 
parallel map operations via ssh.

sshmap provides a python module in order to operate:
  sshmap - This module provides the multiprocessing ssh functionality

Dependencies
============

sshmap uses two open source modules.

This file summarizes the tools used, their purpose, and the licenses under
which they're released.

paramiko (LGPL license)
+++++++++++++++++++++++

This is a python module for making SSH2 connections (client or server). 
Emphasis is on using SSH2 as an alternative to SSL for making secure 
connections between python scripts. All major ciphers and hash methods 
are supported.  SFTP client and server mode are both supported too.

[http://www.lag.net/paramiko/]

hostlists (Apache License)
++++++++++++++++++++++++++

This is a python module for querying and managing lists of hosts from
various systems.

[https://github.com/yahoo/hostlists]
